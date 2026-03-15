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

COMPANIES, METADATA = load_companies()
INTELLIGENCE = load_intelligence()


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
