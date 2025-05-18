import streamlit as st
import pandas as pd
import sqlite3
import os

# Judul aplikasi
st.title("Agin query")

# Fungsi load data
@st.cache_data
def load_data():
    graph_df = pd.read_csv('graph_edges_with_usernames.csv')
    tweet_df = pd.read_excel('bitcoin_100_tweet.xlsx')
    return graph_df, tweet_df

# Load data
graph_df, tweet_df = load_data()

# Gunakan SQLite lokal
db_path = 'social.db'

# Buat ulang database tiap kali aplikasi dijalankan
def setup_database(graph_df, tweet_df):
    if os.path.exists(db_path):
        os.remove(db_path)  # Hapus file lama

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Buat tabel graf
    cursor.execute('DROP TABLE IF EXISTS graph')
    graph_df[['source', 'target']].to_sql('graph', conn, index=False)

    # Buat tabel tweet
    cursor.execute('DROP TABLE IF EXISTS tweets')
    tweet_df.to_sql('tweets', conn, index=False)

    conn.commit()
    return conn

# Setup DB dan koneksi
conn = setup_database(graph_df, tweet_df)

# Pilihan query dari user
query_option = st.selectbox("Pilih Query:", [
    "Gabungkan DB1 & DB2 berdasarkan username",
    "Tampilkan semua tweets dari user yang ada di graf",
    "Hitung jumlah koneksi tiap user (degree)",
    "Top 5 user paling aktif (graf & tweet)"
])

# Bangun query berdasarkan pilihan
if query_option == "Gabungkan DB1 & DB2 berdasarkan username":
    query = """
    SELECT DISTINCT t.username, t.full_text, t.created_at
    FROM tweets t
    JOIN (
        SELECT source AS username FROM graph
        UNION
        SELECT target AS username FROM graph
    ) g ON t.username = g.username
    """

elif query_option == "Tampilkan semua tweets dari user yang ada di graf":
    query = """
    SELECT t.*
    FROM tweets t
    WHERE t.username IN (
        SELECT source FROM graph
        UNION
        SELECT target FROM graph
    )
    """

elif query_option == "Hitung jumlah koneksi tiap user (degree)":
    query = """
    SELECT username, COUNT(*) AS degree
    FROM (
        SELECT source AS username FROM graph
        UNION ALL
        SELECT target AS username FROM graph
    )
    GROUP BY username
    ORDER BY degree DESC
    """

elif query_option == "Top 5 user paling aktif (graf & tweet)":
    query = """
    WITH degrees AS (
        SELECT username, COUNT(*) AS degree
        FROM (
            SELECT source AS username FROM graph
            UNION ALL
            SELECT target AS username FROM graph
        )
        GROUP BY username
    ),
    tweets_count AS (
        SELECT username, COUNT(*) AS tweet_count
        FROM tweets
        GROUP BY username
    )
    SELECT d.username, d.degree, t.tweet_count
    FROM degrees d
    JOIN tweets_count t ON d.username = t.username
    ORDER BY (d.degree + t.tweet_count) DESC
    LIMIT 5
    """

# Jalankan query dan tampilkan hasilnya
try:
    df_result = pd.read_sql_query(query, conn)
    st.dataframe(df_result)
except Exception as e:
    st.error(f"Terjadi kesalahan saat menjalankan query: {e}")
