Gemini said
UTTR // NOVI
Professional Table Tennis Ranking and Tournament Management System
UTTR (Unified Table Tennis Rankings) is a sophisticated league management platform developed for Detroit Catholic Central. It utilizes the Glicko-2 rating system—the same mathematical framework used by competitive chess and professional esports—to provide highly accurate skill assessment, automated tournament seeding, and longitudinal performance tracking.

Technical Architecture
The system is built on a high-concurrency, cloud-synchronized architecture:

Logic Engine: Implementation of the Glicko-2 algorithm, accounting for Rating Deviation (RD) and Volatility (σ).

Data Layer: Real-time integration with Google Sheets via st.connection, serving as a distributed database.

Interface: Streamlit-driven SPA (Single Page Application) with custom CSS injection for high-contrast, low-latency navigation.

Predictive Modeling: Logistic distribution functions used to calculate win probabilities for any given matchup.

Core Functionality
1. Competitive Rating System
Unlike traditional Elo systems, UTTR measures three distinct variables for every player:

Rating: The estimated skill level (standardized at 1500 for new subjects).

Rating Deviation (RD): The degree of certainty the system has in a player's rank. High RD indicates "Unknown" status; low RD indicates a "Stable" rank.

Volatility: The degree of expected fluctuation in a player's performance.

2. Tournament Bracket Control
The system features an automated 8-man bracket generator. Matches are seeded to ensure competitive integrity:

Primary Pairings: 1v8, 4v5, 2v7, 3v6.

Dynamic Advancement: Winners are moved through Quarterfinals, Semifinals, and Finals in real-time, with results immediately impacting league standings.

3. Subject Dossiers and Matchup Analysis
Intel Tracking: Comprehensive win/loss records and win-rate percentages.

Progression Visualization: Time-series charts tracking rating shifts over the course of the season.

Head-to-Head Statistics: Historical data comparison between specific players to determine historical dominance.

System Status Key
The platform utilizes a dynamic badge system to signify performance milestones and psychological states:

Installation and Deployment
Environment Requirements
Python 3.9 or higher

Google Cloud Console Service Account (for Sheets API access)

Dependency Installation
Configuration
Create a .streamlit/secrets.toml file.

Populate the file with your Google Sheets spreadsheet URL and service_account credentials.

Ensure the spreadsheet contains three worksheets: players, history, and tournament_matches.

Execution
Document Revision: 4.2.0

Environment: NOVI_MI // Detroit Catholic Central

Developer Note: Ensure st.cache_data.clear() is called during match logs to prevent state desynchronization.
