import random
import utils
import load_data

DRAFT_ORDER = [
    ("Ban", 1), ("Ban", 2), ("Ban", 3), ("Ban", 4),
    ("Pick", 5), ("Pick", 6), ("Pick", 7), ("Pick", 8), ("Pick", 9),
    ("Ban", 10), ("Ban", 11),
    ("Pick", 12), ("Pick", 13), ("Pick", 14), ("Pick", 15), ("Pick", 16)
]

FIRST_PICK_SLOTS = {1, 3, 5, 8, 9, 10, 14, 15}  # Actions made by the team that bans first


def initialize_draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe_type, timeframe):
    """Loads draft data and initializes tracking variables."""

    draft_data = load_data.load_draft_data(our_team_tags, enemy_team_tags, first_pick_team, map_name, timeframe_type, timeframe)

    return {
        "map_name": map_name,  # ✅ Ensure map_name is stored correctly as a string
        "team_1": draft_data["team_1"],
        "team_2": draft_data["team_2"],
        "hero_matchup_data": draft_data["hero_matchup_data"],
        "hero_winrates_by_map": draft_data["hero_winrates_by_map"],
        "enemy_player_mmr_data": draft_data["enemy_player_hero_mmr"],
        "friendly_player_mmr_data": draft_data["friendly_player_hero_mmr"],
        "enemy_team_data": draft_data["team_2"] if first_pick_team == 1 else draft_data["team_1"],
        "available_heroes": draft_data["available_heroes"],
        "team_1_name": our_team_name if first_pick_team == 1 else enemy_team_name,
        "team_2_name": enemy_team_name if first_pick_team == 1 else our_team_name,
        "available_players_team_1": our_team_tags[:] if first_pick_team == 1 else enemy_team_tags[:],
        "available_players_team_2": enemy_team_tags[:] if first_pick_team == 1 else our_team_tags[:],
        "draft_log": [],
        "banned_heroes": set(),
        "picked_heroes": set(),
        "team_1_picked_heroes": {},
        "team_2_picked_heroes": {},
        "hero_roles": utils.get_hero_roles()
    }


def execute_draft_phase(draft_data):
    """Executes the draft process, handling bans and picks, including special rules for Cho'Gall."""

    print(f"\nDraft for {draft_data['team_1_name']} vs {draft_data['team_2_name']}\n")
    print(f"{'Order':<6}\t{'Type':<6}\t{'Team':<25}\t{'Player':<20}\t{'Hero':<15}\t{'Reason'}")
    print("=" * 120)

    remaining_picks = sum(1 for pick in DRAFT_ORDER if pick[0] == "Pick")  # ✅ Count remaining picks

    for draft_type, order in DRAFT_ORDER:
        team_name = draft_data["team_1_name"] if order in FIRST_PICK_SLOTS else draft_data["team_2_name"]
        team_tags = draft_data["available_players_team_1"] if team_name == draft_data["team_1_name"] else draft_data["available_players_team_2"]

        if draft_type == "Ban":
            ally_picked_heroes = set(draft_data["team_1_picked_heroes"].values()) if team_name == draft_data["team_1_name"] else set(draft_data["team_2_picked_heroes"].values())
            enemy_picked_heroes = set(draft_data["team_2_picked_heroes"].values()) if team_name == draft_data["team_1_name"] else set(draft_data["team_1_picked_heroes"].values())

            map_name = draft_data["map_name"]

            suggested_ban, ban_reason, draft_data["banned_heroes"], draft_data["available_heroes"] = select_best_ban_with_reason(
                draft_data["enemy_player_mmr_data"], draft_data["hero_winrates_by_map"], draft_data["hero_matchup_data"],
                draft_data["banned_heroes"], draft_data["available_heroes"], draft_data["enemy_team_data"],
                map_name, ally_picked_heroes, enemy_picked_heroes
            )

            print(f"{order:<6}\t{'Ban':<6}\t{team_name:<25}\t{'-':<20}\t{suggested_ban:<15}\t{ban_reason}")
            draft_data["draft_log"].append((order, "Ban", team_name, suggested_ban, ban_reason))

        else:  # Pick
            picking_team_mmr_data = draft_data["friendly_player_mmr_data"] if team_name == draft_data["team_1_name"] else draft_data["enemy_player_mmr_data"]

            ally_picked_heroes = set(draft_data["team_1_picked_heroes"].values()) if team_name == draft_data["team_1_name"] else set(draft_data["team_2_picked_heroes"].values())
            enemy_picked_heroes = set(draft_data["team_2_picked_heroes"].values()) if team_name == draft_data["team_1_name"] else set(draft_data["team_1_picked_heroes"].values())

            picks, team_tags, draft_data["available_heroes"], draft_data["picked_heroes"] = select_best_pick_with_reason(
                team_tags, picking_team_mmr_data, draft_data["available_heroes"], draft_data["picked_heroes"],
                draft_data["banned_heroes"], draft_data["hero_winrates_by_map"], draft_data["hero_matchup_data"],
                draft_data["map_name"], ally_picked_heroes, enemy_picked_heroes, remaining_picks
            )

            remaining_picks -= len(picks)  # ✅ Decrease remaining picks

            for picking_player, suggested_pick, pick_reason in picks:
                if team_name == draft_data["team_1_name"]:
                    draft_data["team_1_picked_heroes"][picking_player] = suggested_pick
                else:
                    draft_data["team_2_picked_heroes"][picking_player] = suggested_pick

                print(f"{order:<6}\t{'Pick':<6}\t{team_name:<25}\t{picking_player:<20}\t{suggested_pick:<15}\t{pick_reason}")
                draft_data["draft_log"].append((order, "Pick", team_name, picking_player, suggested_pick, pick_reason))



