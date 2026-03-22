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
            self.players[name] = glicko2.Player(rating=750)
        self.save_to_cloud()

    def check_or_add_player(self, name):
        """Internal check to ensure a player exists in the local dictionary."""
        if name not in self.players:
            self.players[name] = glicko2.Player(rating=750)

    def add_new_player(self, name):
        """Registers a new player and immediately pushes to Google Sheets."""
        name = name.strip()
        if name and name not in self.players:
            self.players[name] = glicko2.Player(rating=750)
            self.save_to_cloud() 
            return True
        return False
    
    def update_match(self, w_name, l_name, parsed_scores, match_type="Single"):
        """
        parsed_scores: List of lists, e.g., [[11, 5], [11, 9]]
        """
        self.check_or_add_player(w_name)
        self.check_or_add_player(l_name)

        winner = self.players[w_name]
        loser = self.players[l_name]
        w_old_r, l_old_r = winner.rating, loser.rating
        w_old_rd, l_old_rd = winner.rd, loser.rd

        # 1. Core Glicko-2 Calculation (The "Who won" part)
        winner.update_player([l_old_r], [l_old_rd], [1])
        loser.update_player([w_old_r], [w_old_rd], [0])

        # 2. Multiplier Logic (The "How badly" part)
        # Calculate the average point spread across all games
        total_spread = sum(abs(game[0] - game[1]) for game in parsed_scores)
        avg_spread = total_spread / len(parsed_scores)
        
        # Spread multiplier (capped to prevent extreme spikes)
        spread_mult = 1 + (avg_spread / 22)
        
        # Match type boost (1.5x for Bo3)
        type_mult = 1.5 if match_type == "Best of 3" else 1.0
        
        final_multiplier = spread_mult * type_mult

        # Apply the weighted shift
        winner.rating += (winner.rating - w_old_r) * (final_multiplier - 1)
        loser.rating += (loser.rating - l_old_r) * (final_multiplier - 1)

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
        st.cache_data.clear()

    def create_tournament_bracket(self, player_list):
        """Creates an 8-man seeded bracket."""
        seeded = sorted(player_list, key=lambda x: self.players[x].rating, reverse=True)
        
        while len(seeded) < 8:
            seeded.append("BYE")

        bracket = {
            "QF": [
                {"p1": seeded[0], "p2": seeded[7], "w": None}, 
                {"p1": seeded[3], "p2": seeded[4], "w": None}, 
                {"p1": seeded[1], "p2": seeded[6], "w": None}, 
                {"p1": seeded[2], "p2": seeded[5], "w": None}  
            ],
            "SF": [
                {"p1": "TBD", "p2": "TBD", "w": None},
                {"p1": "TBD", "p2": "TBD", "w": None}
            ],
            "F": {"p1": "TBD", "p2": "TBD", "w": None}
        }
        return bracket