import streamlit as st
import pandas as pd
import os
from glicko_logic import ClubManager

# --- INITIALIZE ---
if 'club' not in st.session_state:
    st.session_state.club = ClubManager()
club = st.session_state.club

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTTR | NOVI TT", layout="wide")

# --- CUSTOM CSS (Tactical/Technical Aesthetic) ---
st.markdown("""
    <style>
    /* Global Background and Font */
    .stApp {
        background-color: #05070a;
        color: #e6edf3;
        font-family: 'Inter', 'Roboto', sans-serif;
    }
    
    /* Header Bar */
    .header-container {
        border-left: 5px solid #58a6ff;
        padding-left: 20px;
        margin-bottom: 30px;
    }
    .main-title {
        font-size: 42px;
        font-weight: 900;
        letter-spacing: -1px;
        margin: 0;
        color: #ffffff;
    }
    .sub-title {
        color: #8b949e;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        color: #58a6ff !important;
        font-size: 36px !important;
    }
    [data-testid="stMetricLabel"] {
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 12px !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #30363d;
    }

    /* Dataframe/Table Styling */
    .stDataFrame {
        border: 1px solid #30363d;
        border-radius: 8px;
    }

    /* Success/Info Boxes */
    .stAlert {
        background-color: #161b22;
        border: 1px solid #30363d;
        color: #58a6ff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### SYSTEM MENU")
    menu = st.radio("", ["LEADERBOARD", "MATCH ENTRY", "PLAYER INTEL", "HEAD TO HEAD"])
    st.markdown("---")
    st.markdown("**LOCAL SERVER:** ACTIVE")
    st.markdown("**DATABASE:** NOVI_V2.DB")

# --- TOP HEADER SECTION ---
st.markdown("""
    <div class="header-container">
        <p class="sub-title">Universal Table Tennis Rating</p>
        <p class="main-title">UTTR DATA HUB</p>
    </div>
    """, unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---
if menu == "LEADERBOARD":
    st.markdown("#### CURRENT POWER RANKINGS")
    # Preparing data
    data = []
    sorted_players = sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True)
    
    for i, (name, p) in enumerate(sorted_players):
        data.append({
            "RANK": i + 1,
            "PLAYER NAME": name.upper(),
            "UTTR RATING": int(p.rating),
            "STABILITY": f"{int(100 - (p.rd/3.5))}%"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "MATCH ENTRY":
    st.markdown("#### RECORD NEW DATA POINT")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            w_name = st.selectbox("WINNER ID", sorted(list(club.players.keys())))
            w_score = st.number_input("WINNER SCORE", min_value=0, value=11)
        with c2:
            l_name = st.selectbox("LOSER ID", sorted([p for p in club.players.keys() if p != w_name]))
            l_score = st.number_input("LOSER SCORE", min_value=0, value=9)
        
        st.markdown("---")
        if st.button("EXECUTE DATA LOG", use_container_width=True):
            club.update_match(w_name, l_name, w_score, l_score)
            club.save_and_show()
            st.success(f"ENTRY CONFIRMED: {w_name.upper()} DEFEATED {l_name.upper()}")

elif menu == "PLAYER INTEL":
    st.markdown("#### SUBJECT DOSSIER")
    player_list = sorted(list(club.players.keys()))
    search_name = st.selectbox("SELECT SUBJECT", player_list)
    p = club.players[search_name]
    
    # Visual grid for player stats
    col1, col2, col3 = st.columns(3)
    col1.metric("CURRENT RATING", int(p.rating))
    
    if os.path.exists(club.history_file):
        h_df = pd.read_csv(club.history_file)
        wins = len(h_df[h_df['Winner'] == search_name])
        losses = len(h_df[h_df['Loser'] == search_name])
        col2.metric("W / L RECORD", f"{wins} - {losses}")
    
    col3.metric("RATING STABILITY", f"{int(100 - (p.rd/3.5))}%")
    
    st.markdown("---")
    st.markdown("#### RECENT ACTIVITY LOG")
    if os.path.exists(club.history_file):
        h_df = pd.read_csv(club.history_file)
        p_history = h_df[(h_df['Winner'] == search_name) | (h_df['Loser'] == search_name)].tail(10)
        st.table(p_history[['Date', 'Winner', 'Loser', 'Score']])

elif menu == "HEAD TO HEAD":
    st.markdown("#### COMPARISON ANALYSIS")
    p_list = sorted(list(club.players.keys()))
    c1, c2 = st.columns(2)
    subject_a = c1.selectbox("SUBJECT A", p_list)
    subject_b = c2.selectbox("SUBJECT B", sorted([x for x in p_list if x != subject_a]))
    
    if st.button("RUN MATCHUP SIMULATION", use_container_width=True):
        if os.path.exists(club.history_file):
            df = pd.read_csv(club.history_file)
            h2h = df[((df['Winner'] == subject_a) & (df['Loser'] == subject_b)) | 
                     ((df['Winner'] == subject_b) & (df['Loser'] == subject_a))]
            
            if not h2h.empty:
                a_wins = len(h2h[h2h['Winner'] == subject_a])
                b_wins = len(h2h[h2h['Winner'] == subject_b])
                
                # Big Scoreboard Layout
                m1, m2, m3 = st.columns([3, 1, 3])
                m1.markdown(f"<h1 style='text-align:right;'>{a_wins}</h1>", unsafe_allow_html=True)
                m1.markdown(f"<p style='text-align:right; font-weight:bold;'>{subject_a.upper()}</p>", unsafe_allow_html=True)
                
                m2.markdown("<h1 style='text-align:center; color:#30363d;'>VS</h1>", unsafe_allow_html=True)
                
                m3.markdown(f"<h1>{b_wins}</h1>", unsafe_allow_html=True)
                m3.markdown(f"<p style='font-weight:bold;'>{subject_b.upper()}</p>", unsafe_allow_html=True)
                
                st.markdown("---")
                st.dataframe(h2h[['Date', 'Winner', 'Score']].tail(10), use_container_width=True)
            else:
                st.info("NO HISTORICAL DATA EXISTS FOR THIS SPECIFIC MATCHUP.")