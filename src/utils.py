import pickle
import requests
import json
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

API_KEY = os.getenv('HEROES_PROFILE_API_KEY')
BASE_URL = "https://api.heroesprofile.com/api"
DATA_DIR = "../data"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)


def save_to_pickle(data, filename):
    """Saves data to a pickle file."""
    with open(os.path.join(DATA_DIR, filename), "wb") as f:
        pickle.dump(data, f)


def load_from_pickle(filename):
    """Loads data from a pickle file if it exists."""
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    return None


def load_hero_config(config_file="../config/hero_config.json"):
    """Loads hero role configuration from a JSON file."""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"❌ Error: Hero configuration file '{config_file}' not found.")

    with open(config_file, "r") as file:
        hero_config = json.load(file)

    return hero_config


def load_team_config(config_file="../config/team_config.json"):
    """Loads team names and player tags from a JSON config file."""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"❌ Error: Team configuration file '{config_file}' not found.")

    with open(config_file, "r") as file:
        team_config = json.load(file)

    return team_config


def get_hero_roles():
    import hero_config
    hero_roles_response = fetch_api_data("Heroes")
    if not hero_roles_response:
        raise ValueError("❌ Error: Failed to retrieve hero roles from API.")
    # Base roles from API
    api_roles = {hero: [hero_roles_response[hero]["new_role"]] for hero in hero_roles_response}

    # Override API roles with additional roles from the config
    for hero, roles in hero_config.additional_hero_roles.items():
        api_roles[hero] = roles
    return api_roles


