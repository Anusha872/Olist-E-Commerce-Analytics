import os
import pandas as pd
from sqlalchemy import create_engine

def load_csv_to_sqlite():
    data_dir = 'data'
    db_path = 'sqlite:///data/olist.db'
    engine = create_engine(db_path)
    
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    print(f"Found {len(csv_files)} CSV files. Starting to load into database...")
    
    for file in csv_files:
        table_name = file.replace('.csv', '')
        # Remove 'olist_' prefix and '_dataset' suffix for cleaner table names
        table_name = table_name.replace('olist_', '').replace('_dataset', '')
        
        file_path = os.path.join(data_dir, file)
        
        print(f"Loading {file} into table '{table_name}'...")
        
        # We read the CSV in chunks for better memory management, although these files fit in memory
        chunksize = 100000
        for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunksize)):
            # If it's the first chunk, replace the table if it exists. Otherwise, append.
            if i == 0:
                chunk.to_sql(table_name, engine, if_exists='replace', index=False)
            else:
                chunk.to_sql(table_name, engine, if_exists='append', index=False)
                
    print("All files loaded successfully into data/olist.db!")

if __name__ == "__main__":
    load_csv_to_sqlite()
