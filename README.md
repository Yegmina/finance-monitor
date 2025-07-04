# Finance Monitor

A personal finance management web application for tracking income, spendings, and investments/savings with multi-level categorisation, analytics and an admin panel – all backed by simple JSON files.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup](#setup)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Roadmap](#roadmap)
- [License](#license)
- [Author](#author)

---

## Features

1. **Income, Spendings & Investments**  
   • Track one-time or regular income.  
   • Record spendings with multi-select sub-categories and optional sub-sub-categories.  
   • Mark transactions as *Invest / Saving* so they are treated positively in statistics.
2. **Dynamic Categorisation**  
   • Built-in defaults (Food, Transport, Crypto, etc.).  
   • Add new categories, sub-categories or sub-subs on-the-fly; suggestions learn from your input.
3. **Admin Panel**  
   • Manage (delete) income categories, spending categories, sub-categories and sub-sub-categories without touching JSON.
4. **Statistics & Analytics**  
   • Monthly or custom-range dashboard: totals, balance, top spending categories (investments excluded), per-category breakdown, top low-importance spendings, and more.
5. **Rich Metadata**  
   • Optional notes + importance slider (1–5) for every record.
6. **Responsive UI & Animations**  
   • Bootstrap 5 + animate.css – smooth fade-ins, clean design.
7. **100 % Local – no DB**  
   • Data stored in `data/*.json`; easy to back up or sync via cloud/VCS.

---

## Tech Stack

- **Backend**: Python 3, Flask
- **Frontend**: HTML, Bootstrap 5, JavaScript (jQuery)
- **Storage**: Local JSON files (`income.json`, `spendings.json`, `defaults.json`)

---

## Setup

### Prerequisites

* Python 3.9+  
* `pip` (comes with Python)  
* (Optional) virtual environment

### Installation

```bash
# 1. Clone
git clone https://github.com/Yegmina/finance-monitor.git
cd finance-monitor

# 2. (Optional) create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install deps
pip install -r requirements.txt

# 4. Run
python app.py
```

Open http://127.0.0.1:5000 and start tracking!  
Change host/port in `app.py` if you need LAN access or a custom port.

---

## Usage

1. **Add Income / Spending / Invest** via buttons on the dashboard.  
2. **Multi-select sub-categories** (Ctrl/Cmd-click) or type new ones (comma-separated).  
3. **Add notes & choose importance** (slider).  
4. **Admin** – manage categories from `/admin`.  
5. **Stats** – click *Stats* to analyse any month, year or custom date range.  
6. **Clear all** – wipe data (with confirmation) if you want a fresh start.

---

## File Structure

```text
.
├── app.py                 # Flask application
├── requirements.txt       # Python deps (Flask)
├── data/
│   ├── defaults.json      # Category trees & suggestions
│   ├── income.json        # Income records
│   └── spendings.json     # Spending / invest records
├── templates/             # Jinja2 templates
│   ├── index.html         # Dashboard
│   ├── add_income.html    # Add income form
│   ├── add_spending.html  # Add spending / invest form
│   ├── admin.html         # Admin panel
│   └── stats.html         # Statistics & analytics
└── README.md
```

---

## Roadmap / Future Enhancements

- Charts with Chart.js (trend lines, category pies).  
- CSV / Excel export & import.  
- Authentication for multi-user scenarios.  
- Mobile-first redesign.  
- Budget goals & alerts.

---

## License

Licensed under the MIT License – see [LICENSE](LICENSE) for details.

---

## Author

**Tereshchenko Yehor**  
[GitHub](https://github.com/Yegmina) | [LinkedIn](https://www.linkedin.com/in/yehor-tere/)
