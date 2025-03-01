import random
from utils import get_team_data, get_heroes_stats, save_to_pickle
from load_data import load_draft_data

DRAFT_ORDER = [
    ("Ban", 1), ("Ban", 2), ("Ban", 3), ("Ban", 4),
    ("Pick", 5), ("Pick", 6), ("Pick", 7), ("Pick", 8), ("Pick", 9),
    ("Ban", 10), ("Ban", 11),
    ("Pick", 12), ("Pick", 13), ("Pick", 14), ("Pick", 15), ("Pick", 16)
]

FIRST_PICK_SLOTS = {1, 3, 5, 8, 9, 10, 14, 15}  # Actions made by the team that bans first

def select_best_ban_with_reason(enemy_hero_performance, hero_winrates_by_map, hero_matchup_data, banned_heroes, enemy_team_data, map_name):
    """Selects the best hero to ban and provides a reason."""
    best_ban = None
    best_score = -1
    best_reason = ""

    for hero, stats in enemy_hero_performance.items():
        if hero in banned_heroes:
            continue

        hero_mmr = stats.get("mmr", 2000)
        map_bonus = hero_winrates_by_map.get(map_name, {}).get(hero, {}).get("win_rate", 50) - 50

        # Extract matchup disadvantage properly
        matchup_disadvantage = sum(
            v.get("win_rate", 50) - 50 for v in hero_matchup_data.get(hero, {}).values() if isinstance(v, dict)
        )

        # Find the enemy player with the highest MMR for this hero
        top_player = "Unknown"
        top_mmr = 0
        for player, player_data in enemy_team_data.items():
            if "Storm League" in player_data and hero in player_data["Storm League"]:
                player_mmr = player_data["Storm League"][hero].get("mmr", 2000)
                if player_mmr > top_mmr:
                    top_mmr = player_mmr
                    top_player = player

        score = hero_mmr + (map_bonus * 10) + matchup_disadvantage

        if score > best_score:
            best_score = score
            best_ban = hero
            best_reason = f"MMR {hero_mmr}, Map Bonus {map_bonus:+.1f}%, Matchup {matchup_disadvantage:+.1f}, {top_player} ({top_mmr} MMR)"

    return best_ban, best_reason



def select_best_pick_with_reason(team_data, available_heroes, picked_heroes, banned_heroes, hero_winrates_by_map, hero_matchup_data, player_mmr_data):
    """Selects the best hero pick and provides a reason."""
    best_pick = None
    best_score = -1
    best_reason = ""

    for player, player_data in team_data.items():
        if "Storm League" not in player_data:
            continue

        player_mmr = player_mmr_data.get(player, 2000)

        for hero in available_heroes:
            if hero in picked_heroes or hero in banned_heroes:
                continue

            hero_mmr = player_data["Storm League"].get(hero, {}).get("mmr", 2000)
            map_bonus = hero_winrates_by_map.get(hero, {}).get("win_rate", 50) - 50
            matchup_score = sum(
                value for value in hero_matchup_data.get(hero, {}).values() if isinstance(value, (int, float))
            )

            score = hero_mmr + (map_bonus * 10) + matchup_score

            if score > best_score:
                best_score = score
                best_pick = hero
                best_reason = f"MMR {hero_mmr}, Map Bonus {map_bonus:+.1f}%, Matchup {matchup_score:+.1f}"

    remaining_heroes = available_heroes - picked_heroes - banned_heroes
    return (best_pick, best_reason) if best_pick else (random.choice(list(remaining_heroes)), "No strong picks available")

def draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe_type="major", timeframe="2.47"):
    """Runs the draft process, predicting bans and picks intelligently."""

    # Load all necessary data
    draft_data = load_draft_data(our_team_tags, enemy_team_tags, first_pick_team, map_name, timeframe_type, timeframe)

    team_1 = draft_data["team_1"]
    team_2 = draft_data["team_2"]
    enemy_hero_performance = draft_data["enemy_hero_performance"]
    hero_matchup_data = draft_data["hero_matchup_data"]
    hero_winrates_by_map = draft_data["hero_winrates_by_map"]
    player_mmr_data = draft_data["player_hero_mmr"]
    enemy_team_data = draft_data["team_2"] if first_pick_team == 1 else draft_data["team_1"]
    available_heroes = draft_data["available_heroes"]

    team_1_name = our_team_name if first_pick_team == 1 else enemy_team_name
    team_2_name = enemy_team_name if first_pick_team == 1 else our_team_name

    available_players_team_1 = our_team_tags[:] if first_pick_team == 1 else enemy_team_tags[:]
    available_players_team_2 = enemy_team_tags[:] if first_pick_team == 1 else our_team_tags[:]

    draft_log = []
    banned_heroes = set()
    picked_heroes = set()

    print(f"\nDraft for {map_name}: {team_1_name} vs {team_2_name}\n")
    print(f"{'Order':<6}\t{'Type':<6}\t{'Team':<25}\t{'Player':<20}\t{'Hero':<15}\t{'Reason'}")
    print("=" * 120)

    for draft_type, order in DRAFT_ORDER:
        team = team_1 if order in FIRST_PICK_SLOTS else team_2
        team_name = team_1_name if order in FIRST_PICK_SLOTS else team_2_name
        team_tags = available_players_team_1 if team_name == team_1_name else available_players_team_2

        if draft_type == "Ban":
            suggested_ban, ban_reason = select_best_ban_with_reason(
                enemy_hero_performance, hero_winrates_by_map, hero_matchup_data, banned_heroes, enemy_team_data, map_name
            )
            banned_heroes.add(suggested_ban)
            print(f"{order:<6}\t{'Ban':<6}\t{team_name:<25}\t{'-':<20}\t{suggested_ban:<15}\t{ban_reason}")
            draft_log.append((order, "Ban", team_name, suggested_ban, ban_reason))

        else:  # Pick
            suggested_pick, pick_reason = select_best_pick_with_reason(
                team, available_heroes, picked_heroes, banned_heroes, hero_winrates_by_map, hero_matchup_data, player_mmr_data
            )
            picked_heroes.add(suggested_pick)
            picking_player = team_tags.pop(0) if team_tags else "Unknown Player"
            print(f"{order:<6}\t{'Pick':<6}\t{team_name:<25}\t{picking_player:<20}\t{suggested_pick:<15}\t{pick_reason}")
            draft_log.append((order, "Pick", team_name, picking_player, suggested_pick, pick_reason))

    save_to_pickle(draft_log, f"draft_{map_name}.pkl")
    return draft_log


if __name__ == "__main__":
    # Our team - Came From Behind
    our_team_name = "Came From Behind"
    our_team_tags = ["HuckIt#1840", "topgun707#1875", "beachyman#1138", "mrhustler#1686", "mojoe#11242"]

    # Enemy team - Fancy Flightless Fowl
    enemy_team_name = "Fancy Flightless Fowl"
    enemy_team_tags = ["Alfie#1948", "Silverbell#11333", "AngryPanda#12178", "GingiBoi#1791", "XxLuNaTiCxX#11820"]

    # Map selection
    map_name = "Towers of Doom"

    # Default first_pick_team to 1 for now (1 = Came From Behind, 2 = Fancy Flightless Fowl)
    first_pick_team = 1
    # Uncomment below for interactive selection:
    # while True:
    #     first_pick_team = input("Which team has first pick? (1 = Came From Behind, 2 = Fancy Flightless Fowl): ").strip()
    #     if first_pick_team in {"1", "2"}:
    #         first_pick_team = int(first_pick_team)
    #         break
    #     print("Invalid input. Please enter 1 or 2.")

    # Run the draft
    draft_log = draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name)

    # Print final draft results
    # print("\nFinal Draft Results:")
    # for entry in draft_log:
    #     if entry[1] == "Ban":
    #         order, draft_type, team_name, hero, reason = entry
    #         print(f"{draft_type} {order} ({team_name}): {hero} - {reason}")
    #     else:  # Pick
    #         order, draft_type, team_name, player, hero, reason = entry
    #         print(f"{draft_type} {order} ({team_name} - {player}): {hero} - {reason}")
