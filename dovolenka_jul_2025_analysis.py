import csv
import gzip
import hashlib
import html
import json
import re
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path


SNAPSHOTS = [
    "20250710064927",
    "20250730145258",
]

HOTEL_SOURCE_PAGES = [
    ("20250710064927", "https://dovolenka.sme.sk/last-minute/turecko/antalya"),
    ("20250730145258", "https://dovolenka.sme.sk/last-minute/turecko"),
    ("20250730145258", "https://dovolenka.sme.sk/last-minute/grecko"),
    ("20250705124437", "https://dovolenka.sme.sk/last-minute/grecko/kos"),
    ("20250717222929", "https://dovolenka.sme.sk/last-minute/grecko/zakynthos/laganas"),
    ("20250717223046", "https://dovolenka.sme.sk/last-minute/grecko/zakynthos/tsilivi"),
]

EXCLUDED_SLUGS = {
    "tunisko",
    "egypt",
    "albansko",
    "cierna-hora",
    "čierna-hora",
}

PREFERRED_SLUGS = {"grecko", "turecko", "taliansko"}
MAX_REGION_PAGES_PER_DESTINATION = 8

OUT_DIR = Path(".")
CACHE_DIR = OUT_DIR / "wayback_cache"
DESTINATION_CSV = OUT_DIR / "dovolenka_jul_2025_destination_prices.csv"
HOTEL_CSV = OUT_DIR / "dovolenka_jul_2025_hotel_candidates.csv"
REPORT_MD = OUT_DIR / "dovolenka_jul_2025_report.md"


def fetch(url, attempts=3):
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / (hashlib.sha1(url.encode("utf-8")).hexdigest() + ".html")
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    last_error = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 historical-price-research",
                    "Accept-Encoding": "gzip, deflate",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            text = raw.decode("utf-8", "replace")
            if "Wayback Machine has not archived that URL" not in text:
                cache_path.write_text(text, encoding="utf-8")
            return text
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def archived_url(timestamp, original):
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def clean_text(value):
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_int(value):
    if not value:
        return None
    match = re.search(r"\d[\d\s]*", value)
    if not match:
        return None
    return int(match.group(0).replace(" ", ""))


def snapshot_date(timestamp):
    return datetime.strptime(timestamp[:8], "%Y%m%d").strftime("%Y-%m-%d")


def slug_from_last_minute_url(url):
    parsed = urllib.parse.urlparse(html.unescape(url))
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "last-minute":
        return parts[1]
    return ""


def path_from_last_minute_url(url):
    parsed = urllib.parse.urlparse(html.unescape(url))
    return parsed.path


def parse_destination_cards(timestamp):
    original = (
        "https://dovolenka.sme.sk/last-minute/regions"
        "?priority=100&custom_last_minute_page=last-minute"
    )
    source = archived_url(timestamp, original)
    text = fetch(source)
    rows = []
    for match in re.finditer(r'<a href="([^"]+)"[^>]*>\s*<div class="destination_card\b.*?</a>', text, re.S):
        block = match.group(0)
        href = html.unescape(match.group(1))
        slug = slug_from_last_minute_url(href)
        if not slug or slug in EXCLUDED_SLUGS:
            continue
        name_match = re.search(r'<div class="ellipsis">(.*?)</div>', block, re.S)
        price_match = re.search(r'<span class="price">([^<]+)</span>', block, re.S)
        name = clean_text(name_match.group(1)) if name_match else slug
        price = parse_int(price_match.group(1) if price_match else "")
        rows.append(
            {
                "snapshot": timestamp,
                "snapshot_date": snapshot_date(timestamp),
                "destination": name,
                "destination_slug": slug,
                "price_from_eur": price,
                "source_url": source,
                "priority": slug in PREFERRED_SLUGS,
            }
        )
    return rows


