import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import os

# Create outputs folder if it doesn't exist
os.makedirs('outputs', exist_ok=True)

# Connect to the database
conn = sqlite3.connect('../data/olist.db')

def explore_and_clean():
    print("--- STAGE 3: DATA CLEANING & EXPLORATION ---")
    
    # 1. Load orders table to check for nulls and data types
    orders_df = pd.read_sql("SELECT * FROM orders", conn)
    print("\nOrders Table Info:")
    print(orders_df.info())
    
    # Check for missing values
    print("\nMissing Values in Orders:")
    print(orders_df.isnull().sum())
    
    # Data Quality Issue: Nulls in 'order_delivered_customer_date'
    # Why? Orders might be canceled or still in transit.
    # Handling: Let's fill nulls with 'Not Delivered' for canceled, or we drop them if we only care about delivered orders.
    # We will keep them but convert dates to actual datetime objects
    date_cols = ['order_purchase_timestamp', 'order_approved_at', 
                 'order_delivered_carrier_date', 'order_delivered_customer_date', 
                 'order_estimated_delivery_date']
    
    for col in date_cols:
        orders_df[col] = pd.to_datetime(orders_df[col], errors='coerce')
        
    print("\nDates converted to datetime objects.")
    
    # 2. Basic Exploration: Order volume over time
    orders_df['purchase_month'] = orders_df['order_purchase_timestamp'].dt.to_period('M')
    monthly_orders = orders_df.groupby('purchase_month').size()
    
    # Plotting
    plt.figure(figsize=(10, 5))
    monthly_orders.plot(kind='bar', color='skyblue')
    plt.title('Order Volume Over Time')
    plt.xlabel('Month')
    plt.ylabel('Number of Orders')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('../outputs/order_volume.png')
    print("Saved plot to outputs/order_volume.png")
    
    # 3. Basic Exploration: Review score distribution
    reviews_df = pd.read_sql("SELECT review_score FROM order_reviews", conn)
    plt.figure(figsize=(8, 5))
    reviews_df['review_score'].value_counts().sort_index().plot(kind='bar', color='lightgreen')
    plt.title('Distribution of Review Scores')
    plt.xlabel('Score (1-5)')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig('../outputs/review_scores.png')
    print("Saved plot to outputs/review_scores.png")

if __name__ == "__main__":
    explore_and_clean()
    conn.close()
