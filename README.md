# Heroes of the Storm Draft Optimizer

## Overview
The **Heroes of the Storm Draft Optimizer** is a smart drafting system designed to **select the strongest possible team composition** by leveraging **map strength, role balance, and counter-picking against enemy tendencies**.

## Features

✅ **Map-Specific Hero Selection**
- Prioritizes heroes with **high win rates on the current map**.
- Uses a **×10 weighting multiplier** for map strength.

✅ **Counter-Based Drafting**
- Factors in **matchup advantage** against enemy picks.
- Helps **avoid weak matchups** while targeting enemy weaknesses.

✅ **Flexible Role Balance**
- Enforces **required roles (Tank, Healer, Offlaner)**.
- Allows **early-draft flexibility**, ensuring required roles are filled later.

✅ **Banning Algorithm with Score Impact**
- **Targets heroes that significantly weaken enemy players**.
- Shows **score drop impact** and the **second-best pick forced on the enemy**.

## Drafting Priorities
- **Primary Focus:** **Map-Specific Performance** (heavily weighted).
- **Secondary Focus:** **Countering Opponents** (included but less dominant).
- **Synergy Consideration:** **Role balance only** (no direct synergy scoring).

## Installation

### **1. Clone the Repository**
```sh
git clone https://github.com/<your-username>/HeroesOfTheStormDraftOptimizer.git
cd HeroesOfTheStormDraftOptimizer
