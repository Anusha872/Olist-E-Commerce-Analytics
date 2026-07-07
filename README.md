Olist E-Commerce Analytics Project
Business Question
How can we optimize delivery logistics and identify our most valuable customer segments to improve overall customer satisfaction and profitability?

Data Source
The dataset used is the Olist Brazilian E-Commerce Dataset, consisting of 100k real, anonymized orders made between 2016 and 2018. It includes 9 linked datasets covering orders, products, customers, reviews, and payments.

Methodology
Data : Ingested 9 raw CSV files into a relational SQLite database (olist.db) to enable efficient querying and enforce data integrity.
Data Exploration & Cleaning: Processed missing values and converted temporal data into workable datetime objects using Pandas.
SQL Analysis: Executed complex relational queries (JOINs, aggregations) to extract business KPIs, including revenue by category, delivery performance by state, and customer RFM (Recency, Frequency, Monetary) segmentation.
Predictive Modeling: Developed a Logistic Regression model using scikit-learn to predict the likelihood of late deliveries based on spatial and transactional features.
Interactive Dashboard: Built a Streamlit application to democratize data access, allowing stakeholders to filter KPIs and visualize revenue distribution interactively.
Key Insight
A significant portion of low review scores correlates directly with late deliveries, particularly in specific states. For example, certain northern states experience the highest average delivery times, directly driving down regional customer satisfaction.

Business Recommendation
Logistics Reallocation: Renegotiate carrier contracts or establish new distribution hubs closer to states with consistently slow delivery times to reduce churn.
Targeted Marketing (RFM): Implement an exclusive loyalty program for the top 5% of customers identified in the RFM analysis to maximize Customer Lifetime Value (CLV).
