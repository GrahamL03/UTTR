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
