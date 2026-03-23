import glicko2
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

class ClubManager:
    def __init__(self):
        self.conn = st.connection("gsheets", type=GSheetsConnection)
        self.players = {}
        self.load_players()

    def load_players(self):
        """Pulls the latest ratings from Google Sheets."""
        try:
            # ttl=0 ensures we don't get cached (old) data
            df = self.conn.read(worksheet="players", ttl=0)
            if df is not None and not df.empty:
                self.players = {}
                for _, row in df.iterrows():
                    # Ensure we handle the volatility attribute correctly
                    vol = float(row.get('Sigma', 0.06)) 
                    self.players[row['Name']] = glicko2.Player(
                        float(row['Rating']), 
                        float(row['RD']), 
                        vol
                    )
            else:
                self.initialize_default_roster()
        except Exception as e:
            st.error(f"DATABASE READ ERROR: {e}")
            self.initialize_default_roster()

    def initialize_default_roster(self):
        names = ["Graham Long", "Cooper Juchno", "Oliver Strickfaden", "Vincent Spoljarick"]
        for name in names:
            self.players[name] = glicko2.Player(rating=750)
        self.save_to_cloud()

    def check_or_add_player(self, name):
        if name not in self.players:
            self.players[name] = glicko2.Player(rating=750)

    def add_new_player(self, name):
        name = name.strip()
        if name and name not in self.players:
            self.players[name] = glicko2.Player(rating=750)
            self.save_to_cloud() 
            return True
        return False

    def update_match(self, w_name, l_name, scores, match_type="Single"):
        """
        Updates ratings. 
        'scores' should be a list of lists, e.g., [[11, 5], [11, 7]]
        """
        self.check_or_add_player(w_name)
        self.check_or_add_player(l_name)

        winner = self.players[w_name]
        loser = self.players[l_name]
        
        # 1. Standard Glicko-2 Update (The mathematical core)
        # Snapshot old values
        w_old_r, l_old_r = winner.rating, loser.rating
        w_old_rd, l_old_rd = winner.rd, loser.rd

        # Update based on a Match Win (1) vs Match Loss (0)
        winner.update_player([l_old_r], [l_old_rd], [1])
        loser.update_player([w_old_r], [w_old_rd], [0])

        # 2. Score-Based Multiplier Logic
        # Ensure scores is a list of lists even if only one game was passed
        if isinstance(scores[0], int):
            scores = [scores]

        total_spread = sum(abs(game[0] - game[1]) for game in scores)
        avg_spread = total_spread / len(scores)
        
        # Boost rating change: more points for blowouts (avg_spread) 
        # and more points for long-format matches (type_mult)
        spread_mult = 1 + (avg_spread / 22)
        type_mult = 1.5 if match_type == "Best of 3" or len(scores) > 1 else 1.0
        final_multiplier = spread_mult * type_mult

        # Apply multiplier to the DIFFERENCE between new and old rating
        winner.rating = w_old_r + ((winner.rating - w_old_r) * final_multiplier)
        loser.rating = l_old_r + ((loser.rating - l_old_r) * final_multiplier)

        self.save_to_cloud()

    def save_to_cloud(self):
        """Pushes local dictionary state to Google Sheets."""
        data = []
        for name, p in self.players.items():
            data.append({
                "Name": name, 
                "Rating": p.rating, 
                "RD": p.rd, 
                "Sigma": p.vol # Using .vol to match the glicko2 library attribute
            })
        
        df = pd.DataFrame(data).sort_values(by="Rating", ascending=False)
        self.conn.update(worksheet="players", data=df)
        # Force Streamlit to forget old data versions
        st.cache_data.clear()

    def create_tournament_bracket(self, player_list):
        seeded = sorted(player_list, key=lambda x: self.players[x].rating, reverse=True)
        while len(seeded) < 8:
            seeded.append("BYE")

        return {
            "QF": [
                {"p1": seeded[0], "p2": seeded[7], "w": None}, 
                {"p1": seeded[3], "p2": seeded[4], "w": None}, 
                {"p1": seeded[1], "p2": seeded[6], "w": None}, 
                {"p1": seeded[2], "p2": seeded[5], "w": None}  
            ],
            "SF": [{"p1": "TBD", "p2": "TBD", "w": None}, {"p1": "TBD", "p2": "TBD", "w": None}],
            "F": {"p1": "TBD", "p2": "TBD", "w": None}
        }
        
    def save_to_sheets(self):
        # We must import these inside the function to avoid circular imports
        import streamlit as st
        from streamlit_gsheets import GSheetsConnection
        import pandas as pd

        # 1. RE-ESTABLISH THE CONNECTION LOCALLY
        conn = st.connection("gsheets", type=GSheetsConnection)

        # 2. PREPARE DATA
        data = []
        for name, p in self.players.items():
            data.append({
                "Name": name,
                "Rating": p.rating,
                "RD": p.rd,
                "Sigma": p.vol,
                "Wins": p.wins,
                "Losses": p.losses
            })
        
        # 3. PUSH TO CLOUD
        df = pd.DataFrame(data)
        conn.update(worksheet="players", data=df)
    
    def rebuild_ratings(self, history_df):
        import glicko2
        # 1. Reset everyone to baseline
        for name in self.players:
            self.players[name].rating = 750
            self.players[name].rd = 350
            self.players[name].vol = 0.06
            self.players[name].wins = 0    # Reset these!
            self.players[name].losses = 0  # Reset these!

        # 2. Sort history by date to ensure chronological order
        history_df = history_df.sort_values('Date')

        # 3. Replay every match
        for _, row in history_df.iterrows():
            w_name = row['Winner']
            l_name = row['Loser']
            
            # Ensure players exist in the current session
            if w_name in self.players and l_name in self.players:
                # We treat every match in history as a "Single" 
                # unless you want to get complex with scores here
                self.update_match(w_name, l_name, [[11, 5]], match_type="Single")

        # 4. Push the final recalculated numbers back to Google Sheets
        self.save_to_sheets()