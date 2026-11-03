"""Classify manually reviewed, commodity-specific CAFF role evidence.

No text heuristics infer production. An accepted review asserts that the named reviewer
checked the cited source and its commodity-specific statement.
"""
import argparse
import csv
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = ['business_id', 'name', 'listing_url', 'address', 'state', 'zip', 'commodity',
          'listed_label', 'asserted_role', 'evidence_type', 'evidence_text',
          'evidence_url', 'checked_on', 'review_status']
ROLES = {'grower', 'seller', 'handler', 'processor', 'packer', 'distributor'}
EVIDENCE_TYPES = {'published_statement', 'certification_record', 'direct_confirmation'}
OUTPUT_FIELDS = ['business_id', 'name', 'listing_url', 'address', 'state', 'zip',
                 'commodity', 'listed_labels', 'roles', 'role_status', 'evidence', 'review_reasons']


def web_url(value):
    parsed = urlsplit(value)
    return parsed.scheme in {'http', 'https'} and bool(parsed.hostname) and not parsed.username and not parsed.password


def classify(rows):
    groups = {}
    for line, row in enumerate(rows, 2):
        missing = [key for key in FIELDS if key not in row]
        if missing:
            raise ValueError(f'Line {line}: missing columns {missing}')
        row = {key: (row[key] or '').strip() for key in FIELDS}
        if not row['business_id'] or not row['name'] or not row['commodity']:
            raise ValueError(f'Line {line}: business_id, name and commodity are required')
        key = (row['business_id'], row['commodity'].casefold())
        if key not in groups:
            groups[key] = dict(business_id=key[0], name=row['name'], listing_url=row['listing_url'],
                               address=row['address'], state=row['state'], zip=row['zip'], commodity=key[1],
                               listed_labels=[], roles=[], role_status='commodity_listed_role_unknown', evidence=[], review_reasons=[])
        result = groups[key]
        for field in ['name', 'listing_url', 'address', 'state', 'zip']:
            if result[field] != row[field]:
                raise ValueError(f'Line {line}: conflicting {field} for business/commodity; resolve before import')
        if row['listed_label'] and row['listed_label'] not in result['listed_labels']:
            result['listed_labels'].append(row['listed_label'])
        reason = None
        if row['review_status'] != 'accepted':
            reason = 'not_reviewed_and_accepted'
        elif row['asserted_role'] not in ROLES:
            reason = 'unsupported_or_unknown_role'
        elif row['evidence_type'] not in EVIDENCE_TYPES:
            reason = 'commodity_label_or_business_name_is_not_role_evidence'
        elif not row['evidence_text'] or not web_url(row['evidence_url']) or not web_url(row['listing_url']):
            reason = 'missing_statement_or_valid_source_url'
        else:
            try:
                checked = date.fromisoformat(row['checked_on'])
                if checked.isoformat() != row['checked_on'] or checked > date.today():
                    raise ValueError('future review')
            except ValueError:
                reason = 'invalid_or_future_review_date'
        result['evidence'].append(dict(row, eligibility='accepted' if reason is None else 'needs_review'))
        if reason:
            if reason not in result['review_reasons']:
                result['review_reasons'].append(reason)
        elif row['asserted_role'] not in result['roles']:
            result['roles'].append(row['asserted_role'])
    for record in groups.values():
        if record['roles']:
            record['role_status'] = 'supported_by_reviewed_evidence'
    return list(groups.values())


def read_evidence(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or set(FIELDS) - set(reader.fieldnames):
            raise ValueError('Evidence CSV must include all required header columns')
        return classify(reader)


def write_records(path, records):
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v for k,v in r.items()} for r in records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    records = read_evidence(args.input)
    args.out.mkdir(parents=True, exist_ok=True)
    write_records(args.out/'classifications.csv', records)
    write_records(args.out/'unknown_roles.csv', [r for r in records if not r['roles']])
    (args.out/'classifications.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
    print(json.dumps(dict(business_commodity_records=len(records), supported=sum(bool(r['roles']) for r in records), unknown=sum(not r['roles'] for r in records))))

if __name__ == '__main__':
    main()
