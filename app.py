import streamlit as st
import pandas as pd
from glicko_logic import ClubManager
import math
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection


# --- 1. INITIALIZE CONNECTION & CACHED DATA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def archive_and_reset_season(season_name):
    # 1. Load current data
    players_df = conn.read(worksheet="players")
    
    # 2. Prepare Archive Data
    # Add a column for the Season Name and the Date
    archive_snapshot = players_df.copy()
    archive_snapshot['Season'] = season_name
    archive_snapshot['Date_Archived'] = datetime.now().strftime("%Y-%m-%d") # FIXED: Proper datetime formatting
    
    # 3. Append to Archives
    existing_archives = conn.read(worksheet="archives")
    updated_archives = pd.concat([existing_archives, archive_snapshot], ignore_index=True)
    conn.update(worksheet="archives", data=updated_archives)
    
    # 4. Reset Players for New Season
    # We keep the names but reset stats to baseline
    reset_players = players_df.copy()
    reset_players['Rating'] = 750
    reset_players['RD'] = 350
    reset_players['Sigma'] = 0.06
    reset_players['Wins'] = 0
    reset_players['Losses'] = 0
    
    conn.update(worksheet="players", data=reset_players)
    
    # 5. Clear Match History
    # We create an empty dataframe with the same columns to wipe the history sheet
    history_columns = conn.read(worksheet="history").columns
    empty_history = pd.DataFrame(columns=history_columns)
    conn.update(worksheet="history", data=empty_history)

def load_data():
    try:
        h_df = conn.read(worksheet="history", ttl=600) 
        p_df = conn.read(worksheet="players", ttl=600)
        try:
            t_df = conn.read(worksheet="tournament_matches", ttl=600)
        except:
            t_df = pd.DataFrame(columns=["Tournament_ID", "Player_A", "Player_B", "Round", "Winner", "Status"])
        return h_df, p_df, t_df
    except Exception as e:
        st.error(f"DATABASE LINK FAILURE: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

h_df, p_df, t_df = load_data()

def get_current_season():
    try:
        archive_df = conn.read(worksheet="archives", ttl=600)
        if not archive_df.empty:
            # Gets the very last season name added to the archives
            return archive_df['Season'].iloc[-1]
        return "Inaugural Season"
    except:
        return "Active Season"

# --- 2. INITIALIZE CLUB LOGIC ---
if 'club' not in st.session_state:
    st.session_state.club = ClubManager()
club = st.session_state.club

if 'bracket' not in st.session_state:
    st.session_state.bracket = None

# --- 3. PAGE CONFIG & UI ---
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

    /* NEW BANNER STYLES START HERE */
    .main-banner-content {
        text-align: center;
        padding: 30px 20px; /* Increased padding for more space */
        margin-top: 10px; /* Small gap from the top-banner line */
        margin-bottom: 40px; /* More space before the content below */
        background: linear-gradient(180deg, rgba(88, 166, 255, 0.05) 0%, rgba(5, 5, 5, 0) 100%); /* Subtle gradient */
        border-bottom: 1px solid rgba(88, 166, 255, 0.2); /* Soft separator line */
    }

    .banner-title {
        font-size: 3.2em; /* Larger font for the main title */
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 2px;
        margin-bottom: 10px;
        text-shadow: 0 0 10px rgba(88, 166, 255, 0.4); /* Subtle glow */
    }

    .banner-subtitle {
        font-family: 'Consolas', 'Monaco', monospace; /* Monospace for the UTTR part */
        font-size: 1.1em;
        color: #58a6ff; /* Your theme's blue */
        letter-spacing: 5px; /* Wider spacing */
        text-transform: uppercase;
        opacity: 0.8;
    }
    /* NEW BANNER STYLES END HERE */

    .header-section { /* This seems unused, but keeping it if you plan to use it */
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
st.markdown("""
    <div class="main-banner-content">
        <div class="banner-title">CATHOLIC CENTRAL TABLE TENNIS</div>
        <div class="banner-subtitle">UNIVERSAL TABLE TENNIS RANKING (UTTR)</div>
    </div>
""", unsafe_allow_html=True)
# --- 4. LOGGING UTILITY (Must be defined globally) ---
def log_tournament_match(p1, p2, round_name, winner, score_str="11-0", status="Completed"):
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
        "Score": score_str,  # Use the passed string
        "Match_Type": "Tournament"
    }])
    updated_h = pd.concat([h_df, new_h_row], ignore_index=True)
    conn.update(worksheet="history", data=updated_h)

