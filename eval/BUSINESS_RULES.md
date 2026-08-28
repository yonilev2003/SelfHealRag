# Meridian Goods Co. — Revenue Recognition & Reconciliation Policy (v1.0)

This policy defines how the monthly recognized revenue figure is computed from
the three system exports. It is the single source of truth for the monthly
close. Every arm of the evaluation (baseline and solution) receives this exact
document.

## Inputs

For a close month `M` you receive four files:

| File | Source system | Contents |
|---|---|---|
| `orders.csv` | Order management (storefront) | One row per order placed in month M |
| `payments.csv` | Payment processor | One row per payment event **dated in month M** (charges and refunds) |
| `shipments.csv` | Fulfillment | One row per shipment dispatched in month M |
| `fx_rates.csv` | Treasury | Fixed month-M conversion rate per currency to USD |

Exports are date-filtered independently by each system; the files are known to
contain occasional export artifacts (duplicate postings, dropped rows, test
traffic). Part of the close is detecting and correcting for these.

## Recognized revenue definition (cash basis)

**Recognized revenue for month M (USD)** =
sum of *countable charges* − sum of *countable refunds*, where amounts are the
**gross** payment amounts (processor fees are an expense, not contra-revenue),
converted to USD using `fx_rates.csv` (round each converted amount to cents;
round the final total to cents).

### Countable charge
A `payments.csv` row with `type = charge` that satisfies ALL of:

1. `status = captured`. (`failed` and `pending` rows are export noise — never
   counted.)
2. Not a **test transaction**: any payment or order whose `customer_email`
   ends in `@qa.internal` is internal QA traffic and is excluded entirely.
3. Not a **duplicate posting**: captured charge rows with the same
   `(order_id, gross_amount)` whose timestamps fall within 24 hours of each
   other are the same real-world charge double-posted by the processor —
   count it **once**.
4. **Orphan charges** (the `order_id` does not appear in `orders.csv`):
   - If the charge is a test transaction per rule 2 → exclude.
   - Otherwise → **count it**. The storefront's order export is known to drop
     rows occasionally; the payment processor is the system of record for
     cash. Corroborating evidence (e.g. a shipment for the same `order_id`)
     should be cited in the reconciliation report when available.

### Countable refund
A `payments.csv` row with `type = refund`, `status = captured`, not a test
transaction. Refund `gross_amount` is recorded as a **positive number** and
must be **subtracted**.

### Explicitly out of scope for the total
- Orders with no payment row in month M (e.g. placed at month end, charged in
  M+1): no cash captured in M → contribute $0. List them in the
  reconciliation report as timing items.
- Cancelled orders with no captured payment: $0.
- Shipment records never affect the revenue number; they are corroborating
  evidence only.

## Required output

The close deliverable is a reconciliation report containing:

1. `total_revenue_usd` — the recognized revenue for month M per this policy.
2. A discrepancy list: every export artifact or reconciliation item found
   (duplicate postings, excluded test traffic, excluded failed/pending rows,
   orphan charges counted, timing items), each with the row-level evidence
   (IDs) and its USD impact on a naive sum.

A close is acceptable when `total_revenue_usd` is within **0.5%** of the true
figure; the discrepancy list is what makes the number auditable.
