import streamlit as st
import pandas as pd
import os
from glicko_logic import ClubManager

# --- INITIALIZE ---
if 'club' not in st.session_state:
    st.session_state.club = ClubManager()
club = st.session_state.club

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTTR | NOVI", layout="wide", initial_sidebar_state="expanded")

# --- FORCED DARK MODE & STYLING ---
st.markdown("""
    <style>
    /* Force Dark Theme regardless of system settings */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050505 !important;
        color: #e0e0e0 !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #222;
    }

    /* Remove Light/Dark toggle and other menu items for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Modern "Glow" Header */
    .hero-text {
        font-family: 'Inter', sans-serif;
        font-size: 50px;
        font-weight: 900;
        letter-spacing: -2px;
        color: #ffffff;
        margin-bottom: 0px;
        text-shadow: 0px 0px 15px rgba(88, 166, 255, 0.3);
    }
    .status-tag {
        font-family: monospace;
        background-color: #161b22;
        color: #58a6ff;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        border: 1px solid #30363d;
    }

    /* Metric "Cards" */
    [data-testid="stMetric"] {
        background-color: #0d1117;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }
    [data-testid="stMetricValue"] {
        color: #58a6ff !important;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Custom Table Styling */
    .stDataFrame {
        border: 1px solid #30363d;
    }
    
    /* Input fields styling */
    .stSelectbox, .stNumberInput {
        background-color: #0d1117 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### SYSTEM LOG")
    menu = st.radio("PRIMARY NAVIGATION", ["LEADERBOARD", "MATCH ENTRY", "PLAYER INTEL", "HEAD TO HEAD"])
    st.markdown("---")
    st.markdown("`LOCATION: NOVI_MI`")
    st.markdown("`STATUS: ENCRYPTED`")

# --- HEADER SECTION ---
st.markdown('<p class="hero-text">UTTR // SYSTEM</p>', unsafe_allow_html=True)
st.markdown('<span class="status-tag">CORE_V2.0_STABLE</span>', unsafe_allow_html=True)
st.markdown("---")

# --- NAVIGATION LOGIC ---
if menu == "LEADERBOARD":
    st.markdown("### GLOBAL STANDINGS")
    players_data = []
    sorted_players = sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True)
    
    for i, (name, p) in enumerate(sorted_players):
        players_data.append({
            "RK": i + 1,
            "PLAYER": name.upper(),
            "RATING": int(p.rating),
            "STABILITY": f"{int(100 - (p.rd/3.5))}%"
        })
    
    st.dataframe(pd.DataFrame(players_data), use_container_width=True, hide_index=True)

elif menu == "MATCH ENTRY":
    st.markdown("### DATA ACQUISITION")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            w_name = st.selectbox("WINNER_ID", sorted(list(club.players.keys())))
            w_score = st.number_input("W_SCORE", min_value=0, value=11)
        with c2:
            l_name = st.selectbox("LOSER_ID", sorted([p for p in club.players.keys() if p != w_name]))
            l_score = st.number_input("L_SCORE", min_value=0, value=9)
        
        if st.button("EXECUTE DATA OVERWRITE", use_container_width=True):
            club.update_match(w_name, l_name, w_score, l_score)
            club.save_and_show()
            st.success(f"SUCCESS: ENTRY RECORDED FOR {w_name.upper()}")

elif menu == "PLAYER INTEL":
    st.markdown("### SUBJECT DOSSIER")
    search_name = st.selectbox("IDENTIFY SUBJECT", sorted(list(club.players.keys())))
    p = club.players[search_name]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("UTTR_RATING", int(p.rating))
    
    if os.path.exists(club.history_file):
        h_df = pd.read_csv(club.history_file)
        w = len(h_df[h_df['Winner'] == search_name])
        l = len(h_df[h_df['Loser'] == search_name])
        col2.metric("RECORD", f"{w}W - {l}L")
    
    col3.metric("STABILITY", f"{int(100 - (p.rd/3.5))}%")
    
    st.markdown("---")
    st.markdown("### ACTIVITY LOG")
    if os.path.exists(club.history_file):
        h_df = pd.read_csv(club.history_file)
        p_history = h_df[(h_df['Winner'] == search_name) | (h_df['Loser'] == search_name)].tail(10)
        st.table(p_history[['Date', 'Winner', 'Loser', 'Score']])

elif menu == "HEAD TO HEAD":
    st.markdown("### BATTLE LOGS")
    c1, c2 = st.columns(2)
    s_a = c1.selectbox("SUBJECT_A", sorted(list(club.players.keys())))
    s_b = c2.selectbox("SUBJECT_B", sorted([x for x in club.players.keys() if x != s_a]))
    
    if st.button("RUN ANALYTICS", use_container_width=True):
        if os.path.exists(club.history_file):
            df = pd.read_csv(club.history_file)
            h2h = df[((df['Winner'] == s_a) & (df['Loser'] == s_b)) | 
                     ((df['Winner'] == s_b) & (df['Loser'] == s_a))]
            
            if not h2h.empty:
                w_a = len(h2h[h2h['Winner'] == s_a])
                w_b = len(h2h[h2h['Winner'] == s_b])
                
                m1, m2, m3 = st.columns([3, 1, 3])
                m1.markdown(f"<h1 style='text-align:right;'>{w_a}</h1><p style='text-align:right;'>{s_a.upper()}</p>", unsafe_allow_html=True)
                m2.markdown("<h1 style='text-align:center; color:#333;'>VS</h1>", unsafe_allow_html=True)
                m3.markdown(f"<h1>{w_b}</h1><p>{s_b.upper()}</p>", unsafe_allow_html=True)
                
                st.dataframe(h2h[['Date', 'Winner', 'Score']].tail(10), use_container_width=True)