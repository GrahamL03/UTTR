import streamlit as st
import pandas as pd
import os
from glicko_logic import ClubManager

# --- INITIALIZE ---
if 'club' not in st.session_state:
    st.session_state.club = ClubManager()
club = st.session_state.club

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTTR | Novi Table Tennis", layout="wide")

# --- CUSTOM CSS (Minimalist Dark Theme) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
        color: #58a6ff;
        font-family: 'Courier New', Courier, monospace;
    }
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    .main-header {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        color: #f0f6fc;
        font-size: 2.5rem;
        border-bottom: 2px solid #30363d;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
    }
    .stButton>button:hover {
        border-color: #8b949e;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### UTTR NAVIGATION")
    menu = st.radio("SELECT VIEW", ["LEADERBOARD", "RECORD MATCH", "PLAYER SEARCH", "HEAD-TO-HEAD"])
    st.markdown("---")
    st.caption("SYSTEM ID: NOVI-TT-01")

# --- HEADER ---
st.markdown('<p class="main-header">UTTR RANKING SYSTEM</p>', unsafe_allow_html=True)

# --- LOGIC SECTIONS ---
if menu == "LEADERBOARD":
    st.markdown("### CURRENT STANDINGS")
    data = [{"RANK": i+1, "NAME": name, "RATING": int(p.rating), "CONFIDENCE": f"{int(100 - (p.rd/3.5))}%"} 
            for i, (name, p) in enumerate(sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True))]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "RECORD MATCH":
    st.markdown("### MATCH ENTRY")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            w_name = st.selectbox("WINNER", sorted(list(club.players.keys())))
            w_score = st.number_input("WINNER SCORE", min_value=0, value=11)
        with col2:
            l_name = st.selectbox("LOSER", sorted([p for p in club.players.keys() if p != w_name]))
            l_score = st.number_input("LOSER SCORE", min_value=0, value=9)

        if st.button("COMMIT MATCH TO HISTORY", use_container_width=True):
            club.update_match(w_name, l_name, w_score, l_score)
            club.save_and_show()
            st.success(f"DATA LOGGED: {w_name} vs {l_name}")

elif menu == "PLAYER SEARCH":
    st.markdown("### PLAYER INVESTIGATION")
    search_name = st.selectbox("SELECT PLAYER", sorted(list(club.players.keys())))
    p = club.players[search_name]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("RATING", int(p.rating))
    with col2:
        if os.path.exists(club.history_file):
            h_df = pd.read_csv(club.history_file)
            wins = len(h_df[h_df['Winner'] == search_name])
            losses = len(h_df[h_df['Loser'] == search_name])
            st.metric("RECORD", f"{wins}W - {losses}L")
    with col3:
        st.metric("CONFIDENCE", f"{int(100 - (p.rd/3.5))}%")

elif menu == "HEAD-TO-HEAD":
    st.markdown("### RIVALRY DATA")
    c1, c2 = st.columns(2)
    p1 = c1.selectbox("PLAYER 1", sorted(list(club.players.keys())))
    p2 = c2.selectbox("PLAYER 2", sorted([p for p in club.players.keys() if p != p1]))
    
    if st.button("RUN COMPARISON", use_container_width=True):
        if os.path.exists(club.history_file):
            df = pd.read_csv(club.history_file)
            h2h = df[((df['Winner'] == p1) & (df['Loser'] == p2)) | 
                     ((df['Winner'] == p2) & (df['Loser'] == p1))]
            
            if not h2h.empty:
                p1_w = len(h2h[h2h['Winner'] == p1])
                p2_w = len(h2h[h2h['Winner'] == p2])
                
                sc1, sc2, sc3 = st.columns([2,1,2])
                sc1.markdown(f"<h2 style='text-align:right;'>{p1}</h2><h1 style='text-align:right; color:#58a6ff;'>{p1_w}</h1>", unsafe_allow_html=True)
                sc2.markdown("<h1 style='text-align:center; padding-top:20px;'>VS</h1>", unsafe_allow_html=True)
                sc3.markdown(f"<h2 style='text-align:left;'>{p2}</h2><h1 style='text-align:left; color:#58a6ff;'>{p2_w}</h1>", unsafe_allow_html=True)
                
                st.markdown("#### RECENT MATCH LOGS")
                st.table(h2h[['Date', 'Winner', 'Score']].tail(5))
            else:
                st.info("NO MATCH DATA RECORDED FOR THIS PAIR.")