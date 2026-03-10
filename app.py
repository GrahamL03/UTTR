import streamlit as st
import pandas as pd
import os
from glicko_logic import ClubManager

# --- INITIALIZE ---
if 'club' not in st.session_state:
    st.session_state.club = ClubManager()
club = st.session_state.club

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="UTTR // NOVI", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- CSS: FORCED DARK & CLEAN TACTICAL ---
st.markdown("""
    <style>
    /* Force Deep Dark Mode */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #050505 !important;
        color: #e0e0e0 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #080808 !important;
        border-right: 1px solid #1a1a1a;
    }

    /* Make Sidebar Toggle Visible */
    [data-testid="collapsedControl"] {
        color: #58a6ff !important;
    }

    /* Minimalist Header */
    .header-box {
        border-left: 4px solid #58a6ff;
        padding-left: 20px;
        margin-bottom: 40px;
        margin-top: -30px;
    }
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 40px;
        font-weight: 800;
        letter-spacing: -1px;
        color: #ffffff;
        margin: 0;
    }
    .sub-title {
        color: #58a6ff;
        font-family: monospace;
        font-size: 13px;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

    /* Clean Metric Cards */
    [data-testid="stMetric"] {
        background-color: #0d1117 !important;
        border: 1px solid #21262d !important;
        padding: 15px !important;
        border-radius: 8px !important;
    }
    [data-testid="stMetricValue"] {
        color: #58a6ff !important;
        font-family: 'JetBrains Mono', monospace;
    }

    /* UI Cleanup */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### SYSTEM MENU")
    menu = st.radio("", ["STANDINGS", "LOG MATCH", "PLAYER INTEL", "VERSUS"])
    st.markdown("---")
    st.caption("NOVI_TT_NETWORK // ACTIVE")

# --- HEADER SECTION ---
st.markdown("""
    <div class="header-box">
        <p class="sub-title">Universal Table Tennis Rating</p>
        <p class="main-title">UTTR // COMMAND</p>
    </div>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
if menu == "STANDINGS":
    st.markdown("#### CURRENT RANKINGS")
    players_data = []
    sorted_players = sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True)
    for i, (name, p) in enumerate(sorted_players):
        players_data.append({
            "RK": i + 1,
            "PLAYER": name.upper(),
            "RATING": int(p.rating),
            "CONFIDENCE": f"{int(100 - (p.rd/3.5))}%"
        })
    st.dataframe(pd.DataFrame(players_data), use_container_width=True, hide_index=True)

elif menu == "LOG MATCH":
    st.markdown("#### INPUT MATCH DATA")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            w_name = st.selectbox("WINNER", sorted(list(club.players.keys())))
            w_score = st.number_input("W_PTS", min_value=0, value=11)
        with c2:
            l_name = st.selectbox("LOSER", sorted([p for p in club.players.keys() if p != w_name]))
            l_score = st.number_input("L_PTS", min_value=0, value=9)
        
        if st.button("CONFIRM ENTRY", use_container_width=True):
            club.update_match(w_name, l_name, w_score, l_score)
            club.save_and_show()
            st.success(f"LOGGED: {w_name.upper()}")

elif menu == "PLAYER INTEL":
    st.markdown("#### SUBJECT DOSSIER")
    search_name = st.selectbox("IDENTIFY", sorted(list(club.players.keys())))
    p = club.players[search_name]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("RATING", int(p.rating))
    
    if os.path.exists(club.history_file):
        h_df = pd.read_csv(club.history_file)
        w = len(h_df[h_df['Winner'] == search_name])
        l = len(h_df[h_df['Loser'] == search_name])
        col2.metric("RECORD", f"{w}W - {l}L")
    
    col3.metric("STABILITY", f"{int(100 - (p.rd/3.5))}%")

elif menu == "VERSUS":
    st.markdown("#### MATCHUP ANALYSIS")
    c1, c2 = st.columns(2)
    s_a = c1.selectbox("SUBJECT_A", sorted(list(club.players.keys())))
    s_b = c2.selectbox("SUBJECT_B", sorted([x for x in club.players.keys() if x != s_a]))
    
    if st.button("RUN COMPARISON", use_container_width=True):
        if os.path.exists(club.history_file):
            df = pd.read_csv(club.history_file)
            h2h = df[((df['Winner'] == s_a) & (df['Loser'] == s_b)) | 
                     ((df['Winner'] == s_b) & (df['Loser'] == s_a))]
            
            if not h2h.empty:
                w_a = len(h2h[h2h['Winner'] == s_a])
                w_b = len(h2h[h2h['Winner'] == s_b])
                
                sc1, sc2, sc3 = st.columns([2,1,2])
                sc1.markdown(f"<h1 style='text-align:right;'>{w_a}</h1><p style='text-align:right;'>{s_a.upper()}</p>", unsafe_allow_html=True)
                sc2.markdown("<h1 style='text-align:center; padding-top:20px; color:#222;'>VS</h1>", unsafe_allow_html=True)
                sc3.markdown(f"<h1>{w_b}</h1><p>{s_b.upper()}</p>", unsafe_allow_html=True)
                
                st.dataframe(h2h[['Date', 'Winner', 'Score']].tail(5), use_container_width=True)