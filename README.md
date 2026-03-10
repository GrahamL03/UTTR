# UTTR // NOVI

## Universal Table Tennis Rankings & Tournament Management System

UTTR (Universal Table Tennis Rankings) is a professional-grade league management platform developed for Detroit Catholic Central. It utilizes the **Glicko-2** rating system—the same mathematical framework used by competitive chess and professional esports—to provide highly accurate skill assessment, automated tournament seeding, and longitudinal performance tracking.

---

## Technical Architecture

The system is built on a high-concurrency, cloud-synchronized architecture designed for low latency and data integrity:

* **Logic Engine:** A custom implementation of the Glicko-2 algorithm, accounting for Rating Deviation (RD) and Volatility ($\sigma$).
* **Data Layer:** Real-time integration with Google Sheets API via `streamlit-gsheets`, serving as a distributed database for cross-device synchronization.
* **Interface:** A Streamlit-driven Single Page Application (SPA) utilizing custom CSS injection to provide a high-contrast, professional-grade user interface.
* **Predictive Modeling:** Logistic distribution functions used to calculate win probabilities for any given matchup based on historical performance data.

---

## Mathematical Foundation: Glicko-2

The UTTR engine operates on the Glicko-2 scale. This system improves upon traditional Elo by introducing a confidence interval (Rating Deviation) and a consistency factor (Volatility).

### 1. Scaling to Glicko-2

Before computation, standard ratings ($R$) and deviations ($RD$) are converted to the Glicko-2 scale ($\mu$ and $\phi$):

$$\mu = \frac{R - 1500}{173.7178}$$

$$\phi = \frac{RD}{173.7178}$$

### 2. The Estimated Improvement

The system calculates the estimated improvement ($\Delta$) and the variance ($v$) based on the player's performance against opponents:

$$v = \left[ \sum_{j=1}^{m} g(\phi_j)^2 E(\mu, \mu_j, \phi_j) (1 - E(\mu, \mu_j, \phi_j)) \right]^{-1}$$

Where $g(\phi)$ is a weighting function:

$$g(\phi) = \frac{1}{\sqrt{1 + 3\phi^2 / \pi^2}}$$

### 3. Win Probability Calculation

The expected outcome $E$ (win probability) between Player A and Player B is calculated using a logistic curve:

$$E = \frac{1}{1 + e^{-g(\phi_j)(\mu - \mu_j)}}$$

### 4. Dominant Win Multiplier

To reward high-performance outcomes (e.g., an 11-0 shutout), UTTR applies a point-spread multiplier to the final rating shift:

$$\text{Multiplier} = 1 + \frac{|\text{Score Difference}|}{22}$$

---

Core Functionality1. Competitive Rating SystemThe UTTR engine moves beyond the static nature of traditional Elo by implementing a tri-variable assessment for every athlete. This ensures that the rankings reflect not just who you beat, but how reliably you perform.Rating ($\mu$): The primary skill estimate. New players enter the system at a standardized 1500. This value represents the player's "true" skill level after accounting for the difficulty of their historical opponents.Rating Deviation (RD / $\phi$): A measure of the system’s confidence in a player's rank.Activity-Based Decay: RD increases over time if a player is inactive, reflecting the system’s growing uncertainty about their current skill.Reliability: A low RD (represented by the 🛡️ WALL badge) indicates a verified veteran, while a high RD indicates a "Rookie" or "Inactive" status.Volatility ($\sigma$): A consistency metric that tracks a player's performance fluctuations. A player with high volatility is prone to "upsets," while low volatility indicates a highly predictable, consistent performance profile.2. Tournament Bracket ControlUTTR features a proprietary 8-man bracket automation system designed to minimize "easy paths" and maximize high-stakes matchups.Seeding-to-Rating Mapping: The system automatically scrapes the top 8 (or selected 8) ratings to generate a mathematically balanced bracket:Quadrant A: Seed 1 vs Seed 8 | Seed 4 vs Seed 5Quadrant B: Seed 2 vs Seed 7 | Seed 3 vs Seed 6Real-Time Advancement: Utilizing a state-machine architecture, the bracket handles "BYE" rounds for smaller fields and pushes winners to the next phase with a single click.Standings Integration: Unlike standard "friendly" tournaments, every match played within the bracket is fed back into the Glicko-2 engine, ensuring that playoff performance directly impacts the official league rankings.3. Predictive Analytics (The "Versus" Module)Before a match even begins, the system utilizes a Logistic Win-Probability Function. By comparing the $\mu$ and $\phi$ of two players, the engine can output a statistical favorite.Underdog Calculation: This is the foundation of the 🔨 SLAYER badge logic.Matchmaking: This tool allows club administrators to simulate potential matchups to find the most competitive pairings for exhibition play.
---

## System Status Key

The platform utilizes a dynamic badge system to signify performance milestones and statistical outliers:

| Badge | Criteria |
| --- | --- |
| 🥇 CHAMP | Occupies the Rank 1 position in the league standings. |
| 😤 DOMINANT | Secured the last 3 match victories by a point spread greater than 6. |
| 🔥 ON FIRE | Achieved 3 consecutive match victories. |
| 👑 UNSTOPPABLE | Achieved 5 or more consecutive match victories. |
| 🛡️ WALL | RD is below 50, signifying a highly stable and verified rank. |
| 🔨 SLAYER | A non-top 3 player who defeated a Top 3 opponent. |
| 💎 VETERAN | Logged a minimum of 50 competitive matches. |
| 🐣 ROOKIE | Logged fewer than 5 competitive matches. |
| 🧊 COLD | Sustained 3 or more consecutive match losses. |
| ⚡ RAID | Maintained a perfect 5-0 record over the most recent 5 matches. |
| ❓ UNKNOWN | RD exceeds 120, requiring more data for an accurate assessment. |

---

## Installation and Deployment

### Dependency Installation

To set up the local environment, install the required packages:

```bash
pip install streamlit pandas streamlit-gsheets glicko2

```

### Execution

Run the application via the Streamlit CLI:

```bash
streamlit run app.py

```

---

**Document Revision:** 4.2.1

**Environment:** NOVI_MI // Detroit Catholic Central

**Developer:** G. Long
