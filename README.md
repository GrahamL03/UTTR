# UTTR // NOVI

## Unified Table Tennis Rankings & Tournament Management System

UTTR (Unified Table Tennis Rankings) is a professional-grade league management platform developed for Detroit Catholic Central. It utilizes the **Glicko-2** rating system—the same mathematical framework used by competitive chess and professional esports—to provide highly accurate skill assessment, automated tournament seeding, and longitudinal performance tracking.

---

## Technical Architecture

The system is built on a high-concurrency, cloud-synchronized architecture:

* **Logic Engine:** Implementation of the Glicko-2 algorithm, accounting for Rating Deviation (RD) and Volatility ($\sigma$).
* **Data Layer:** Real-time integration with Google Sheets via `st.connection`, serving as a distributed database.
* **Interface:** Streamlit-driven SPA (Single Page Application) with custom CSS injection for high-contrast, low-latency navigation.
* **Predictive Modeling:** Logistic distribution functions used to calculate win probabilities for any given matchup.

---

## Core Functionality

### 1. Competitive Rating System

Unlike traditional Elo systems, UTTR measures three distinct variables for every player:

* **Rating:** The estimated skill level (standardized at 1500 for new subjects).
* **Rating Deviation (RD):** The degree of certainty the system has in a player's rank. High RD indicates "Unknown" status; low RD indicates a "Stable" rank.
* **Volatility:** The degree of expected fluctuation in a player's performance.

### 2. Tournament Bracket Control

The system features an automated 8-man bracket generator. Matches are seeded to ensure competitive integrity:

* **Primary Pairings:** 1v8, 4v5, 2v7, 3v6.
* **Dynamic Advancement:** Winners are moved through Quarterfinals, Semifinals, and Finals in real-time, with results immediately impacting league standings.

### 3. Subject Dossiers and Matchup Analysis

* **Intel Tracking:** Comprehensive win/loss records and win-rate percentages.
* **Progression Visualization:** Time-series charts tracking rating shifts over the course of the season.
* **Head-to-Head Statistics:** Historical data comparison between specific players to determine historical dominance.

---

## System Status Key

The platform utilizes a dynamic badge system to signify performance milestones and psychological states:

| Badge | Criteria |
| --- | --- |
| 🥇 CHAMP | Occupies the Rank 1 position in the league. |
| 🔥 ON FIRE | Achieved 3 consecutive match victories. |
| 👑 UNSTOPPABLE | Achieved 5+ consecutive match victories. |
| 🛡️ WALL | RD is below 50, signifying a highly stable and verified rank. |
| 🔨 SLAYER | A non-top 3 player who defeated a Top 3 opponent. |
| 💎 VETERAN | Logged a minimum of 50 competitive matches. |
| 🐣 ROOKIE | Logged fewer than 5 competitive matches. |
| 🧊 COLD | Sustained 3+ consecutive match losses. |
| ⚡ RAID | Maintained a perfect 5-0 record over the last 5 matches. |
| ❓ UNKNOWN | RD exceeds 120, requiring more data for an accurate rank. |

---

## Installation and Deployment

### Environment Requirements

* Python 3.9 or higher
* Google Cloud Console Service Account (for Sheets API access)

### Dependency Installation

```bash
pip install streamlit pandas streamlit-gsheets glicko2

```

### Configuration

1. Create a `.streamlit/secrets.toml` file.
2. Populate the file with your Google Sheets `spreadsheet` URL and `service_account` credentials.
3. Ensure the spreadsheet contains three worksheets: `players`, `history`, and `tournament_matches`.

### Execution

```bash
streamlit run app.py

```

---

**Document Revision:** 4.2.0
**Environment:** NOVI_MI // Detroit Catholic Central
**Developer Note:** Ensure `st.cache_data.clear()` is called during match logs to prevent state desynchronization.

Would you like me to generate a technical deep-dive into the specific Glicko-2 equations used in the Python logic?
