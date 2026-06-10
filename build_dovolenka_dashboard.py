import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(".")
DESTINATION_CSV = ROOT / "dovolenka_jul_2025_destination_prices.csv"
HOTEL_CSV = ROOT / "dovolenka_jul_2025_hotel_candidates.csv"
AI_CSV = ROOT / "historical_all_inclusive_packages_july_2025.csv"
OUT_HTML = ROOT / "dovolenka_jul_2025_dashboard.html"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def as_int(value):
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def median(values):
    return round(statistics.median(values), 2) if values else None


def summarize_destinations(rows):
    grouped = defaultdict(list)
    labels = {}
    for row in rows:
        price = as_int(row["price_from_eur"])
        if price is None:
            continue
        slug = row["destination_slug"]
        grouped[slug].append(price)
        labels[slug] = row["destination"]

    result = []
    for slug, prices in grouped.items():
        result.append(
            {
                "slug": slug,
                "destination": labels[slug],
                "count": len(prices),
                "min": min(prices),
                "median": median(prices),
                "max": max(prices),
                "range": max(prices) - min(prices),
            }
        )
    return sorted(result, key=lambda item: item["median"])


def prepare_hotels(rows):
    result = []
    for row in rows:
        price = as_int(row["price_from_eur"])
        if price is None:
            continue
        is_beach = row["direct_beach_verified"].lower() == "true"
        is_4star = row["stars_verified"].lower() == "true"
        result.append(
            {
                "date": row["snapshot_date"],
                "destination": row["destination_slug"],
                "region": row["region_slug"],
                "hotel": row["hotel"],
                "price": price,
                "stars": row["stars"],
                "food": row["food"],
                "beach": row["beach"],
                "source": row["source_page"],
                "hotel_url": row["hotel_url"],
                "isBeach4Star": is_beach and is_4star,
                "isVerifiedAllInclusive": row["all_inclusive_verified"].lower() == "true",
                "isPoolVerified": row["pool_verified_in_archived_card"].lower() == "true",
            }
        )
    return sorted(result, key=lambda item: item["price"])


def prepare_ai_packages(rows):
    result = []
    for row in rows:
        price = as_int(row["price_per_person_eur"])
        nights = as_int(row["nights"])
        if price is None or nights is None:
            continue
        result.append(
            {
                "source": row["source"],
                "date": row["snapshot_date"],
                "destination": row["destination"],
                "region": row["region"],
                "hotel": row["hotel"],
                "checkIn": row["check_in"],
                "checkOut": row["check_out"],
                "nights": nights,
                "meal": row["meal"],
                "stars": row["stars"],
                "transport": row["transport"],
                "price": price,
                "perNight": round(price / nights, 2) if nights else None,
                "confidence": row["confidence"],
                "archive": row["archive_url"],
            }
        )
    return sorted(result, key=lambda item: item["price"])


def summarize_ai_packages(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["destination"]].append(row["price"])
    result = []
    for destination, prices in grouped.items():
        result.append(
            {
                "destination": destination,
                "count": len(prices),
                "min": min(prices),
                "median": median(prices),
                "max": max(prices),
            }
        )
    return sorted(result, key=lambda item: item["median"])


