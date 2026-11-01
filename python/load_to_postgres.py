import pandas as pd
from sqlalchemy import create_engine, text

# ── YOUR POSTGRESQL PASSWORD ──
PASSWORD = "your_password_here"  # Replace with your PostgreSQL password
# ─────────────────────────────

engine = create_engine(
    f'postgresql://postgres:{PASSWORD}@localhost:5432/supply_chain_db'
)

# Order matters — load parent tables before child tables
tables = [
    ('warehouses',      'data/warehouses.csv'),
    ('suppliers',       'data/suppliers.csv'),
    ('products',        'data/products.csv'),
    ('inventory',       'data/inventory.csv'),
    ('purchase_orders', 'data/purchase_orders.csv'),
    ('shipments',       'data/shipments.csv'),
]

with engine.connect() as conn:
    for table, filepath in tables:
        conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        conn.commit()
        df = pd.read_csv(filepath)
        df.to_sql(table, engine, if_exists='append', index=False)
        print(f"✓ Loaded {len(df):,} rows  →  {table}")

print("\n✓ All data loaded successfully!")