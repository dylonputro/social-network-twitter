import streamlit as st
import pandas as pd
import sqlite3
import os

st.title("Twitter Engagement Dashboard")

@st.cache_data
def load_data():
    graph_df = pd.read_csv('graph_edges_with_usernames.csv')
    tweet_df = pd.read_excel('bitcoin_100_tweet.xlsx')
    return graph_df, tweet_df

graph_df, tweet_df = load_data()

db_path = 'social.db'

def setup_database(graph_df, tweet_df):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    
    # Simpan graph
    graph_df[['source', 'target']].to_sql('graph', conn, index=False)
    
    # Simpan tweet
    tweet_df.to_sql('tweets', conn, index=False)
    
    # Buat tabel followers_count dari graph
    conn.execute("DROP TABLE IF EXISTS followers")
    conn.execute("""
        CREATE TABLE followers AS
        SELECT target AS username, COUNT(*) AS followers_count
        FROM graph
        GROUP BY target
    """)
    
    conn.commit()
    return conn

conn = setup_database(graph_df, tweet_df)

query_option = st.selectbox("Pilih Query:", [
    "Follower paling banyak",
    "Retweet paling banyak",
    "Engagement Score (followers + retweets)"
])

if query_option == "Follower paling banyak":
    query = """
    SELECT f.username, f.followers_count
    FROM followers f
    ORDER BY f.followers_count DESC
    LIMIT 10
    """

elif query_option == "Retweet paling banyak":
    query = """
    SELECT username, MAX(retweet_count) as retweets
    FROM tweets
    GROUP BY username
    ORDER BY retweets DESC
    LIMIT 10
    """

elif query_option == "Engagement Score (followers + retweets)":
    query = """
    WITH tweet_sum AS (
        SELECT username, SUM(retweet_count) AS total_retweets
        FROM tweets
        GROUP BY username
    )
    SELECT f.username, f.followers_count, t.total_retweets,
           f.followers_count + t.total_retweets AS engagement_score
    FROM followers f
    JOIN tweet_sum t ON f.username = t.username
    ORDER BY engagement_score DESC
    LIMIT 10
    """

try:
    df_result = pd.read_sql_query(query, conn)
    st.dataframe(df_result)
except Exception as e:
    st.error(f"Terjadi kesalahan saat menjalankan query: {e}")
