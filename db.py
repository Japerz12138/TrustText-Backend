import sqlite3
import pandas as pd

# Load CSV file
csv_file = 'spam.csv'
df = pd.read_csv(csv_file, encoding='latin1')  # encoding used for compatibility with SMS datasets

# Rename columns for clarity
df = df.rename(columns={'v1': 'class', 'v2': 'sms'})

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('trusttext.db')
cursor = conn.cursor()

def init_db():
    conn = sqlite3.connect("trusttext.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class TEXT CHECK(class IN ('spam', 'ham')),
            sms TEXT NOT NULL
        )
    ''')

# Insert data into the table
# for _, row in df.iterrows():
#     cursor.execute('INSERT INTO messages (class, sms) VALUES (?, ?)', (row['class'], row['sms']))

# Commit and close
conn.commit()
conn.close()

print("Data inserted successfully.")
