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

# --- CSS: FORCED DARK + OMBRE BANNER ---
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

    /* Light Blue Ombre Banner */
    .top-banner {
        background: linear-gradient(90deg, #58a6ff 0%, #0052cc 100%);
        height: 6px;
        width: 100%;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 9999;
    }

    .header-section {
        background: linear-gradient(180deg, rgba(88, 166, 255, 0.1) 0%, rgba(5, 5, 5, 0) 100%);
        padding: 40px 20px;
        border-radius: 0 0 20px 20px;
        margin-top: -50px;
        margin-bottom: 30px;
    }

    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 42px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: -1px;
    }

    .sub-title {
        color: #58a6ff;
        font-family: monospace;
        font-size: 12px;
        letter-spacing: 4px;
        text-transform: uppercase;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid #21262d !important;
        padding: 15px !important;
        border-radius: 10px !important;
    }
    [data-testid="stMetricValue"] {
        color: #58a6ff !important;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Sidebar Fixes */
    [data-testid="collapsedControl"] {
        color: #58a6ff !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- TOP DECORATIVE BANNER ---
st.markdown('<div class="top-banner"></div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### UTTR // NAV")
    menu = st.radio("", ["STANDINGS", "LOG MATCH", "PLAYER INTEL", "VERSUS"])
    st.markdown("---")
    st.caption("CORE_V3.0 // NOVI_MI")

# --- HEADER SECTION ---
st.markdown(f"""
    <div class="header-section">
        <p class="sub-title">Universal Table Tennis Rating</p>
        <p class="main-title">UTTR // COMMAND</p>
    </div>
    """, unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---
if menu == "STANDINGS":
    st.markdown("#### LEAGUE TABLE")
    
    # Load history to calculate form
    history_exists = os.path.exists(club.history_file)
    if history_exists:
        h_df = pd.read_csv(club.history_file)
    
    players_data = []
    sorted_players = sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True)
    
    for i, (name, p) in enumerate(sorted_players):
        # --- FORM CALCULATION ---
        form_str = ""
        if history_exists:
            # Filter matches for this player
            p_matches = h_df[(h_df['Winner'] == name) | (h_df['Loser'] == name)].tail(5)
            
            # Create the W L string (Newest on the right)
            for _, row in p_matches.iterrows():
                if row['Winner'] == name:
                    form_str += "W "
                else:
                    form_str += "L "
        
        players_data.append({
            "RK": i + 1,
            "PLAYER": name.upper(),
            "RATING": int(p.rating),
            "FORM (LAST 5)": form_str.strip() if form_str else "---",
            "STABILITY": f"{int(100 - (p.rd/3.5))}%"
        })
    
    # Display the table
    st.dataframe(pd.DataFrame(players_data), use_container_width=True, hide_index=True)

elif menu == "LOG MATCH":
    st.markdown("#### RECORD RECENT DATA")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            w_name = st.selectbox("WINNER", sorted(list(club.players.keys())))
            w_score = st.number_input("W_PTS", min_value=0, value=11)
        with c2:
            l_name = st.selectbox("LOSER", sorted([p for p in club.players.keys() if p != w_name]))
            l_score = st.number_input("L_PTS", min_value=0, value=9)
        
        if st.button("EXECUTE LOG", use_container_width=True):
            club.update_match(w_name, l_name, w_score, l_score)
            club.save_and_show()
            st.toast(f"LOGGED: {w_name.upper()}")

elif menu == "PLAYER INTEL":
    st.markdown("#### SUBJECT DOSSIER")
    search_name = st.selectbox("IDENTIFY", sorted(list(club.players.keys())))
    p = club.players[search_name]
    
    # Metrics Row
    col1, col2, col3 = st.columns(3)
    col1.metric("CURRENT RATING", int(p.rating))
    
    history_exists = os.path.exists(club.history_file)
    if history_exists:
        h_df = pd.read_csv(club.history_file)
        # Calculate W/L
        w = len(h_df[h_df['Winner'] == search_name])
        l = len(h_df[h_df['Loser'] == search_name])
        col2.metric("RECORD", f"{w}W - {l}L")
        
        # --- RATING PROGRESSION GRAPH ---
        st.markdown("---")
        st.markdown("#### RATING EVOLUTION")
        
        # We'll simulate the rating over time for the graph
        # Note: In a larger app, you'd store ratings after every match.
        # For now, we'll show their performance trend.
        p_matches = h_df[(h_df['Winner'] == search_name) | (h_df['Loser'] == search_name)].copy()
        
        if not p_matches.empty:
            # We create a simple point-in-time list
            # Since Glicko is complex, we'll track the "Performance Index"
            progression = []
            current_viz_rating = 1500 # Starting baseline
            for _, row in p_matches.iterrows():
                if row['Winner'] == search_name:
                    current_viz_rating += 15 # Simple visual approximation
                else:
                    current_viz_rating -= 12
                progression.append(current_viz_rating)
            
            # Create a DataFrame for the chart
            chart_data = pd.DataFrame(progression, columns=["UTTR RATING"])
            
            # Display a sleek line chart
            st.line_chart(chart_data, color="#58a6ff")
        else:
            st.info("INSUFFICIENT DATA FOR EVOLUTION ANALYSIS.")
    
    col3.metric("STABILITY", f"{int(100 - (p.rd/3.5))}%")

    st.markdown("---")
    st.markdown("#### RECENT ACTIVITY LOG")
    if history_exists:
        p_history = h_df[(h_df['Winner'] == search_name) | (h_df['Loser'] == search_name)].tail(10)
        st.table(p_history[['Date', 'Winner', 'Loser', 'Score']])

elif menu == "VERSUS":
    st.markdown("#### MATCHUP ANALYSIS")
    p_list = sorted(list(club.players.keys()))
    c1, c2 = st.columns(2)
    s_a = c1.selectbox("SUBJECT_A", p_list)
    s_b = c2.selectbox("SUBJECT_B", sorted([x for x in p_list if x != s_a]))
    
    # --- WIN PROBABILITY MATH ---
    p1 = club.players[s_a]
    p2 = club.players[s_b]
    
    # Glicko-2 Win Probability Formula
    import math
    def win_probability(player, opponent):
        delta_rating = opponent.rating - player.rating
        # Scale factor for Glicko-2
        g = 1 / math.sqrt(1 + 3 * (math.pow(0.00046, 2) * (math.pow(player.rd, 2) + math.pow(opponent.rd, 2))) / math.pow(math.pi, 2))
        return 1 / (1 + math.pow(10, (g * delta_rating / 400)))

    prob_a = win_probability(p1, p2)
    prob_b = 1 - prob_a

    # Display Probability Bar
    st.markdown(f"**PREDICTED WIN PROBABILITY**")
    st.progress(prob_a)
    col_pa, col_pb = st.columns(2)
    col_pa.caption(f"{s_a.upper()}: {int(prob_a * 100)}%")
    col_pb.markdown(f"<p style='text-align:right; color:#888; font-size:12px;'>{s_b.upper()}: {int(prob_b * 100)}%</p>", unsafe_allow_html=True)

    if st.button("RUN HISTORICAL COMPARISON", use_container_width=True):
        if os.path.exists(club.history_file):
            df = pd.read_csv(club.history_file)
            h2h = df[((df['Winner'] == s_a) & (df['Loser'] == s_b)) | 
                     ((df['Winner'] == s_b) & (df['Loser'] == s_a))]
            
            if not h2h.empty:
                w_a = len(h2h[h2h['Winner'] == s_a])
                w_b = len(h2h[h2h['Winner'] == s_b])
                
                m1, m2, m3 = st.columns([3, 1, 3])
                m1.markdown(f"<h1 style='text-align:right;'>{w_a}</h1><p style='text-align:right;'>{s_a.upper()}</p>", unsafe_allow_html=True)
                m2.markdown("<h1 style='text-align:center; color:#333; padding-top:10px;'>VS</h1>", unsafe_allow_html=True)
                m3.markdown(f"<h1>{w_b}</h1><p>{s_b.upper()}</p>", unsafe_allow_html=True)
                
                st.dataframe(h2h[['Date', 'Winner', 'Score']].tail(10), use_container_width=True)
            else:
                st.info("NO PREVIOUS ENCOUNTERS RECORDED.")