def build_html(destination_summary, hotel_rows, ai_packages, ai_summary):
    reference = {
        "label": "Júl 2026 referencia",
        "price": 1600,
        "nights": 7,
        "fullDays": 5,
        "stars": "5*",
        "food": "Ultra all inclusive",
        "beach": "hotelová pláž cca do 200 m",
        "perNight": round(1600 / 7, 2),
        "perFullDay": round(1600 / 5, 2),
    }

    beach_hotels = [row for row in hotel_rows if row["isBeach4Star"]]
    beach_prices = [row["price"] for row in beach_hotels]
    stats = {
        "destinationCount": len(destination_summary),
        "hotelCount": len(hotel_rows),
        "beachHotelCount": len(beach_hotels),
        "aiPackageCount": len(ai_packages),
        "aiDestinationCount": len(ai_summary),
        "beachMin": min(beach_prices) if beach_prices else None,
        "beachMedian": median(beach_prices),
        "beachMax": max(beach_prices) if beach_prices else None,
    }

    template = r'''<!doctype html>
<html lang="sk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dovolenka.SME.sk - júl 2025 vs referencia 2026</title>
  <style>
    :root {
      --bg: #f6f7f2;
      --panel: #ffffff;
      --ink: #18201b;
      --muted: #667166;
      --line: #dfe4da;
      --green: #1f7a5a;
      --blue: #2f6fb0;
      --gold: #ba7b19;
      --red: #b34848;
      --shadow: 0 18px 42px rgba(24, 32, 27, 0.09);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, Segoe UI, Roboto, Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      padding: 28px 32px 18px;
      border-bottom: 1px solid var(--line);
      background: #fff;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.1;
      letter-spacing: 0;
    }
    .subtitle {
      color: var(--muted);
      max-width: 980px;
      line-height: 1.45;
    }
    main { padding: 24px 32px 40px; }
    .controls {
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .control {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
    }
    label {
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
    }
    select, input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      min-height: 36px;
      padding: 6px 8px;
      color: var(--ink);
      background: #fff;
      font: inherit;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
      gap: 18px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 18px;
    }
    .panel h2 {
      margin: 0 0 4px;
      font-size: 18px;
      letter-spacing: 0;
    }
    .panel p {
      margin: 0 0 16px;
      color: var(--muted);
      line-height: 1.45;
    }
    .notice {
      margin: 12px 0 20px;
      padding: 12px 14px;
      border: 1px solid #ead7a7;
      border-left: 4px solid #c5891f;
      border-radius: 8px;
      background: #fff8e6;
      color: #5c4519;
      font-size: 14px;
      line-height: 1.45;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(5, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .kpi {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .kpi .value {
      font-size: 24px;
      font-weight: 750;
      margin-bottom: 3px;
    }
    .kpi .label {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .chart {
      display: grid;
      gap: 10px;
    }
    .bar-row {
      display: grid;
      grid-template-columns: 150px minmax(180px, 1fr) 70px;
      gap: 10px;
      align-items: center;
      min-height: 30px;
    }
    .bar-label {
      font-size: 13px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .bar-track {
      height: 18px;
      background: #eef1ea;
      border-radius: 5px;
      position: relative;
      overflow: hidden;
    }
    .bar {
      height: 100%;
      border-radius: 5px;
      background: var(--blue);
      min-width: 2px;
      transition: width .2s ease;
    }
    .bar.ref {
      background: var(--gold);
    }
    .bar-value {
      font-variant-numeric: tabular-nums;
      text-align: right;
      font-size: 13px;
    }
    .reference-card {
      border: 1px solid #ead6ad;
      background: #fff8e9;
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 14px;
    }
    .reference-card strong {
      display: block;
      font-size: 18px;
      margin-bottom: 8px;
    }
    .tagline {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }
    .tag {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 8px;
      font-size: 12px;
      color: var(--muted);
      background: #fff;
    }
    .insight {
      padding: 12px 0;
      border-top: 1px solid var(--line);
      line-height: 1.45;
    }
    .insight:first-of-type { border-top: 0; }
    .insight b { color: var(--ink); }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    th {
      color: var(--muted);
      font-size: 12px;
      cursor: pointer;
      user-select: none;
    }
    tbody tr:hover { background: #f8faf5; }
    .small-note {
      margin-top: 12px;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
    }
    .split {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin-top: 18px;
    }
    .empty {
      color: var(--muted);
      padding: 20px;
      text-align: center;
      border: 1px dashed var(--line);
      border-radius: 8px;
    }
    @media (max-width: 980px) {
      header, main { padding-left: 16px; padding-right: 16px; }
      .controls, .grid, .split, .kpis { grid-template-columns: 1fr; }
      .bar-row { grid-template-columns: 105px minmax(120px, 1fr) 62px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Last minute ceny: júl 2025 vs referenčná dovolenka 2026</h1>
    <div class="subtitle">Interaktívne porovnanie historických archívnych cien z Dovolenka.SME.sk. Prísny filter 4*+, AI/UAI, hotelová pláž a bazén sa z archívnych kariet nepodarilo kompletne potvrdiť, preto dashboard oddeľuje destinácie, neoverené hotelové karty pri pláži a referenciu 2026.</div>
  </header>
  <main>
    <div class="notice">
      Dôležité: hotelové riadky nižšie nie sú all-inclusive ceny. Archívne karty pri hoteloch uvádzali najlacnejší zachytený variant, často „Bez stravy“ alebo „Raňajky“. Použi ich iba ako orientačné minimum hotelov pri pláži; s referenciou 2026 ich neporovnávaj ako rovnocenné AI/UAI zájazdy.
    </div>
    <section class="kpis">
      <div class="kpi"><div class="value" id="kpiDestinations"></div><div class="label">destinácií v archívnom porovnaní</div></div>
      <div class="kpi"><div class="value" id="kpiHotels"></div><div class="label">extrahovaných hotelových kariet</div></div>
      <div class="kpi"><div class="value" id="kpiBeach"></div><div class="label">4*+ hotelových kariet s plážou 0 m</div></div>
      <div class="kpi"><div class="value" id="kpiAi"></div><div class="label">AI/UAI balíkov z Invia/Fischer archívov</div></div>
      <div class="kpi"><div class="value">1 600 €</div><div class="label">referencia júl 2026, 5*, UAI, 7 nocí</div></div>
    </section>

    <section class="controls">
      <div class="control">
        <label for="viewSelect">Zobrazenie</label>
        <select id="viewSelect">
          <option value="destination">Destinácie 2025: medián ceny od</option>
          <option value="ai">AI/UAI balíky 2025: cena za osobu</option>
          <option value="beach">Hotely 4*+ pri pláži 2025</option>
          <option value="comparison">Porovnanie s 2026 referenciou</option>
        </select>
      </div>
      <div class="control">
        <label for="destinationFilter">Destinácia hotelov</label>
        <select id="destinationFilter"></select>
      </div>
      <div class="control">
        <label for="maxPrice">Max cena</label>
        <input id="maxPrice" type="range" min="300" max="2600" value="2600" step="50">
        <div class="small-note" id="maxPriceLabel"></div>
      </div>
      <div class="control">
        <label for="searchInput">Hľadať hotel</label>
        <input id="searchInput" type="search" placeholder="napr. Rixos, Lara, Barut">
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2 id="chartTitle"></h2>
        <p id="chartSubtitle"></p>
        <div class="chart" id="chart"></div>
      </div>

      <aside class="panel">
        <div class="reference-card">
          <strong>Referencia 2026: 1 600 €</strong>
          <div>7 nocí: <b>228,57 €/noc</b></div>
          <div>5 plných dní: <b>320 €/deň</b></div>
          <div class="tagline">
            <span class="tag">5*</span>
            <span class="tag">Ultra all inclusive</span>
            <span class="tag">pláž cca do 200 m</span>
          </div>
        </div>
        <div class="insight" id="insightMain"></div>
        <div class="insight" id="insightSecond"></div>
        <div class="insight" id="insightThird"></div>
        <div class="small-note">Historické ceny sú archívne ceny “od”, pravdepodobne na osobu. Referencia 2026 je vložená ako porovnávací bod, nie ako historická ponuka.</div>
      </aside>
    </section>

    <section class="split">
      <div class="panel">
        <h2>Overené AI/UAI balíky z iných zdrojov</h2>
        <p>Historické júlové 2025 letové balíky z Invia.sk a Fischer.sk archívov. Cena je za osobu, nie dnešná dostupnosť.</p>
        <div id="aiTable"></div>
      </div>
      <div class="panel">
        <h2>Hotelové karty bez overenej AI/UAI ceny</h2>
        <p>Filtrované podľa ovládacích prvkov vyššie. Stĺpec Strava ukazuje, že tieto riadky nie sú all-inclusive varianty.</p>
        <div id="hotelTable"></div>
      </div>
      <div class="panel">
        <h2>Destinačný súhrn</h2>
        <p>Slabšie, ale širšie porovnanie cien “od” na úrovni destinácií.</p>
        <div id="destinationTable"></div>
      </div>
    </section>
  </main>

  <script>
    const destinationSummary = __DESTINATION_JSON__;
    const hotels = __HOTEL_JSON__;
    const aiPackages = __AI_JSON__;
    const aiSummary = __AI_SUMMARY_JSON__;
    const reference = __REFERENCE_JSON__;
    const stats = __STATS_JSON__;
    let hotelSort = { key: "price", direction: "asc" };

    const euro = new Intl.NumberFormat("sk-SK", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

    function percent(value, max) {
      return max ? Math.max(1, Math.round((value / max) * 100)) : 0;
    }

    function uniqueDestinations() {
      return [...new Set([...hotels.map(h => h.destination), ...aiPackages.map(p => p.destination)])].sort();
    }

    function populateFilters() {
      const select = document.getElementById("destinationFilter");
      select.innerHTML = '<option value="all">Všetky dostupné</option>' + uniqueDestinations().map(d => `<option value="${d}">${d}</option>`).join("");
      document.getElementById("kpiDestinations").textContent = stats.destinationCount;
      document.getElementById("kpiHotels").textContent = stats.hotelCount;
      document.getElementById("kpiBeach").textContent = stats.beachHotelCount;
      document.getElementById("kpiAi").textContent = stats.aiPackageCount;
    }

    function filteredHotels() {
      const dest = document.getElementById("destinationFilter").value;
      const maxPrice = Number(document.getElementById("maxPrice").value);
      const term = document.getElementById("searchInput").value.trim().toLowerCase();
      return hotels.filter(h => {
        if (dest !== "all" && h.destination !== dest) return false;
        if (h.price > maxPrice) return false;
        if (term && !h.hotel.toLowerCase().includes(term)) return false;
        return true;
      });
    }

    function filteredAiPackages() {
      const dest = document.getElementById("destinationFilter").value;
      const maxPrice = Number(document.getElementById("maxPrice").value);
      const term = document.getElementById("searchInput").value.trim().toLowerCase();
      return aiPackages.filter(p => {
        if (dest !== "all" && p.destination !== dest) return false;
        if (p.price > maxPrice) return false;
        if (term && !p.hotel.toLowerCase().includes(term)) return false;
        return true;
      });
    }

    function renderChart() {
      const view = document.getElementById("viewSelect").value;
      const chart = document.getElementById("chart");
      const title = document.getElementById("chartTitle");
      const subtitle = document.getElementById("chartSubtitle");
      chart.innerHTML = "";

      if (view === "destination") {
        title.textContent = "Destinácie: medián archívnej ceny “od”";
        subtitle.textContent = "Ceny sú z dvoch júlových snapshotov, bez hotelového overenia parametrov.";
        const max = Math.max(reference.price, ...destinationSummary.map(d => d.median));
        destinationSummary.forEach(d => chart.appendChild(barRow(d.destination, d.median, max, "bar", `${euro.format(d.min)} až ${euro.format(d.max)}`)));
        chart.appendChild(barRow(reference.label, reference.price, max, "bar ref", "vložený porovnávací bod"));
      }

      if (view === "ai") {
        title.textContent = "AI/UAI balíky: historická cena za osobu";
        subtitle.textContent = "Invia.sk a Fischer.sk, archivované júlové záznamy s odchodom v júli 2025. Cena je za osobu.";
        const rows = filteredAiPackages();
        const max = Math.max(reference.price, ...rows.map(p => p.price), 1);
        if (!rows.length) chart.innerHTML = '<div class="empty">Pre aktuálne filtre nie sú dostupné AI/UAI balíky.</div>';
        rows.forEach(p => chart.appendChild(barRow(p.hotel, p.price, max, "bar", `${p.destination}, ${p.meal}, ${p.nights} nocí, ${p.source}`)));
        chart.appendChild(barRow(reference.label, reference.price, max, "bar ref", "5*, UAI, 7 nocí, pláž do 200 m"));
      }

      if (view === "beach") {
        title.textContent = "Hotelové karty 4*+ pri pláži, bez AI/UAI ceny";
        subtitle.textContent = "Graf ukazuje lacné zachytené hotelové varianty. Nie sú to ceny s All inclusive/Ultra all inclusive.";
        const rows = filteredHotels().filter(h => h.isBeach4Star);
        const max = Math.max(reference.price, ...rows.map(h => h.price), 1);
        if (!rows.length) chart.innerHTML = '<div class="empty">Pre aktuálne filtre nie sú dostupné hotelové karty.</div>';
        rows.forEach(h => chart.appendChild(barRow(h.hotel, h.price, max, "bar", `${h.destination}, ${h.region}, ${h.stars}*, pláž ${h.beach}`)));
        chart.appendChild(barRow(reference.label, reference.price, max, "bar ref", "5*, UAI, pláž do 200 m"));
      }

      if (view === "comparison") {
        title.textContent = "Ako ďaleko je 1 600 € od historických cien";
        subtitle.textContent = "Porovnanie voči historickým AI/UAI balíkom z Invia.sk a Fischer.sk.";
        const rows = filteredAiPackages();
        const markers = [
          { label: "Min AI/UAI 2025", value: Math.min(...rows.map(p => p.price), reference.price) },
          { label: "Medián AI/UAI 2025", value: median(rows.map(p => p.price)) || 0 },
          { label: "Max AI/UAI 2025", value: Math.max(...rows.map(p => p.price), 0) },
          { label: reference.label, value: reference.price, ref: true },
          { label: "Cena na 7 nocí v 2026", value: reference.price, ref: true }
        ];
        const max = Math.max(...markers.map(m => m.value), 1);
        markers.forEach(m => chart.appendChild(barRow(m.label, m.value, max, m.ref ? "bar ref" : "bar", "")));
      }
    }

    function median(values) {
      const nums = values.filter(v => Number.isFinite(v)).sort((a, b) => a - b);
      if (!nums.length) return null;
      const mid = Math.floor(nums.length / 2);
      return nums.length % 2 ? nums[mid] : Math.round((nums[mid - 1] + nums[mid]) / 2);
    }

    function barRow(label, value, max, cls, detail) {
      const row = document.createElement("div");
      row.className = "bar-row";
      row.title = detail ? `${label}: ${euro.format(value)} (${detail})` : `${label}: ${euro.format(value)}`;
      row.innerHTML = `
        <div class="bar-label">${label}</div>
        <div class="bar-track"><div class="${cls}" style="width:${percent(value, max)}%"></div></div>
        <div class="bar-value">${euro.format(value)}</div>
      `;
      return row;
    }

    function renderInsights() {
      const aiRows = filteredAiPackages();
      const prices = aiRows.map(p => p.price);
      const med = median(prices);
      const min = prices.length ? Math.min(...prices) : null;
      const max = prices.length ? Math.max(...prices) : null;
      document.getElementById("insightMain").innerHTML = med
        ? `Referencia 2026 je <b>${euro.format(reference.price - med)}</b> oproti mediánu historických AI/UAI balíkov (${euro.format(med)}).`
        : "Pre aktuálny filter nie je dostupný AI/UAI medián.";
      document.getElementById("insightSecond").innerHTML = min
        ? `Rozpätie historických AI/UAI balíkov: <b>${euro.format(min)} až ${euro.format(max)}</b>.`
        : "Zmeň filter destinácie alebo cenu, ak chceš vidieť AI/UAI rozpätie.";
      document.getElementById("insightThird").innerHTML = `Prepočet referencie: <b>${euro.format(reference.perNight)}</b> za noc alebo <b>${euro.format(reference.perFullDay)}</b> za plný deň.`;
    }

    function renderAiTable() {
      const rows = filteredAiPackages();
      const target = document.getElementById("aiTable");
      if (!rows.length) {
        target.innerHTML = '<div class="empty">Žiadne AI/UAI balíky pre aktuálny filter.</div>';
        return;
      }
      target.innerHTML = `
        <table>
          <thead><tr><th>Hotel</th><th>Cena</th><th>€/noc</th><th>Noci</th><th>Strava</th><th>Dest.</th><th>Zdroj</th></tr></thead>
          <tbody>
            ${rows.map(p => `<tr>
              <td>${p.hotel}</td>
              <td>${euro.format(p.price)}</td>
              <td>${euro.format(p.perNight)}</td>
              <td>${p.nights}</td>
              <td>${p.meal}</td>
              <td>${p.destination}</td>
              <td><a href="${p.archive}" target="_blank" rel="noreferrer">${p.source.replace(" Wayback", "")}</a></td>
            </tr>`).join("")}
          </tbody>
        </table>
      `;
    }

    function renderHotelTable() {
      const rows = filteredHotels().slice().sort((a, b) => {
        const key = hotelSort.key;
        const av = a[key];
        const bv = b[key];
        const result = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv), "sk");
        return hotelSort.direction === "asc" ? result : -result;
      });
      const target = document.getElementById("hotelTable");
      if (!rows.length) {
        target.innerHTML = '<div class="empty">Žiadne hotely pre aktuálny filter.</div>';
        return;
      }
      target.innerHTML = `
        <table>
          <thead>
            <tr>
              <th data-key="hotel">Hotel</th>
              <th data-key="price">Cena</th>
              <th data-key="stars">Hviezdy</th>
              <th data-key="food">Strava</th>
              <th data-key="beach">Pláž</th>
              <th data-key="destination">Dest.</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(h => `<tr>
              <td>${h.hotel}</td>
              <td>${euro.format(h.price)}</td>
              <td>${h.stars}</td>
              <td>${h.food}</td>
              <td>${h.beach}</td>
              <td>${h.destination}</td>
            </tr>`).join("")}
          </tbody>
        </table>
      `;
      target.querySelectorAll("th").forEach(th => {
        th.addEventListener("click", () => {
          const key = th.dataset.key;
          hotelSort = {
            key,
            direction: hotelSort.key === key && hotelSort.direction === "asc" ? "desc" : "asc"
          };
          renderAll();
        });
      });
    }

    function renderDestinationTable() {
      const target = document.getElementById("destinationTable");
      target.innerHTML = `
        <table>
          <thead><tr><th>Destinácia</th><th>Min</th><th>Medián</th><th>Max</th></tr></thead>
          <tbody>
            ${destinationSummary.map(d => `<tr>
              <td>${d.destination}</td>
              <td>${euro.format(d.min)}</td>
              <td>${euro.format(d.median)}</td>
              <td>${euro.format(d.max)}</td>
            </tr>`).join("")}
          </tbody>
        </table>
      `;
    }

    function renderAll() {
      document.getElementById("maxPriceLabel").textContent = `do ${euro.format(Number(document.getElementById("maxPrice").value))}`;
      renderChart();
      renderInsights();
      renderAiTable();
      renderHotelTable();
      renderDestinationTable();
    }

    ["viewSelect", "destinationFilter", "maxPrice", "searchInput"].forEach(id => {
      document.getElementById(id).addEventListener("input", renderAll);
      document.getElementById(id).addEventListener("change", renderAll);
    });

    populateFilters();
    renderAll();
  </script>
</body>
</html>
'''

    return (
        template
        .replace("__DESTINATION_JSON__", json.dumps(destination_summary, ensure_ascii=False))
        .replace("__HOTEL_JSON__", json.dumps(hotel_rows, ensure_ascii=False))
        .replace("__AI_JSON__", json.dumps(ai_packages, ensure_ascii=False))
        .replace("__AI_SUMMARY_JSON__", json.dumps(ai_summary, ensure_ascii=False))
        .replace("__REFERENCE_JSON__", json.dumps(reference, ensure_ascii=False))
        .replace("__STATS_JSON__", json.dumps(stats, ensure_ascii=False))
    )


def main():
    destination_rows = read_csv(DESTINATION_CSV)
    hotel_rows = read_csv(HOTEL_CSV)
    ai_rows = read_csv(AI_CSV)
    destination_summary = summarize_destinations(destination_rows)
    hotels = prepare_hotels(hotel_rows)
    ai_packages = prepare_ai_packages(ai_rows)
    ai_summary = summarize_ai_packages(ai_packages)
    OUT_HTML.write_text(build_html(destination_summary, hotels, ai_packages, ai_summary), encoding="utf-8")
    print(f"created {OUT_HTML}")


if __name__ == "__main__":
    main()
