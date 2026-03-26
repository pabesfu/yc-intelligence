#!/usr/bin/env python3
"""
Crawl 100% of YC companies from the last 5 years.
Sources: YC-OSS API (free, no auth) + Algolia API (for newer batches).
"""

import json
import urllib.request
import urllib.parse
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Config ---
YC_OSS_BASE = "https://yc-oss.github.io/api/batches"
ALGOLIA_URL = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/YCCompany_production/query"
ALGOLIA_APP_ID = "45BWZJ1SGC"
ALGOLIA_API_KEY = "NzllNTY5MzJiZGM2OTY2ZTQwMDEzOTNhYWZiZGRjODlhYzVkNjBmOGRjNzJiMWM4ZTU0ZDlhYTZjOTJiMjlhMWFuYWx5dGljc1RhZ3M9eWNkYyZyZXN0cmljdEluZGljZXM9WUNDb21wYW55X3Byb2R1Y3Rpb24lMkNZQ0NvbXBhbnlfQnlfTGF1bmNoX0RhdGVfcHJvZHVjdGlvbiZ0YWdGaWx0ZXJzPSU1QiUyMnljZGNfcHVibGljJTIyJTVE"

OUTPUT_FILE = "data/yc_wiki_master.json"

# Batches: last 5 years (2021-2026)
# YC-OSS has: w21, s21, w22, s22, w23, s23, w24, s24, f24, w25
# Algolia needed for: S25, F25, Spring 2025, W26
YC_OSS_BATCHES = ["w21", "s21", "w22", "s22", "w23", "s23", "w24", "s24", "f24", "w25"]

ALGOLIA_ONLY_BATCHES = {
    "S25": "Summer 2025",
    "F25": "Fall 2025",
    "Sp25": "Spring 2025",
    "W26": "Winter 2026",
}

BATCH_ORDER = ["W21", "S21", "W22", "S22", "W23", "S23", "W24", "S24", "F24", "W25", "Sp25", "S25", "F25", "W26"]

BATCH_DISPLAY = {
    "W21": "Winter 2021", "S21": "Summer 2021",
    "W22": "Winter 2022", "S22": "Summer 2022",
    "W23": "Winter 2023", "S23": "Summer 2023",
    "W24": "Winter 2024", "S24": "Summer 2024", "F24": "Fall 2024",
    "W25": "Winter 2025", "Sp25": "Spring 2025", "S25": "Summer 2025", "F25": "Fall 2025",
    "W26": "Winter 2026",
}

BATCH_YEAR = {
    "W21": 2021, "S21": 2021,
    "W22": 2022, "S22": 2022,
    "W23": 2023, "S23": 2023,
    "W24": 2024, "S24": 2024, "F24": 2024,
    "W25": 2025, "Sp25": 2025, "S25": 2025, "F25": 2025,
    "W26": 2026,
}


def fetch_url(url, headers=None, data=None):
    """Fetch URL with optional headers and POST data."""
    req = urllib.request.Request(url, headers=headers or {})
    if data:
        req.data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_company(raw, source="yc-oss"):
    """Normalize company data to a standard format."""
    if source == "yc-oss":
        return {
            "name": raw.get("name", ""),
            "slug": raw.get("slug", ""),
            "one_liner": raw.get("one_liner", ""),
            "long_description": raw.get("long_description", ""),
            "website": raw.get("website", ""),
            "yc_url": raw.get("url", ""),
            "batch": raw.get("batch", ""),
            "industry": raw.get("industry", ""),
            "subindustry": raw.get("subindustry", ""),
            "tags": raw.get("tags", []),
            "status": raw.get("status", ""),
            "stage": raw.get("stage", ""),
            "team_size": raw.get("team_size", 0),
            "location": raw.get("all_locations", ""),
            "regions": raw.get("regions", []),
            "industries": raw.get("industries", []),
            "logo": raw.get("small_logo_thumb_url", ""),
            "top_company": raw.get("top_company", False),
            "is_hiring": raw.get("isHiring", False),
            "nonprofit": raw.get("nonprofit", False),
            "founded_year": None,
            "launched_at": raw.get("launched_at"),
        }
    else:  # algolia
        return {
            "name": raw.get("name", ""),
            "slug": raw.get("slug", ""),
            "one_liner": raw.get("one_liner", ""),
            "long_description": raw.get("long_description", ""),
            "website": raw.get("website", ""),
            "yc_url": f"https://www.ycombinator.com/companies/{raw.get('slug', '')}",
            "batch": raw.get("batch", ""),
            "industry": raw.get("industry", ""),
            "subindustry": raw.get("subindustry", ""),
            "tags": raw.get("tags", []),
            "status": raw.get("status", ""),
            "stage": raw.get("stage", ""),
            "team_size": raw.get("team_size", 0),
            "location": raw.get("all_locations", ""),
            "regions": raw.get("regions", []),
            "industries": raw.get("industries", []),
            "logo": raw.get("small_logo_thumb_url", ""),
            "top_company": raw.get("top_company", False),
            "is_hiring": raw.get("isHiring", False),
            "nonprofit": raw.get("nonprofit", False),
            "founded_year": None,
            "launched_at": raw.get("launched_at"),
        }


