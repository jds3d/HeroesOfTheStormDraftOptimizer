from dotenv import load_dotenv
import os
import pickle
import requests

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('HEROES_PROFILE_API_KEY')

BASE_URL = "https://api.heroesprofile.com/api"


def get_hero_data(hero_name):
    """Fetches data for a given hero from the Heroes Profile API."""
    url = f"{BASE_URL}/heroes/{hero_name}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for {hero_name}: {response.status_code}")
        return None


def get_player_data(battle_tag, region=1):
    """Fetches a player’s match history and hero data using their BattleTag."""

    # Ensure the BattleTag is URL-encoded
    battle_tag_encoded = battle_tag.replace("#", "%23")

    url = f"{BASE_URL}/Player?battletag={battle_tag_encoded}&region={region}&api_token={API_KEY}"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for BattleTag {battle_tag}: {response.status_code}")
        print("Response:", response.text)  # Print detailed error for debugging
        return None


def get_player_hero_data(battle_tag, region=1):
    """
    Fetches hero-specific data for a player using their BattleTag.

    Args:
        battle_tag (str): The player's BattleTag (e.g., "Zemill#1940").
        region (int): The region code (1 = NA, 2 = EU, etc.).

    Returns:
        dict or None: The player's hero data if successful, otherwise None.
    """
    # Ensure the BattleTag is URL-encoded
    battle_tag_encoded = battle_tag.replace("#", "%23")

    # API Endpoint for retrieving hero data
    url = f"{BASE_URL}/Player/Hero/All?battletag={battle_tag_encoded}&region={region}&api_token={API_KEY}"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve hero data for BattleTag {battle_tag}: {response.status_code}")
        print("Response:", response.text)  # Print detailed error for debugging
        return None


def get_match_data(match_id):
    """Fetches data for a specific match."""
    url = f"{BASE_URL}/matches/{match_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for match {match_id}: {response.status_code}")
        return None


def get_team_data(battle_tags, ngs=False):
    """Fetches data for all players on the team, using cached data if available."""
    team_data = {}
    save_dir = "../data"
    os.makedirs(save_dir, exist_ok=True)  # Ensure the data directory exists

    for tag in battle_tags:
        save_path = os.path.join(save_dir, f"{tag.replace('#', '_')}_{ngs=}.pkl")

        # Check if cached data exists
        if os.path.exists(save_path):
            print(f"Loading cached data for {tag} from {save_path}...")
            with open(save_path, "rb") as f:
                team_data[tag] = pickle.load(f)
        else:
            print(f"Fetching data for {tag} from API...")
            if ngs:
                player_data = get_player_profile_data(tag)
            else:
                player_data = get_player_hero_data(tag)
            if player_data:
                team_data[tag] = player_data

                # Save new data as a pickle file
                with open(save_path, "wb") as f:
                    pickle.dump(player_data, f)
                print(f"Saved {tag}'s data to {save_path}")

    return team_data


def get_player_profile_data(battle_tag, region=1, season=19):
    """
    Fetches a player's NGS profile data, including top three heroes, heroes played, and preferred role.

    Args:
        battle_tag (str): The player's BattleTag (e.g., "Zemill#1940").
        region (int): The region code (1 = NA, 2 = EU, etc.).
        season (int): The season number to query.

    Returns:
        dict or None: A dictionary containing top three heroes, heroes played, and preferred role if successful, otherwise None.
    """
    # Ensure the BattleTag is URL-encoded
    battle_tag_encoded = battle_tag.replace("#", "%23")

    # API Endpoint for retrieving player profile data
    url = f"{BASE_URL}/NGS/Player/Profile?battletag={battle_tag_encoded}&region={region}&season={season}&api_token={API_KEY}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Extract relevant fields
        profile_data = {
            "top_three_heroes": data.get("top_three_heroes", []),
            "heroes_played": data.get("heroes_played", {}),
            "preferred_role": data.get("preferred_role", "Unknown"),
        }

        return profile_data
    else:
        print(f"Failed to retrieve profile data for BattleTag {battle_tag}: {response.status_code}")
        print("Response:", response.text)  # Print detailed error for debugging
        return None
