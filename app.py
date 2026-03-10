import streamlit as st
import pandas as pd
from glicko_logic import ClubManager
import math
from streamlit_gsheets import GSheetsConnection

# --- INITIALIZE CONNECTION ---
# Strip out the spreadsheet= part
conn = st.connection("gsheets", type=GSheetsConnection)# --- INITIALIZE CLUB LOGIC ---
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
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #050505 !important;
        color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #080808 !important;
        border-right: 1px solid #1a1a1a;
    }
    .top-banner {
        background: linear-gradient(90deg, #58a6ff 0%, #0052cc 100%);
        height: 6px; width: 100%; position: fixed; top: 0; left: 0; z-index: 9999;
    }
    .header-section {
        background: linear-gradient(180deg, rgba(88, 166, 255, 0.1) 0%, rgba(5, 5, 5, 0) 100%);
        padding: 40px 20px; border-radius: 0 0 20px 20px; margin-top: -50px; margin-bottom: 30px;
    }
    .main-title { font-size: 42px; font-weight: 800; color: #ffffff; margin: 0; }
    .sub-title { color: #58a6ff; font-family: monospace; font-size: 12px; letter-spacing: 4px; text-transform: uppercase; }
    [data-testid="stMetric"] { background-color: rgba(255, 255, 255, 0.03) !important; border: 1px solid #21262d !important; padding: 15px !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="top-banner"></div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### UTTR // NAV")
    menu = st.radio("", ["STANDINGS", "LOG MATCH", "PLAYER INTEL", "VERSUS"])
    st.markdown("---")
    st.caption("CORE_V3.0 // NOVI_MI")

# --- HEADER ---
st.markdown(f"""<div class="header-section"><p class="sub-title">Universal Table Tennis Rating</p><p class="main-title">UTTR</p></div>""", unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---

if menu == "STANDINGS":
    st.markdown("#### LEAGUE TABLE")
    
    # Load history from Sheets for form calculation
    try:
        h_df = conn.read(worksheet="history", ttl=0)
        has_history = not h_df.empty
    except:
        has_history = False
    
    players_data = []
    sorted_players = sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True)
    
    for i, (name, p) in enumerate(sorted_players):
        form_str = ""
        if has_history:
            p_matches = h_df[(h_df['Winner'] == name) | (h_df['Loser'] == name)].tail(5)
            for _, row in p_matches.iterrows():
                form_str += "W " if row['Winner'] == name else "L "
        
        players_data.append({
            "RK": i + 1,
            "PLAYER": name.upper(),
            "RATING": int(p.rating),
            "FORM (LAST 5)": form_str.strip() if form_str else "---",
            "STABILITY": f"{int(100 - (p.rd/3.5))}%"
        })
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
            # The logic in club.update_match should now handle the conn.update
            club.update_match(w_name, l_name, w_score, l_score)
            st.toast(f"LOGGED: {w_name.upper()} DEFEATED {l_name.upper()}")
            st.rerun()

elif menu == "PLAYER INTEL":
    st.markdown("#### SUBJECT DOSSIER")
    search_name = st.selectbox("IDENTIFY", sorted(list(club.players.keys())))
    p = club.players[search_name]
    
    # --- ADDED SAFETY CHECK HERE ---
    h_df = conn.read(worksheet="history", ttl=0)
    
    # Initialize counts to zero in case history is empty
    w, l = 0, 0
    p_matches = pd.DataFrame()

    if not h_df.empty and 'Winner' in h_df.columns:
        w = len(h_df[h_df['Winner'] == search_name])
        l = len(h_df[h_df['Loser'] == search_name])
        p_matches = h_df[(h_df['Winner'] == search_name) | (h_df['Loser'] == search_name)].copy()
    # -------------------------------

    col1, col2, col3 = st.columns(3)
    col1.metric("CURRENT RATING", int(p.rating))
    col2.metric("RECORD", f"{w}W - {l}L")
    col3.metric("STABILITY", f"{int(100 - (p.rd/3.5))}%")

    # Rating progression
    if not p_matches.empty:
        progression = []
        val = 1500
        for _, row in p_matches.iterrows():
            # This is a visual estimate; real Glicko values are in the 'players' sheet
            val += 15 if row['Winner'] == search_name else -12
            progression.append(val)
        st.line_chart(pd.DataFrame(progression, columns=["UTTR RATING"]), color="#58a6ff")
    else:
        st.info("No match history found for this player yet.")

elif menu == "VERSUS":
    st.markdown("#### MATCHUP ANALYSIS")
    p_list = sorted(list(club.players.keys()))
    s_a = st.selectbox("SUBJECT_A", p_list)
    s_b = st.selectbox("SUBJECT_B", [x for x in p_list if x != s_a])
    
    p1, p2 = club.players[s_a], club.players[s_b]
    
    # Win Prob Logic
    delta = p2.rating - p1.rating
    g = 1 / math.sqrt(1 + 3 * (math.pow(0.00046, 2) * (math.pow(p1.rd, 2) + math.pow(p2.rd, 2))) / math.pow(math.pi, 2))
    prob_a = 1 / (1 + math.pow(10, (g * delta / 400)))
    
    st.progress(prob_a)
    st.write(f"{s_a}: {int(prob_a*100)}% | {s_b}: {int((1-prob_a)*100)}%")

    if st.button("RUN H2H"):
        h_df = conn.read(worksheet="history", ttl=0)
        h2h = h_df[((h_df['Winner'] == s_a) & (h_df['Loser'] == s_b)) | ((h_df['Winner'] == s_b) & (h_df['Loser'] == s_a))]
        st.table(h2h.tail(5))