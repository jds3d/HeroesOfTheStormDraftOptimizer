from dotenv import load_dotenv
import os
import pickle
import requests

# Load environment variables
load_dotenv()

API_KEY = os.getenv('HEROES_PROFILE_API_KEY')
BASE_URL = "https://api.heroesprofile.com/api"
DATA_DIR = "../data"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def _save_to_pickle(data, filename):
    """Saves data to a pickle file."""
    with open(os.path.join(DATA_DIR, filename), "wb") as f:
        pickle.dump(data, f)

def _load_from_pickle(filename):
    """Loads data from a pickle file if it exists."""
    file_path = os.path.join(DATA_DIR, filename)
    return pickle.load(open(file_path, "rb")) if os.path.exists(file_path) else None

def _fetch_api_data(url):
    """Handles API requests with error handling."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    print(f"Failed API request: {url} | Status Code: {response.status_code}")
    return None

def get_hero_data(hero_name):
    """Fetches hero-specific data."""
    return _fetch_api_data(f"{BASE_URL}/heroes/{hero_name}")

def get_player_data(battle_tag, region=1):
    """Fetches player profile data."""
    battle_tag_encoded = battle_tag.replace("#", "%23")
    return _fetch_api_data(f"{BASE_URL}/Player?battletag={battle_tag_encoded}&region={region}&api_token={API_KEY}")

def get_player_hero_data(battle_tag, region=1):
    """Fetches hero performance data for a player."""
    battle_tag_encoded = battle_tag.replace("#", "%23")
    return _fetch_api_data(f"{BASE_URL}/Player/Hero/All?battletag={battle_tag_encoded}&region={region}&api_token={API_KEY}")

def get_match_data(match_id):
    """Fetches match details."""
    return _fetch_api_data(f"{BASE_URL}/matches/{match_id}")

def get_player_profile_data(battle_tag, region=1, season=19):
    """Fetches NGS player profile including top heroes and roles."""
    battle_tag_encoded = battle_tag.replace("#", "%23")
    data = _fetch_api_data(f"{BASE_URL}/NGS/Player/Profile?battletag={battle_tag_encoded}&region={region}&season={season}&api_token={API_KEY}")
    return {
        "top_three_heroes": data.get("top_three_heroes", []),
        "heroes_played": data.get("heroes_played", {}),
        "preferred_role": data.get("preferred_role", "Unknown"),
    } if data else None

def get_team_data(battle_tags, ngs=False):
    """Fetches and caches team data, using NGS data if requested."""
    team_data = {}

    for tag in battle_tags:
        cache_file = f"{tag.replace('#', '_')}_{'NGS' if ngs else 'Profile'}.pkl"
        cached_data = _load_from_pickle(cache_file)

        if cached_data:
            print(f"Loaded cached data for {tag}")
            team_data[tag] = cached_data
            continue

        print(f"Fetching data for {tag} from API...")
        player_data = get_player_profile_data(tag) if ngs else get_player_hero_data(tag)
        if player_data:
            team_data[tag] = player_data
            _save_to_pickle(player_data, cache_file)

    return team_data
