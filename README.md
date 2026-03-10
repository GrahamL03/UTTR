Universal Table Tennis Rating
Based off of UTR (Universal Tennis Rating)

## Quick Start
1. Clone the repo: `git clone https://github.com/GrahamL03/uttr.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Launch the hub: `streamlit run app.py`

 # System Features
## Advanced Rating Engine
Glicko-2 Implementation: Uses the industry-standard Glicko-2 algorithm for high-accuracy skill assessment.

Dynamic Volatility Tracking: The system calculates "Rating Deviation" (RD) to determine how stable or "certain" a player's rank is.

Point-Spread Sensitivity: Match updates factor in the margin of victory (e.g., an 11-0 shutout impacts ratings differently than an 11-9 nail-biter).

## Tactical User Interface
Forced Dark-Mode Aesthetics: A custom-coded "Onyx & Ombre" interface designed for high-contrast data readability.

Glassmorphism UI Elements: Modern, semi-transparent metric cards for displaying Elo, Win/Loss records, and Stability percentages.

Top-Tier Navigation: A streamlined sidebar for quick switching between the global leaderboard and individual player dossiers.

## Intelligence & Analytics
Predictive Win Probability: Real-time calculation of win chances between any two players using Glicko-2 mathematical curves.

Performance Evolution Graphs: Interactive line charts that visualize a player's rating journey and "climb" through the ranks.

Live Form Guide: Instant "Last 5" match tracking (W-L-W-W-L) to identify who is currently on a "heater."

Head-to-Head (H2H) Archive: A dedicated rivalry module that pulls historical match logs and total win counts between specific opponents.

## Data Management
Persistent Storage: Local CSV-based database architecture (players.csv, history.csv) ensures no data is lost between sessions.

Automated Match Logging: A simplified "Execute Log" interface that updates the entire global ranking system with a single click.

Cloud-Ready Architecture: Fully optimized for deployment on Streamlit Cloud with standardized requirements.txt dependency management.
