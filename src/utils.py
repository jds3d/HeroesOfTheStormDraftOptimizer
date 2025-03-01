import os
import pickle
import requests
import json
from dotenv import load_dotenv

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


import sys

import sys

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

        print(f"Fetching NGS profile data for {tag} from API...")
        player_data = fetch_api_data("NGS/Player/Profile", {"battletag": tag.replace("#", "%23")})

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


def get_hero_roles():
    """Fetches hero roles from the Heroes Profile API."""
    hero_roles_response = fetch_api_data("Heroes")

    if not hero_roles_response:
        raise ValueError("❌ Error: Failed to retrieve hero roles from API.")

    return {hero: hero_roles_response[hero]["new_role"] for hero in hero_roles_response}
