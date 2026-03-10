import glicko2
import pandas as pd
import streamlit as st
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

class ClubManager:
    def __init__(self):
        # This will now look at your fresh secrets.toml
        self.conn = st.connection("gsheets", type=GSheetsConnection)
        self.players = {}
        self.load_players()
    def load_players(self):
        """Pulls the latest ratings from Google Sheets."""
        try:
            df = self.conn.read(worksheet="players", ttl=0)
            if not df.empty:
                for _, row in df.iterrows():
                    self.players[row['Name']] = glicko2.Player(
                        float(row['Rating']), 
                        float(row['RD']), 
                        float(row['Sigma'])
                    )
            else:
                self.initialize_default_roster()
        except Exception:
            self.initialize_default_roster()

    def initialize_default_roster(self):
        """Sets up starting players if the sheet is empty."""
        names = ["Graham Long", "Cooper Juchno", "Oliver Strickfaden", "Vincent Spoljarick"]
        for name in names:
            self.players[name] = glicko2.Player()
        self.save_to_cloud()

    def check_or_add_player(self, name):
        if name not in self.players:
            self.players[name] = glicko2.Player()

    def update_match(self, w_name, l_name, w_pts, l_pts):
        self.check_or_add_player(w_name)
        self.check_or_add_player(l_name)

        winner = self.players[w_name]
        loser = self.players[l_name]

        spread = w_pts - l_pts
        multiplier = 1 + (spread / 22) 

        w_old_r, l_old_r = winner.rating, loser.rating
        w_old_rd, l_old_rd = winner.rd, loser.rd

        winner.update_player([l_old_r], [l_old_rd], [1])
        loser.update_player([w_old_r], [w_old_rd], [0])

        winner.rating += (winner.rating - w_old_r) * (multiplier - 1)
        loser.rating += (loser.rating - l_old_r) * (multiplier - 1)
        
        self.log_match_cloud(w_name, l_name, w_pts, l_pts)
        self.save_to_cloud()

    def log_match_cloud(self, w, l, wp, lp):
        new_entry = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Winner": w,
            "Loser": l,
            "Score": f"{wp}-{lp}"
        }])
        
        history_df = self.conn.read(worksheet="history", ttl=0)
        updated_history = pd.concat([history_df, new_entry], ignore_index=True)
        self.conn.update(worksheet="history", data=updated_history)

    def save_to_cloud(self):
        """Overwrites the 'players' worksheet with current ratings."""
        data = []
        for name, p in self.players.items():
            data.append({
                "Name": name, 
                "Rating": p.rating, 
                "RD": p.rd, 
                "Sigma": p.vol
            })
        
        df = pd.DataFrame(data).sort_values(by="Rating", ascending=False)
        self.conn.update(worksheet="players", data=df)