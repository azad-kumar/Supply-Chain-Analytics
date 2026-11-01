import pandas as pd
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# ── YOUR POSTGRESQL PASSWORD ──
PASSWORD = "your_password_here"  # Replace with your PostgreSQL password
# ─────────────────────────────

engine = create_engine(
    f'postgresql://postgres:{PASSWORD}@localhost:5432/supply_chain_db'
)

print("Running supply chain analysis...\n")

# ─────────────────────────────────────────
# 1. INVENTORY HEALTH SUMMARY
# ─────────────────────────────────────────
inventory_health = pd.read_sql("""
    SELECT
        stock_status,
        COUNT(*)                                     AS product_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*))
              OVER(), 1)                             AS percentage,
        ROUND(AVG(current_stock)::NUMERIC, 0)        AS avg_stock,
        ROUND(AVG(days_of_supply)::NUMERIC, 1)       AS avg_days_of_supply
    FROM inventory
    GROUP BY stock_status
    ORDER BY product_count DESC
""", engine)
print(f"✓ Inventory health summary")

# ─────────────────────────────────────────
# 2. WAREHOUSE UTILIZATION
# ─────────────────────────────────────────
warehouse_util = pd.read_sql("""
    SELECT
        w.warehouse_name,
        w.city,
        w.capacity_units,
        w.used_units,
        w.utilization_pct,
        CASE
            WHEN w.utilization_pct >= 90 THEN 'Critical'
            WHEN w.utilization_pct >= 75 THEN 'High'
            WHEN w.utilization_pct >= 50 THEN 'Medium'
            ELSE 'Low'
        END                                          AS utilization_level,
        COUNT(DISTINCT i.product_id)                 AS products_stored
    FROM warehouses w
    LEFT JOIN inventory i ON w.warehouse_id = i.warehouse_id
    GROUP BY w.warehouse_id, w.warehouse_name, w.city,
             w.capacity_units, w.used_units, w.utilization_pct
    ORDER BY w.utilization_pct DESC
""", engine)
print(f"✓ Warehouse utilization")

# ─────────────────────────────────────────
# 3. SUPPLIER PERFORMANCE
# ─────────────────────────────────────────
supplier_performance = pd.read_sql("""
    SELECT
        s.supplier_name,
        s.country,
        s.category,
        s.reliability_score,
        s.defect_rate_pct,
        COUNT(po.po_id)                              AS total_orders,
        ROUND(AVG(po.lead_time_days)::NUMERIC, 1)    AS avg_lead_days,
        ROUND(AVG(po.delay_days)::NUMERIC, 1)        AS avg_delay_days,
        ROUND(SUM(po.total_cost)::NUMERIC, 2)        AS total_order_value,
        SUM(CASE WHEN po.status = 'Delivered'
                 AND po.delay_days = 0 THEN 1 ELSE 0 END) AS on_time_deliveries,
        ROUND(
            SUM(CASE WHEN po.status = 'Delivered'
                     AND po.delay_days = 0 THEN 1 ELSE 0 END)
            * 100.0 / NULLIF(COUNT(po.po_id), 0), 1
        )                                            AS on_time_pct
    FROM suppliers s
    LEFT JOIN purchase_orders po ON s.supplier_id = po.supplier_id
    GROUP BY s.supplier_id, s.supplier_name, s.country,
             s.category, s.reliability_score, s.defect_rate_pct
    ORDER BY on_time_pct DESC
    LIMIT 20
""", engine)
print(f"✓ Supplier performance: top 20")

# ─────────────────────────────────────────
# 4. MONTHLY PURCHASE ORDER TRENDS
# ─────────────────────────────────────────
po_trends = pd.read_sql("""
    SELECT
        TO_CHAR(order_date, 'YYYY-MM')               AS month,
        COUNT(*)                                     AS total_orders,
        ROUND(SUM(total_cost)::NUMERIC, 2)           AS total_spend,
        ROUND(AVG(lead_time_days)::NUMERIC, 1)       AS avg_lead_time,
        ROUND(AVG(delay_days)::NUMERIC, 1)           AS avg_delay,
        SUM(CASE WHEN status = 'Delivered'
                 AND delay_days = 0 THEN 1 ELSE 0 END) AS on_time_count,
        ROUND(
            SUM(CASE WHEN status = 'Delivered'
                     AND delay_days = 0 THEN 1 ELSE 0 END)
            * 100.0 / NULLIF(COUNT(*), 0), 1
        )                                            AS on_time_pct
    FROM purchase_orders
    GROUP BY TO_CHAR(order_date, 'YYYY-MM')
    ORDER BY month
""", engine)
print(f"✓ Monthly PO trends: {len(po_trends)} months")

