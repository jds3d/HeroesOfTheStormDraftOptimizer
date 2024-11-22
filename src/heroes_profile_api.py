from dotenv import load_dotenv
import os
import requests

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('HEROES_PROFILE_API_KEY')

BASE_URL = "https://api.heroesprofile.com"


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


def get_player_data(battle_tag):
    """Fetches a player’s match history and hero data using their BattleTag."""
    url = f"{BASE_URL}/players/{battle_tag}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for player {battle_tag}: {response.status_code}")
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


def get_team_data(battle_tags):
    """Fetches data for all players on the team."""
    team_data = {}

    for tag in battle_tags:
        print(f"Fetching data for {tag}...")
        player_data = get_player_data(tag)
        if player_data:
            team_data[tag] = player_data

    return team_data
