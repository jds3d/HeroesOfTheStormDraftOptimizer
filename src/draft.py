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
    DRAFT_DATA['available_heroes'].remove(best_pick)

    if best_candidate[4] in required_roles:
        DRAFT_DATA["team_roles"][team_name][best_candidate[4]] += 1  # Ensure role count updates properly

    return [(best_player, best_pick, best_score, best_reason)]


def execute_draft_phase():
    """Executes the draft process, ensuring bans and picks are handled correctly."""

    global DRAFT_DATA

    print(f"\nDraft for {DRAFT_DATA['team_1_name']} vs {DRAFT_DATA['team_2_name']}")
    print(f"Map: {DRAFT_DATA['map_name']}\n")  # ✅ Map Name on its own line
    print(f"{'Order':<6}\t{'Type':<6}\t{'Team':<25}\t{'Player':<20}\t{'Hero':<15}\t{'Score':<10}\t{'Reason'}")
    print("=" * 200)

    for draft_type, order in DRAFT_ORDER:
        team_name = DRAFT_DATA["team_1_name"] if order in FIRST_PICK_SLOTS else DRAFT_DATA["team_2_name"]
        team_tags = DRAFT_DATA["available_players_team_1"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["available_players_team_2"]

        if draft_type == "Ban":
            # **Call ban selection function with correct team name**
            ban, score, reason = select_best_ban_with_reason(team_name)

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


def select_best_ban_with_reason(team_name):
    """Selects the best hero to ban based on global draft data and returns the ban, its score, and reason."""

    global DRAFT_DATA

    best_ban = None
    best_score = -1
    best_reason = ""
    best_player = "Unknown"
    second_best_hero = "Unknown"
    score_drop = 0

    # **Determine the correct enemy team data based on who is banning**
    if team_name == DRAFT_DATA["team_1_name"]:
        enemy_mmr_data = DRAFT_DATA["enemy_player_mmr_data"]  # Banning team = Team 1, enemy = Team 2
        enemy_picked_heroes = set(DRAFT_DATA["team_2_picked_heroes"].values())
        enemy_players_remaining = set(DRAFT_DATA["enemy_player_mmr_data"].keys()) - set(DRAFT_DATA["team_2_picked_heroes"].keys())
    else:
        enemy_mmr_data = DRAFT_DATA["friendly_player_mmr_data"]  # Banning team = Team 2, enemy = Team 1
        enemy_picked_heroes = set(DRAFT_DATA["team_1_picked_heroes"].values())
        enemy_players_remaining = set(DRAFT_DATA["friendly_player_mmr_data"].keys()) - set(DRAFT_DATA["team_1_picked_heroes"].keys())

    hero_winrates_by_map = DRAFT_DATA["hero_winrates_by_map"]
    hero_matchup_data = DRAFT_DATA["hero_matchup_data"]
    map_name = DRAFT_DATA["map_name"]
    ally_picked_heroes = set(DRAFT_DATA["team_1_picked_heroes"].values()) if team_name == DRAFT_DATA["team_1_name"] else set(DRAFT_DATA["team_2_picked_heroes"].values())

    # **Filter `available_heroes` to remove heroes that have already been picked**
    available_heroes = DRAFT_DATA["available_heroes"] - enemy_picked_heroes

    for player in enemy_players_remaining:
        heroes = enemy_mmr_data.get(player, {})
        if "Storm League" not in heroes:
            continue  # Skip players without Storm League data

        player_hero_scores = []

        for hero in available_heroes:
            if hero not in heroes["Storm League"]:
                continue  # Skip if this player never played the hero

            stats = heroes["Storm League"][hero]
            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(hero_winrates_by_map.get(map_name, {}).get(hero, {}).get("win_rate", 50) - 50, 2)
            matchup_advantage = round(utils.calculate_matchup_advantage(hero, hero_matchup_data, ally_picked_heroes, enemy_picked_heroes), 2)

            # **Compute hero score**
            score = hero_mmr + (map_bonus * 10) + matchup_advantage
            player_hero_scores.append((score, hero, hero_mmr, map_bonus, matchup_advantage))

        # **Sort the hero scores for this player, from best to worst**
        player_hero_scores.sort(reverse=True, key=lambda x: x[0])

        if len(player_hero_scores) > 1:
            first_choice_score, first_choice_hero, first_choice_mmr, first_choice_map_bonus, first_choice_matchup_advantage = player_hero_scores[0]
            second_choice_score, second_choice_hero, *_ = player_hero_scores[1]  # Get second-best hero info
        elif len(player_hero_scores) == 1:
            first_choice_score, first_choice_hero, first_choice_mmr, first_choice_map_bonus, first_choice_matchup_advantage = player_hero_scores[0]
            second_choice_score, second_choice_hero = 2000, "Unknown"  # Default score for second pick if only one hero exists
        else:
            continue  # This player has no valid picks

        # **Calculate score drop if banning the best hero**
        drop = first_choice_score - second_choice_score

        if first_choice_score > best_score:
            best_score = first_choice_score
            best_ban = first_choice_hero
            best_player = player
            second_best_hero = second_choice_hero
            score_drop = drop
            best_reason = (
                f"Score: {best_score:.2f}, MMR {first_choice_mmr:.2f}, "
                f"Map Bonus {first_choice_map_bonus:+.2f}%, Matchup Advantage {first_choice_matchup_advantage:+.2f}, "
                f"Banning {best_ban} forces {best_player} to pick {second_best_hero}, reducing score by {score_drop:.2f}"
            )

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
    # our_team_tags = ["HuckIt#1840", "topgun707#1875", "papichulo#12352", "mrhustler#1686", "mojoe#11242"]

    # Enemy team - Fancy Flightless Fowl
    enemy_team_name = "Fancy Flightless Fowl"
    # enemy_team_tags = ["Alfie#1948", "Silverbell#11333", "AngryPanda#12178", "GingiBoi#1791", "XxLuNaTiCxX#11820"]
    enemy_team_tags = ["Alfie#1948", "Batmang#11255", "AngryPanda#12178", "GingiBoi#1791", "Stefwithanf#1470"] # Valkrye#11330

    # Map selection
    map_name = "Garden of Terror"

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
    ## TODO: Make this use 2.55.
    draft_log = draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe="2.47")

    # Print final draft results
    # print("\nFinal Draft Results:")
    # for entry in draft_log:
    #     if entry[1] == "Ban":
    #         order, draft_type, team_name, hero, reason = entry
    #         print(f"{draft_type} {order} ({team_name}): {hero} - {reason}")
    #     else:  # Pick
    #         order, draft_type, team_name, player, hero, reason = entry
    #         print(f"{draft_type} {order} ({team_name} - {player}): {hero} - {reason}")
