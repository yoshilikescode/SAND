"""
utils/generate_data.py
======================
Generates the synthetic data files used throughout this project.

Run this first before opening any notebook:
    python utils/generate_data.py

This creates two CSV files in the data/ folder:
    - facilities.csv   : one row per health facility
    - stock.csv        : one row per facility per medicine per month
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)

FACILITIES_COUNT = 50
MONTHS = 12  # one year of data

ZONES = ["Oromia", "Amhara", "SNNPR", "Tigray"]
FACILITY_TYPES = ["Health Post", "Health Centre", "Hospital"]
MEDICINES = ["Oxytocin", "ORS/Zinc", "Artemether-Lumefantrine", "Magnesium Sulphate"]


# ── Facilities ────────────────────────────────────────────────────────────────

def make_facilities():
    rows = []
    for i in range(FACILITIES_COUNT):
        ftype = rng.choice(FACILITY_TYPES, p=[0.4, 0.45, 0.15])
        rows.append({
            "facility_id":   f"ETH{i+1:03d}",
            "facility_name": f"Facility {i+1}",
            "facility_type": ftype,
            "zone":          rng.choice(ZONES),
            # Hospitals get longer lead times; health posts shorter
            "lead_time_days": int(rng.integers(7, 14) if ftype == "Health Post"
                                  else rng.integers(14, 30) if ftype == "Health Centre"
                                  else rng.integers(21, 45)),
        })
    return pd.DataFrame(rows)


# ── Stock records ─────────────────────────────────────────────────────────────

def make_stock(facilities: pd.DataFrame):
    rows = []
    months = pd.date_range("2024-01-01", periods=MONTHS, freq="MS")

    for _, fac in facilities.iterrows():
        base = {"Health Post": 20, "Health Centre": 80, "Hospital": 300}[fac["facility_type"]]

        # Convert lead time days to months for our monthly simulation step
        # E.g., 10 days -> 1 month. 35 days -> 2 months.
        lead_time_months = max(1, int(np.ceil(fac["lead_time_days"] / 30.0)))

        for medicine in MEDICINES:
            # Start with a healthy random stock level
            stock = float(rng.integers(int(base * 0.8), int(base * 2.0)))

            # Dictionary to track arriving orders: {arrival_month_index: quantity}
            pending_orders = {}

            for month_idx, month in enumerate(months):

                # 1. Receive incoming shipments scheduled for this month
                received_this_month = pending_orders.pop(month_idx, 0)
                stock += received_this_month

                # 2. Determine patient demand (with malaria seasonality)
                seasonal = 1.5 if (medicine == "Artemether-Lumefantrine"
                                   and month.month in [6, 7, 8, 9]) else 1.0
                demand = max(1, int(rng.poisson(base * 0.3 * seasonal)))

                # 3. Actual consumption (Cannot dispense more than what's in stock!)
                consumption = min(int(stock), demand)

                # 4. Update stock
                stock -= consumption

                # 5. Determine flags and metrics
                is_stockout = 1 if stock == 0 else 0
                days_of_stock = round((stock / consumption) * 30, 1) if consumption > 0 else 0.0

                # 6. Inventory Control: Reorder if total pipeline stock is low
                pipeline_stock = stock + sum(pending_orders.values())
                reorder_point = base * 0.5

                if pipeline_stock < reorder_point:
                    order_qty = int((base * 1.5) - pipeline_stock)
                    order_qty = max(order_qty, int(base * 0.5))

                    # --- REALISM INJECTION FOR ETHIOPIA ---
                    # 1. EPSA/Supplier Stockout: 25% chance the central supplier cannot fulfill the order at all this month
                    supplier_has_stock = rng.random() > 0.25

                    if supplier_has_stock:
                        # 2. Partial Fulfillment: If they have stock, they often only send 50% to 100% of what was asked
                        fulfilled_qty = int(order_qty * rng.uniform(0.5, 1.0))

                        # 3. Transportation Delays: 20% chance the truck is delayed by an extra month
                        extra_delay = 1 if rng.random() < 0.20 else 0
                        arrival_month_idx = month_idx + lead_time_months + extra_delay

                        pending_orders[arrival_month_idx] = pending_orders.get(arrival_month_idx, 0) + fulfilled_qty
                # 7. Simulated Reporting System Failure (Missing Data)
                # We do this AFTER the simulation steps so the "physics" of the supply chain
                # keep running, even if the facility forgets to submit their paperwork.
                if rng.random() < 0.10:
                    continue

                rows.append({
                    "facility_id":    fac["facility_id"],
                    "facility_type":  fac["facility_type"],
                    "zone":           fac["zone"],
                    "lead_time_days": fac["lead_time_days"],
                    "medicine":       medicine,
                    "month":          month.strftime("%Y-%m"),
                    "stock_on_hand":  round(stock, 0),
                    "consumption":    consumption,
                    "resupply":       received_this_month, # Accurately logs when stock physically arrived
                    "days_of_stock":  min(days_of_stock, 180),
                    "stockout":       is_stockout,         # Mathematically flawless now
                })

    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out = Path("data")
    out.mkdir(exist_ok=True)

    print("Generating facilities...")
    facilities = make_facilities()
    facilities.to_csv(out / "facilities.csv", index=False)
    print(f"  ✓ {len(facilities)} facilities → data/facilities.csv")

    print("Generating stock records...")
    stock = make_stock(facilities)
    stock.to_csv(out / "stock.csv", index=False)
    print(f"  ✓ {len(stock):,} records → data/stock.csv")

    stockout_rate = stock["stockout"].mean() * 100
    completeness  = len(stock) / (FACILITIES_COUNT * MONTHS * len(MEDICINES)) * 100
    print(f"\nQuick check:")
    print(f"  Stock-out rate     : {stockout_rate:.1f}%")
    print(f"  Reporting coverage : {completeness:.1f}%")
    print("\nDone! Open notebooks/week1_explore.ipynb to get started.")