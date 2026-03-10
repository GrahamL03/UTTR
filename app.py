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
        /* Styling for the Status column in the dataframe isn't direct, 
       but we can make the text glow or stand out in the metrics */
    [data-testid="stHeader"] {
        border-bottom: 1px solid #21262d;
    }
    /* Floating Legend Button */
    .floating-legend {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    
    /* Make the popover button look like a tech-badge */
    div[data-testid="stPopover"] > button {
        background-color: #1a1a1a !important;
        border: 1px solid #58a6ff !important;
        color: #58a6ff !important;
        border-radius: 20px !important;
        padding: 5px 15px !important;
    }
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
    st.markdown("### SYSTEM TOOLS")
    with st.expander("REGISTER NEW SUBJECT"):
        new_name = st.text_input("NAME", placeholder="Full Name...")
        if st.button("INITIALIZE", use_container_width=True):
            if new_name:
                success = club.add_new_player(new_name)
                if success:
                    st.success(f"INITIALIZED: {new_name.upper()}")
                    st.rerun()
                else:
                    st.error("SUBJECT ALREADY EXISTS")
            else:
                st.warning("INPUT REQUIRED")
    st.markdown("---")
    st.caption("CORE_V3.0 // NOVI_MI")

# --- HEADER ---
st.markdown(f"""<div class="header-section"><p class="sub-title">Universal Table Tennis Rating</p><p class="main-title">UTTR</p></div>""", unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---

if menu == "STANDINGS":
    st.markdown("#### LEAGUE TABLE")
    
    # 1. FETCH DATA
    try:
        h_df = conn.read(worksheet="history", ttl=0)
        has_history = not h_df.empty
    except:
        has_history = False
    
    players_data = []
    # Sort by Rating (Glicko-2)
    sorted_players = sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True)
    top_3_names = [x[0] for x in sorted_players[:3]]
    
    # 2. CALCULATION LOOP
    for i, (name, p) in enumerate(sorted_players):
        badges = []
        form_str = ""
        
        if has_history:
            # Filter matches for this specific subject
            p_matches = h_df[(h_df['Winner'] == name) | (h_df['Loser'] == name)]
            last_5 = p_matches.tail(5)
            total_games = len(p_matches)
            
            # --- FORM & STREAKS ---
            streak = 0
            l_streak = 0
            for _, row in last_5.iterrows():
                if row['Winner'] == name:
                    form_str += "W "
                    streak += 1
                    l_streak = 0
                else:
                    form_str += "L "
                    l_streak += 1
                    streak = 0

            # --- PERFORMANCE BADGES ---
            if streak >= 3: badges.append("🔥 ON FIRE")
            if streak >= 5: badges.append("👑 UNSTOPPABLE")
            if l_streak >= 3: badges.append("🧊 COLD")
            
            # GIANT SLAYER: Beat a Top 3 player while not being Top 3 yourself
            if not last_5.empty:
                last_match = last_5.iloc[-1]
                if last_match['Winner'] == name and last_match['Loser'] in top_3_names and name not in top_3_names:
                    badges.append("🔨 SLAYER")

            # --- EXPERIENCE BADGES ---
            if total_games >= 50: badges.append("💎 VETERAN")
            elif total_games >= 20: badges.append("🎖️ SENIOR")
            elif total_games < 5: badges.append("🐣 ROOKIE")

            # --- PLAYSTYLE BADGES ---
            # CLUTCH: Check for 2-point margin wins in history
            clutch_count = 0
            for _, row in p_matches.iterrows():
                if row['Winner'] == name:
                    try:
                        scores = [int(x) for x in row['Score'].split('-')]
                        if abs(scores[0] - scores[1]) <= 2:
                            clutch_count += 1
                    except: continue
            if clutch_count >= 3: badges.append("🎯 CLUTCH")

            # --- SYSTEM STATUS ---
            if p.rd < 50: badges.append("🛡️ WALL")      # High Stability
            if p.rd > 120: badges.append("❓ UNKNOWN")  # High Uncertainty
            if i == 0: badges.append("🥇 CHAMP")         # Rank 1

        # 3. CONSTRUCT ROW
        players_data.append({
            "RK": i + 1,
            "PLAYER": name.upper(),
            "RATING": int(p.rating),
            "STATUS": " ".join(badges) if badges else "---",
            "FORM": form_str.strip() if form_str else "---",
            "STABILITY": f"{int(100 - (p.rd/3.5))}%"
        })

    # 4. RENDER
    df_display = pd.DataFrame(players_data)
    
    # Custom styling for the dataframe
    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "RK": st.column_config.NumberColumn("RK", format="#%d"),
            "RATING": st.column_config.ProgressColumn("RATING", min_value=1000, max_value=2000, format="%d"),
            "STABILITY": st.column_config.TextColumn("STABILITY"),
            "STATUS": st.column_config.TextColumn("STATUS EFFECTS")
        }
    )

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
    
    # 1. LOAD DATA & SAFETY CHECKS
    h_df = conn.read(worksheet="history", ttl=0)
    w, l = 0, 0
    p_matches = pd.DataFrame()
    badges = []

    if not h_df.empty and 'Winner' in h_df.columns:
        p_matches = h_df[(h_df['Winner'] == search_name) | (h_df['Loser'] == search_name)].copy()
        all_matches = p_matches # for badge logic
        last_5 = p_matches.tail(5)
        w = len(p_matches[p_matches['Winner'] == search_name])
        l = len(p_matches[p_matches['Loser'] == search_name])

        # --- 2. BADGE LOGIC (DUPLICATED FROM STANDINGS) ---
        streak = 0
        l_streak = 0
        for _, row in last_5.iterrows():
            if row['Winner'] == search_name:
                streak += 1
                l_streak = 0
            else:
                l_streak += 1
                streak = 0
        
        if streak >= 3: badges.append("🔥 ON FIRE")
        if streak >= 5: badges.append("👑 UNSTOPPABLE")
        if l_streak >= 3: badges.append("🧊 COLD")
        if len(all_matches) >= 50: badges.append("💎 VETERAN")
        if p.rd < 50: badges.append("🛡️ WALL")
        if p.rd > 120: badges.append("❓ UNKNOWN")
        if len(all_matches) < 5: badges.append("🐣 ROOKIE")

    # --- 3. DISPLAY BADGES AS TAGS ---
    if badges:
        badge_html = " ".join([f'<span style="background-color: #1a1a1a; border: 1px solid #58a6ff; color: #58a6ff; padding: 2px 10px; border-radius: 10px; margin-right: 5px; font-size: 12px; font-weight: bold;">{b}</span>' for b in badges])
        st.markdown(badge_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # --- 4. METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("CURRENT RATING", int(p.rating))
    col2.metric("RECORD", f"{w}W - {l}L")
    col3.metric("STABILITY", f"{int(100 - (p.rd/3.5))}%")

    # --- 5. PROGRESSION CHART ---
    if not p_matches.empty:
        progression = []
        val = 1500
        for _, row in p_matches.iterrows():
            val += 15 if row['Winner'] == search_name else -12
            progression.append(val)
        st.line_chart(pd.DataFrame(progression, columns=["UTTR RATING"]), color="#58a6ff")
    else:
        st.info("No match history found for this subject.")

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
# --- FLOATING BADGE LEGEND ---
st.markdown('<div class="floating-legend">', unsafe_allow_html=True)
with st.popover("📜 STATUS KEY"):
    st.markdown("### UTTR // STATUS EFFECTS")
    st.markdown("---")
    
    # Define your badges here
    legend_items = [
        ("🔥 ON FIRE", "3+ Win Streak. High momentum."),
        ("👑 UNSTOPPABLE", "5+ Win Streak. League leader behavior."),
        ("🔨 SLAYER", "Defeated a Top 3 player while lower ranked."),
        ("🎯 CLUTCH", "Won 3+ matches by exactly 2 points."),
        ("🛡️ WALL", "Stability > 85%. Rating is firmly established."),
        ("💎 VETERAN", "Has logged 50+ total matches."),
        ("🎖️ SENIOR", "Has logged 20+ total matches."),
        ("🐣 ROOKIE", "Fewer than 5 matches played."),
        ("🧊 COLD", "3+ Loss Streak. Needs a recovery win."),
        ("❓ UNKNOWN", "High uncertainty. Needs more matches."),
        ("🥇 CHAMP", "The current #1 ranked player.")
    ]
    
    for badge, desc in legend_items:
        st.markdown(f"**{badge}** \n*{desc}*")
st.markdown('</div>', unsafe_allow_html=True)