import utils  # Import utils for API calls

DATA_DIR = "../data"

def load_and_initialize_draft(team_1_tags, team_2_tags, team_1_name, team_2_name, first_pick_team, map_name, timeframe_type="major", timeframe="2.55"):
    """
    Loads all necessary data and initializes the draft structure.
    """
    print(f"\nLoading draft data for {map_name}...")

    # Load team data
    team_1 = utils.get_ngs_profile_data(team_1_tags)
    team_2 = utils.get_ngs_profile_data(team_2_tags)

    # Load team hero performance data
    team_1_data = utils.get_player_hero_data(team_1_tags, region=1, game_type="Storm League")
    team_2_data = utils.get_player_hero_data(team_2_tags, region=1, game_type="Storm League")

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
    team_1_player_hero_mmr = {tag: utils.get_player_hero_data([tag], region=1, game_type="Storm League").get(tag, {}) for tag in team_1_tags}
    team_2_player_hero_mmr = {tag: utils.get_player_hero_data([tag], region=1, game_type="Storm League").get(tag, {}) for tag in team_2_tags}

    # Fetch hero matchup data
    heroes_list = utils.get_heroes_list()
    available_heroes = set(heroes_list)

    hero_matchup_data = {}
    for hero in heroes_list:
        matchup_data = utils.get_hero_matchup_data(hero, timeframe_type, timeframe)
        if matchup_data:
            hero_matchup_data.update(matchup_data)

    # Load hero role configuration
    hero_config = utils.load_hero_config()
    api_roles = utils.get_hero_roles()

    # Merge API roles with additional roles from config
    for hero, roles in hero_config.get("additional_hero_roles", {}).items():
        api_roles[hero] = roles

    required_roles = set(hero_config.get("required_roles", []))

    # Return the fully initialized draft structure
    return {
        "map_name": map_name,
        "team_1": team_1,
        "team_2": team_2,
        "team_1_hero_performance": team_1_hero_performance,
        "team_2_hero_performance": team_2_hero_performance,
        "hero_matchup_data": hero_matchup_data,
        "hero_winrates_by_map": hero_winrates_by_map,
        "team_1_player_mmr_data": team_1_player_hero_mmr,
        "team_2_player_mmr_data": team_2_player_hero_mmr,
        "available_heroes": available_heroes,
        "team_1_name": team_1_name,
        "team_2_name": team_2_name,
        "available_players_team_1": team_1_tags[:],
        "available_players_team_2": team_2_tags[:],
        "draft_log": [],
        "banned_heroes": set(),
        "picked_heroes": set(),
        "team_1_picked_heroes": {},
        "team_2_picked_heroes": {},
        "hero_roles": api_roles,
        "forbidden_heroes": set(hero_config.get("forbidden_heroes", [])),
        "required_roles": required_roles,
        "team_roles": {
            team_1_name: {role: 0 for role in required_roles},
            team_2_name: {role: 0 for role in required_roles}
        }
    }
