"""YC Batch Intelligence 2025 — Public standalone site."""
import json
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"

# Load startup data once at startup
def load_companies():
    path = DATA_DIR / "yc_2025_master_list.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("companies", []), data.get("metadata", {})
    return [], {}

def load_intelligence():
    path = DATA_DIR / "yc_intelligence.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def load_wiki_data():
    path = DATA_DIR / "yc_wiki_master.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"metadata": {}, "batches": {}, "batch_stats": [], "top_industries": []}

COMPANIES, METADATA = load_companies()
INTELLIGENCE = load_intelligence()
WIKI_DATA = load_wiki_data()

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
    "W21": 2021, "S21": 2021, "W22": 2022, "S22": 2022,
    "W23": 2023, "S23": 2023, "W24": 2024, "S24": 2024, "F24": 2024,
    "W25": 2025, "Sp25": 2025, "S25": 2025, "F25": 2025, "W26": 2026,
}


# --- HTML Routes ---

@app.route("/")
def index():
    """Landing page — YC Batch Intelligence 2025."""
    return render_template("index.html")


@app.route("/builder")
def builder():
    """YC Application Builder."""
    from sections_new import SECTIONS, GROUPS
    return render_template(
        "builder.html",
        sections_json=json.dumps(SECTIONS),
        groups_json=json.dumps(GROUPS),
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "companies": len(COMPANIES)})


# --- API Routes ---

@app.route("/api/companies")
def api_companies():
    """Search/filter companies. Params: q, batch, category, limit, offset."""
    q = (request.args.get("q") or "").lower()
    batch = request.args.get("batch")
    category = request.args.get("category")
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))

    results = COMPANIES
    if q:
        results = [c for c in results if q in (c.get("name", "") + " " + c.get("one_liner", "") + " " + c.get("category", "")).lower()]
    if batch:
        results = [c for c in results if c.get("batch") == batch]
    if category:
        cat_lower = category.lower()
        results = [c for c in results if cat_lower in (c.get("category", "")).lower() or any(cat_lower in t.lower() for t in c.get("categories", []))]

    total = len(results)
    results = results[offset:offset + limit]
    return jsonify({"total": total, "companies": results, "metadata": METADATA})


@app.route("/api/stats")
def api_stats():
    """Aggregate statistics."""
    batches = {}
    categories = {}
    for c in COMPANIES:
        b = c.get("batch", "Unknown")
        batches[b] = batches.get(b, 0) + 1
        cat = c.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    return jsonify({
        "total": len(COMPANIES),
        "batches": dict(sorted(batches.items())),
        "categories": dict(sorted(categories.items(), key=lambda x: -x[1])),
        "intelligence": INTELLIGENCE,
    })


@app.route("/api/company/<name>")
def api_company(name):
    """Get single company by name (slug match)."""
    name_lower = name.lower().replace("-", " ").replace("_", " ")
    for c in COMPANIES:
        if c.get("name", "").lower() == name_lower or c.get("slug", "").lower() == name_lower:
            return jsonify(c)
    return jsonify({"error": "Company not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5054, debug=True)