# --- 5. SIDEBAR & ADMIN CHECK ---
with st.sidebar:
    st.subheader(f"🏆 {get_current_season()}")
    st.markdown("---")
    st.markdown("### UTTR // NAV")
    
    # Password Protection for Admin Tools
    admin_key = st.text_input("Admin Key", type="password")
    is_admin = (admin_key == "ccpingpong") # Change "ccpingpong" to your preferred password

    menu = st.radio("", ["STANDINGS", "TOURNAMENT", "LOG MATCH", "PLAYER INTEL", "VERSUS", "HALL OF FAME", "ADMIN SETTINGS"])    
    st.markdown("---")
    
    # Only show registration to admins
    if is_admin:
        with st.expander("REGISTER NEW SUBJECT"):
            new_name = st.text_input("NAME")
            if st.button("INITIALIZE"):
                if new_name and club.add_new_player(new_name):
                    st.success("SUCCESS"); st.rerun()
    else:
        st.info("Enter Admin Key to unlock registration & reset tools.")
        
    st.caption("CORE_V4.2 // NOVI_MI")

# --- 6. NAVIGATION LOGIC ---
if menu == "ADMIN SETTINGS":
    st.markdown("#### ⚙️ CORE SYSTEM CONTROL")
    if is_admin:
        with st.container(border=True):
            st.subheader("🏁 Season Transition")
            st.write(f"Current Phase: **{get_current_season()}**")
            st.warning("Ending the season will archive current ratings and reset everyone to 750.")
            
            season_input = st.text_input("NEW SEASON NAME", placeholder="e.g. Spring 2026")
            confirm_check = st.checkbox("I confirm I want to wipe the current leaderboard.")
            
            if st.button("🚀 EXECUTE ARCHIVE & RESET", use_container_width=True):
                if confirm_check and season_input:
                    with st.spinner("Archiving data..."):
                        archive_and_reset_season(season_input)
                    st.success(f"SEASON {season_input} INITIALIZED.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Action Required: Provide a name and check the confirmation box.")
    else:
        st.warning("Admin Key required to access system settings.")
