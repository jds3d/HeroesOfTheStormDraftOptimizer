import os
import sys

# ✅ Add the config directory to sys.path to enable importing
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config"))
if config_path not in sys.path:
    sys.path.append(config_path)

DATA_DIR = "../data"

import hero_config
import team_config
import utils

def load_and_initialize_draft(timeframe_type="major", timeframe="2.55"):
    """
    Loads all necessary data and initializes the draft structure.
    """
    print(f"\nLoading draft data for {team_config.map_name}...")

    # Load team data
    team_1 = utils.get_ngs_profile_data(team_config.team_1_tags)
    team_2 = utils.get_ngs_profile_data(team_config.team_2_tags)

    # Load team hero performance data
    team_1_data = utils.get_player_hero_data(team_config.team_1_tags, region=1, game_type="Storm League")
    team_2_data = utils.get_player_hero_data(team_config.team_2_tags, region=1, game_type="Storm League")

    team_1_hero_performance = {
        player: {
            hero_name: {
                "games_played": int(stats.get("games_played", 0)),
                "mmr": int(stats.get("mmr", 2000))
            }
            for hero_name, stats in player_data["Storm League"].items()
        }
        for player, player_data in team_1_data.items() if player_data and "Storm League" in player_data
    }

    team_2_hero_performance = {
        player: {
            hero_name: {
                "games_played": int(stats.get("games_played", 0)),
                "mmr": int(stats.get("mmr", 2000))
            }
            for hero_name, stats in player_data["Storm League"].items()
        }
        for player, player_data in team_2_data.items() if player_data and "Storm League" in player_data
    }

    # Fetch hero win rates by map
    hero_winrates_by_map = utils.get_hero_winrates_by_map(timeframe_type, timeframe)

    # Load MMR data for both teams
    team_1_player_hero_mmr = {tag: utils.get_player_hero_data([tag], region=1, game_type="Storm League").get(tag, {}) for tag in team_config.team_1_tags}
    team_2_player_hero_mmr = {tag: utils.get_player_hero_data([tag], region=1, game_type="Storm League").get(tag, {}) for tag in team_config.team_2_tags}

    # Fetch hero matchup data
    heroes_list = utils.get_heroes_list()
    forbidden_heroes = set(hero_config.forbidden_heroes)
    available_heroes = set(heroes_list) - forbidden_heroes

    hero_matchup_data = {}
    for hero in heroes_list:
        matchup_data = utils.get_hero_matchup_data(hero, timeframe_type, timeframe)
        if matchup_data:
            hero_matchup_data.update(matchup_data)

    # ✅ Use direct Python imports instead of JSON loading
    return {
        "map_name": team_config.map_name,
        "team_1": team_1,
        "team_2": team_2,
        "team_1_hero_performance": team_1_hero_performance,
        "team_2_hero_performance": team_2_hero_performance,
        "hero_matchup_data": hero_matchup_data,
        "hero_winrates_by_map": hero_winrates_by_map,
        "team_1_player_mmr_data": team_1_player_hero_mmr,
        "team_2_player_mmr_data": team_2_player_hero_mmr,
        "available_heroes": available_heroes,
        "team_1_name": team_config.team_1_name,
        "team_2_name": team_config.team_2_name,
        "available_players_team_1": team_config.team_1_tags[:],
        "available_players_team_2": team_config.team_2_tags[:],
        "draft_log": [],
        "banned_heroes": set(),
        "picked_heroes": set(),
        "team_1_picked_heroes": {},
        "team_2_picked_heroes": {},
        "hero_roles": utils.get_hero_roles(),
        "forbidden_heroes": forbidden_heroes,
        "required_roles": set(hero_config.required_roles),
        "role_limits": hero_config.role_limits,
        "role_pick_restrictions": hero_config.role_pick_restrictions,
        "hero_pick_restrictions": hero_config.hero_pick_restrictions,
        "team_roles": {
            team_config.team_1_name: {role: 0 for role in hero_config.required_roles},
            team_config.team_2_name: {role: 0 for role in hero_config.required_roles}
        }
    }
