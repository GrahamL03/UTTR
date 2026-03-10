import glicko2
import pandas as pd
import streamlit as st
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

class ClubManager:
    def __init__(self):
        # Initialize connection to Google Sheets
        self.conn = st.connection("gsheets", type=GSheetsConnection)
        self.players = {}
        self.load_players()

    def load_players(self):
        """Pulls the latest ratings from Google Sheets with 0 cache to prevent ghosting."""
        try:
            df = self.conn.read(worksheet="players", ttl=0)
            if df is not None and not df.empty:
                self.players = {}
                for _, row in df.iterrows():
                    self.players[row['Name']] = glicko2.Player(
                        float(row['Rating']), 
                        float(row['RD']), 
                        float(row['Sigma'])
                    )
            else:
                self.initialize_default_roster()
        except Exception as e:
            st.error(f"DATABASE READ ERROR: {e}")
            self.initialize_default_roster()

    def initialize_default_roster(self):
        """Sets up starting players if the sheet is found empty."""
        names = ["Graham Long", "Cooper Juchno", "Oliver Strickfaden", "Vincent Spoljarick"]
        for name in names:
            self.players[name] = glicko2.Player()
        self.save_to_cloud()

    def check_or_add_player(self, name):
        """Internal check to ensure a player exists in the local dictionary."""
        if name not in self.players:
            self.players[name] = glicko2.Player()

    def add_new_player(self, name):
        """Registers a new player and immediately pushes to Google Sheets."""
        name = name.strip()
        if name and name not in self.players:
            self.players[name] = glicko2.Player()
            self.save_to_cloud() # Forces the new player into the DB immediately
            return True
        return False
    
    def update_match(self, w_name, l_name, w_pts, l_pts):
        """Calculates Glicko-2 shift and pushes result to the cloud."""
        self.check_or_add_player(w_name)
        self.check_or_add_player(l_name)

        winner = self.players[w_name]
        loser = self.players[l_name]

        # Capture old states for the Glicko update
        w_old_r, l_old_r = winner.rating, loser.rating
        w_old_rd, l_old_rd = winner.rd, loser.rd

        # Core Glicko-2 Update (1 = win, 0 = loss)
        winner.update_player([l_old_r], [l_old_rd], [1])
        loser.update_player([w_old_r], [w_old_rd], [0])

        # Point Spread Multiplier: Rewards dominant wins (e.g., 11-0)
        spread = abs(w_pts - l_pts)
        multiplier = 1 + (spread / 22) 

        # Apply the multiplier to the rating change
        winner.rating += (winner.rating - w_old_r) * (multiplier - 1)
        loser.rating += (loser.rating - l_old_r) * (multiplier - 1)
        
        self.save_to_cloud()

    def save_to_cloud(self):
        """Overwrites the 'players' worksheet with sorted, updated ratings."""
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
        
        # Clear Streamlit's internal cache so the next load_players() sees the new data
        st.cache_data.clear()

    def create_tournament_bracket(self, player_list):
        """
        Creates an 8-man seeded bracket.
        Seeds based on current rating: 1 vs 8, 2 vs 7, 3 vs 6, 4 vs 5.
        """
        # Sort selected players by their current rating
        seeded = sorted(player_list, key=lambda x: self.players[x].rating, reverse=True)
        
        # Handle cases with fewer than 8 by padding with 'BYE' (if necessary)
        while len(seeded) < 8:
            seeded.append("BYE")

        bracket = {
            "QF": [
                {"p1": seeded[0], "p2": seeded[7], "w": None}, # Seed 1 vs 8
                {"p1": seeded[3], "p2": seeded[4], "w": None}, # Seed 4 vs 5
                {"p1": seeded[1], "p2": seeded[6], "w": None}, # Seed 2 vs 7
                {"p1": seeded[2], "p2": seeded[5], "w": None}  # Seed 3 vs 6
            ],
            "SF": [
                {"p1": "TBD", "p2": "TBD", "w": None},
                {"p1": "TBD", "p2": "TBD", "w": None}
            ],
            "F": {"p1": "TBD", "p2": "TBD", "w": None}
        }
        return bracket