def fetch_yc_oss_batch(batch_code):
    """Fetch a single batch from YC-OSS API."""
    url = f"{YC_OSS_BASE}/{batch_code}.json"
    print(f"  [YC-OSS] Fetching {batch_code.upper()}... ", end="", flush=True)
    try:
        raw = fetch_url(url)
        companies = [normalize_company(c, "yc-oss") for c in raw]
        print(f"{len(companies)} companies")
        return batch_code.upper() if len(batch_code) <= 3 else batch_code, companies
    except Exception as e:
        print(f"ERROR: {e}")
        return batch_code.upper(), []


def fetch_algolia_batch(short_code, full_name):
    """Fetch a single batch from Algolia API."""
    print(f"  [Algolia] Fetching {short_code} ({full_name})... ", end="", flush=True)
    headers = {
        "X-Algolia-Application-Id": ALGOLIA_APP_ID,
        "X-Algolia-API-Key": ALGOLIA_API_KEY,
    }
    all_hits = []
    page = 0
    while True:
        data = {
            "query": "",
            "hitsPerPage": 1000,
            "page": page,
            "facetFilters": [[f"batch:{full_name}"]],
        }
        try:
            resp = fetch_url(ALGOLIA_URL, headers=headers, data=data)
            hits = resp.get("hits", [])
            all_hits.extend(hits)
            if page >= resp.get("nbPages", 1) - 1:
                break
            page += 1
        except Exception as e:
            print(f"ERROR on page {page}: {e}")
            break

    companies = [normalize_company(c, "algolia") for c in all_hits]
    print(f"{len(companies)} companies")
    return short_code, companies


# Map YC-OSS batch codes to our normalized codes
YC_OSS_CODE_MAP = {
    "w21": "W21", "s21": "S21", "w22": "W22", "s22": "S22",
    "w23": "W23", "s23": "S23", "w24": "W24", "s24": "S24",
    "f24": "F24", "w25": "W25",
}


def main():
    print("=" * 60)
    print("YC WIKI CRAWLER - Last 5 Years (2021-2026)")
    print("=" * 60)

    all_companies = {}  # batch_code -> [companies]
    total = 0

    # Phase 1: YC-OSS (parallel)
    print("\n--- Phase 1: YC-OSS API (10 batches) ---")
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch_yc_oss_batch, b): b for b in YC_OSS_BATCHES}
        for f in as_completed(futures):
            code, companies = f.result()
            normalized_code = YC_OSS_CODE_MAP.get(code.lower(), code)
            all_companies[normalized_code] = companies
            total += len(companies)

    # Phase 2: Algolia (sequential to be safe with rate limits)
    print("\n--- Phase 2: Algolia API (4 newer batches) ---")
    for short_code, full_name in ALGOLIA_ONLY_BATCHES.items():
        code, companies = fetch_algolia_batch(short_code, full_name)
        all_companies[code] = companies
        total += len(companies)
        time.sleep(0.5)

    # Also fetch Algolia versions for YC-OSS batches to fill gaps
    # (some companies might be missing from YC-OSS)
    print("\n--- Phase 3: Algolia supplement for existing batches ---")
    algolia_supplement_map = {
        "W25": "Winter 2025",
        "S24": "Summer 2024",
        "F24": "Fall 2024",
        "W24": "Winter 2024",
    }
    for short_code, full_name in algolia_supplement_map.items():
        if short_code in all_companies:
            existing_slugs = {c["slug"] for c in all_companies[short_code]}
            _, algolia_companies = fetch_algolia_batch(short_code, full_name)
            new_count = 0
            for c in algolia_companies:
                if c["slug"] not in existing_slugs:
                    all_companies[short_code].append(c)
                    existing_slugs.add(c["slug"])
                    new_count += 1
                    total += 1
            if new_count:
                print(f"    +{new_count} new companies added to {short_code}")
            time.sleep(0.5)

    # Build output
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total} companies across {len(all_companies)} batches")
    print(f"{'=' * 60}")

    # Stats per batch
    batch_stats = []
    for code in BATCH_ORDER:
        if code in all_companies:
            count = len(all_companies[code])
            batch_stats.append({"batch": code, "display": BATCH_DISPLAY.get(code, code), "year": BATCH_YEAR.get(code), "count": count})
            print(f"  {BATCH_DISPLAY.get(code, code):20s} ({code}): {count:4d} companies")

    # Industry breakdown
    industry_counts = {}
    for batch_companies in all_companies.values():
        for c in batch_companies:
            ind = c.get("industry") or "Unknown"
            industry_counts[ind] = industry_counts.get(ind, 0) + 1

    top_industries = sorted(industry_counts.items(), key=lambda x: -x[1])[:20]
    print(f"\nTop Industries:")
    for ind, count in top_industries:
        print(f"  {ind:30s}: {count}")

    # Sort companies within each batch by name
    for code in all_companies:
        all_companies[code].sort(key=lambda c: c.get("name", "").lower())

    # Build final JSON
    output = {
        "metadata": {
            "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "total_companies": total,
            "total_batches": len(all_companies),
            "batch_order": [b for b in BATCH_ORDER if b in all_companies],
            "sources": ["YC-OSS GitHub API", "YC Algolia API"],
            "coverage": "2021-2026 (last 5 years)",
        },
        "batch_stats": batch_stats,
        "top_industries": [{"industry": ind, "count": count} for ind, count in top_industries],
        "batches": {code: all_companies[code] for code in BATCH_ORDER if code in all_companies},
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=1)

    file_size = len(json.dumps(output, ensure_ascii=False)) / (1024 * 1024)
    print(f"\nOutput: {OUTPUT_FILE} ({file_size:.1f} MB)")
    print("DONE!")


if __name__ == "__main__":
    main()