# ─────────────────────────────────────────
# 5. CARRIER PERFORMANCE
# ─────────────────────────────────────────
carrier_performance = pd.read_sql("""
    SELECT
        carrier,
        COUNT(*)                                     AS total_shipments,
        ROUND(AVG(delay_days)::NUMERIC, 1)           AS avg_delay_days,
        ROUND(SUM(on_time) * 100.0
              / NULLIF(COUNT(*), 0), 1)              AS on_time_pct,
        ROUND(AVG(shipping_cost)::NUMERIC, 2)        AS avg_shipping_cost,
        ROUND(SUM(shipping_cost)::NUMERIC, 2)        AS total_shipping_cost
    FROM shipments
    GROUP BY carrier
    ORDER BY on_time_pct DESC
""", engine)
print(f"✓ Carrier performance: {len(carrier_performance)} carriers")

# ─────────────────────────────────────────
# 6. CATEGORY LEVEL INVENTORY ANALYSIS
# ─────────────────────────────────────────
category_inventory = pd.read_sql("""
    SELECT
        p.category,
        COUNT(DISTINCT p.product_id)                 AS total_products,
        SUM(i.current_stock)                         AS total_stock,
        ROUND(AVG(i.current_stock)::NUMERIC, 0)      AS avg_stock_per_product,
        SUM(CASE WHEN i.stock_status = 'Out of Stock'
                 THEN 1 ELSE 0 END)                  AS out_of_stock_count,
        SUM(CASE WHEN i.stock_status = 'Low Stock'
                 THEN 1 ELSE 0 END)                  AS low_stock_count,
        SUM(CASE WHEN i.stock_status = 'Overstock'
                 THEN 1 ELSE 0 END)                  AS overstock_count,
        ROUND(AVG(i.days_of_supply)::NUMERIC, 1)     AS avg_days_of_supply
    FROM products p
    JOIN inventory i ON p.product_id = i.product_id
    GROUP BY p.category
    ORDER BY out_of_stock_count DESC
""", engine)
print(f"✓ Category inventory analysis")

# ─────────────────────────────────────────
# 7. SHIPMENT DELAY ANALYSIS
# ─────────────────────────────────────────
delay_analysis = pd.read_sql("""
    SELECT
        CASE
            WHEN delay_days = 0          THEN 'On Time'
            WHEN delay_days BETWEEN 1 AND 3  THEN '1-3 Days Late'
            WHEN delay_days BETWEEN 4 AND 7  THEN '4-7 Days Late'
            WHEN delay_days > 7          THEN '7+ Days Late'
        END                                          AS delay_bucket,
        COUNT(*)                                     AS shipment_count,
        ROUND(COUNT(*) * 100.0
              / SUM(COUNT(*)) OVER(), 1)             AS percentage,
        ROUND(AVG(shipping_cost)::NUMERIC, 2)        AS avg_shipping_cost
    FROM shipments
    GROUP BY delay_bucket
    ORDER BY shipment_count DESC
""", engine)
print(f"✓ Shipment delay analysis")

# ─────────────────────────────────────────
# 8. TOP 10 PRODUCTS BY REORDER URGENCY
# ─────────────────────────────────────────
reorder_urgency = pd.read_sql("""
    SELECT
        p.product_name,
        p.category,
        i.current_stock,
        i.reorder_point,
        i.reorder_quantity,
        i.stock_status,
        i.days_of_supply,
        ROUND((i.reorder_point - i.current_stock)::NUMERIC, 0) AS stock_gap,
        s.supplier_name,
        s.avg_lead_days
    FROM inventory i
    JOIN products p  ON i.product_id  = p.product_id
    JOIN suppliers s ON p.supplier_id = s.supplier_id
    WHERE i.stock_status IN ('Low Stock', 'Out of Stock')
    ORDER BY i.days_of_supply ASC
    LIMIT 10
""", engine)
print(f"✓ Top 10 reorder urgency products")

# ─────────────────────────────────────────
# EXPORT ALL TO EXCEL
# ─────────────────────────────────────────
output_path = 'data/supply_chain_analysis.xlsx'

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    inventory_health.to_excel(writer,     sheet_name='Inventory Health',    index=False)
    warehouse_util.to_excel(writer,       sheet_name='Warehouse Util',      index=False)
    supplier_performance.to_excel(writer, sheet_name='Supplier Performance',index=False)
    po_trends.to_excel(writer,            sheet_name='PO Trends',           index=False)
    carrier_performance.to_excel(writer,  sheet_name='Carrier Performance', index=False)
    category_inventory.to_excel(writer,   sheet_name='Category Inventory',  index=False)
    delay_analysis.to_excel(writer,       sheet_name='Delay Analysis',      index=False)
    reorder_urgency.to_excel(writer,      sheet_name='Reorder Urgency',     index=False)

print(f"\n✓ Excel report saved → {output_path}")
print("  8 sheets exported, ready for Power BI!")