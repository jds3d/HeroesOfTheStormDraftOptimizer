from heroes_profile_api import get_hero_data, get_player_data, get_match_data
from heroes_profile_api import get_team_data

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





def fetch_team_profile(battle_tags):
    """Retrieves and displays profile data for each team member."""
    team_data = get_team_data(battle_tags)

    if not team_data:
        print("Failed to retrieve team data.")
        return

    for tag, data in team_data.items():
        print(f"\n--- {tag} ---")
        for hero in data.get("heroes", []):
            hero_name = hero.get("name")
            win_rate = hero.get("win_rate")
            games_played = hero.get("games_played")
            print(f"Hero: {hero_name}, Win Rate: {win_rate}%, Games Played: {games_played}")



# # Example usage
# match_id = "123456"  # Replace with the actual match ID
# draft_data = fetch_match_data_for_draft(match_id)
# print(draft_data)

if __name__ == "__main__":
    # Replace with the BattleTags of your team members
    team_battle_tags = ["HuckIt#1830"]#, "Player2#5678", "Player3#9101"]
    fetch_team_profile(team_battle_tags)
