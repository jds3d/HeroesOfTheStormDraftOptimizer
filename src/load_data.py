import os
import pickle
from heroes_profile_api import get_team_data, get_match_data, get_hero_data

DATA_DIR = "../data"


def fetch_match_data_for_draft(match_id):
    """Fetches and caches match data for drafting."""
    cache_file = f"match_{match_id}.pkl"
    file_path = os.path.join(DATA_DIR, cache_file)

    if os.path.exists(file_path):
        print(f"Loaded cached match data for {match_id}")
        return pickle.load(open(file_path, "rb"))

    match_data = get_match_data(match_id)
    if not match_data:
        return None

    team_heroes, opponent_heroes = [], []

    for player in match_data["players"]:
        hero_data = get_hero_data(player["hero"])
        (team_heroes if player["team"] == "ally" else opponent_heroes).append(hero_data)

    draft_data = {"team_heroes": team_heroes, "opponent_heroes": opponent_heroes}
    pickle.dump(draft_data, open(file_path, "wb"))

    print(f"Saved match data for {match_id}")
    return draft_data


def fetch_team_profile(battle_tags, mmr_threshold=2700):
    """
    Fetches and displays each player's:
    - Top 3 heroes and preferred role from NGS.
    - Heroes over 2700 MMR in Storm League with win rate and games played.
    """
    team_ngs_data = get_team_data(battle_tags, ngs=True)  # NGS data
    team_sl_data = get_team_data(battle_tags, ngs=False)  # Storm League data

    if not team_ngs_data and not team_sl_data:
        print("Failed to retrieve team data.")
        return None

    for tag in battle_tags:
        print(f"\n--- {tag} ---")

        # Fetch NGS data
        ngs_data = team_ngs_data.get(tag, {})
        top_three_heroes = ngs_data.get("top_three_heroes", [])
        preferred_role = ngs_data.get("preferred_role", "Unknown")

        print(f"Preferred Role: {preferred_role}")
        print(f"Top 3 Heroes: {', '.join(top_three_heroes) if top_three_heroes else 'N/A'}")

        # Fetch Storm League data
        sl_data = team_sl_data.get(tag, {}).get("Storm League", {})

        if not sl_data:
            print("No Storm League data available.")
            continue

        # Extract heroes with MMR > threshold
        filtered_heroes = [
            (hero, stats["mmr"], stats["win_rate"], stats["games_played"])
            for hero, stats in sl_data.items()
            if stats.get("mmr", 0) > mmr_threshold
        ]

        # Sort by MMR in descending order
        sorted_heroes = sorted(filtered_heroes, key=lambda x: x[1], reverse=True)

        # Display Storm League heroes over threshold
        if sorted_heroes:
            print("\nStorm League Heroes (MMR > 2700):")
            for hero, mmr, win_rate, games_played in sorted_heroes:
                print(f" - {hero}: MMR: {mmr:.2f}, Win Rate: {win_rate:.2f}%, Games Played: {games_played}")
        else:
            print("\nNo heroes over 2700 MMR in Storm League.")

    return team_ngs_data, team_sl_data


if __name__ == "__main__":
    # Replace with the BattleTags of your team members
    # team_battle_tags = ["HuckIt#1840", "topgun707#1875", "beachyman#1138", "mrhustler#1686", "mojoe#11242", "papichulo#12352", "grkfreezer#1906", "yarrface#1316", "woot#11617"]

    # Fancy Flightless Fowl - https://nexusgamingseries.org/teamProfile/Fancy_Flightless_Fowl
    team_battle_tags = ["Alfie#1948", "Silverbell#11333", "AngryPanda#12178", "GingiBoi#1791", "XxLuNaTiCxX#11820", "Stefwithanf#1470"]
    fetch_team_profile(team_battle_tags, mmr_threshold=2700)
