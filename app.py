import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import calendar

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

app = Flask(__name__)
app.secret_key = "super-secret-key"  # Replace for production

# Directory and file paths
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DEFAULTS_FILE = DATA_DIR / "defaults.json"
INCOME_FILE = DATA_DIR / "income.json"
SPEND_FILE = DATA_DIR / "spendings.json"

# ---------- Helper functions -------------------------------------------------

def load_json(path: Path, default):
    if not path.exists():
        save_json(path, default)
        return default
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)

def save_json(path: Path, obj):
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(obj, fp, indent=2, ensure_ascii=False)

# ----- Defaults handling -----------------------------------------------------

DEFAULT_DATA_TEMPLATE = {
    "categories": {
        "one_time": {
            "Food": ["Pizza", "Sushi", "Buffet", "Restaurant", "Cafe", "Market"],
            "Clothes": ["Shoes", "Jacket", "T-Shirt"],
            "Entertainment": ["Movies", "Airsoft", "Games"],
            "Transport": ["Taxi", "Bus ticket", "Fuel"],
        },
        "regular": {
            "Subscription": ["AI subscription", "Netflix", "Gym"],
            "Transport": ["Season ticket"],
            "Utilities": ["Electricity", "Internet"],
        },
        "invest": {
            "Crypto": ["Deposit to Bybit"],
            "AeroRozum": ["Self-funding"],
            "Saving": ["Long-time fiat saving", "Bank deposit"],
        },
    },
    "destinations": {
        "Pizza": ["Dominos", "Pizza Hut"],
        "Sushi": ["Sushibar", "Itsu"],
        "Market": ["K-Supermarket", "Lidl", "R-kioski"],
        "Taxi": ["Uber", "Bolt"],
        "Season ticket": ["HSL"],
    },
    "subsubcategories": {
        "HSL": [
            "Single", "Multi", "Day",
            "AB", "ABC", "ABCD", "BC", "BCD", "CD",
        ]
    },
    "income_categories": ["Salary", "Gift", "Award", "Sales"],
}

def load_defaults():
    data = load_json(DEFAULTS_FILE, DEFAULT_DATA_TEMPLATE)
    # migrate: ensure invest categories present
    if "invest" not in data["categories"]:
        data["categories"]["invest"] = DEFAULT_DATA_TEMPLATE["categories"]["invest"]
        save_defaults(data)
    return data

def save_defaults(data):
    save_json(DEFAULTS_FILE, data)

# ----- Income and Spending helpers ------------------------------------------

def load_income():
    data = load_json(INCOME_FILE, [])
    changed = False
    for rec in data:
        if "id" not in rec:
            rec["id"] = str(uuid4())
            changed = True
    if changed:
        save_income(data)
    return data

def save_income(income_list):
    save_json(INCOME_FILE, income_list)

def load_spendings():
    data = load_json(SPEND_FILE, [])
    changed = False
    for rec in data:
        if "id" not in rec:
            rec["id"] = str(uuid4())
            changed = True
    if changed:
        save_spendings(data)
    return data

def save_spendings(spend_list):
    save_json(SPEND_FILE, spend_list)

def add_category(data, spend_type, category, subcategory):
    cat_tree = data["categories"].setdefault(spend_type, {})
    sub_list = cat_tree.setdefault(category, [])
    if subcategory and subcategory not in sub_list:
        sub_list.append(subcategory)

# ---------- Routes -----------------------------------------------------------

@app.route("/")
def index():
    defaults = load_defaults()
    income = load_income()
    spendings = load_spendings()
    total_income = sum(item["amount"] for item in income)
    investings = [s for s in spendings if s["type"] == "invest"]
    expenditures = [s for s in spendings if s["type"] != "invest"]

    total_invest = sum(i["amount"] for i in investings)
    total_spendings = sum(s["amount"] for s in expenditures)
    balance = total_income - total_spendings
    return render_template(
        "index.html",
        income=income,
        spendings=spendings,
        total_income=total_income,
        total_spendings=total_spendings,
        total_invest=total_invest,
        balance=balance,
    )

# ---- Income -----------------------------------------------------------------

