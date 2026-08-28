#!/usr/bin/env python3
"""Deterministic synthetic case generator for LedgerGuard.

Generates one reconciliation case: three system exports (orders / payments /
shipments), an FX table, and a hidden manifest holding the planted ground
truth. The true total is computed from the clean event stream BEFORE
corruption artifacts are written into the CSV views, so the oracle shares no
code path with any solution or baseline.

Stdlib only. Same (seed, size) always produces byte-identical output.

Usage:
    python3 eval/generate.py --seed 101 --orders 800 --month 2026-07 \
        --out eval/data/pilot/case_m800_s101
"""

import argparse
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

GENERATOR_VERSION = "1.0"
FX = {"USD": 1.0, "EUR": 1.09}  # fixed month rate written to fx_rates.csv

FIRST = ["ava", "noah", "mia", "liam", "zoe", "eli", "ivy", "max", "lea", "sam",
         "amir", "dana", "omar", "nina", "jack", "rosa", "hugo", "faye", "ben", "lucy"]
LAST = ["cohen", "smith", "garcia", "kim", "levi", "brown", "patel", "chen",
        "rossi", "novak", "silva", "weber", "jones", "mori", "khan", "diaz"]
CARRIERS = ["UPS", "FedEx", "USPS", "DHL"]


def money(x: float) -> float:
    return round(x + 1e-9, 2)


def usd(amount: float, currency: str) -> float:
    return money(amount * FX[currency])


