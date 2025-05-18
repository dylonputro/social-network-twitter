import streamlit as st
import pandas as pd
import sqlite3
import os

st.title("Twitter Data Analysis")

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
    cursor = conn.cursor()

    # Simpan data ke dalam tabel
    graph_df[['source', 'target']].to_sql('graph', conn, index=False)
    tweet_df.to_sql('tweets', conn, index=False)

    conn.commit()
    return conn

conn = setup_database(graph_df, tweet_df)

query_option = st.selectbox("Pilih Query:", [
    "Follower paling banyak",
    "Retweet paling banyak",
    "Combine score (follower + retweet)"
])

if query_option == "Follower paling banyak":
    query = """
    SELECT username, MAX(followers_count) as followers
    FROM tweets
    GROUP BY username
    ORDER BY followers DESC
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

elif query_option == "Combine score (follower + retweet)":
    query = """
    SELECT username,
           MAX(followers_count) as followers,
           SUM(retweet_count) as total_retweets,
           MAX(followers_count) + SUM(retweet_count) as score
    FROM tweets
    GROUP BY username
    ORDER BY score DESC
    LIMIT 10
    """

try:
    df_result = pd.read_sql_query(query, conn)
    st.dataframe(df_result)
except Exception as e:
    st.error(f"Terjadi kesalahan saat menjalankan query: {e}")