elif menu == "STANDINGS":
    st.markdown("#### LEAGUE TABLE")
    sorted_players = sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True)
    top_3 = [x[0] for x in sorted_players[:3]]
    players_data = []
    
    # We use a separate counter to keep ranks sequential (1, 2, 3...)
    rank_counter = 1 

    for i, (name, p) in enumerate(sorted_players):
        badges = []
        form_str = ""
        rating_val = int(p.rating)
        
        tier_emoji = "🥉" # Bronze
        if rating_val >= 2000: tier_emoji = "💎" # Diamond
        elif rating_val >= 1400: tier_emoji = "🥇" # Gold
        elif rating_val >= 1000: tier_emoji = "🥈" # Silver
        
        if not h_df.empty:
            p_matches = h_df[(h_df['Winner'] == name) | (h_df['Loser'] == name)]
            
            # --- FILTER: Skip players with 0 matches ---
            if p_matches.empty:
                continue 
            
            last_5 = p_matches.tail(5)
            streak, l_streak = 0, 0
            
            last_3 = p_matches.tail(3)
            dominance_count = 0
            
            if len(last_3) >= 3:
                for _, row in last_3.iterrows():
                    # Only count if they actually won the match
                    if row['Winner'] == name:
                        try:
                            # Split "11-4" into [11, 4]
                            pts = [int(x) for x in row['Score'].split('-')]
                            spread = abs(pts[0] - pts[1])
                            if spread > 6:
                                dominance_count += 1
                        except:
                            pass # Handle any malformed score strings
            
            for _, row in last_5.iterrows():
                if row['Winner'] == name:
                    form_str += "W "; streak += 1; l_streak = 0
                else:
                    form_str += "L "; l_streak += 1; streak = 0
            
            # --- BADGE LOGIC ---
            if rank_counter == 1: badges.append("🥇 CHAMP")
            if dominance_count >= 3: badges.append("😤 DOMINANT")
            if streak >= 3: badges.append("🔥 ON FIRE")
            if streak >= 5: badges.append("👑 UNSTOPPABLE")
            if l_streak >= 3: badges.append("🧊 COLD")
            if p.rd < 50: badges.append("🛡️ WALL")
            if len(p_matches) >= 50: badges.append("💎 VETERAN")
            if len(p_matches) < 5: badges.append("🐣 ROOKIE")
            if not last_5.empty and last_5.iloc[-1]['Winner'] == name and last_5.iloc[-1]['Loser'] in top_3 and name not in top_3:
                badges.append("🔨 SLAYER")
            if p.rd > 200: badges.append("❓ UNKNOWN")
        else:
            # If the entire history database is empty, skip everyone
            continue

        players_data.append({
            "RK": rank_counter,
            "PLAYER": f"{tier_emoji} {name.upper()}",
            "RATING": rating_val,
            "STATUS": " ".join(badges) if badges else "---",
            "FORM": form_str.strip() if form_str else "---",
            "STABILITY": f"{int(100 - (p.rd/3.5))}%"
        })
        
        # Increment the rank counter only when a player is actually added
        rank_counter += 1

    # --- RENDER TABLE ---
    if players_data:
        st.dataframe(
            pd.DataFrame(players_data), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "RATING": st.column_config.ProgressColumn(
                    "RATING", min_value=0, max_value=3000, format="%d"
                )
            }
        )
    else:
        st.info("No matches have been played yet. Record a match to generate the standings!")

    # --- CLUSTERED RATING DISTRIBUTION ---
    st.markdown("---")
    st.caption("LEAGUE RATING DISTRIBUTION (250pt TIERS)")
    
    # Update this to only chart players who are actively displayed on the board
    all_ratings = [row['RATING'] for row in players_data]
    
    if all_ratings:
        df_dist = pd.DataFrame(all_ratings, columns=['Rating'])
        
        # Cluster into 250-point buckets
        df_dist['Tier'] = (df_dist['Rating'] // 250) * 250
        
        # Create the label (e.g., 1000-1249)
        df_dist['Range'] = df_dist['Tier'].apply(lambda x: f"{int(x)}-{int(x+249)}")
        
        # Count players per tier and sort numerically
        dist_counts = df_dist.groupby(['Tier', 'Range']).size().reset_index(name='Players')
        dist_counts = dist_counts.sort_values('Tier')
        
        # Render the chart
        st.bar_chart(dist_counts.set_index('Range')['Players'])
elif menu == "TOURNAMENT":
    st.markdown("#### 🏆 BRACKET CONTROL")
    if st.session_state.bracket is None:
        if is_admin:
            t_id = st.text_input("TOURNAMENT ID", value=f"T-{datetime.now().strftime('%m%d-%H%M')}")
            selected = st.multiselect("Select 8 Players", sorted(list(club.players.keys())))
            if len(selected) == 8 and st.button("GENERATE SEEDED BRACKET", use_container_width=True):
                seeded = sorted(selected, key=lambda x: club.players[x].rating, reverse=True)
                pairings = [(seeded[0], seeded[7]), (seeded[3], seeded[4]), (seeded[1], seeded[6]), (seeded[2], seeded[5])]
                st.session_state.bracket = {
                    "id": t_id, 
                    "QF": [{"p1": p1, "p2": p2, "w": None} for p1, p2 in pairings], 
                    "SF": [{"p1": "TBD", "p2": "TBD", "w": None}, {"p1": "TBD", "p2": "TBD", "w": None}], 
                    "F": {"p1": "TBD", "p2": "TBD", "w": None}
                }
                st.rerun()
        else:
            st.warning("No active tournament. Admin key required to start one.")
    else:
        if is_admin and st.sidebar.button("RESET TOURNAMENT"):
            st.session_state.bracket = None
            st.rerun()

        col1, col2, col3 = st.columns(3)
        
        # --- Quarterfinals ---
        with col1:
            st.caption("QUARTERFINALS")
            for i, m in enumerate(st.session_state.bracket["QF"]):
                with st.container(border=True):
                    st.write(f"**{m['p1']}** vs **{m['p2']}**")
                    if m["w"] is None:
                        if is_admin:
                            t_score = st.text_input("Score", value="11-5 | 11-5", key=f"score_qf_{i}", help="Winner-Loser per game, separated by |")
                            win = st.selectbox("Winner", [m['p1'], m['p2']], key=f"qf_{i}")
                            if st.button(f"Confirm QF{i+1}"):
                                try:
                                    parsed = [[int(x.strip()) for x in s.split('-')] for s in t_score.split('|')]
                                    log_tournament_match(m['p1'], m['p2'], "QF", win, score_str=t_score)
                                    club.update_match(win, (m['p2'] if win == m['p1'] else m['p1']), parsed, match_type="Best of 3")
                                    st.session_state.bracket["QF"][i]["w"] = win
                                    sf_idx, slot = i // 2, ("p1" if i % 2 == 0 else "p2")
                                    st.session_state.bracket["SF"][sf_idx][slot] = win
                                    st.rerun()
                                except: st.error("Format Error. Use '11-5 | 11-5'")
                        else: st.info("Match in progress...")
                    else: st.success(f"🏆 {m['w']}")
        
        # --- Semifinals ---
        with col2:
            st.caption("SEMIFINALS")
            for i, m in enumerate(st.session_state.bracket["SF"]):
                with st.container(border=True):
                    st.write(f"**{m['p1']}** vs **{m['p2']}**")
                    if m["w"] is None and "TBD" not in [m['p1'], m['p2']]:
                        if is_admin:
                            t_score = st.text_input("Score", value="11-5 | 11-5", key=f"score_sf_{i}")
                            win = st.selectbox("Winner", [m['p1'], m['p2']], key=f"sf_{i}")
                            if st.button(f"Confirm SF{i+1}"):
                                try:
                                    parsed = [[int(x.strip()) for x in s.split('-')] for s in t_score.split('|')]
                                    log_tournament_match(m['p1'], m['p2'], "SF", win, score_str=t_score)
                                    club.update_match(win, (m['p2'] if win == m['p1'] else m['p1']), parsed, match_type="Best of 3")
                                    st.session_state.bracket["SF"][i]["w"] = win
                                    st.session_state.bracket["F"]["p1" if i == 0 else "p2"] = win
                                    st.rerun()
                                except: st.error("Format Error.")
                        else: st.info("Match in progress...")
                    elif m["w"]: st.success(f"🏆 {m['w']}")

        # --- Finals ---
        with col3:
            st.caption("FINALS")
            m = st.session_state.bracket["F"]
            with st.container(border=True):
                st.write(f"**{m['p1']}** vs **{m['p2']}**")
                if m["w"] is None and "TBD" not in [m['p1'], m['p2']]:
                    if is_admin:
                        t_score = st.text_input("Score", value="11-5 | 11-5", key="score_f")
                        win = st.selectbox("Winner", [m['p1'], m['p2']], key="f_win")
                        if st.button("Confirm Champion"):
                            try:
                                parsed = [[int(x.strip()) for x in s.split('-')] for s in t_score.split('|')]
                                log_tournament_match(m['p1'], m['p2'], "Final", win, score_str=t_score)
                                club.update_match(win, (m['p2'] if win == m['p1'] else m['p1']), parsed, match_type="Best of 3")
                                st.session_state.bracket["F"]["w"] = win
                                st.balloons(); st.rerun()
                            except: st.error("Format Error.")
                    else: st.info("Match in progress...")
                elif m["w"]: st.success(f"👑 {m['w']}")

    st.markdown("---")
    st.markdown("#### 📜 SYSTEM ARCHIVE: TOURNAMENT MATCHES")
    st.dataframe(t_df.sort_index(ascending=False), use_container_width=True, hide_index=True)
elif menu == "LOG MATCH":
    st.markdown("#### 📝 RECORD RECENT DATA")
    if is_admin:
        with st.container(border=True):
            m_type = st.radio("MATCH FORMAT", ["Single", "Best of 3"], horizontal=True)

            col1, col2 = st.columns(2)
            with col1:
                w_name = st.selectbox("WINNER", sorted(list(club.players.keys())))
            with col2:
                l_name = st.selectbox("LOSER", sorted([p for p in club.players.keys() if p != w_name]))

            scores = []
            if m_type == "Best of 3":
                st.caption("Enter scores for each game (Winner-Loser)")
                c1, c2, c3 = st.columns(3)
                with c1: g1 = st.text_input("Game 1", value="11-5")
                with c2: g2 = st.text_input("Game 2", value="11-5")
                with c3: g3 = st.text_input("Game 3 (Optional)", value="", help="Leave blank if 2-0")
                
                scores = [g1, g2]
                if g3.strip(): scores.append(g3)
            else:
                score_single = st.text_input("SCORE", value="11-5")
                scores = [score_single]

            # --- EXECUTION BUTTON ---
            if st.button("🚀 EXECUTE LOG", use_container_width=True):
                try:
                    parsed_scores = []
                    for s in scores:
                        if "-" in s:
                            pts = [int(x.strip()) for x in s.split('-')]
                            if len(pts) == 2:
                                parsed_scores.append(pts)
                    
                    if not parsed_scores:
                        st.error("Invalid Score Format. Use '11-5'")
                    else:
                        # 1. Update the Glicko Ratings via the ClubManager
                        club.update_match(w_name, l_name, parsed_scores, match_type=m_type)
                        
                        # 2. Log to History Sheet
                        history_score = " | ".join(scores)
                        new_h_row = pd.DataFrame([{
                            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Winner": w_name,
                            "Loser": l_name,
                            "Score": history_score,
                            "Match_Type": m_type
                        }])
                        
                        updated_h = pd.concat([h_df, new_h_row], ignore_index=True)
                        conn.update(worksheet="history", data=updated_h)
                        
                        st.success(f"✅ MATCH ARCHIVED: {w_name} def. {l_name} ({history_score})")
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"LOGGING ERROR: {e}")
    else:
        st.warning("🔒 Admin Key required to log match results.")
