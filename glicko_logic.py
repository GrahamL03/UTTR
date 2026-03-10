import glicko2
import pandas as pd
import os
from datetime import datetime

class ClubManager:
    def head_to_head(self, name1, name2):
        # 1. Load history
        if not os.path.exists(self.history_file):
            print("❌ No match history found yet.")
            return
            
        df = pd.read_csv(self.history_file)
        
        # 2. Find the full names from the current player list (fuzzy search)
        n1_matches = [p for p in self.players.keys() if name1.lower() in p.lower()]
        n2_matches = [p for p in self.players.keys() if name2.lower() in p.lower()]
        
        if not n1_matches or not n2_matches:
            print("❌ One or both players not found.")
            return
            
        p1 = n1_matches[0]
        p2 = n2_matches[0]

        # 3. Filter for matches between these two specifically
        # (Where P1 won and P2 lost, OR P2 won and P1 lost)
        h2h = df[((df['Winner'] == p1) & (df['Loser'] == p2)) | 
                 ((df['Winner'] == p2) & (df['Loser'] == p1))]

        if h2h.empty:
            print(f"🤷 {p1} and {p2} haven't played each other yet.")
            return

        # 4. Count the wins
        p1_wins = len(h2h[h2h['Winner'] == p1])
        p2_wins = len(h2h[h2h['Winner'] == p2])
        
        print(f"\n🔥 --- HEAD TO HEAD: {p1} vs {p2} --- 🔥")
        print(f"🏆 Total Matches: {len(h2h)}")
        print(f"🥇 {p1}: {p1_wins} Wins")
        print(f"🥈 {p2}: {p2_wins} Wins")
        
        # Show the most recent scores
        print("\nRecent Results:")
        print(h2h[['Date', 'Winner', 'Score']].tail(5).to_string(index=False))
    def get_top_10(self):
        data = []
        for name, p in self.players.items():
            data.append({"Name": name, "Rating": p.rating, "RD": p.rd})
        
        df = pd.DataFrame(data).sort_values(by="Rating", ascending=False)
        print("\n🏆 --- TOP 10 LEADERBOARD --- 🏆")
        print(df.head(10).round(1).to_string(index=False))

    def search_player(self, name):
        # Case-insensitive search to find the correct full name
        matches = [p for p in self.players.keys() if name.lower() in p.lower()]
        
        if not matches:
            print(f"❌ No player found matching '{name}'.")
            return

        # Load history to calculate stats
        history_df = pd.read_csv(self.history_file) if os.path.exists(self.history_file) else pd.DataFrame()

        print("\n🔍 --- PLAYER PROFILE ---")
        for m in matches:
            p = self.players[m]
            
            # Calculate Wins and Losses from the history file
            wins = 0
            losses = 0
            if not history_df.empty:
                wins = len(history_df[history_df['Winner'] == m])
                losses = len(history_df[history_df['Loser'] == m])
            
            total_games = wins + losses
            win_rate = (wins / total_games * 100) if total_games > 0 else 0

            print(f"👤 Name: {m}")
            print(f"📊 UTTR Rating: {round(p.rating, 1)}")
            print(f"📈 Record: {wins}W - {losses}L ({round(win_rate, 1)}% Win Rate)")
            print(f"📉 Confidence (RD): {round(p.rd, 1)}")
            print("-" * 25)

    def save_and_show(self):
        # We keep this for saving, but we'll call specific show methods in the menu
        data = []
        for name, p in self.players.items():
            data.append({"Name": name, "Rating": p.rating, "RD": p.rd, "Sigma": p.vol})
        
        df = pd.DataFrame(data).sort_values(by="Rating", ascending=False)
        df.to_csv(self.filename, index=False)
    def __init__(self, filename="players.csv", history_file="history.csv"):
        self.filename = filename
        self.history_file = history_file
        self.players = {}
        self.load_players()

    def load_players(self):
        if os.path.exists(self.filename):
            df = pd.read_csv(self.filename)
            for _, row in df.iterrows():
                self.players[row['Name']] = glicko2.Player(row['Rating'], row['RD'], row['Sigma'])
        else:
            # Default starting roster
            for name in ["Graham Long", "Cooper Juchno", "Oliver Strickfaden", "Vincent Spoljarick"]:
                self.players[name] = glicko2.Player()
            self.save_and_show()

    def check_or_add_player(self, name):
        if name not in self.players:
            print(f"✨ New player detected! Adding {name} to the league.")
            self.players[name] = glicko2.Player()

    def update_match(self, w_name, l_name, w_pts, l_pts):
        # Ensure both players exist in the system
        self.check_or_add_player(w_name)
        self.check_or_add_player(l_name)

        winner = self.players[w_name]
        loser = self.players[l_name]

        spread = w_pts - l_pts
        multiplier = 1 + (spread / 22) 

        w_old_r = winner.rating
        l_old_r = loser.rating

        winner.update_player([l_old_r], [loser.rd], [1])
        loser.update_player([w_old_r], [winner.rd], [0])

        winner.rating += (winner.rating - w_old_r) * (multiplier - 1)
        loser.rating += (loser.rating - l_old_r) * (multiplier - 1)
        
        self.log_match(w_name, l_name, w_pts, l_pts)

    def log_match(self, w, l, wp, lp):
        # Create a history entry
        new_entry = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Winner": w,
            "Loser": l,
            "Score": f"{wp}-{lp}"
        }])
        
        # Append to history file
        if not os.path.exists(self.history_file):
            new_entry.to_csv(self.history_file, index=False)
        else:
            new_entry.to_csv(self.history_file, mode='a', header=False, index=False)

    def save_and_show(self):
        data = []
        for name, p in self.players.items():
            data.append({"Name": name, "Rating": p.rating, "RD": p.rd, "Sigma": p.vol})
        
        df = pd.DataFrame(data).sort_values(by="Rating", ascending=False)
        df.to_csv(self.filename, index=False)
        
        print("\n--- CURRENT RANKINGS ---")
        print(df[["Name", "Rating", "RD"]].round(1).to_string(index=False))
        
        
