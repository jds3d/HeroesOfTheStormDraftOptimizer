# Heroes of the Storm Draft Optimizer

This project is an optimized drafting system for **Heroes of the Storm** that uses game theory to create resilient drafts against opponent counters. By leveraging real-time data, synergy matrices, and map-specific adjustments, this system dynamically adapts drafts based on opponent tendencies and team strengths.

## Features

- **Game Theory-Based Drafting**: Focuses 70% on countering opponents' high-frequency heroes and 30% on internal team synergies.
- **Real-Time Adaptation**: Automatically updates draft recommendations based on opponent picks, using screen scraping to capture real-time data.
- **Map-Specific Hero Selection**: Balances map-specific win rates with general hero win rates, adjusting drafts to leverage map strengths.
- **Flexible Role Balance**: Allows flexibility in role balance if team composition shows high synergy.
- **Exponential Decay Weighting**: Prioritizes recent games, especially those on the latest patch, for draft decisions.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/HeroesOfTheStormDraftOptimizer.git