@app.route("/add_income", methods=["GET", "POST"])
def add_income():
    defaults = load_defaults()
    if request.method == "POST":
        income_type = request.form["income_type"]  # one_time or regular
        raw_new_cat = request.form.get("new_income_category", "").strip()
        category = raw_new_cat if raw_new_cat else request.form.get("income_category")
        amount = float(request.form["amount"])
        notes = request.form.get("notes", "").strip()
        importance = int(request.form.get("importance") or 3)
        date_str = request.form.get("date") or datetime.today().strftime("%Y-%m-%d")

        # store entry
        income = load_income()
        income.append({
            "id": str(uuid4()),
            "amount": amount,
            "date": date_str,
            "type": income_type,
            "category": category,
            "notes": notes,
            "importance": importance,
        })
        save_income(income)

        # update defaults for new category
        defaults = load_defaults()
        if category not in defaults.get("income_categories", []):
            defaults.setdefault("income_categories", []).append(category)
            save_defaults(defaults)

        flash("Income added.")
        return redirect(url_for("index"))
    return render_template("add_income.html", income_categories=defaults.get("income_categories", []))

# ---- Spendings --------------------------------------------------------------

@app.route("/add_spending", methods=["GET", "POST"])
def add_spending():
    defaults = load_defaults()
    if request.method == "POST":
        spend_type = request.form["spend_type"]  # one_time or regular
        raw_new_category = request.form.get("new_category", "").strip()
        category = raw_new_category if raw_new_category else request.form.get("category")

        # multiple subcategories allowed
        subcategories = [s.strip() for s in request.form.getlist("subcategory") if s.strip()]
        new_subcats_raw = request.form.get("new_subcategory", "")
        new_subcats = [s.strip() for s in new_subcats_raw.split(",") if s.strip()]

        subcategories.extend(new_subcats)

        if not subcategories:
            flash("Please select or add at least one subcategory.")
            return redirect(url_for("add_spending"))

        # if exactly one subcategory chosen we may get subsubcategory
        raw_new_subsub = request.form.get("new_subsubcategory", "").strip()
        subsubcategory = raw_new_subsub if raw_new_subsub else request.form.get("subsubcategory")

        destination = request.form["destination"]
        amount = float(request.form["amount"])
        notes = request.form.get("notes", "").strip()
        importance = int(request.form.get("importance") or 3)
        date_str = request.form.get("date") or datetime.today().strftime("%Y-%m-%d")

        # update db
        spending_entry = {
            "id": str(uuid4()),
            "type": spend_type,
            "category": category,
            "subcategories": subcategories,
            "subsubcategory": subsubcategory,
            "destination": destination,
            "amount": amount,
            "date": date_str,
            "notes": notes,
            "importance": importance,
        }
        spendings = load_spendings()
        spendings.append(spending_entry)
        for subcat in subcategories:
            add_category(defaults, spend_type, category, subcat)
        # subsubcategory maintenance
        if subsubcategory:
            defaults.setdefault("subsubcategories", {}).setdefault(subcategories[0], [])
            if subsubcategory not in defaults["subsubcategories"][subcategories[0]]:
                defaults["subsubcategories"][subcategories[0]].append(subsubcategory)
        first_subcat = subcategories[0]
        if destination not in defaults.get("destinations", {}).get(first_subcat, []):
            defaults.setdefault("destinations", {}).setdefault(first_subcat, []).append(destination)
        # save all
        save_spendings(spendings)
        save_defaults(defaults)
        flash("Spending added.")
        return redirect(url_for("index"))

    return render_template(
        "add_spending.html",
        categories=defaults["categories"],
    )

# ---- API --------------------------------------------------------------------

@app.route("/api/categories")
def api_categories():
    return jsonify(load_defaults()["categories"])

# destinations API
@app.route("/api/destinations/<subcategory>")
def api_destinations(subcategory):
    defaults = load_defaults()
    suggestions = defaults.get("destinations", {}).get(subcategory, [])
    return jsonify(suggestions)

# API for subsubcategories suggestions
@app.route("/api/subsub/<subcategory>")
def api_subsub(subcategory):
    defaults = load_defaults()
    return jsonify(defaults.get("subsubcategories", {}).get(subcategory, []))

# ---- Delete routes ----------------------------------------------------------

@app.route("/delete_income/<id>")
def delete_income(id):
    income = load_income()
    income = [rec for rec in income if rec.get("id") != id]
    save_income(income)
    flash("Income deleted.")
    return redirect(url_for("index"))

@app.route("/delete_spending/<id>")
def delete_spending(id):
    spendings = load_spendings()
    spendings = [rec for rec in spendings if rec.get("id") != id]
    save_spendings(spendings)
    flash("Spending deleted.")
    return redirect(url_for("index"))

