from heroes_profile_api import get_hero_data, get_player_data, get_match_data
from heroes_profile_api import get_team_data
import os
import pickle


def fetch_match_data_for_draft(match_id):
    """Retrieves data for all heroes in a match to help in drafting."""
    match_data = get_match_data(match_id)
    if not match_data:
        return

    # Extract player and hero information
    team_heroes = []
    opponent_heroes = []

    for player in match_data["players"]:
        hero_name = player["hero"]
        hero_data = get_hero_data(hero_name)

        # Classify hero as either team or opponent
        if player["team"] == "ally":
            team_heroes.append(hero_data)
        else:
            opponent_heroes.append(hero_data)

    return {
        "team_heroes": team_heroes,
        "opponent_heroes": opponent_heroes
    }


def fetch_team_profile(battle_tags, ngs=False):
    """Retrieves, displays, and saves profile data for each team member as a pickle file."""
    team_data = get_team_data(battle_tags, ngs)

    if not team_data:
        print("Failed to retrieve team data.")
        return

    # Ensure the ../data directory exists
    save_dir = "../data"
    os.makedirs(save_dir, exist_ok=True)

    for tag, data in team_data.items():
        print(f"\n--- {tag} ---")

        # Save each player's data as a pickle file
        save_path = os.path.join(save_dir, f"{tag.replace('#', '_')}.pkl")

        with open(save_path, "wb") as f:
            pickle.dump(data, f)

        print(f"Saved {tag}'s data to {save_path}")

        # Check if "Storm League" exists in player's data
        print(data)
        if "Storm League" not in data:
            continue

        # Extract heroes with MMR > 2500
        filtered_heroes = [
            (hero_name, stats["mmr"], stats["win_rate"], stats["games_played"])
            for hero_name, stats in data["Storm League"].items()
            if stats.get("mmr", 0) > 2700
        ]

        # Sort by MMR in descending order
        sorted_heroes = sorted(filtered_heroes, key=lambda x: x[1], reverse=True)

        # Print sorted heroes
        for hero_name, mmr, win_rate, games_played in sorted_heroes:
            print(f"Hero: {hero_name}, MMR: {mmr:.2f}, Win Rate: {win_rate:.2f}%, Games Played: {games_played}")

    return team_data


# # Example usage
# match_id = "123456"  # Replace with the actual match ID
# draft_data = fetch_match_data_for_draft(match_id)
# print(draft_data)

if __name__ == "__main__":
    # Replace with the BattleTags of your team members
    # team_battle_tags = ["HuckIt#1840", "topgun707#1875", "beachyman#1138", "mrhustler#1686", "mojoe#11242", "papichulo#12352", "grkfreezer#1906", "yarrface#1316", "woot#11617"]

    # Fancy Flightless Fowl - https://nexusgamingseries.org/teamProfile/Fancy_Flightless_Fowl
    team_battle_tags = ["Alfie#1948", "Silverbell#11333", "AngryPanda#12178", "GingiBoi#1791", "XxLuNaTiCxX#11820", "Stefwithanf#1470"]
    team_profile = fetch_team_profile(team_battle_tags, ngs=True)

