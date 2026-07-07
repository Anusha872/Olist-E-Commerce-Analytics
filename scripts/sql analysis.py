import pandas as pd
import sqlite3

# Connect to the database
conn = sqlite3.connect('../data/olist.db')

def sql_analysis():
    print("--- STAGE 4: SQL ANALYSIS ---")
    
    # Query A: Which product categories generate the most revenue?
    # Logic: Join order_items, products, and category translation. Group by category and sum price.
    query_a = """
    SELECT 
        t.product_category_name_english AS category,
        SUM(oi.price) AS total_revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
    GROUP BY category
    ORDER BY total_revenue DESC
    LIMIT 10;
    """
    print("\nA) Top 10 Categories by Revenue:")
    print(pd.read_sql(query_a, conn))
    
    # Query B: Which regions (states) have the slowest delivery times and lowest review scores?
    # Logic: Calculate delivery time in days, join with customers and reviews.
    query_b = """
    SELECT 
        c.customer_state,
        AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)) AS avg_delivery_days,
        AVG(r.review_score) AS avg_review_score
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    LEFT JOIN order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_state
    ORDER BY avg_delivery_days DESC
    LIMIT 5;
    """
    print("\nB) Top 5 States with Slowest Delivery:")
    print(pd.read_sql(query_b, conn))
    
    # Query C: Percentage of orders delivered late
    query_c = """
    SELECT 
        COUNT(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 END) * 100.0 / COUNT(*) AS late_percentage
    FROM orders
    WHERE order_status = 'delivered';
    """
    print("\nC) Percentage of late deliveries:")
    print(pd.read_sql(query_c, conn))
    
    # Query D: RFM (Recency, Frequency, Monetary) Analysis
    # Logic: Group by customer_unique_id to find last purchase (Recency), count of orders (Frequency), total spent (Monetary)
    query_d = """
    SELECT 
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp) AS last_purchase_date,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(p.payment_value) AS monetary_value
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
    ORDER BY monetary_value DESC
    LIMIT 5;
    """
    print("\nD) Top 5 Customers by Monetary Value (RFM segment):")
    print(pd.read_sql(query_d, conn))

if __name__ == "__main__":
    sql_analysis()
    conn.close()