def print_final_teams(draft_data):
    """Prints final team compositions and warns if roles are missing."""

    print("\nFinal Team Compositions:")
    for team_name, team_picked_heroes in [(draft_data["team_1_name"], draft_data["team_1_picked_heroes"]),
                                          (draft_data["team_2_name"], draft_data["team_2_picked_heroes"])]:
        print(f"\n{team_name}:")
        team_roles = {"Tank": 0, "Healer": 0, "Assassin": 0}
        for player, hero in team_picked_heroes.items():
            role = draft_data["hero_roles"].get(hero, "Unknown Role")
            team_roles[role] = team_roles.get(role, 0) + 1
            print(f"  {player}: {hero} ({role})")

        missing_roles = [role for role in ["Tank", "Healer", "Assassin"] if team_roles[role] == 0]
        if missing_roles:
            print(f"⚠️ WARNING: {team_name} is missing {'/'.join(missing_roles)}!")


def calculate_matchup_advantage(hero, hero_matchup_data, ally_picked_heroes, enemy_picked_heroes):
    """Calculates the matchup advantage for a hero based on ally and enemy picks."""

    ally_synergy = sum(
        float(hero_matchup_data.get(hero, {}).get(ally_hero, {}).get("ally", {}).get("win_rate_as_ally", 50)) - 50
        for ally_hero in ally_picked_heroes if ally_hero in hero_matchup_data.get(hero, {})
    )

    enemy_counter = sum(
        float(hero_matchup_data.get(hero, {}).get(enemy_hero, {}).get("enemy", {}).get("win_rate_against", 50)) - 50
        for enemy_hero in enemy_picked_heroes if enemy_hero in hero_matchup_data.get(hero, {})
    )

    return ally_synergy + enemy_counter  # ✅ Combined synergy & counter advantage

def get_enemy_top_mmr_drop(hero, enemy_hero_performance, picked_players):
    """Finds the highest MMR remaining player for a hero and calculates the MMR drop if they lose it."""
    best_mmr = 0
    best_player = "Unknown"
    mmr_drop = 0

    if hero in enemy_hero_performance:
        for player, heroes in enemy_hero_performance.items():
            if hero not in heroes or player in picked_players:
                continue  # Ignore players who don't play this hero or who have already picked

            player_mmr = heroes[hero]["mmr"]

            if player_mmr > best_mmr:
                best_mmr = player_mmr
                best_player = player

                # Find next best hero for the player
                alternative_mmr = min(
                    heroes[other_hero]["mmr"] for other_hero in heroes if other_hero != hero
                ) if len(heroes) > 1 else 2000

                mmr_drop = best_mmr - alternative_mmr

    return best_player, best_mmr, mmr_drop


