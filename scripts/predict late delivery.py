import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, classification_report
from sklearn.preprocessing import LabelEncoder

# Connect to the database
conn = sqlite3.connect('../data/olist.db')

def build_model():
    print("--- STAGE 5: PREDICTIVE MODELING ---")
    
    # 1. Fetch data: We want to predict if an order will be late
    query = """
    SELECT 
        o.order_id,
        o.order_status,
        c.customer_state,
        CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
        julianday(o.order_estimated_delivery_date) - julianday(o.order_purchase_timestamp) AS estimated_delivery_days,
        COUNT(oi.order_item_id) as num_items,
        SUM(oi.price) as total_price
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered' 
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
    GROUP BY o.order_id
    LIMIT 10000; -- Limit for speed in this example
    """
    df = pd.read_sql(query, conn)
    
    # 2. Preprocessing
    # Encode categorical features (customer_state)
    le = LabelEncoder()
    df['customer_state_encoded'] = le.fit_transform(df['customer_state'])
    
    # Fill any nulls in numerical columns
    df['num_items'] = df['num_items'].fillna(1)
    df['total_price'] = df['total_price'].fillna(df['total_price'].mean())
    df['estimated_delivery_days'] = df['estimated_delivery_days'].fillna(df['estimated_delivery_days'].mean())
    
    # Define features (X) and target (y)
    X = df[['customer_state_encoded', 'estimated_delivery_days', 'num_items', 'total_price']]
    y = df['is_late']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Model Training
    # We use Logistic Regression - it's simple, interpretable, and answers "what is the probability of this being late?"
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    
    # 4. Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    
    print(f"Model Accuracy: {acc:.2f} (Percentage of correct predictions overall)")
    print(f"Model Precision: {prec:.2f} (When it predicts 'Late', how often is it actually late?)")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, zero_division=0))
    
    print("Interpretation: The model struggles with precision because late deliveries are rare (class imbalance). In a real job, we would use techniques like SMOTE or class weights to improve this.")

if __name__ == "__main__":
    build_model()
    conn.close()
