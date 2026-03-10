# UTTR // NOVI

## Universal Table Tennis Rankings & Tournament Management System

UTTR (Universal Table Tennis Rankings) is a professional-grade league management platform developed for Detroit Catholic Central. It utilizes the **Glicko-2** rating system—the same mathematical framework used by competitive chess and professional esports—to provide highly accurate skill assessment, automated tournament seeding, and longitudinal performance tracking.

---

## Technical Architecture

The system is built on a high-concurrency, cloud-synchronized architecture:

* **Logic Engine:** Implementation of the Glicko-2 algorithm, accounting for Rating Deviation (RD) and Volatility ($\sigma$).
* **Data Layer:** Real-time integration with Google Sheets via `st.connection`, serving as a distributed database.
* **Interface:** Streamlit-driven SPA (Single Page Application) with custom CSS injection for high-contrast, low-latency navigation.
* **Predictive Modeling:** Logistic distribution functions used to calculate win probabilities for any given matchup.

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

In the "Versus" module, this is presented as a percentage to represent the statistical favorite.

### 4. Dominant Win Multiplier

To reward high-performance outcomes (e.g., an 11-0 shutout), UTTR applies a point-spread multiplier to the final rating shift:

$$\text{Multiplier} = 1 + \frac{|\text{Score Difference}|}{22}$$

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

---

## System Status Key

The platform utilizes a dynamic badge system to signify performance milestones:

| Badge | Criteria |
| --- | --- |
| 🥇 CHAMP | Occupies the Rank 1 position in the league. |
| 🔥 ON FIRE | Achieved 3 consecutive match victories. |
| 👑 UNSTOPPABLE | Achieved 5+ consecutive match victories. |
| 🛡️ WALL | RD is below 50, signifying a highly stable rank. |
| 🔨 SLAYER | A non-top 3 player who defeated a Top 3 opponent. |
| 💎 VETERAN | Logged a minimum of 50 competitive matches. |
| 🐣 ROOKIE | Logged fewer than 5 competitive matches. |
| 🧊 COLD | Sustained 3+ consecutive match losses. |
| ⚡ RAID | Maintained a perfect 5-0 record over the last 5 matches. |
| ❓ UNKNOWN | RD exceeds 120, requiring more data for an accurate rank. |
| 😤  Dominant | Last 3 matches have been won by 6 or more. |

---

## Installation and Deployment

### Dependency Installation

```bash
pip install streamlit pandas streamlit-gsheets glicko2

```

### Execution

```bash
streamlit run app.py

```

---

**Document Revision:** 4.2.0
**Environment:** NOVI_MI // Detroit Catholic Central
