import streamlit as st
import pandas as pd
import os # <--- ADDED THIS
from glicko_logic import ClubManager

# Initialize the backend
if 'club' not in st.session_state:
    st.session_state.club = ClubManager()

club = st.session_state.club

st.set_page_config(page_title="UTTR League", page_icon="🏓", layout="wide")

st.title("🏓 UTTR: Universal Table Tennis Ranking")
st.markdown("---")

# --- SIDEBAR MENU ---
menu = st.sidebar.radio("Navigation", ["Leaderboard", "Record Match", "Player Search", "Head-to-Head"])

if menu == "Leaderboard":
    st.header("🏆 Top Rankings")
    data = [{"Rank": i+1, "Name": name, "Rating": round(p.rating, 1), "RD": round(p.rd, 1)} 
            for i, (name, p) in enumerate(sorted(club.players.items(), key=lambda x: x[1].rating, reverse=True))]
    df = pd.DataFrame(data)
    st.table(df.head(10)) 

elif menu == "Record Match":
    st.header("📝 Record a Match Result")
    
    # Checkbox to add someone new
    new_player = st.checkbox("Is there a new player?")
    
    col1, col2 = st.columns(2)
    with col1:
        if new_player:
            w_name = st.text_input("Winner Name")
        else:
            w_name = st.selectbox("Winner", sorted(list(club.players.keys())))
        w_score = st.number_input("Winner Score", min_value=0, value=11)
        
    with col2:
        if new_player:
            l_name = st.text_input("Loser Name")
        else:
            l_name = st.selectbox("Loser", sorted([p for p in club.players.keys() if p != w_name]))
        l_score = st.number_input("Loser Score", min_value=0, value=9)

    if st.button("Submit Result"):
        if w_name and l_name:
            club.update_match(w_name, l_name, w_score, l_score)
            club.save_and_show()
            st.success(f"Match recorded! {w_name} vs {l_name} ({w_score}-{l_score})")
            st.rerun() # Refresh to update the player list
        else:
            st.error("Please enter both names!")

elif menu == "Player Search":
    st.header("🔍 Player Profile")
    search_name = st.selectbox("Select Player", sorted(list(club.players.keys())))
    p = club.players[search_name]
    
    # Calculate Wins/Losses for the profile
    if os.path.exists(club.history_file):
        h_df = pd.read_csv(club.history_file)
        wins = len(h_df[h_df['Winner'] == search_name])
        losses = len(h_df[h_df['Loser'] == search_name])
    else:
        wins, losses = 0, 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Rating", round(p.rating, 1))
    c2.metric("Record", f"{wins}W - {losses}L")
    c3.metric("Confidence (RD)", round(p.rd, 1))

elif menu == "Head-to-Head":
    st.header("🔥 Rivalry Stats")
    p1 = st.selectbox("Player 1", sorted(list(club.players.keys())))
    p2 = st.selectbox("Player 2", sorted([p for p in club.players.keys() if p != p1]))
    
    if st.button("Compare"):
        if os.path.exists(club.history_file):
            df = pd.read_csv(club.history_file)
            h2h = df[((df['Winner'] == p1) & (df['Loser'] == p2)) | 
                     ((df['Winner'] == p2) & (df['Loser'] == p1))]
            
            if h2h.empty:
                st.warning(f"No matches found between {p1} and {p2} yet!")
            else:
                p1_wins = len(h2h[h2h['Winner'] == p1])
                p2_wins = len(h2h[h2h['Winner'] == p2])
                
                c1, c2, c3 = st.columns(3)
                c1.metric(p1, f"{p1_wins} Wins")
                c2.markdown("<h1 style='text-align: center;'>VS</h1>", unsafe_allow_html=True)
                c3.metric(p2, f"{p2_wins} Wins")
                
                st.subheader("Match History")
                st.dataframe(h2h[['Date', 'Winner', 'Score']].tail(10), use_container_width=True)
        else:
            st.error("No history file found.")