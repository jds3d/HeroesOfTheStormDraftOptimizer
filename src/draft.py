import utils  # ✅ Import utils as a package
import load_data

DRAFT_ORDER = [
    ("Ban", 1),
    ("Ban", 2),
    ("Ban", 3),
    ("Ban", 4),
    ("Pick", 5),
    ("Pick", 6), ("Pick", 7),
    ("Pick", 8), ("Pick", 9),
    ("Ban", 10), ("Ban", 11),
    ("Pick", 12), ("Pick", 13),
    ("Pick", 14), ("Pick", 15),
    ("Pick", 16)
]

FIRST_PICK_SLOTS = {1, 3, 5, 8, 9, 10, 14, 15}

DRAFT_DATA = {}


def initialize_draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe_type, timeframe):
    """Loads all draft data into a global variable for efficiency."""

    global DRAFT_DATA

    draft_data = load_data.load_draft_data(our_team_tags, enemy_team_tags, first_pick_team, map_name, timeframe_type, timeframe)

    hero_config = utils.load_hero_config()
    api_roles = utils.get_hero_roles()  # Load hero roles from API once

    # Merge API roles with additional roles from config
    for hero, roles in hero_config.get("additional_hero_roles", {}).items():
        api_roles[hero] = roles  # Override/add roles from config

    required_roles = set(hero_config.get("required_roles", []))  # Load required roles from config

    # Populate global DRAFT_DATA
    DRAFT_DATA.update({
        "map_name": map_name,
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
        "hero_roles": api_roles,  # Store merged hero roles globally
        "forbidden_heroes": set(hero_config.get("forbidden_heroes", [])),  # Store forbidden heroes globally
        "required_roles": required_roles,  # Store required roles dynamically
        "team_roles": {
            our_team_name if first_pick_team == 1 else enemy_team_name: {role: 0 for role in required_roles},
            enemy_team_name if first_pick_team == 1 else our_team_name: {role: 0 for role in required_roles}
        }
    })


