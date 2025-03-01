import utils  # Import utils to use all encapsulated API calls

DATA_DIR = "../data"


def load_draft_data(our_team_tags, enemy_team_tags, first_pick_team, map_name, timeframe_type="major", timeframe="2.47"):
    """
    Loads all necessary data for the draft.
    """
    print(f"\nLoading draft data for {map_name}...")

    # Assign correct team roles
    team_1_tags = our_team_tags if first_pick_team == 1 else enemy_team_tags
    team_2_tags = enemy_team_tags if first_pick_team == 1 else our_team_tags

    # Load team data separately
    team_1 = utils.get_ngs_profile_data(team_1_tags)
    team_2 = utils.get_ngs_profile_data(team_2_tags)

    # Load enemy hero performance data
    enemy_team_data = utils.get_player_hero_data(enemy_team_tags, region=1, game_type="Storm League")
    enemy_hero_performance = {}

    for player, player_data in enemy_team_data.items():
        if not player_data or "Storm League" not in player_data:
            continue

        enemy_hero_performance[player] = {
            hero_name: {
                "games_played": int(stats.get("games_played", 0)),
                "mmr": int(stats.get("mmr", 2000))
            }
            for hero_name, stats in player_data["Storm League"].items()
        }

    # ✅ Load friendly team hero data separately
    friendly_team_data = utils.get_player_hero_data(our_team_tags, region=1, game_type="Storm League")
    friendly_hero_performance = {}

    for player, player_data in friendly_team_data.items():
        if not player_data or "Storm League" not in player_data:
            continue

        friendly_hero_performance[player] = {
            hero_name: {
                "games_played": int(stats.get("games_played", 0)),
                "mmr": int(stats.get("mmr", 2000))
            }
            for hero_name, stats in player_data["Storm League"].items()
        }

    # Fetch hero win rates by map
    hero_winrates_by_map = utils.get_hero_winrates_by_map(timeframe_type, timeframe)

    # ✅ Keep player hero MMRs separate for enemy and friendly teams
    enemy_player_hero_mmr = {
        tag: utils.get_player_hero_data([tag], region=1, game_type="Storm League").get(tag, {})
        for tag in enemy_team_tags
    }

    friendly_player_hero_mmr = {
        tag: utils.get_player_hero_data([tag], region=1, game_type="Storm League").get(tag, {})
        for tag in our_team_tags
    }

    # Fetch hero matchup data
    heroes_list = utils.get_heroes_list()
    # Fetch all valid heroes from the API
    available_heroes = set(utils.get_heroes_list())  # ✅ Now using the full hero list

    hero_matchup_data = {}

    for hero in heroes_list:
        matchup_data = utils.get_hero_matchup_data(hero, timeframe_type, timeframe)
        if matchup_data:  # ✅ Ensure data exists
            hero_matchup_data.update(matchup_data)  # ✅ Merge directly into `hero_matchup_data`

    return {
        "team_1": team_1,
        "team_2": team_2,
        "enemy_hero_performance": enemy_hero_performance,
        "friendly_hero_performance": friendly_hero_performance,  # ✅ Separate friendly hero data
        "hero_matchup_data": hero_matchup_data,
        "hero_winrates_by_map": hero_winrates_by_map,
        "enemy_player_hero_mmr": enemy_player_hero_mmr,  # ✅ Separate enemy MMR data
        "friendly_player_hero_mmr": friendly_player_hero_mmr,  # ✅ Separate friendly MMR data
        "available_heroes": available_heroes  # ✅ Now correctly contains hero names only
    }
