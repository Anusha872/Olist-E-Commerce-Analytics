import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# Make sure we read from the right path whether run from scripts or root
db_path = 'data/olist.db' if os.path.exists('data/olist.db') else '../data/olist.db'
conn = sqlite3.connect(db_path)

st.set_page_config(page_title="Olist Analytics", layout="wide")

st.title("📊 Olist Brazilian E-Commerce Analytics Report")
st.caption("Full dataset — no sampling. Use the sidebar to filter by state.")

# --- Filters ---
st.sidebar.header("Filters")
state_query = "SELECT DISTINCT customer_state FROM customers ORDER BY customer_state"
states = ['All'] + pd.read_sql(state_query, conn)['customer_state'].tolist()
selected_state = st.sidebar.selectbox("Select State", states)

where_clause = f"WHERE c.customer_state = '{selected_state}'" if selected_state != 'All' else ""
where_and = f"AND c.customer_state = '{selected_state}'" if selected_state != 'All' else ""

# ============================================================
# SECTION 1: TOP-LINE METRICS
# ============================================================
with st.container(border=True):
    @st.cache_data
    def load_summary(where_clause):
        query = f"""
        SELECT 
            o.order_id,
            o.order_status,
            c.customer_state,
            oi.price,
            oi.freight_value
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        {where_clause};
        """
        return pd.read_sql(query, conn)

    df = load_summary(where_clause)

    # One row per order (since order_items can have multiple rows per order)
    order_level = df.groupby('order_id').agg(
        revenue=('price', 'sum'),
        state=('customer_state', 'first')
    ).reset_index()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Orders", f"{len(order_level):,}")
    col2.metric("Total Revenue", f"${order_level['revenue'].sum():,.2f}")
    col3.metric("Avg Order Value", f"${order_level['revenue'].mean():,.2f}")

    # Late delivery % 
    late_query = f"""
    SELECT 
        COUNT(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date 
              THEN 1 END) * 100.0 / COUNT(*) AS late_pct
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered' {where_and}
    """
    late_pct = pd.read_sql(late_query, conn)['late_pct'].iloc[0]
    col4.metric("Late Delivery Rate", f"{late_pct:.1f}%")

# ============================================================
# SECTION 2: REVENUE TREND & PAYMENT METHODS (NEW)
# ============================================================
col_trend, col_pay = st.columns([2, 1])

with col_trend:
    with st.container(border=True):
        st.subheader("📈 Monthly Revenue Trend")
        @st.cache_data
        def load_trend(where_and):
            query = f"""
            SELECT 
                strftime('%Y-%m', o.order_purchase_timestamp) as month,
                SUM(oi.price) as total_revenue
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_status = 'delivered' AND o.order_purchase_timestamp IS NOT NULL {where_and}
            GROUP BY month
            ORDER BY month;
            """
            return pd.read_sql(query, conn).dropna()

        trend_df = load_trend(where_and)
        if not trend_df.empty:
            fig_trend = px.line(trend_df, x='month', y='total_revenue', markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)
            st.caption("**Key Insight:** Sales peaked notably in late 2017 (Black Friday), indicating a highly seasonal e-commerce market.")
        else:
            st.write("No trend data available for this selection.")

with col_pay:
    with st.container(border=True):
        st.subheader("💳 Payment Methods")
        @st.cache_data
        def load_payments(where_clause):
            query = f"""
            SELECT 
                p.payment_type,
                SUM(p.payment_value) as total_value
            FROM order_payments p
            JOIN orders o ON p.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            {where_clause}
            GROUP BY p.payment_type
            ORDER BY total_value DESC;
            """
            return pd.read_sql(query, conn)
            
        pay_df = load_payments(where_clause)
        fig_pay = px.pie(pay_df, names='payment_type', values='total_value', hole=0.4)
        st.plotly_chart(fig_pay, use_container_width=True)
        st.caption("**Key Insight:** Credit cards absolutely dominate transaction volume, far exceeding boletos (cash invoices) and vouchers.")