def gen_case(seed: int, n_orders: int, month: str, out_dir: Path) -> dict:
    rng = random.Random(seed)
    year, mon = map(int, month.split("-"))
    month_start = datetime(year, mon, 1)
    next_month = datetime(year + (mon == 12), mon % 12 + 1, 1)
    days_in_month = (next_month - month_start).days

    def rand_dt(day_lo=1, day_hi=None, base=None):
        if base is not None:
            return base + timedelta(hours=rng.randint(1, 48), minutes=rng.randint(0, 59))
        day = rng.randint(day_lo, day_hi or days_in_month)
        return month_start + timedelta(days=day - 1, hours=rng.randint(6, 23),
                                       minutes=rng.randint(0, 59), seconds=rng.randint(0, 59))

    def email(is_test=False):
        if is_test:
            return f"qa+{rng.randint(100, 999)}@qa.internal"
        return f"{rng.choice(FIRST)}.{rng.choice(LAST)}{rng.randint(1, 99)}@example.com"

    # ---- clean event stream -------------------------------------------------
    orders, payments, shipments = [], [], []
    true_charges, true_refunds = [], []   # (usd_amount, payment_id)
    corruption_log = []
    n_test = max(2, n_orders // 150)
    n_loss = max(1, n_orders // 400)
    n_dup = max(2, n_orders // 300)
    n_cutoff = max(1, n_orders // 100)
    test_idx = set(rng.sample(range(n_orders), n_test))
    cutoff_pool = [i for i in range(n_orders) if i not in test_idx]
    cutoff_idx = set(rng.sample(cutoff_pool, n_cutoff))

    pay_seq = 0
    for i in range(n_orders):
        is_test = i in test_idx
        oid = f"ORD-{seed % 10000:04d}-{i:05d}"
        currency = "EUR" if rng.random() < 0.10 else "USD"
        big = rng.random() < 0.03
        total = money(rng.uniform(900, 3200)) if big else money(rng.uniform(15, 480))
        cust = email(is_test)
        digital = rng.random() < 0.15

        if i in cutoff_idx:
            # placed at month end, charged next month: order row only
            odate = rand_dt(day_lo=days_in_month - 1)
            orders.append([oid, odate.isoformat(sep=" "), cust, currency, f"{total:.2f}", "completed", "web"])
            continue

        r = rng.random()
        status_flow = ("cancelled" if r < 0.03 else
                       "retry" if r < 0.07 else
                       "pending" if r < 0.09 else "captured")
        odate = rand_dt(day_hi=days_in_month - 3)
        orders.append([oid, odate.isoformat(sep=" "), cust, currency, f"{total:.2f}",
                       "cancelled" if status_flow == "cancelled" else "completed", "web"])

        if status_flow == "cancelled":
            continue

        fee = money(total * 0.029 + 0.30)

        def add_payment(ptype, pstatus, amount, pdate, fee_amt):
            nonlocal pay_seq
            pay_seq += 1
            pid = f"PAY-{seed % 10000:04d}-{pay_seq:06d}"
            payments.append([pid, oid, pdate.isoformat(sep=" "), ptype, pstatus,
                             currency, f"{amount:.2f}", f"{fee_amt:.2f}", cust,
                             f"BATCH-{pdate.day:02d}{rng.randint(1, 4)}"])
            return pid

        if status_flow == "pending":
            add_payment("charge", "pending", total, rand_dt(base=odate), 0.0)
            continue

        if status_flow == "retry":
            add_payment("charge", "failed", total, rand_dt(base=odate), 0.0)
        cdate = rand_dt(base=odate)
        cpid = add_payment("charge", "captured", total, cdate, fee)
        if not is_test:
            true_charges.append((usd(total, currency), cpid))

        # refunds: 6% of captured, dated later in month
        if rng.random() < 0.06 and cdate.day <= days_in_month - 2:
            frac = 1.0 if rng.random() < 0.6 else rng.uniform(0.2, 0.8)
            ramt = money(total * frac)
            rdate = rand_dt(day_lo=min(cdate.day + 1, days_in_month), day_hi=days_in_month)
            rpid = add_payment("refund", "captured", ramt, rdate, 0.0)
            if not is_test:
                true_refunds.append((usd(ramt, currency), rpid))

        if not digital:
            sdate = rand_dt(base=cdate)
            n_ship = 2 if rng.random() < 0.08 else 1
            for k in range(n_ship):
                shipments.append([f"SHP-{seed % 10000:04d}-{pay_seq:06d}-{k}", oid,
                                  sdate.isoformat(sep=" "), rng.choice(CARRIERS),
                                  rng.choice(["shipped", "delivered"])])

    # ---- planted corruption artifacts --------------------------------------
    # 1. duplicate postings of captured charges (count-once per policy)
    captured_rows = [p for p in payments if p[3] == "charge" and p[4] == "captured"
                     and not p[8].endswith("@qa.internal")]
    for p in rng.sample(captured_rows, n_dup):
        pay_seq += 1
        dup_ts = (datetime.fromisoformat(p[2]) + timedelta(hours=rng.randint(1, 5))).isoformat(sep=" ")
        dup = [f"PAY-{seed % 10000:04d}-{pay_seq:06d}", p[1], dup_ts, "charge", "captured",
               p[5], p[6], p[7], p[8], f"BATCH-RP{rng.randint(1, 9)}"]
        payments.append(dup)
        corruption_log.append({
            "type": "duplicate_charge", "order_id": p[1],
            "payment_ids": [p[0], dup[0]],
            "naive_overstatement_usd": usd(float(p[6]), p[5]),
        })

    # 2. order-export data loss: drop order rows whose payments/shipments remain
    loss_candidates = [o for o in orders
                       if o[5] == "completed" and not o[2].endswith("@qa.internal")
                       and any(p[1] == o[0] and p[3] == "charge" and p[4] == "captured" for p in payments)
                       and any(s[1] == o[0] for s in shipments)]
    for o in rng.sample(loss_candidates, min(n_loss, len(loss_candidates))):
        orders.remove(o)
        pid = next(p[0] for p in payments if p[1] == o[0] and p[3] == "charge" and p[4] == "captured")
        corruption_log.append({
            "type": "order_row_dropped", "order_id": o[0], "payment_id": pid,
            "naive_understatement_usd_if_orphans_excluded": usd(float(o[4]), o[3]),
        })

    # bookkeeping entries for other planted reconciliation items
    corruption_log.extend([
        {"type": "test_transactions", "count": n_test,
         "naive_overstatement_usd": money(sum(
             usd(float(p[6]), p[5]) for p in payments
             if p[8].endswith("@qa.internal") and p[3] == "charge" and p[4] == "captured")
             - sum(usd(float(p[6]), p[5]) for p in payments
                   if p[8].endswith("@qa.internal") and p[3] == "refund"))},
        {"type": "noncaptured_rows_present",
         "count": sum(1 for p in payments if p[4] in ("failed", "pending")),
         "naive_overstatement_usd": money(sum(
             usd(float(p[6]), p[5]) for p in payments if p[4] in ("failed", "pending")))},
        {"type": "refund_sign_trap",
         "note": "refunds appear as positive gross_amount and must be subtracted",
         "count": sum(1 for p in payments if p[3] == "refund")},
        {"type": "orders_without_payment_timing", "count": len(cutoff_idx),
         "order_ids": sorted(f"ORD-{seed % 10000:04d}-{i:05d}" for i in cutoff_idx)},
    ])

    true_total = money(sum(a for a, _ in true_charges) - sum(a for a, _ in true_refunds))

    # ---- write files (stable order) ----------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    rng.shuffle(payments)  # exports are not conveniently ordered
    with open(out_dir / "orders.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "order_date", "customer_email", "currency", "order_total", "status", "channel"])
        w.writerows(orders)
    with open(out_dir / "payments.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["payment_id", "order_id", "payment_date", "type", "status",
                    "currency", "gross_amount", "fee_amount", "customer_email", "processor_batch"])
        w.writerows(payments)
    with open(out_dir / "shipments.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["shipment_id", "order_id", "ship_date", "carrier", "status"])
        w.writerows(shipments)
    with open(out_dir / "fx_rates.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["currency", "usd_rate", "month"])
        for cur, rate in FX.items():
            w.writerow([cur, rate, month])

    manifest = {
        "case_id": out_dir.name, "generator_version": GENERATOR_VERSION,
        "seed": seed, "n_orders": n_orders, "month": month,
        "true_total_usd": true_total,
        "n_countable_charges": len(true_charges),
        "n_countable_refunds": len(true_refunds),
        "corruption_log": corruption_log,
    }
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--orders", type=int, required=True)
    ap.add_argument("--month", default="2026-07")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    m = gen_case(args.seed, args.orders, args.month, Path(args.out))
    print(json.dumps({k: m[k] for k in ("case_id", "true_total_usd",
                                        "n_countable_charges", "n_countable_refunds")}, indent=1))


if __name__ == "__main__":
    main()