def discover_destination_and_region_pages(timestamp, destination_rows):
    pages = set()
    for row in destination_rows:
        slug = row["destination_slug"]
        if slug in PREFERRED_SLUGS:
            pages.add(f"https://dovolenka.sme.sk/last-minute/{slug}")

    # Add one level of region pages discovered from destination pages.
    by_destination = defaultdict(list)
    for original in list(pages):
        try:
            text = fetch(archived_url(timestamp, original))
        except RuntimeError:
            continue
        base_slug = slug_from_last_minute_url(original)
        for href in re.findall(r'href="(https://dovolenka\.sme\.sk/last-minute/[^"#?]+)"', text):
            path = path_from_last_minute_url(href)
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 3 and parts[0] == "last-minute" and parts[1] == base_slug:
                # Limit to country/region pages, not deeper hotel-detail-like noise.
                if len(parts) <= 3:
                    by_destination[base_slug].append(f"https://dovolenka.sme.sk{path}")

    for slug, region_pages in by_destination.items():
        for region_page in sorted(set(region_pages))[:MAX_REGION_PAGES_PER_DESTINATION]:
            pages.add(region_page)
    return sorted(pages)


def extract_footer_value(block, desc_label):
    for number, desc in re.findall(
        r'<div class="footer__number">\s*(.*?)\s*</div>\s*<div class="footer__desc">\s*(.*?)\s*</div>',
        block,
        re.S | re.I,
    ):
        if clean_text(desc).lower() == desc_label.lower():
            return clean_text(number)
    return ""


def parse_hotel_cards(timestamp, original_page, text):
    rows = []
    parts = re.split(
        r'<div class="col-lg-4 col-sm-6 d-flex product__card_holder-fix" itemscope itemtype="https://schema.org/Product">',
        text,
    )[1:]
    page_path = path_from_last_minute_url(original_page)
    page_parts = [p for p in page_path.split("/") if p]
    page_destination = page_parts[1] if len(page_parts) > 1 else ""
    page_region = page_parts[2] if len(page_parts) > 2 else ""

    for block in parts:
        block = block.split(
            '<div class="col-lg-4 col-sm-6 d-flex product__card_holder-fix"',
            1,
        )[0]
        if "/h/" not in block:
            continue

        link_match = re.search(r'href="(https://dovolenka\.sme\.sk/h/[^"]+)"', block)
        name_match = re.search(r'<h4 class="product__title"[^>]*>\s*<span>(.*?)</span>', block, re.S)
        img_match = re.search(r'<img[^>]+(?:alt|title)="([^"]+)"', block)
        price_match = re.search(r'itemprop="price" content="(\d+)"', block)
        if not link_match or not price_match:
            continue

        link = html.unescape(link_match.group(1))
        name = clean_text(name_match.group(1)) if name_match else clean_text(img_match.group(1) if img_match else "")
        price = int(price_match.group(1))
        star_match = re.search(r'star-rating rating-(\d)(?:\s+half)?', block)
        stars = int(star_match.group(1)) if star_match else None
        has_half_star = bool(star_match and "half" in star_match.group(0))
        food = extract_footer_value(block, "Strava")
        beach = extract_footer_value(block, "Pláž")
        airport = extract_footer_value(block, "Letisko")
        center = extract_footer_value(block, "Centrum")

        text_only = clean_text(block)
        all_inclusive_ok = food.lower() in {"all inclusive", "ultra all inclusive"}
        stars_ok = stars is not None and stars >= 4
        direct_beach_ok = beach == "0 m"
        pool_ok = any(term in text_only.lower() for term in ["bazén", "bazen", "pool"])

        verification_notes = []
        if stars_ok:
            verification_notes.append("4*+ v karte")
        if all_inclusive_ok:
            verification_notes.append("AI/UAI v karte")
        if direct_beach_ok:
            verification_notes.append("pláž 0 m v karte")
        if pool_ok:
            verification_notes.append("bazén v karte")

        fully_verified = stars_ok and all_inclusive_ok and direct_beach_ok and pool_ok
        partial_candidate = stars_ok and all_inclusive_ok and direct_beach_ok

        rows.append(
            {
                "snapshot": timestamp,
                "snapshot_date": snapshot_date(timestamp),
                "destination_slug": page_destination,
                "region_slug": page_region,
                "hotel": name,
                "price_from_eur": price,
                "stars": f"{stars}.5" if stars and has_half_star else (str(stars) if stars else ""),
                "food": food,
                "beach": beach,
                "airport": airport,
                "center": center,
                "pool_verified_in_archived_card": pool_ok,
                "direct_beach_verified": direct_beach_ok,
                "all_inclusive_verified": all_inclusive_ok,
                "stars_verified": stars_ok,
                "fully_verified": fully_verified,
                "partial_candidate_without_pool": partial_candidate and not fully_verified,
                "verification_notes": "; ".join(verification_notes),
                "source_page": archived_url(timestamp, original_page),
                "hotel_url": link,
            }
        )
    return rows


