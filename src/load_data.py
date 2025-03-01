import os
import pickle
from utils import get_team_data, fetch_api_data, get_heroes_stats, save_to_pickle

DATA_DIR = "../data"


def fetch_match_data_for_draft(match_id):
    """Fetches and caches match data for drafting."""
    cache_file = f"match_{match_id}.pkl"
    file_path = os.path.join(DATA_DIR, cache_file)

    if os.path.exists(file_path):
        print(f"Loaded cached match data for {match_id}")
        return pickle.load(open(file_path, "rb"))

    match_data = fetch_api_data(f"matches/{match_id}")

    if not match_data:
        return None

    save_to_pickle(match_data, cache_file)
    return match_data


def load_draft_data(our_team_tags, enemy_team_tags, first_pick_team, map_name, timeframe_type="major", timeframe="2.47"):
    """
    Loads all necessary data for the draft, including:
        - Team data (Storm League stats only)
        - Prefetched hero matchup data (win rates with & against other heroes)
        - Hero win rates by map
        - Hero MMR for each player

    Args:
        our_team_tags (list): BattleTags of our team.
        enemy_team_tags (list): BattleTags of the enemy team.
        first_pick_team (int): 1 if our team has first pick, 2 if the enemy does.
        map_name (str): Name of the map being played.
        timeframe_type (str): The type of timeframe ("major" or "minor").
        timeframe (str): The specific timeframe value.

    Returns:
        dict: Contains all required data for drafting, including:
            - team_1 (dict)
            - team_2 (dict)
            - enemy_hero_performance (dict)
            - hero_matchup_data (dict)
            - hero_winrates_by_map (dict)
            - player_hero_mmr (dict)
            - available_heroes (set)
    """
    print(f"\nLoading draft data for {map_name}...")

    # Assign correct team roles
    team_1_tags = our_team_tags if first_pick_team == 1 else enemy_team_tags
    team_2_tags = enemy_team_tags if first_pick_team == 1 else our_team_tags

    # Load team data (Storm League only)
    team_1 = get_team_data(team_1_tags, ngs=True)
    team_2 = get_team_data(team_2_tags, ngs=True)

    # Load enemy hero performance, filtering only "Storm League" stats
    enemy_team_data = get_team_data(enemy_team_tags, ngs=False)
    enemy_hero_performance = {}

    for player_data in enemy_team_data.values():
        if not player_data or "Storm League" not in player_data:
            continue  # Skip players with no Storm League data

        for hero_name, stats in player_data["Storm League"].items():
            games_played = int(stats.get("games_played", 0))
            hero_mmr = int(stats.get("mmr", 2000))  # Default to 2000 if missing

            if hero_name not in enemy_hero_performance:
                enemy_hero_performance[hero_name] = {"games_played": 0, "mmr": 2000}

            # Aggregate stats across all enemy players
            enemy_hero_performance[hero_name]["games_played"] += games_played
            enemy_hero_performance[hero_name]["mmr"] = max(enemy_hero_performance[hero_name]["mmr"], hero_mmr)

    # Fetch hero win rates by map from "Heroes/Stats"
    hero_winrates_by_map = fetch_api_data("Heroes/Stats", params={
        "timeframe_type": timeframe_type,
        "timeframe": timeframe,
        "game_type": "Storm League",
        "group_by_map": "true"
    })

    # Fetch hero MMR for each player
    player_hero_mmr = {}
    for tag in our_team_tags + enemy_team_tags:
        formatted_tag = tag.replace("#", "%23")
        response = fetch_api_data("Player/Hero/All", params={
            "battletag": formatted_tag,
            "region": "1",
            "game_type": "Storm League"
        })
        if response:
            player_hero_mmr[tag] = response  # Store hero-specific MMR data

    # Prefetch hero matchup data for every hero
    hero_matchup_data = {}
    for hero in enemy_hero_performance.keys():  # Only fetch data for relevant heroes
        matchup_response = fetch_api_data("Heroes/Matchups", params={
            "timeframe_type": timeframe_type,
            "timeframe": timeframe,
            "game_type": "Storm League",
            "hero": hero
        })
        if matchup_response:
            hero_matchup_data[hero] = matchup_response

    return {
        "team_1": team_1,
        "team_2": team_2,
        "enemy_hero_performance": enemy_hero_performance,
        "hero_matchup_data": hero_matchup_data,
        "hero_winrates_by_map": hero_winrates_by_map,
        "player_hero_mmr": player_hero_mmr,  # Now includes MMR for each hero a player has played
        "available_heroes": set(enemy_hero_performance.keys())
    }