# ============================================================
# SECTION 3: REVENUE BY STATE (only meaningful when viewing "All")
# ============================================================
if selected_state == 'All':
    with st.container(border=True):
        st.subheader("💰 Revenue by State")
        state_rev = order_level.groupby('state')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
        fig = px.bar(state_rev, x='state', y='revenue')
        st.plotly_chart(fig, use_container_width=True)
        st.caption("**Key Insight:** SP (São Paulo) accounts for the vast majority of e-commerce revenue, dwarfing all other regions.")

# ============================================================
# SECTION 4: TOP PRODUCT CATEGORIES
# ============================================================
with st.container(border=True):
    st.subheader("🏆 Top Product Categories by Revenue")

    @st.cache_data
    def load_categories(where_clause):
        cat_where = where_clause.replace('c.customer_state', 'cust.customer_state') if where_clause else ""
        query = f"""
        SELECT 
            t.product_category_name_english AS category,
            SUM(oi.price) AS total_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
        JOIN orders o ON oi.order_id = o.order_id
        JOIN customers cust ON o.customer_id = cust.customer_id
        {cat_where}
        GROUP BY category
        ORDER BY total_revenue DESC
        LIMIT 10;
        """
        return pd.read_sql(query, conn)

    cat_df = load_categories(where_clause)
    fig_cat = px.bar(cat_df, x='total_revenue', y='category', orientation='h')
    fig_cat.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_cat, use_container_width=True)
    st.caption("**Key Insight:** Health/Beauty and Watches/Gifts drive the most top-line revenue, showing strong demand for personal lifestyle products.")

# ============================================================
# SECTION 5: DELIVERY TIME vs REVIEW SCORE BY STATE
# ============================================================
with st.container(border=True):
    st.subheader("🚚 Delivery Time & Customer Satisfaction by State")

    @st.cache_data
    def load_delivery(where_clause, where_and):
        query = f"""
        SELECT 
            c.customer_state,
            AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)) AS avg_delivery_days,
            AVG(r.review_score) AS avg_review_score
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN order_reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered' {where_and}
        GROUP BY c.customer_state
        ORDER BY avg_delivery_days DESC;
        """
        return pd.read_sql(query, conn)

    delivery_df = load_delivery(where_clause, where_and)
    fig_delivery = px.bar(delivery_df, x='customer_state', y='avg_delivery_days',
                           color='avg_review_score', color_continuous_scale='RdYlGn')
    st.plotly_chart(fig_delivery, use_container_width=True)
    st.caption("**Key Insight:** States with the longest delivery times (often in the north) tend to have lower average review scores, proving logistics directly impacts satisfaction.")

# ============================================================
# SECTION 6: TOP CUSTOMERS (RFM)
# ============================================================
with st.container(border=True):
    st.subheader("⭐ Top 10 Highest-Value Customers (RFM)")

    @st.cache_data
    def load_top_customers(where_clause):
        query = f"""
        SELECT 
            c.customer_unique_id,
            MAX(o.order_purchase_timestamp) AS last_purchase_date,
            COUNT(DISTINCT o.order_id) AS frequency,
            SUM(p.payment_value) AS monetary_value
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_payments p ON o.order_id = p.order_id
        {where_clause}
        GROUP BY c.customer_unique_id
        ORDER BY monetary_value DESC
        LIMIT 10;
        """
        return pd.read_sql(query, conn)

    top_customers = load_top_customers(where_clause)
    st.dataframe(top_customers, use_container_width=True)
    st.caption("**Key Insight:** A small segment of 'whale' customers spend significantly more than average; marketing should target these IDs with VIP retention campaigns.")

st.divider()

st.write("""
### What is this?
This is a full analytics report dashboard built on the complete Olist dataset (no sampling).
It combines revenue analysis, product performance, delivery/logistics health, and customer 
value segmentation (RFM) in one view — the kind of report a real e-commerce ops or marketing 
team would use weekly to make decisions.
""")