import streamlit as st
import pandas as pd
from glicko_logic import ClubManager
import math
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. INITIALIZE CONNECTION & CACHED DATA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        h_df = conn.read(worksheet="history", ttl=2) 
        p_df = conn.read(worksheet="players", ttl=60)
        try:
            t_df = conn.read(worksheet="tournament_matches", ttl=2)
        except:
            t_df = pd.DataFrame(columns=["Tournament_ID", "Player_A", "Player_B", "Round", "Winner", "Status"])
        return h_df, p_df, t_df
    except Exception as e:
        st.error(f"DATABASE LINK FAILURE: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

h_df, p_df, t_df = load_data()

# --- 2. INITIALIZE CLUB LOGIC ---
if 'club' not in st.session_state:
    st.session_state.club = ClubManager()
club = st.session_state.club

if 'bracket' not in st.session_state:
    st.session_state.bracket = None

# --- 3. PAGE CONFIG & UI ---
st.set_page_config(page_title="UTTR // NOVI", layout="wide", initial_sidebar_state="expanded")

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
    
    .floating-legend { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
    div[data-testid="stPopover"] > button {
        background-color: #1a1a1a !important;
        border: 1px solid #58a6ff !important;
        color: #58a6ff !important;
        border-radius: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="top-banner"></div>', unsafe_allow_html=True)

# --- 4. LOGGING UTILITY (Must be defined globally) ---
def log_tournament_match(p1, p2, round_name, winner, status="Completed"):
    global h_df, t_df
    # 1. Log to tournament_matches sheet
    new_t_row = pd.DataFrame([{
        "Tournament_ID": st.session_state.bracket["id"],
        "Player_A": p1, "Player_B": p2, "Round": round_name, "Winner": winner, "Status": status
    }])
    updated_t = pd.concat([t_df, new_t_row], ignore_index=True)
    conn.update(worksheet="tournament_matches", data=updated_t)
    
    # 2. Log to history sheet
    new_h_row = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Winner": winner, 
        "Loser": p2 if winner == p1 else p1,
        "Score": "11-0", 
        "Match_Type": "Tournament"
    }])
    updated_h = pd.concat([h_df, new_h_row], ignore_index=True)
    conn.update(worksheet="history", data=updated_h)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### UTTR // NAV")
    menu = st.radio("", ["STANDINGS", "TOURNAMENT", "LOG MATCH", "PLAYER INTEL", "VERSUS"])
    st.markdown("---")
    with st.expander("REGISTER NEW SUBJECT"):
        new_name = st.text_input("NAME")
        if st.button("INITIALIZE"):
            if new_name and club.add_new_player(new_name):
                st.success("SUCCESS"); st.rerun()
    st.caption("CORE_V4.2 // NOVI_MI")

st.markdown(f'<div class="header-section"><p class="sub-title">Detroit Catholic Central</p><p class="main-title">UTTR</p></div>', unsafe_allow_html=True)

# --- 6. NAVIGATION LOGIC ---

if menu == "STANDINGS":
    st.markdown("#### LEAGUE TABLE")
    sorted_players = sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True)
    top_3_names = [x[0] for x in sorted_players[:3]]
    players_data = []

    for i, (name, p) in enumerate(sorted_players):
        badges = []
        form_str = ""
        
        if not h_df.empty:
            p_matches = h_df[(h_df['Winner'] == name) | (h_df['Loser'] == name)]
            last_5 = p_matches.tail(5)
            streak, l_streak = 0, 0
            for _, row in last_5.iterrows():
                if row['Winner'] == name:
                    form_str += "W "; streak += 1; l_streak = 0
                else:
                    form_str += "L "; l_streak += 1; streak = 0
            
            if i == 0: badges.append("🥇 CHAMP")                  # 1. Rank 1
            if streak >= 3: badges.append("🔥 ON FIRE")          # 2. 3 Wins
            if streak >= 5: badges.append("👑 UNSTOPPABLE")       # 3. 5 Wins
            if l_streak >= 3: badges.append("🧊 COLD")             # 4. 3 Losses
            if p.rd < 50: badges.append("🛡️ WALL")                # 5. Stability > 85%
            if len(p_matches) >= 50: badges.append("💎 VETERAN")  # 6. 50+ Games
            if len(p_matches) < 5: badges.append("🐣 ROOKIE")     # 7. < 5 Games
            if not last_5.empty and last_5.iloc[-1]['Winner'] == name and last_5.iloc[-1]['Loser'] in top_3 and name not in top_3:
                badges.append("🔨 SLAYER")                        # 8. Beat Top 3
            if p.rd > 120: badges.append("❓ UNKNOWN")            # 9. Low Stability
            if "W W W W W" in form_str: badges.append("⚡ RAID")  # 10. Perfect Recent Form

        players_data.append({
            "RK": i + 1,
            "PLAYER": name.upper(),
            "RATING": int(p.rating),
            "STATUS": " ".join(badges) if badges else "---",
            "FORM": form_str.strip() if form_str else "---",
            "STABILITY": f"{int(100 - (p.rd/3.5))}%"
        })

    st.dataframe(pd.DataFrame(players_data), use_container_width=True, hide_index=True,
                 column_config={"RATING": st.column_config.ProgressColumn("RATING", min_value=1000, max_value=2000, format="%d")})