@app.route("/clear_all", methods=["GET", "POST"])
def clear_all():
    if request.method == "POST":
        save_income([])
        save_spendings([])
        flash("All records cleared.")
        return redirect(url_for("index"))
    return (
        "<h2>Confirm clear all income and spending data?</h2>"
        '<form method="post"><button type="submit">Confirm</button></form>'
        '<a href="/">Cancel</a>'
    )

# ---- Manage categories ------------------------------------------------------

@app.route("/delete_income_category/<cat>")
def delete_income_category(cat):
    defaults = load_defaults()
    defaults["income_categories"] = [c for c in defaults.get("income_categories", []) if c != cat]
    save_defaults(defaults)
    flash("Income category removed.")
    return redirect(url_for("index"))

@app.route("/delete_category/<spend_type>/<category>")
def delete_category(spend_type, category):
    defaults = load_defaults()
    defaults["categories"].get(spend_type, {}).pop(category, None)
    save_defaults(defaults)
    flash("Category removed.")
    return redirect(url_for("index"))

@app.route("/delete_subcategory/<spend_type>/<category>/<subcat>")
def delete_subcategory(spend_type, category, subcat):
    defaults = load_defaults()
    cat_dict = defaults["categories"].get(spend_type, {}).get(category, [])
    if subcat in cat_dict:
        cat_dict.remove(subcat)
    save_defaults(defaults)
    flash("Subcategory removed.")
    return redirect(url_for("index"))

# ---- Admin page ------------------------------------------------------------

@app.route("/admin")
def admin():
    defaults = load_defaults()
    return render_template(
        "admin.html",
        categories=defaults["categories"],
        income_categories=defaults.get("income_categories", []),
        subsubs=defaults.get("subsubcategories", {}),
    )

# delete sub-subcategory
@app.route("/delete_subsub/<subcategory>/<subsub>")
def delete_subsub(subcategory, subsub):
    defaults = load_defaults()
    lst = defaults.get("subsubcategories", {}).get(subcategory, [])
    if subsub in lst:
        lst.remove(subsub)
        save_defaults(defaults)
        flash("Sub-subcategory removed.")
    return redirect(url_for("admin"))

# ---- Statistics ------------------------------------------------------------

def _filter_records_by_date(records, start_date, end_date):
    return [r for r in records if start_date <= datetime.strptime(r["date"], "%Y-%m-%d").date() <= end_date]

@app.route("/stats")
def stats():
    # date range params
    today = datetime.today().date()
    year_param = request.args.get("year")
    month_param = request.args.get("month")
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if start_str and end_str:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        current_year = start_date.year
    elif year_param and month_param:
        year = int(year_param)
        month = int(month_param)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, calendar.monthrange(year, month)[1]).date()
        current_year = year
    elif year_param:
        year = int(year_param)
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        current_year = year
    else:
        start_date = today.replace(day=1)
        end_date = today
        current_year = today.year

    income = _filter_records_by_date(load_income(), start_date, end_date)
    spendings = _filter_records_by_date(load_spendings(), start_date, end_date)

    total_income = sum(i["amount"] for i in income)
    investings = [s for s in spendings if s["type"] == "invest"]
    expenditures = [s for s in spendings if s["type"] != "invest"]

    total_invest = sum(i["amount"] for i in investings)
    total_spendings = sum(s["amount"] for s in expenditures)

    # category aggregation (exclude investments)
    category_totals = {}
    for s in expenditures:
        cat = s["category"]
        category_totals.setdefault(cat, 0)
        category_totals[cat] += s["amount"]

    top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    # per category details
    per_category = {}
    for s in spendings:
        per_category.setdefault(s["category"], []).append(s)

    # top non-important spendings (importance 1 or 2)
    non_imp = [s for s in spendings if s.get("importance", 3) <= 2]
    non_imp_sorted = sorted(non_imp, key=lambda x: x["amount"], reverse=True)[:10]

    months = [(m, calendar.month_name[m]) for m in range(1, 13)]

    return render_template(
        "stats.html",
        start_date=start_date,
        end_date=end_date,
        total_income=total_income,
        total_spendings=total_spendings,
        total_invest=total_invest,
        balance=total_income - total_spendings,
        top_categories=top_categories,
        per_category=per_category,
        non_imp=non_imp_sorted,
        months=months,
        current_year=current_year,
    )

# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True) 