elif menu == "PLAYER INTEL":
    st.markdown("#### SUBJECT DOSSIER")
    name = st.selectbox("IDENTIFY", sorted(list(club.players.keys())))
    p = club.players[name]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("CURRENT RATING", int(p.rating), delta=f"{int(p.rd)} RD")
        if not h_df.empty:
            p_matches = h_df[(h_df['Winner'] == name) | (h_df['Loser'] == name)]
            wins = len(p_matches[p_matches['Winner'] == name])
            losses = len(p_matches[p_matches['Loser'] == name])
            st.write(f"**RECORD:** {wins}W - {losses}L")
            if (wins + losses) > 0:
                st.write(f"**WIN RATE:** {int((wins/(wins+losses))*100)}%")

    with col2:
        st.caption("RATING PROGRESSION")
        if not h_df.empty:
            personal_history = h_df[(h_df['Winner'] == name) | (h_df['Loser'] == name)].copy()
            
            current_rating = 750
            ratings_over_time = []
            
            for _, row in personal_history.iterrows():
                # It adds 25 for a win and subtracts 20 for a loss just for the visual
                if row['Winner'] == name:
                    current_rating += 25
                else:
                    current_rating -= 20
                ratings_over_time.append(current_rating)
            
            personal_history['Rating_History'] = ratings_over_time
            st.line_chart(personal_history.set_index('Date')['Rating_History'])
            st.markdown("---")
        st.caption("RECENT MATCH HISTORY")
        if not personal_history.empty:
            # We reverse it to show the most recent matches at the top
            display_history = personal_history.sort_index(ascending=False).head(10)
            
            # Clean up columns for a better look
            display_history = display_history[['Date', 'Winner', 'Loser', 'Score', 'Match_Type']]
            
            st.dataframe(display_history, use_container_width=True, hide_index=True)
        else:
            st.info("No match data recorded for this subject.")
            