def get_available_players(DRAFT_DATA, team_name):
    team_tags = DRAFT_DATA["available_players_team_1"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["available_players_team_2"]
    return team_tags


def get_hero_player_pool_sizes(DRAFT_DATA, team_name, mmr_threshold=2700):
    # ✅ Calculate hero pool size for each player (heroes with MMR > 2700)
    available_players = get_available_players(DRAFT_DATA, team_name)
    team_mmr_data = DRAFT_DATA["team_1_player_mmr_data"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["team_2_player_mmr_data"]
    player_hero_pools = {
        player: sum(1 for hero, stats in team_mmr_data.get(player, {}).get("Storm League", {}).items() if stats.get("mmr", 2000) > mmr_threshold)
        for player in available_players
    }
    return player_hero_pools


def fetch_api_data(endpoint, params=None, cache=True):
    """
    Generalized API request function for HeroesProfile.

    Args:
        endpoint (str): API endpoint path, excluding BASE_URL.
        params (dict, optional): Query parameters for the request.
        cache (bool, optional): Whether to use caching. Default is True.

    Returns:
        dict: JSON response data if successful.
        Exits program on failure.
    """
    params = params or {}
    params["api_token"] = API_KEY  # Ensure API token is always included

    # Construct the full query string manually
    query_string = "&".join(f"{key}={value}" for key, value in params.items())

    url = f"{BASE_URL}/{endpoint}?{query_string}"

    # Remove API key from cache filename
    cache_params = {k: v for k, v in params.items() if k != "api_token"}
    cache_file = f"{endpoint.replace('/', '_')}_{'_'.join(map(str, cache_params.values()))}.pkl"

    if cache:
        cached_data = load_from_pickle(cache_file)
        if cached_data:
            print(f"Loaded cached data for {endpoint} with query: {query_string}")
            return cached_data

    print(f"Executing API call: {url}")  # Debugging output

    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            print(
                "❌ Error: Could not parse JSON response. It looks like you've run out of API calls with your subscription.")
            print("Response text:", response.text)
            sys.exit(1)
        if cache:
            save_to_pickle(data, cache_file)
        return data

    print(f"❌ Failed API request: {url} | Status Code: {response.status_code} | Response: {response.text}")
    sys.exit(1)  # Exit the program on failure


def get_ngs_profile_data(battle_tags):
    """Fetches and caches NGS profile data for a list of players."""
    team_data = {}

    for tag in battle_tags:
        cache_file = f"{tag.replace('#', '_')}_NGS.pkl"
        cached_data = load_from_pickle(cache_file)

        if cached_data:
            print(f"Loaded cached NGS profile data for {tag}")
            team_data[tag] = cached_data
            continue

        try:
            print(f"Fetching NGS profile data for {tag} from API...")
            player_data = fetch_api_data("NGS/Player/Profile", {"battletag": tag.replace("#", "%23")})
        except:
            print(f"No NGS profile found for {tag}.")
            player_data = None

        if player_data:
            team_data[tag] = player_data
            save_to_pickle(player_data, cache_file)

    return team_data


def get_player_hero_data(battle_tags, region=1, game_type="Storm League"):
    """Fetches and caches hero-specific data for a list of players."""
    team_data = {}

    for tag in battle_tags:
        cache_file = f"{tag.replace('#', '_')}_Profile.pkl"
        cached_data = load_from_pickle(cache_file)

        if cached_data:
            print(f"Loaded cached hero data for {tag}")
            team_data[tag] = cached_data
            continue

        print(f"Fetching hero data for {tag} from API...")
        player_data = fetch_api_data("Player/Hero/All", {
            "battletag": tag.replace("#", "%23"),
            "region": region,   # ✅ Now correctly passing region
            "game_type": game_type  # ✅ Now correctly passing game_type
        })

        if player_data:
            team_data[tag] = player_data
            save_to_pickle(player_data, cache_file)

    return team_data



def get_hero_stats(hero_name, game_type="Storm League", region=1):
    """
    Fetches hero stats from HeroesProfile API.

    Args:
        hero_name (str): The name of the hero.
        game_type (str): The type of game mode (default: "Storm League").
        region (int): The region code (default: 1 for NA).

    Returns:
        dict: Hero stats if successful, otherwise None.
    """
    if not hero_name or hero_name == "None":
        print("❌ Error: Hero name is missing.")
        return None

    url = f"https://api.heroesprofile.com/api/Hero/Stats?hero={hero_name}&game_type={game_type}&region={region}&api_token={API_KEY}"

    print(f"🔍 Executing API Call: {url}")  # Debugging
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed API request: {url} | Status Code: {response.status_code} | Response: {response.text}")
        sys.exit(1)  # Terminate program if API call fails


def get_heroes_stats(timeframe_type="major", timeframe="2.47", game_type="Storm League", group_by_map=False):
    """Fetches stats for all heroes, including popularity, from the Heroes Profile API."""

    params = {
        "timeframe_type": timeframe_type,
        "timeframe": timeframe,
        "game_type": game_type,
        "group_by_map": str(group_by_map).lower(),
    }

    data = fetch_api_data("1.0/Heroes/Stats", params)

    # Process response into a dictionary where key = hero name, value = stats
    hero_stats = {
        hero_entry.get("hero", "Unknown Hero"): {
            "popularity": float(hero_entry.get("popularity", 0)),
            "win_rate": float(hero_entry.get("win_rate", 0)),
            "games_played": int(hero_entry.get("games_played", 0))
        }
        for hero_entry in data
    }

    return hero_stats


def get_hero_winrates_by_map(timeframe_type, timeframe):
    """Fetches hero win rates by map from Heroes Profile API."""
    return fetch_api_data("Heroes/Stats", params={
        "timeframe_type": timeframe_type,
        "timeframe": timeframe,
        "game_type": "Storm League",
        "group_by_map": "true"
    })


def get_player_hero_mmr(battletag):
    """Fetches hero-specific MMR data for a given player."""
    formatted_tag = battletag.replace("#", "%23")
    return fetch_api_data("Player/Hero/All", params={
        "battletag": formatted_tag,
        "region": "1",
        "game_type": "Storm League"
    })


def get_hero_matchup_data(hero, timeframe_type, timeframe):
    """Fetches matchup data for a specific hero."""
    return fetch_api_data("Heroes/Matchups", params={
        "timeframe_type": timeframe_type,
        "timeframe": timeframe,
        "game_type": "Storm League",
        "hero": hero
    })


def calculate_allied_synergy_score(DRAFT_DATA, hero, team_name):
    hero_matchup_data = DRAFT_DATA['hero_matchup_data']
    ally_picked_heroes = DRAFT_DATA['team_1_picked_heroes'].values() if team_name == DRAFT_DATA['team_1_name'] else DRAFT_DATA['team_2_picked_heroes']
    ally_synergy = sum(
        float(hero_matchup_data.get(hero, {}).get(ally_hero, {}).get("ally", {}).get("win_rate_as_ally", 50)) - 50
        for ally_hero in ally_picked_heroes if ally_hero in hero_matchup_data.get(hero, {})
    )

    return ally_synergy


def calculate_enemy_countering_score(DRAFT_DATA, hero, team_name):
    hero_matchup_data = DRAFT_DATA['hero_matchup_data']
    enemy_picked_heroes = DRAFT_DATA['team_2_picked_heroes'].values() if team_name == DRAFT_DATA['team_1_name'] else DRAFT_DATA['team_1_picked_heroes']

    enemy_counter = sum(
        float(hero_matchup_data.get(hero, {}).get(enemy_hero, {}).get("enemy", {}).get("win_rate_against", 50)) - 50
        for enemy_hero in enemy_picked_heroes if enemy_hero in hero_matchup_data.get(hero, {})
    )

    return enemy_counter


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


def get_heroes_list():
    """Fetches the complete list of heroes from the API."""
    heroes_list_response = fetch_api_data("Heroes")

    if not heroes_list_response:
        raise ValueError("❌ Error: Failed to retrieve hero list from API.")

    return heroes_list_response


def print_final_draft(DRAFT_DATA, user_input_enabled):
    """Prints the full draft summary including bans, picks, team compositions, and missing roles."""

    if user_input_enabled:
        if DRAFT_DATA is None:
            raise ValueError("❌ ERROR: DRAFT_DATA is None. Ensure draft initialization is successful.")

        print("\n" + "=" * 120)
        print("🔹 FINAL DRAFT RESULTS 🔹")
        print("=" * 120)

        print(f"{'Order':<6} {'Type':<6} {'Team':<25} {'Player':<20} {'Hero':<15} {'Score':<10} {'Reason'}")
        print("=" * 120)

        for entry in DRAFT_DATA["draft_log"]:
            if entry[1] == "Ban":
                order, draft_type, team_name, hero, score, reason = entry
                print(f"{order:<6} {draft_type:<6} {team_name:<25} {'-':<20} {hero:<15} {score:<10.2f} {reason}")
            else:  # Pick
                order, draft_type, team_name, player, hero, score, reason = entry
                print(f"{order:<6} {draft_type:<6} {team_name:<25} {player:<20} {hero:<15} {score:<10.2f} {reason}")

        print("=" * 120)

    # ✅ Print Final Team Compositions
    print("\n🔹 FINAL TEAM COMPOSITIONS 🔹")
    for team_name, team_picked_heroes in [(DRAFT_DATA["team_1_name"], DRAFT_DATA["team_1_picked_heroes"]),
                                          (DRAFT_DATA["team_2_name"], DRAFT_DATA["team_2_picked_heroes"])]:
        print(f"\n{team_name}:")
        team_roles = {role: 0 for role in DRAFT_DATA["required_roles"]}

        for player, hero in team_picked_heroes.items():
            roles = DRAFT_DATA["hero_roles"].get(hero, ["Unknown"])
            if isinstance(roles, str):
                roles = [roles]

            # **Convert Bruiser → Offlaner**
            roles = ["Offlaner" if r == "Bruiser" else r for r in roles]

            role_display = "/".join(roles)
            for role in roles:
                if role in team_roles:
                    team_roles[role] += 1
            print(f"  {player}: {hero} ({role_display})")

        # ✅ Display missing roles
        missing_roles = [role for role in DRAFT_DATA["required_roles"] if team_roles[role] == 0]
        if missing_roles:
            print(f"⚠️ WARNING: {team_name} is missing {'/'.join(missing_roles)}!")

    print("=" * 120)