def dedupe_hotels(rows):
    best = {}
    for row in rows:
        key = (row["snapshot"], row["hotel"].lower(), row["destination_slug"], row["region_slug"])
        current = best.get(key)
        if current is None or row["price_from_eur"] < current["price_from_eur"]:
            best[key] = row
    return sorted(best.values(), key=lambda r: (r["snapshot"], r["destination_slug"], r["price_from_eur"], r["hotel"]))


def summary_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        if row.get("price_from_eur") is not None:
            grouped[row[key]].append(row["price_from_eur"])
    result = []
    for group, prices in sorted(grouped.items()):
        result.append(
            {
                key: group,
                "count": len(prices),
                "min": min(prices),
                "median": round(statistics.median(prices), 2),
                "max": max(prices),
            }
        )
    return result


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows, columns, limit=None):
    rows = rows[:limit] if limit else rows
    if not rows:
        return "_Žiadne riadky._"
    out = []
    out.append("| " + " | ".join(columns) + " |")
    out.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in rows:
        vals = []
        for col in columns:
            value = row.get(col, "")
            vals.append(str(value).replace("|", "\\|"))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def main():
    all_destination_rows = []
    all_hotel_rows = []
    fetch_errors = []

    for timestamp in SNAPSHOTS:
        all_destination_rows.extend(parse_destination_cards(timestamp))

    for timestamp, original_page in HOTEL_SOURCE_PAGES:
        slug = slug_from_last_minute_url(original_page)
        if slug in EXCLUDED_SLUGS:
            continue
        try:
            text = fetch(archived_url(timestamp, original_page), attempts=1)
        except RuntimeError as exc:
            fetch_errors.append({"snapshot": timestamp, "page": original_page, "error": str(exc)})
            continue
        all_hotel_rows.extend(parse_hotel_cards(timestamp, original_page, text))

    all_hotel_rows = dedupe_hotels(all_hotel_rows)
    fully_verified = [r for r in all_hotel_rows if r["fully_verified"]]
    partial_candidates = [r for r in all_hotel_rows if r["partial_candidate_without_pool"]]
    nearest_4star_beach = [
        r for r in all_hotel_rows
        if r["stars_verified"] and r["direct_beach_verified"] and not r["all_inclusive_verified"]
    ]
    destination_summary = summary_by(all_destination_rows, "destination")
    candidate_summary = summary_by(partial_candidates, "destination_slug")
    nearest_summary = summary_by(nearest_4star_beach, "destination_slug")

    write_csv(DESTINATION_CSV, all_destination_rows)
    write_csv(HOTEL_CSV, all_hotel_rows)

    report = []
    report.append("# Analýza cien last minute dovoleniek z júla 2025")
    report.append("")
    report.append("Zdrojom sú archívne zachytenia Dovolenka.SME.sk cez Internet Archive. Ceny sú historické zobrazené ceny `od` a nemusia znamenať dnešnú dostupnosť.")
    report.append("")
    report.append("## Metodika")
    report.append("")
    report.append("- Snapshoty pre destinácie: " + ", ".join(f"`{snapshot_date(ts)}` (`{ts}`)" for ts in SNAPSHOTS) + ".")
    report.append("- Hotelové stránky: " + ", ".join(f"`{snapshot_date(ts)}` {page}" for ts, page in HOTEL_SOURCE_PAGES) + ".")
    report.append("- Vynechané destinácie: Tunisko, Egypt, Albánsko, Čierna Hora.")
    report.append("- Hotel je plne overený iba vtedy, keď archívny zdroj priamo potvrdil 4*+, AI/UAI, pláž 0 m a bazén.")
    report.append("- Keď karta potvrdila 4*+, AI/UAI a pláž 0 m, ale nie bazén, hotel je uvedený len ako kandidát bez plného overenia.")
    report.append("")
    report.append("## Záver")
    report.append("")
    if fully_verified:
        report.append(f"Našli sa plne overené hotelové riadky: {len(fully_verified)}.")
    else:
        report.append("V dostupných júlových archívoch sa nenašiel žiadny hotelový riadok, ktorý by priamo v archívnom zdroji potvrdil všetky štyri kritériá vrátane bazéna.")
    report.append(f"Našlo sa {len(partial_candidates)} kandidátov, kde karta potvrdzuje 4*+, AI/UAI a pláž 0 m, ale bazén nie je v archívnej karte potvrdený.")
    report.append(f"Doplnkovo je v CSV {len(nearest_4star_beach)} hotelových kariet so 4*+ a plážou 0 m, ale bez archívne overenej AI/UAI stravy.")
    report.append("")
    report.append("## Kandidáti hotelov")
    candidate_cols = [
        "snapshot_date",
        "destination_slug",
        "region_slug",
        "hotel",
        "price_from_eur",
        "stars",
        "food",
        "beach",
        "verification_notes",
        "source_page",
    ]
    report.append(markdown_table(partial_candidates, candidate_cols, limit=80))
    report.append("")
    report.append("## Súhrn kandidátov podľa destinácie")
    report.append(markdown_table(candidate_summary, ["destination_slug", "count", "min", "median", "max"]))
    report.append("")
    report.append("## Doplnkové hotelové karty: 4*+ a pláž 0 m, bez overenej AI/UAI")
    report.append("")
    report.append("Tieto hotely nespĺňajú prísny filter, pretože archívna karta neuvádza All inclusive/Ultra all inclusive. Sú uvedené len ako orientačné cenové pásmo pre hotely pri pláži.")
    report.append("")
    nearest_cols = [
        "snapshot_date",
        "destination_slug",
        "region_slug",
        "hotel",
        "price_from_eur",
        "stars",
        "food",
        "beach",
        "source_page",
    ]
    report.append(markdown_table(nearest_4star_beach, nearest_cols, limit=80))
    report.append("")
    report.append("## Súhrn doplnkových hotelových kariet")
    report.append(markdown_table(nearest_summary, ["destination_slug", "count", "min", "median", "max"]))
    report.append("")
    report.append("## Slabšie ceny `od` podľa destinácie")
    report.append("Tieto riadky sú ceny na úrovni destinácie, nie hotelovo overené ceny.")
    report.append("")
    report.append(markdown_table(destination_summary, ["destination", "count", "min", "median", "max"]))
    report.append("")
    report.append("## Súbory")
    report.append("")
    report.append(f"- `{DESTINATION_CSV.name}`: ceny `od` na úrovni destinácií.")
    report.append(f"- `{HOTEL_CSV.name}`: všetky extrahované hotelové karty vrátane overovacích flagov.")
    report.append("")
    if fetch_errors:
        report.append("## Chyby pri načítaní")
        report.append("")
        report.append("Niektoré archívne URL nebolo možné načítať; tieto riadky neboli použité.")
        report.append("")
        report.append(markdown_table(fetch_errors, ["snapshot", "page", "error"], limit=20))

    REPORT_MD.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps({
        "destination_rows": len(all_destination_rows),
        "hotel_rows": len(all_hotel_rows),
        "fully_verified": len(fully_verified),
        "partial_candidates": len(partial_candidates),
        "nearest_4star_beach_without_ai": len(nearest_4star_beach),
        "destination_csv": str(DESTINATION_CSV),
        "hotel_csv": str(HOTEL_CSV),
        "report": str(REPORT_MD),
        "fetch_errors": len(fetch_errors),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
