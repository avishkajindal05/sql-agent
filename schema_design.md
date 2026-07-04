# Schema Design

Single-table schema for the orders database (`data/orders.db`).

## Table: `orders`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | |
| `customer_name` | TEXT | NOT NULL | |
| `product` | TEXT | NOT NULL | |
| `quantity` | INTEGER | NOT NULL | |
| `price` | REAL | NOT NULL | unit price in INR |
| `order_date` | TEXT | NOT NULL | ISO format: `YYYY-MM-DD` |
| `region` | TEXT | NOT NULL | one of North / South / East / West |

```
Table: orders
├── id            INTEGER PRIMARY KEY
├── customer_name TEXT NOT NULL
├── product       TEXT NOT NULL
├── quantity      INTEGER NOT NULL
├── price         REAL NOT NULL
├── order_date    TEXT NOT NULL   (ISO format: YYYY-MM-DD)
└── region        TEXT NOT NULL   (North / South / East / West)
```

## Demo questions this schema must support

| Question | Answerable? | How |
|---|---|---|
| Total revenue by region | ✅ | `SUM(quantity * price) GROUP BY region` |
| Orders in a given month | ✅ | `order_date LIKE 'YYYY-MM%'` (ISO dates make prefix matching work) |
| What a specific customer ordered | ✅ | filter on `customer_name` |
| Total revenue from one region | ✅ | `SUM(quantity * price) WHERE region = ?` |
| Best-selling product by quantity | ✅ | `SUM(quantity) GROUP BY product ORDER BY ... LIMIT 1` |

No extra columns needed — every planned demo question is answerable from the seven columns above.

## Design notes

- **Revenue is derived**, not stored: `quantity * price`. Avoids denormalized data going stale.
- **Dates as ISO-format TEXT**: SQLite has no native DATE type; ISO `YYYY-MM-DD` strings sort and prefix-match correctly.
- **Single table, no joins** in v1 — keeps the agent's SQL generation reliable and the ground truth easy to verify.
