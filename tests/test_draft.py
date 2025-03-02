## WIP, doesn't work now.

import unittest
import sys
import os
from unittest.mock import patch

# ✅ Ensure src directory is in sys.path so tests can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import draft  # ✅ Import draft as a package
import utils  # ✅ Import utils as a package
import load_data  # ✅ Import load_data as a package


class TestDraftFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load hero configuration for all tests."""
        cls.hero_config = utils.load_hero_config()  # ✅ Now calling from utils

    def setUp(self):
        """Set up sample draft data for tests."""
        self.draft_data = {
            "team_1_name": "Came From Behind",
            "team_2_name": "Fancy Flightless Fowl",
            "available_players_team_1": ["HuckIt#1840", "topgun707#1875"],
            "available_players_team_2": ["Alfie#1948", "Silverbell#11333"],
            "available_heroes": {"Greymane", "Lucio", "Diablo", "Muradin"},
            "picked_heroes": set(),
            "banned_heroes": set(),
            "team_1_picked_heroes": {},
            "team_2_picked_heroes": {},
            "hero_winrates_by_map": {"Towers of Doom": {"Greymane": {"win_rate": 52.0}, "Lucio": {"win_rate": 54.0}}},
            "hero_matchup_data": {"Greymane": {"Diablo": {"win_rate_as_ally": 50.0, "win_rate_against": 48.0}}},
            "friendly_player_mmr_data": {"HuckIt#1840": {"Storm League": {"Greymane": {"mmr": 3000}}}},
            "enemy_player_mmr_data": {"Alfie#1948": {"Storm League": {"Lucio": {"mmr": 2900}}}},
            "map_name": "Towers of Doom"
        }

    def test_load_hero_config(self):
        """Test if hero configuration loads correctly."""
        config = utils.load_hero_config()  # ✅ Call from utils
        self.assertIn("hero_roles", config, "Config should contain hero_roles.")

    def test_get_hero_roles(self):
        """Test if hero roles are fetched correctly."""
        hero_roles = utils.get_hero_roles()  # ✅ Call from utils
        self.assertIn("Uther", hero_roles, "Uther should be in hero roles config.")

    def test_execute_draft_phase(self):
        """Test if execute_draft_phase runs without errors and produces valid logs."""
        draft.execute_draft_phase(self.draft_data)  # ✅ Call from draft
        self.assertTrue(len(self.draft_data["draft_log"]) > 0, "Draft log should not be empty after execution.")

    def test_select_best_pick_with_reason(self):
        """Test if a pick is correctly chosen based on priority roles."""
        team_roles = {"Tank": 0, "Offlaner": 0, "Healer": 0}
        enemy_has_offlaner = False
        picks, _, _, _, team_roles = draft.select_best_pick_with_reason(
            self.draft_data["available_players_team_1"],
            self.draft_data["friendly_player_mmr_data"],
            self.draft_data["available_heroes"],
            self.draft_data["picked_heroes"],
            self.draft_data["banned_heroes"],
            self.draft_data["hero_winrates_by_map"],
            self.draft_data["hero_matchup_data"],
            self.draft_data["map_name"],
            set(),
            set(),
            5,
            team_roles,
            self.hero_config,
            enemy_has_offlaner
        )
        self.assertTrue(picks, "Should return a valid pick.")
        self.assertIn(picks[0][1], self.draft_data["available_heroes"], "Pick should be from available heroes.")

    def test_select_best_ban_with_reason(self):
        """Test if the best ban is chosen based on enemy MMR drop and hero strength."""
        ally_picked_heroes = set()
        enemy_picked_heroes = set()
        suggested_ban, ban_reason, _, _ = draft.select_best_ban_with_reason(
            self.draft_data["enemy_player_mmr_data"],
            self.draft_data["hero_winrates_by_map"],
            self.draft_data["hero_matchup_data"],
            self.draft_data["banned_heroes"],
            self.draft_data["available_heroes"],
            {},
            self.draft_data["map_name"],
            ally_picked_heroes,
            enemy_picked_heroes
        )
        self.assertTrue(suggested_ban, "Should return a valid ban hero.")

    def test_calculate_matchup_advantage(self):
        """Test matchup advantage calculation based on picked heroes."""
        matchup_advantage = utils.calculate_matchup_advantage("Greymane", self.draft_data["hero_matchup_data"], {"Diablo"}, set())
        self.assertIsInstance(matchup_advantage, float, "Matchup advantage should be a float value.")

    def test_get_enemy_top_mmr_drop(self):
        """Test if enemy MMR drop calculation correctly identifies the top MMR player and their fallback hero."""
        best_player, best_mmr, mmr_drop = utils.get_enemy_top_mmr_drop("Lucio", self.draft_data["enemy_player_mmr_data"], set())
        self.assertEqual(best_player, "Alfie#1948", "Should correctly identify the player with the highest Lucio MMR.")
        self.assertGreaterEqual(mmr_drop, 0, "MMR drop should be a non-negative value.")

    @patch('utils.fetch_api_data')
    def test_load_draft_data(self, mock_fetch_api_data):
        """Test if load_draft_data correctly fetches and loads data."""
        mock_fetch_api_data.return_value = {"Greymane": {"win_rate": 52.0}, "Lucio": {"win_rate": 54.0}}
        draft_data = load_data.load_draft_data(["HuckIt#1840"], ["Alfie#1948"], 1, "Towers of Doom")
        self.assertIn("team_1", draft_data, "Draft data should contain 'team_1'.")
        self.assertIn("hero_winrates_by_map", draft_data, "Draft data should contain 'hero_winrates_by_map'.")

if __name__ == '__main__':
    unittest.main()
