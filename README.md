# Essential Medicine Stock Optimisation — Ethiopia

**A SQL + Dashboard analytics pipeline flagging medicine stock-out risk across Ethiopian health facilities, built in Jupyter and visualized in Apache Superset (hosted via Preset), backed by a live Neon PostgreSQL database.**

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange)
![SQL](https://img.shields.io/badge/SQL-SQLite%20%2F%20PostgreSQL-lightgrey)
![Superset](https://img.shields.io/badge/Dashboard-Apache%20Superset-red)
![Status](https://img.shields.io/badge/status-complete-brightgreen)

🔗 **Live dashboard:** [ADD YOUR PRESET DASHBOARD URL HERE]
📓 **Notebooks:** [`/notebooks`](./notebooks)

---

## The Problem

Health facilities report medicine stock levels monthly. By the time a stock-out shows up in that data, the shortage has often already been happening for weeks. This project builds the data pipeline and dashboard needed to catch declining stock trends *before* they become a stock-out — turning raw monthly CSV exports into a live, queryable dashboard a Ministry health team could actually use.

**Dataset:** 50 facilities across 4 zones (Tigray, Amhara, Oromia, SNNPR), tracking 4 essential medicines (Oxytocin, Artemether-Lumefantrine, ORS/Zinc, Magnesium Sulphate) over 12 months — ~2,150 facility-medicine-month records.

---

## What This Demonstrates

- **SQL fluency** — writing and reasoning about `GROUP BY`, aggregate functions, and multi-column grouping against both an in-memory SQLite database and a live PostgreSQL instance
- **Dashboard engineering** — connecting Apache Superset to a real database and building charts backed by live SQL, not static exports
- **Cloud database integration** — provisioning and connecting to a serverless PostgreSQL instance (Neon), pushing data via SQLAlchemy
- **Data cleaning with pandas** — group-aware missing value imputation, derived business-rule columns
- **End-to-end pipeline thinking** — raw CSV → cleaned data → live database → dashboard, each stage reproducible from the notebooks

---

## Architecture

```
              ┌─────────────────┐
   raw CSVs → │  Jupyter/pandas │ → cleaned data + summary table
              └────────┬────────┘
                       │  SQLAlchemy (to_sql)
                       ▼
              ┌─────────────────┐
              │  Neon PostgreSQL │  ← serverless, hosted, internet-reachable
              └────────┬────────┘
                       │  SQL connection (SQLAlchemy URI)
                       ▼
              ┌─────────────────┐
              │  Apache Superset │  ← hosted via Preset
              │   (SQL Lab +     │
              │    dashboards)   │
              └─────────────────┘
```

A hosted dashboard tool (Preset/Superset) can't reach a database file sitting on a local machine — it needs a database at a real, internet-reachable address. Neon provides that: a free, serverless PostgreSQL instance both the notebook (to push data) and Superset (to read it) can independently connect to.

---

## Database Connection Details

### Local development (SQLite)
Used in the exploratory notebooks for quick, disk-free querying:
```python
import sqlite3
conn = sqlite3.connect(':memory:')   # RAM-only, no file created
facilities.to_sql('facilities', conn, index=False, if_exists='replace')
stock.to_sql('stock', conn, index=False, if_exists='replace')
```

### Production / dashboard-connected (Neon PostgreSQL)
1. Create a free project at [neon.tech](https://neon.tech) — this generates a connection string:
```
   postgresql://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require
```
2. Store it in a local `.env` file (never committed — see `.gitignore`):
```
   NEON_URL=postgresql://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require
```
3. Push cleaned data to it:
```python
   from sqlalchemy import create_engine
   from dotenv import load_dotenv
   import os

   load_dotenv()
   engine = create_engine(os.environ['NEON_URL'])

   summary.to_sql('summary', engine, index=False, if_exists='replace')
   stock.to_sql('stock', engine, index=False, if_exists='replace')
```
4. Connect Superset/Preset to the same database: **Data → Databases → + Database → PostgreSQL**, paste the same connection string, test, connect.

> **Note:** the connection string above is a template, not a live credential. If you're running this yourself, generate your own free Neon project and never commit your real `.env` file.

---

## Basic Project Structure

```
essential-medicine-stock-optimisation/
├── data/
│   ├── facilities.csv          # 50 rows: facility metadata
│   └── stock.csv                # ~2,150 rows: monthly stock records
├── notebooks/
│   ├── week1_explore.ipynb      # pandas basics + first SQL queries
│   ├── week2_clean.ipynb        # missing values, at-risk summary table
│   ├── week3_superset.ipynb     # Neon push + Superset dashboard build guide
│   └── week4_model.ipynb        # baseline regression model
├── .env                          # NEON_URL — not committed
├── .gitignore
└── requirements.txt
```

---

## Key SQL Used

```sql
-- Stock-out rate by medicine
SELECT medicine,
       COUNT(*)                        AS total_records,
       SUM(stockout)                   AS total_stockouts,
       ROUND(AVG(stockout) * 100, 1)   AS stockout_rate_pct
FROM stock
GROUP BY medicine
ORDER BY stockout_rate_pct DESC;

-- Average days of stock by zone and facility type
SELECT zone,
       facility_type,
       ROUND(AVG(days_of_stock), 1)  AS avg_days_of_stock,
       COUNT(DISTINCT facility_id)   AS num_facilities
FROM stock
GROUP BY zone, facility_type
ORDER BY avg_days_of_stock;
```

---

## The Dashboard

Three charts, built in Superset and connected live to the Neon database:

| Chart | Type | What it answers |
|---|---|---|
| Stock-out rate by medicine | Bar | Which medicines run out most often |
| Days of stock over time | Line | Is the system-wide buffer improving or declining |
| Facilities at risk | Table | Which specific facilities are currently below 30 days of stock |

**[ADD SCREENSHOT: full dashboard overview]**
```<img width="1358" height="591" alt="image" src="https://github.com/user-attachments/assets/d4bcd2db-c813-42de-87e9-ad1cb37beec9" />

<img width="1325" height="505" alt="image" src="https://github.com/user-attachments/assets/52be9e27-5c74-4ced-98af-82d22e6f257a" />

<img width="1342" height="558" alt="image" src="https://github.com/user-attachments/assets/560795a7-0ce8-4af6-a526-2eb5620a315b" />

<img width="958" height="409" alt="image" src="https://github.com/user-attachments/assets/c8bf863a-f033-4816-bf6c-fac0dff81b97" />

```

**[ADD SCREENSHOT: individual chart build in Superset's chart editor]**
```
![Chart builder](screenshots/chart-builder.png)
```

**[ADD SCREENSHOT: SQL Lab running a live query against Neon]**
```
<img width="1362" height="601" alt="image" src="https://github.com/user-attachments/assets/39a01050-5186-48ed-b783-da09092eaa6e" />


```

*(Drop your `.png` files into a `/screenshots` folder in the repo root — the markdown above will render them automatically once they're there.)*

---

## Running This Yourself

```bash
git clone https://github.com/<your-username>/essential-medicine-stock-optimisation.git
cd essential-medicine-stock-optimisation
pip install -r requirements.txt
jupyter notebook notebooks/
```
Run the notebooks in order (Week 1 → Week 4). Week 3 requires your own free [Neon](https://neon.tech) project and [Preset](https://preset.io) account — see *Database Connection Details* above.

---

## Findings

- No missing values in the raw data; cleaning focused on deriving the `at_risk` flag (`days_of_stock < 30`)
- Oromia had the lowest average days of stock (62.2 days) across zones
- A baseline linear regression predicting `days_of_stock` from facility type, zone, medicine, consumption, and lead time returned a low R² — a genuine finding, not a failure: five simple features aren't enough to explain stock-level variation well, which motivated the expanded model comparison work in [Part 2 of this project](#) *(link to your Streamlit repo here)*.

---

