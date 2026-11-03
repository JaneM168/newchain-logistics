"""Stage-constrained coffee and pecan business networks, with auditable roles."""
import argparse
import csv
import heapq
import json
from collections import Counter, defaultdict
from pathlib import Path
import geonamescache
from geo_utils import distance, normalize

STAGES = {'coffee': ['crop', 'green_processing', 'roasted', 'general_product'], 'pecan': ['crop', 'general_product']}
COLORS = {'crop': '#16803c', 'green_processing': '#c17a00', 'roasted': '#79503b', 'general_product': '#7555ca'}


def read_members(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        seen = set()
        for line, values in enumerate(reader, 2):
            if len(values) not in (17, 18):
                raise ValueError(f'Unexpected width at line {line}')
            row = dict(zip(header[:11], values[:11]))
            if row['url'] in seen:
                raise ValueError('Duplicate business URL')
            seen.add(row['url'])
            if len(values) == 18:
                row.update(acres=values[11], chapter=values[12], location=values[13], certification=values[14], crop_labels=values[15], product_service_labels=values[16], sales_methods=values[17], schema='18_fields_explicit_crops_products_sales', ambiguous_labels='')
            else:
                # The short rows have one populated commodity field and two blank
                # trailing fields: their source category cannot be recovered safely.
                row.update(chapter=values[11], location=values[12], certification=values[13], crop_labels='', product_service_labels='', sales_methods='', schema='17_fields_category_unverified', ambiguous_labels=' ; '.join(v for v in values[14:] if v))
            yield row


def labels(value):
    return {s.strip().casefold() for s in value.split(';') if s.strip()}


def roles(row, commodity):
    crops, products = labels(row['crop_labels']), labels(row['product_service_labels'])
    result = []
    if commodity == 'coffee':
        if 'coffee' in crops:
            result.append('crop')
        if products & {'coffee (green)', 'coffee processing'}:
            result.append('green_processing')
        if 'coffee (roasted)' in products:
            result.append('roasted')
        if 'coffee' in products:
            result.append('general_product')
    else:
        if crops & {'pecan', 'pecans'}:
            result.append('crop')
        if products & {'pecan', 'pecans'}:
            result.append('general_product')
    return result


def city_index():
    gc = geonamescache.GeonamesCache(min_city_population=500)
    index = defaultdict(dict)
    states = {normalize(v['name']): k for k, v in gc.get_us_states().items()}
    for city in gc.get_cities().values():
        if city['countrycode'] == 'US':
            for name in [city['name'], *city['alternatenames']]:
                index[(city['admin1code'], normalize(name))][city['geonameid']] = city
    return index, states


def locate(row, index, states):
    parts = [p.strip() for p in row['address'].split(',')]
    city = parts[-4] if len(parts) >= 5 else ''
    matches = list(index[(states.get(normalize(row['state']), row['state']), normalize(city))].values())
    if len(matches) != 1:
        return dict(latitude=None, longitude=None, location_precision='unresolved', location_reason='ambiguous_city' if matches else 'city_not_found', city=city)
    c = matches[0]
    return dict(latitude=c['latitude'], longitude=c['longitude'], city=city, location_precision='city_representative_point', location_source='GeoNames / geonamescache 3.0.1', geoname_id=c['geonameid'])


def stage_edges(nodes, stages, k):
    if k < 1:
        raise ValueError('K must be positive')
    edges, gaps = [], []
    for a, b in zip(stages, stages[1:]):
        sources = [n for n in nodes if a in n['roles']]
        targets = [n for n in nodes if b in n['roles']]
        located_targets = [n for n in targets if n['latitude'] is not None]
        for source in sources:
            eligible = [n for n in located_targets if n['id'] != source['id']]
            if source['latitude'] is None or not eligible:
                gaps.append(dict(source=source['id'], from_stage=a, to_stage=b, reason='source_unlocated' if source['latitude'] is None else 'no_other_located_target'))
                continue
            nearest = heapq.nsmallest(k, ((distance((source['latitude'], source['longitude']), (n['latitude'], n['longitude'])), n['id']) for n in eligible))
            for rank, (km, target) in enumerate(nearest, 1):
                edges.append(dict(source=source['id'], target=target, from_stage=a, to_stage=b, rank=rank, distance_km=km, distance_basis='haversine_between_city_points'))
        if not sources or not targets:
            gaps.append(dict(from_stage=a, to_stage=b, reason='missing_source_stage' if not sources else 'missing_target_stage'))
    return edges, gaps


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        fields = list(dict.fromkeys(k for row in rows for k in row)) or ['id']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k,v in row.items()} for row in rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, default=Path(__file__).resolve().parents[1] / 'ccof_members.csv')
    ap.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'visualizations')
    ap.add_argument('-k', type=int, default=5)
    args = ap.parse_args()
    if args.k < 1:
        ap.error('K must be positive')
    rows = list(read_members(args.input))
    index, states = city_index()
    bundle = dict(k=args.k, colors=COLORS, graphs={})
    args.out.mkdir(parents=True, exist_ok=True)
    for commodity, stages in STAGES.items():
        nodes, review = [], []
        for row in rows:
            assigned = roles(row, commodity)
            if assigned:
                nodes.append(dict(row, id=row['url'], roles=assigned, **locate(row,index,states)))
            elif commodity in (row['ambiguous_labels']+' '+row['product_service_labels']+' '+row['crop_labels']).casefold():
                review.append(dict(row, reason='category_unverified' if row['ambiguous_labels'] else 'related_label_outside_requested_stages'))
        edges, gaps = stage_edges(nodes, stages, args.k)
        graph = dict(commodity=commodity, stages=stages, nodes=nodes, edges=edges, gaps=gaps,
                     summary=dict(businesses=len(nodes), stage_counts=dict(Counter(s for n in nodes for s in n['roles'])), located=sum(n['latitude'] is not None for n in nodes), unresolved=sum(n['latitude'] is None for n in nodes), edges=len(edges), review=len(review)))
        bundle['graphs'][commodity] = graph
        (args.out/(commodity+'.json')).write_text(json.dumps(graph, indent=2, ensure_ascii=False))
        write_csv(args.out/(commodity+'_nodes.csv'), nodes)
        write_csv(args.out/(commodity+'_edges.csv'), edges)
        write_csv(args.out/(commodity+'_review.csv'), review)
    (args.out/'graphs.json').write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
    template = Path(__file__).with_name('commodity_view.html').read_text()
    # Escape script delimiters in untrusted directory text.
    (args.out/'network.html').write_text(template.replace('/*GRAPH_DATA*/', json.dumps(bundle, ensure_ascii=False).replace('<', '\\u003c')))
    print(json.dumps({c:g['summary'] for c,g in bundle['graphs'].items()}, indent=2))

if __name__ == '__main__':
    main()
