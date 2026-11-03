"""
Collect CCOF directory member pages into a CSV.

Before running: check CCOF's terms of use / robots.txt, or ask CCOF for a
bulk export. This script is polite (delay, identifying User-Agent, resumable)
but it has NOT been tested against the live site; the parsing is based on the
layout of the member pages I viewed, so expect to adjust it.

Install:  pip install requests beautifulsoup4 lxml
Run:      python ccof_scraper.py --state California --out ccof_members.csv
"""
import argparse
import csv
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib import robotparser

import requests
from bs4 import BeautifulSoup

BASE = "https://ccof.org"
HEADERS = {"User-Agent": "cold-logistics-research/0.1 (contact: you@example.com)"}
DELAY = 1.5  # seconds between requests
SITEMAP_CANDIDATES = [
    f"{BASE}/sitemap_index.xml",   # Yoast
    f"{BASE}/wp-sitemap.xml",      # WordPress core
    f"{BASE}/sitemap.xml",
]
OVERVIEW_LABELS = ["Chapter", "Location", "Certification", "Crop",
                   "Product And Service", "Sales Method"]


def get(url, session):
    r = session.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    time.sleep(DELAY)
    return r.text


def sitemap_urls(url, session, seen=None):
    """Recursively walk sitemaps; yield every <loc>."""
    seen = seen or set()
    if url in seen:
        return
    seen.add(url)
    try:
        root = ET.fromstring(get(url, session))
    except Exception as e:
        print(f"  sitemap failed: {url} ({e})")
        return
    for loc in root.iter():
        if loc.tag.endswith("loc") and loc.text:
            u = loc.text.strip()
            if u.endswith(".xml"):
                yield from sitemap_urls(u, session, seen)
            else:
                yield u


def discover_member_urls(session):
    for sm in SITEMAP_CANDIDATES:
        urls = [u for u in sitemap_urls(sm, session)
                if "/directory-member/" in u and "/es/" not in u]
        if urls:
            print(f"Found {len(urls)} member URLs via {sm}")
            return sorted(set(urls))
    raise SystemExit("No member URLs found via sitemaps. Use the directory's "
                     "filters in a browser or ask CCOF for an export.")


def lines_of(soup):
    text = soup.get_text("\n")
    return [l.strip() for l in text.splitlines() if l.strip()]


def after_label(lines, label):
    """Value on the same line ('Phone: 555') or the next line."""
    for i, l in enumerate(lines):
        if l.lower().startswith(label.lower() + ":"):
            val = l.split(":", 1)[1].strip()
            if val:
                return val
            if i + 1 < len(lines):
                return lines[i + 1]
    return ""


def overview_block(lines, label):
    """Collect list items under 'Label:' in Member Overview until next label."""
    try:
        start = next(i for i, l in enumerate(lines) if l == "Member Overview")
    except StopIteration:
        return []
    out, collecting = [], False
    for l in lines[start + 1:]:
        name = l.rstrip(":")
        if l.endswith(":") and name in OVERVIEW_LABELS:
            collecting = (name == label)
            continue
        if l.endswith(":") and not collecting:
            continue
        if collecting:
            if l.endswith(":"):
                break
            out.append(l)
    return out


def parse_member(url, html):
    soup = BeautifulSoup(html, "lxml")
    lines = lines_of(soup)
    h1 = soup.find("h1")

    programs = []
    for i, l in enumerate(lines):
        if l.lower().startswith("certification:") and i + 2 < len(lines) \
                and lines[i + 1].lower().startswith("status:"):
            programs.append("{} | {} | {}".format(
                l.split(":", 1)[1].strip(),
                lines[i + 1].split(":", 1)[1].strip(),
                lines[i + 2].split(":", 1)[1].strip()
                if lines[i + 2].lower().startswith("date:") else ""))

    address = after_label(lines, "Address")
    m = re.search(r",\s*([^,]+),\s*([^,]+?)\s+(\d{5})(?:-\d{4})?,?\s*(\w+)?$",
                  address)
    row = {
        "url": url,
        "name": h1.get_text(strip=True) if h1 else "",
        "client_code": next((lines[i + 1] for i, l in enumerate(lines)
                             if l == "Client Code" and i + 1 < len(lines)), ""),
        "website": after_label(lines, "Website"),
        "contact_name": after_label(lines, "Contact Name"),
        "phone": after_label(lines, "Phone"),
        "address": address,
        "county": m.group(1).strip() if m else "",
        "state": m.group(2).strip() if m else "",
        "zip": m.group(3) if m else "",
        "programs": " ; ".join(programs),
        "acres": next((lines[i + 1] for i, l in enumerate(lines)
                       if l == "Acres" and i + 1 < len(lines)), ""),
    }
    for label in OVERVIEW_LABELS:
        row[label.lower().replace(" ", "_")] = " ; ".join(
            overview_block(lines, label))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="California",
                    help="keep only rows whose address contains this state "
                         "(use '' to keep all)")
    ap.add_argument("--out", default="ccof_members.csv")
    ap.add_argument("--limit", type=int, default=0, help="debug: first N pages")
    args = ap.parse_args()

    rp = robotparser.RobotFileParser(f"{BASE}/robots.txt")
    try:
        rp.read()
    except Exception:
        rp = None

    session = requests.Session()
    urls = discover_member_urls(session)
    if args.limit:
        urls = urls[:args.limit]

    out = Path(args.out)
    done = set()
    if out.exists():  # resume support
        with out.open(newline="", encoding="utf-8") as f:
            done = {r["url"] for r in csv.DictReader(f)}

    fields = ["url", "name", "client_code", "website", "contact_name", "phone",
              "address", "county", "state", "zip", "programs", "acres"] + \
             [l.lower().replace(" ", "_") for l in OVERVIEW_LABELS]
    new_file = not out.exists()
    with out.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        for n, url in enumerate(urls, 1):
            if url in done:
                continue
            if rp and not rp.can_fetch(HEADERS["User-Agent"], url):
                print(f"robots.txt disallows {url}; skipping")
                continue
            try:
                row = parse_member(url, get(url, session))
            except Exception as e:
                print(f"[{n}/{len(urls)}] FAILED {url}: {e}")
                continue
            if args.state and args.state.lower() not in row["address"].lower():
                continue
            w.writerow(row)
            f.flush()
            print(f"[{n}/{len(urls)}] {row['name']}")


if __name__ == "__main__":
    main()