elif menu == "VERSUS":
    st.markdown("#### MATCHUP ANALYSIS")
    p1_n = st.selectbox("PLAYER A", sorted(list(club.players.keys())))
    p2_n = st.selectbox("PLAYER B", sorted([x for x in club.players.keys() if x != p1_n]))
    
    p1, p2 = club.players[p1_n], club.players[p2_n]
    prob = 1 / (1 + math.pow(10, ((p2.rating - p1.rating) / 400)))
    
    # Visual Probability Bar
    st.write(f"**{p1_n}** has a **{int(prob*100)}%** predicted chance to win.")
    st.progress(prob)
    
    # Head-to-Head Stats
    if not h_df.empty:
        h2h = h_df[((h_df['Winner'] == p1_n) & (h_df['Loser'] == p2_n)) | 
                   ((h_df['Winner'] == p2_n) & (h_df['Loser'] == p1_n))]
        
        p1_h2h_wins = len(h2h[h2h['Winner'] == p1_n])
        p2_h2h_wins = len(h2h[h2h['Winner'] == p2_n])
        
        st.markdown("---")
        st.caption("HEAD-TO-HEAD HISTORY")
        
        chart_data = pd.DataFrame({
            "Player": [p1_n, p2_n],
            "Wins": [p1_h2h_wins, p2_h2h_wins]
        })
        st.bar_chart(chart_data.set_index("Player"))
        