def select_best_pick_with_reason(available_players, team_name):
    """Selects the best hero pick using global draft data, ensuring required roles are filled when necessary."""

    global DRAFT_DATA

    required_roles = DRAFT_DATA["required_roles"]
    already_picked = len(DRAFT_DATA["team_1_picked_heroes"]) if team_name == DRAFT_DATA["team_1_name"] else len(DRAFT_DATA["team_2_picked_heroes"])
    remaining_picks = 5 - already_picked  # Calculate dynamically

    missing_roles = {r for r in required_roles if DRAFT_DATA["team_roles"][team_name].get(r, 0) == 0}

    # **Use correct player MMR data based on the drafting team**
    player_mmr_data = DRAFT_DATA["friendly_player_mmr_data"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["enemy_player_mmr_data"]

    candidates = []

    for player in available_players:
        for hero, stats in player_mmr_data.get(player, {}).get("Storm League", {}).items():
            if hero in DRAFT_DATA["forbidden_heroes"] or hero not in DRAFT_DATA["available_heroes"] or hero in DRAFT_DATA["picked_heroes"] or hero in DRAFT_DATA["banned_heroes"]:
                continue

            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(DRAFT_DATA["hero_winrates_by_map"].get(DRAFT_DATA["map_name"], {}).get(hero, {}).get("win_rate", 50) - 50, 2)

            role_list = DRAFT_DATA["hero_roles"].get(hero, ["Unknown"])
            if not isinstance(role_list, list):
                role_list = [role_list]
            role = "Offlaner" if "Bruiser" in role_list else role_list[0]

            matchup_advantage = round(utils.calculate_matchup_advantage(hero, DRAFT_DATA["hero_matchup_data"],
                                                                        set(DRAFT_DATA["team_1_picked_heroes"].values()), set(DRAFT_DATA["team_2_picked_heroes"].values())), 2)

            score = hero_mmr + (map_bonus * 10) + matchup_advantage
            reason = f"Score: {score:.2f}, MMR {hero_mmr:.2f}, Map Bonus {map_bonus:+.2f}%, Matchup Advantage {matchup_advantage:+.2f}, Role: {role}"
            candidates.append((score, player, hero, reason, role))

    # **Throw a clear error if no valid heroes exist**
    if not candidates:
        raise ValueError(f"❌ ERROR: No valid picks available for {team_name}. "
                         f"Available Players: {available_players}, "
                         f"Available Heroes: {DRAFT_DATA['available_heroes']}, "
                         f"Picked Heroes: {DRAFT_DATA['picked_heroes']}, "
                         f"Banned Heroes: {DRAFT_DATA['banned_heroes']}")

    # **Only enforce missing roles if the number of picks matches the number of missing roles**
    enforce_roles = len(missing_roles) == remaining_picks
    filtered_candidates = [cand for cand in candidates if cand[4] in missing_roles] if enforce_roles else candidates

    # **Ensure `max()` always has a valid input**
    best_candidate = max(filtered_candidates if filtered_candidates else candidates, key=lambda x: x[0])

    best_player = best_candidate[1]
    best_pick = best_candidate[2]
    best_score = best_candidate[0]
    best_reason = best_candidate[3]

    available_players.remove(best_player)

    if best_candidate[4] in required_roles:
        DRAFT_DATA["team_roles"][team_name][best_candidate[4]] += 1  # Ensure role count updates properly

    return [(best_player, best_pick, best_score, best_reason)]


def execute_draft_phase():
    """Executes the draft process, ensuring bans and picks are handled correctly."""

    global DRAFT_DATA

    print(f"\nDraft for {DRAFT_DATA['team_1_name']} vs {DRAFT_DATA['team_2_name']}\n")
    print(f"{'Order':<6}\t{'Type':<6}\t{'Team':<25}\t{'Player':<20}\t{'Hero':<15}\t{'Score':<10}\t{'Reason'}")
    print("=" * 200)

    for draft_type, order in DRAFT_ORDER:
        team_name = DRAFT_DATA["team_1_name"] if order in FIRST_PICK_SLOTS else DRAFT_DATA["team_2_name"]
        team_tags = DRAFT_DATA["available_players_team_1"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["available_players_team_2"]

        already_picked = len(DRAFT_DATA["team_1_picked_heroes"]) if team_name == DRAFT_DATA["team_1_name"] else len(DRAFT_DATA["team_2_picked_heroes"])
        remaining_picks = 5 - already_picked  # Calculate dynamically

        if draft_type == "Ban":
            # **Call ban selection function**
            ban, score, reason = select_best_ban_with_reason()

            # **Save the ban**
            DRAFT_DATA["draft_log"].append((order, "Ban", team_name, ban, score, reason))
            print(f"{order:<6}\tBan   \t{team_name:<25}\t{'-':<20}\t{ban:<15}\t{score:<10.2f}\t{reason}")

        elif draft_type == "Pick":
            picks = select_best_pick_with_reason(team_tags, team_name)
            for player, pick, score, reason in picks:
                if pick in DRAFT_DATA["picked_heroes"]:
                    continue
                DRAFT_DATA["picked_heroes"].add(pick)
                if team_name == DRAFT_DATA["team_1_name"]:
                    DRAFT_DATA["team_1_picked_heroes"][player] = pick
                else:
                    DRAFT_DATA["team_2_picked_heroes"][player] = pick
                DRAFT_DATA["draft_log"].append((order, "Pick", team_name, player, pick, score, reason))
                print(f"{order:<6}\tPick  \t{team_name:<25}\t{player:<20}\t{pick:<15}\t{score:<10.2f}\t{reason}")


def get_enemy_top_mmr_drop(hero, enemy_player_mmr_data, picked_players):
    """Finds the highest MMR remaining player for a hero and calculates the MMR drop if they lose it."""
    best_mmr = 0
    best_player = "Unknown"
    mmr_drop = 0

    for player, heroes in enemy_player_mmr_data.items():
        if "Storm League" not in heroes or player in picked_players:
            continue  # ✅ Skip players who don't have Storm League data or have already picked

        storm_league_heroes = heroes["Storm League"]
        if hero not in storm_league_heroes:
            continue  # ✅ Skip players who haven't played this hero

        player_mmr = storm_league_heroes[hero].get("mmr", 2000)  # ✅ Default to 2000 if missing

        if player_mmr > best_mmr:
            best_mmr = player_mmr
            best_player = player

            # ✅ Get all MMRs for the player's heroes, sorted from highest to lowest
            mmr_values = sorted(
                [storm_league_heroes[other_hero].get("mmr", 2000) for other_hero in storm_league_heroes],
                reverse=True
            )

            # ✅ Second highest MMR, or 2000 if only one hero is played
            second_best_mmr = mmr_values[1] if len(mmr_values) > 1 else 2000

            mmr_drop = best_mmr - second_best_mmr  # ✅ Compare highest to second highest

    return best_player, best_mmr, mmr_drop


def select_best_ban_with_reason():
    """Selects the best hero to ban based on global draft data and returns the ban, its score, and reason."""

    global DRAFT_DATA

    best_ban = None
    best_score = -1
    best_reason = ""

    enemy_mmr_data = DRAFT_DATA["enemy_player_mmr_data"]
    hero_winrates_by_map = DRAFT_DATA["hero_winrates_by_map"]
    hero_matchup_data = DRAFT_DATA["hero_matchup_data"]
    banned_heroes = DRAFT_DATA["banned_heroes"]
    available_heroes = DRAFT_DATA["available_heroes"]
    enemy_team_data = DRAFT_DATA["enemy_team_data"]
    map_name = DRAFT_DATA["map_name"]

    ally_picked_heroes = set(DRAFT_DATA["team_1_picked_heroes"].values())
    enemy_picked_heroes = set(DRAFT_DATA["team_2_picked_heroes"].values())

    for player, heroes in enemy_mmr_data.items():
        if "Storm League" not in heroes:
            continue  # Skip players without Storm League data

        for hero, stats in heroes["Storm League"].items():
            if hero in banned_heroes or hero not in available_heroes:
                continue  # Skip already banned or unavailable heroes

            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(hero_winrates_by_map.get(map_name, {}).get(hero, {}).get("win_rate", 50) - 50, 2)
            matchup_advantage = round(utils.calculate_matchup_advantage(hero, hero_matchup_data, ally_picked_heroes, enemy_picked_heroes), 2)
            top_player, top_mmr, mmr_drop = get_enemy_top_mmr_drop(hero, enemy_mmr_data, enemy_picked_heroes)

            # **Compute ban score**
            score = hero_mmr + (map_bonus * 10) + matchup_advantage + (mmr_drop * 2)

            if score > best_score:
                best_score = score
                best_ban = hero
                best_reason = f"Score: {score:.2f}, MMR {hero_mmr}, Map Bonus {map_bonus:+.2f}%, Matchup Advantage {matchup_advantage:+.2f}, {top_player} forced to drop {round(mmr_drop, 2)} MMR"

    if not best_ban:
        raise ValueError("❌ No valid hero found for banning! Debug the enemy hero data and ban logic.")

    # **Save the ban in DRAFT_DATA**
    DRAFT_DATA["banned_heroes"].add(best_ban)
    DRAFT_DATA["available_heroes"].discard(best_ban)

    return best_ban, best_score, best_reason




def draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name,
          timeframe_type="major", timeframe="2.47"):
    """Runs the draft process, predicting bans and picks intelligently."""

    initialize_draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe_type, timeframe)
    execute_draft_phase()
    utils.print_final_teams(DRAFT_DATA)  # Use DRAFT_DATA instead of draft_data

    utils.save_to_pickle(DRAFT_DATA["draft_log"], f"draft_{map_name}.pkl")
    return DRAFT_DATA["draft_log"]



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