def select_best_ban_with_reason(enemy_player_mmr_data, hero_winrates_by_map, hero_matchup_data, banned_heroes, available_heroes, enemy_team_data, map_name, ally_picked_heroes, enemy_picked_heroes):
    """Selects the best hero to ban based on impact on the enemy team and returns updated sets."""
    best_ban = None
    best_score = -1
    best_reason = ""

    for player, heroes in enemy_player_mmr_data.items():  # ✅ Updated reference
        for hero, stats in heroes.get("Storm League", {}).items():
            if hero in banned_heroes or hero not in available_heroes:
                continue  # Skip already banned or unavailable heroes

            hero_mmr = stats.get("mmr", 2000)
            map_bonus = hero_winrates_by_map.get(map_name, {}).get(hero, {}).get("win_rate", 50) - 50

            matchup_advantage = calculate_matchup_advantage(hero, hero_matchup_data, ally_picked_heroes, enemy_picked_heroes)

            top_player, top_mmr, mmr_drop = get_enemy_top_mmr_drop(hero, enemy_player_mmr_data, enemy_picked_heroes)  # ✅ Updated reference

            score = hero_mmr + (map_bonus * 10) + matchup_advantage + (mmr_drop * 2)

            if score > best_score:
                best_score = score
                best_ban = hero
                best_reason = f"MMR {hero_mmr}, Map Bonus {map_bonus:+.1f}%, Matchup Advantage {matchup_advantage:+.1f}, {top_player} forced to drop {mmr_drop} MMR"

    if not best_ban:
        raise ValueError("❌ No valid hero found for banning! Debug the enemy hero data and ban logic.")

    banned_heroes.add(best_ban)
    available_heroes.discard(best_ban)

    return best_ban, best_reason, banned_heroes, available_heroes


def select_best_pick_with_reason(available_players, player_mmr_data, available_heroes, picked_heroes, banned_heroes,
                                 hero_winrates_by_map, hero_matchup_data, map_name, ally_picked_heroes,
                                 enemy_picked_heroes, remaining_picks):
    """Selects the best hero pick, assigns it to a player, and returns updated sets.
       If Cho or Gall is picked, automatically assigns the other hero to the next available player.
    """
    best_pick = None
    best_player = None
    best_score = -1
    best_reason = ""

    for player in available_players:
        storm_league_data = player_mmr_data.get(player, {}).get("Storm League", {})

        for hero, hero_stats in storm_league_data.items():
            if hero not in available_heroes or hero in picked_heroes or hero in banned_heroes:
                continue  # Skip unavailable heroes

            # ✅ Prevent Cho or Gall from being picked if it's the last pick
            if hero in {"Cho", "Gall"} and remaining_picks < 2:
                continue  # ✅ Skip Cho or Gall if there isn't room for both

            hero_mmr = hero_stats.get("mmr", 2000)
            map_bonus = hero_winrates_by_map.get(map_name, {}).get(hero, {}).get("win_rate", 50) - 50

            matchup_score = calculate_matchup_advantage(hero, hero_matchup_data, ally_picked_heroes,
                                                        enemy_picked_heroes)

            score = hero_mmr + (map_bonus * 10) + matchup_score

            if score > best_score:
                best_score = score
                best_pick = hero
                best_player = player
                best_reason = f"MMR {hero_mmr}, Map Bonus {map_bonus:+.1f}%, Matchup {matchup_score:+.1f}"

    remaining_heroes = available_heroes - picked_heroes - banned_heroes

    if best_pick and best_player:
        available_players.remove(best_player)
        picked_heroes.add(best_pick)
        available_heroes.discard(best_pick)

        # ✅ Handle Cho'Gall Special Case
        if best_pick in {"Cho", "Gall"}:
            second_hero = "Gall" if best_pick == "Cho" else "Cho"

            if second_hero in available_heroes and available_players:
                second_player = available_players.pop(0)  # ✅ Assign the next available player
                picked_heroes.add(second_hero)
                available_heroes.discard(second_hero)

                return [(best_player, best_pick, best_reason), (second_player, second_hero,
                                                                "[Cho'Gall rule - Auto-selected]")], available_players, available_heroes, picked_heroes

        return [(best_player, best_pick, best_reason)], available_players, available_heroes, picked_heroes

    elif remaining_heroes:
        random_player = available_players.pop(0)
        random_pick = random.choice(list(remaining_heroes))
        picked_heroes.add(random_pick)
        available_heroes.discard(random_pick)

        return [(random_player, random_pick,
                 "No strong picks available")], available_players, available_heroes, picked_heroes

    else:
        return [("Unknown Player", "No Available Heroes",
                 "No available heroes to pick")], available_players, available_heroes, picked_heroes


def draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name,
          timeframe_type="major", timeframe="2.47"):
    """Runs the draft process, predicting bans and picks intelligently."""

    draft_data = initialize_draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe_type, timeframe)
    execute_draft_phase(draft_data)
    print_final_teams(draft_data)

    utils.save_to_pickle(draft_data["draft_log"], f"draft_{map_name}.pkl")
    return draft_data["draft_log"]


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