elif menu == "HALL OF FAME":
    st.markdown("#### 🏛️ SEASON RECORDS")
    
    # 1. Load Archive Data
    archive_df = conn.read(worksheet="archives")
    
    if archive_df.empty:
        st.info("No archived seasons found. Finish a season to see history here!")
    else:
        # 2. Season Selector
        seasons = archive_df['Season'].unique()
        selected_season = st.selectbox("Select Season", seasons)
        
        # 3. Filter and Display
        season_data = archive_df[archive_df['Season'] == selected_season].sort_values(by="Rating", ascending=False)
        
        # 4. Display Podium
        top_3 = season_data.head(3)
        cols = st.columns(3)
        podium_titles = ["🥇 1st Place", "🥈 2nd Place", "🥉 3rd Place"]
        
        for i, col in enumerate(cols):
            if i < len(top_3):
                with col:
                    st.metric(podium_titles[i], top_3.iloc[i]['Name'], f"{int(top_3.iloc[i]['Rating'])} pts")

        st.markdown("---")
        st.dataframe(season_data, use_container_width=True, hide_index=True)
        
        


st.markdown('<div class="floating-legend">', unsafe_allow_html=True)
with st.popover("📜 STATUS KEY"):
    st.markdown("### UTTR // SYSTEM STATUS DEFINITIONS")
    st.markdown("""
    | Status | Requirement | Description |
    | :--- | :--- | :--- |
    | 🥇 **CHAMP** | Rank #1 | Current King of the Hill. |
    | 😤 **DOMINANT** | 3+ Blowouts | Won last 3 matches by a spread of 7+ points. |
    | 🔥 **ON FIRE** | 3 Match Streak | Momentum is building; high win probability. |
    | 👑 **UNSTOPPABLE** | 5 Match Streak | Elite consistency; the player to beat. |
    | 🧊 **COLD** | 3 Loss Streak | Performance dip detected; high volatility. |
    | 🛡️ **WALL** | RD < 50 | Rating is solidified; very difficult to move. |
    | 💎 **VETERAN** | 50+ Matches | Long-term data confirmed; highly reliable. |
    | 🐣 **ROOKIE** | < 5 Matches | Initial calibration phase; low data confidence. |
    | 🔨 **SLAYER** | Giant Killer | Recently defeated a Top 3 ranked player. |
    | ❓ **UNKNOWN** | RD > 200 | Inactive or new; rating is highly speculative. |
    """)
st.markdown('</div>', unsafe_allow_html=True)