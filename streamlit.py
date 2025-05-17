import streamlit as st
import psycopg2
import pandas as pd
from textblob import TextBlob

def classify_sentiment(text):
    analysis = TextBlob(str(text))
    polarity = analysis.sentiment.polarity
    if polarity > 0:
        return 'positive'
    elif polarity < 0:
        return 'negative'
    else:
        return 'neutral'

# Database connection details
DB_HOST = 'news-rds.cv22ysi0akwd.ap-south-1.rds.amazonaws.com'
DB_PORT = '5432'
DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = '9895652733'

# Connect to RDS
def get_data():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        query = "SELECT title, article_id, description, link, country, language, image_url FROM news_articles;"
        df = pd.read_sql_query(query, conn)
        conn.close()
        df['sentimental'] = df['title'].apply(classify_sentiment)
        return df
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return pd.DataFrame()

# Function to color sentiment column
def highlight_sentiment(row):
    if row['sentimental'] == 'positive':
        return ['background-color: yellow' if col == 'sentimental' else '' for col in row.index]
    elif row['sentimental'] == 'negative':
        return ['background-color: red' if col == 'sentimental' else '' for col in row.index]
    elif row['sentimental'] == 'neutral':
        return ['background-color: white' if col == 'sentimental' else '' for col in row.index]
    else:
        return ['' for _ in row.index]

# Streamlit app
st.set_page_config(page_title="News Dashboard", layout="wide")
st.title("Latest News Articles")

data = get_data()

if not data.empty:
    styled_data = data.style.apply(highlight_sentiment, axis=1)
    st.write(styled_data)  # Use st.write instead of st.dataframe for styling
else:
    st.warning("No data available or failed to fetch data.")