elif menu == "TOURNAMENT":
    st.markdown("#### 🏆 BRACKET CONTROL")
    if st.session_state.bracket is None:
        t_id = st.text_input("TOURNAMENT ID", value=f"T-{datetime.now().strftime('%m%d-%H%M')}")
        selected = st.multiselect("Select 8 Players", sorted(list(club.players.keys())))
        if len(selected) == 8 and st.button("GENERATE BRACKET", use_container_width=True):
            random.shuffle(selected)
            st.session_state.bracket = {
                "id": t_id,
                "QF": [{"p1": selected[i], "p2": selected[i+1], "w": None} for i in range(0, 8, 2)],
                "SF": [{"p1": "TBD", "p2": "TBD", "w": None}, {"p1": "TBD", "p2": "TBD", "w": None}],
                "F": {"p1": "TBD", "p2": "TBD", "w": None}
            }
            st.rerun()
    else:
        if st.sidebar.button("RESET TOURNAMENT"):
            st.session_state.bracket = None
            st.rerun()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("QUARTERFINALS")
            for i, match in enumerate(st.session_state.bracket["QF"]):
                with st.container(border=True):
                    st.write(f"**{match['p1']}** vs **{match['p2']}**")
                    if match["w"] is None:
                        win = st.selectbox("Winner", [match['p1'], match['p2']], key=f"qf_win_{i}")
                        if st.button(f"Confirm QF{i+1}"):
                            log_tournament_match(match['p1'], match['p2'], "QF", win)
                            club.update_match(win, (match['p2'] if win == match['p1'] else match['p1']), 11, 0)
                            st.session_state.bracket["QF"][i]["w"] = win
                            sf_idx, slot = i // 2, ("p1" if i % 2 == 0 else "p2")
                            st.session_state.bracket["SF"][sf_idx][slot] = win
                            st.rerun()
                    else: st.success(f"🏆 {match['w']}")

        with col2:
            st.caption("SEMIFINALS")
            for i, match in enumerate(st.session_state.bracket["SF"]):
                with st.container(border=True):
                    st.write(f"**{match['p1']}** vs **{match['p2']}**")
                    if match["w"] is None and "TBD" not in [match['p1'], match['p2']]:
                        win = st.selectbox("Winner", [match['p1'], match['p2']], key=f"sf_win_{i}")
                        if st.button(f"Confirm SF{i+1}"):
                            log_tournament_match(match['p1'], match['p2'], "SF", win)
                            club.update_match(win, (match['p2'] if win == match['p1'] else match['p1']), 11, 0)
                            st.session_state.bracket["SF"][i]["w"] = win
                            slot = "p1" if i == 0 else "p2"
                            st.session_state.bracket["F"][slot] = win
                            st.rerun()
                    elif match["w"]: st.success(f"🏆 {match['w']}")

        with col3:
            st.caption("FINALS")
            match = st.session_state.bracket["F"]
            with st.container(border=True):
                st.write(f"**{match['p1']}** vs **{match['p2']}**")
                if match["w"] is None and "TBD" not in [match['p1'], match['p2']]:
                    win = st.selectbox("Winner", [match['p1'], match['p2']], key="f_win")
                    if st.button("Confirm Champion"):
                        log_tournament_match(match['p1'], match['p2'], "Final", win, status="Champion Crowned")
                        club.update_match(win, (match['p2'] if win == match['p1'] else match['p1']), 11, 0)
                        st.session_state.bracket["F"]["w"] = win
                        st.balloons(); st.rerun()
                elif match["w"]: st.success(f"👑 {match['w']}")

    st.markdown("---")
    st.markdown("#### 📜 SYSTEM ARCHIVE: TOURNAMENT MATCHES")
    st.dataframe(t_df.sort_index(ascending=False), use_container_width=True, hide_index=True)

elif menu == "LOG MATCH":
    st.markdown("#### RECORD RECENT DATA")
    with st.container(border=True):
        w_name = st.selectbox("WINNER", sorted(list(club.players.keys())))
        l_name = st.selectbox("LOSER", sorted([p for p in club.players.keys() if p != w_name]))
        score = st.text_input("SCORE", value="11-0")
        if st.button("EXECUTE LOG", use_container_width=True):
            new_hist = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Winner": w_name, "Loser": l_name, "Score": score, "Match_Type": "Ranked"
            }])
            updated_h = pd.concat([h_df, new_hist], ignore_index=True)
            conn.update(worksheet="history", data=updated_h)
            club.update_match(w_name, l_name, 11, 0)
            st.rerun()

elif menu == "PLAYER INTEL":
    st.markdown("#### SUBJECT DOSSIER")
    name = st.selectbox("IDENTIFY", sorted(list(club.players.keys())))
    p = club.players[name]
    st.metric("RATING", int(p.rating), delta=f"{int(p.rd)} RD")
    if not h_df.empty:
        p_matches = h_df[(h_df['Winner'] == name) | (h_df['Loser'] == name)]
        st.write(f"RECORD: {len(p_matches[p_matches['Winner'] == name])}W - {len(p_matches[p_matches['Loser'] == name])}L")

elif menu == "VERSUS":
    st.markdown("#### MATCHUP ANALYSIS")
    p1_n = st.selectbox("A", sorted(list(club.players.keys())))
    p2_n = st.selectbox("B", sorted([x for x in club.players.keys() if x != p1_n]))
    p1, p2 = club.players[p1_n], club.players[p2_n]
    prob = 1 / (1 + math.pow(10, ((p2.rating - p1.rating) / 400)))
    st.write(f"**{p1_n}** has a {int(prob*100)}% chance to win.")
    st.progress(prob)

st.markdown('<div class="floating-legend">', unsafe_allow_html=True)
with st.popover("📜 STATUS KEY"):
    st.markdown("### UTTR // STATUS EFFECTS")
    st.markdown("🥇 CHAMP | 🔥 ON FIRE | 👑 UNSTOPPABLE | 🧊 COLD | 🛡️ WALL | 💎 VETERAN | 🐣 ROOKIE | 🔨 SLAYER | ❓ UNKNOWN | ⚡ RAID")
st.markdown('</div>', unsafe_allow_html=True)