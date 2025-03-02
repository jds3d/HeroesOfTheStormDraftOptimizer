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


def initialize_draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe_type, timeframe):
    """Loads draft data and initializes tracking variables."""

    draft_data = load_data.load_draft_data(our_team_tags, enemy_team_tags, first_pick_team, map_name, timeframe_type, timeframe)

    hero_config = utils.load_hero_config()  # ✅ Now calling from utils

    return {
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
        "hero_roles": utils.get_hero_roles()  # ✅ Now calling from utils
    }


def select_best_pair_pick_with_reason(available_players, player_mmr_data, available_heroes, picked_heroes, banned_heroes,
                                        hero_winrates_by_map, hero_matchup_data, map_name, ally_picked_heroes, enemy_picked_heroes,
                                        team_roles, hero_config, enemy_has_offlaner):
    best_pair = None
    best_score = -float('inf')
    additional_roles = hero_config.get("additional_hero_roles", {})
    dependency_data = hero_config.get("hero_dependencies", {})
    players_list = list(available_players)
    n = len(players_list)
    # Iterate over all unordered pairs of distinct players
    for i in range(n):
        for j in range(i+1, n):
            player1 = players_list[i]
            player2 = players_list[j]
            # Iterate over candidate heroes for each player
            for hero1, stats1 in player_mmr_data.get(player1, {}).get("Storm League", {}).items():
                if hero1 not in available_heroes or hero1 in picked_heroes or hero1 in banned_heroes:
                    continue
                for hero2, stats2 in player_mmr_data.get(player2, {}).get("Storm League", {}).items():
                    if hero2 not in available_heroes or hero2 in picked_heroes or hero2 in banned_heroes:
                        continue
                    # Enforce dependency constraints:
                    valid = True
                    if hero1 in dependency_data:
                        # hero1 requires its dependency to be hero2
                        if hero2 not in dependency_data[hero1]:
                            valid = False
                    if hero2 in dependency_data:
                        # hero2 requires its dependency to be hero1
                        if hero1 not in dependency_data[hero2]:
                            valid = False
                    if not valid:
                        continue
                    # Compute individual scores
                    hero1_mmr = round(stats1.get("mmr", 2000), 2)
                    map_bonus1 = round(hero_winrates_by_map.get(map_name, {}).get(hero1, {}).get("win_rate", 50) - 50, 2)
                    role1 = additional_roles.get(hero1, "Unknown")
                    matchup_advantage1 = round(utils.calculate_matchup_advantage(hero1, hero_matchup_data, ally_picked_heroes, enemy_picked_heroes), 2)
                    score1 = hero1_mmr + (map_bonus1 * 10) + matchup_advantage1

                    hero2_mmr = round(stats2.get("mmr", 2000), 2)
                    map_bonus2 = round(hero_winrates_by_map.get(map_name, {}).get(hero2, {}).get("win_rate", 50) - 50, 2)
                    role2 = additional_roles.get(hero2, "Unknown")
                    matchup_advantage2 = round(utils.calculate_matchup_advantage(hero2, hero_matchup_data, ally_picked_heroes, enemy_picked_heroes), 2)
                    score2 = hero2_mmr + (map_bonus2 * 10) + matchup_advantage2

                    total_score = score1 + score2
                    if total_score > best_score:
                        best_score = total_score
                        reason1 = f"MMR {hero1_mmr:.2f}, Map Bonus {map_bonus1:+.2f}%, Matchup Advantage {matchup_advantage1:+.2f}, Role: {role1}"
                        reason2 = f"MMR {hero2_mmr:.2f}, Map Bonus {map_bonus2:+.2f}%, Matchup Advantage {matchup_advantage2:+.2f}, Role: {role2}"
                        best_pair = [(player1, hero1, reason1), (player2, hero2, reason2)]
    if best_pair is not None:
        available_players.remove(best_pair[0][0])
        available_players.remove(best_pair[1][0])
    return best_pair, available_players, available_heroes, picked_heroes, team_roles


def select_best_pick_with_reason(available_players, player_mmr_data, available_heroes, picked_heroes, banned_heroes, hero_winrates_by_map, hero_matchup_data, map_name, ally_picked_heroes, enemy_picked_heroes, remaining_picks, team_roles, hero_config, enemy_has_offlaner):
    best_pick = None
    best_player = None
    best_score = -1
    best_reason = ""
    additional_roles = hero_config.get("additional_hero_roles", {})
    forbidden_heroes = set(hero_config.get("forbidden_heroes", []))
    for player in available_players:
        for hero, stats in player_mmr_data.get(player, {}).get("Storm League", {}).items():
            if hero in forbidden_heroes:
                continue
            if hero not in available_heroes or hero in picked_heroes or hero in banned_heroes:
                continue
            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(hero_winrates_by_map.get(map_name, {}).get(hero, {}).get("win_rate", 50) - 50, 2)
            role = additional_roles.get(hero, "Unknown")
            matchup_advantage = round(utils.calculate_matchup_advantage(hero, hero_matchup_data, ally_picked_heroes, enemy_picked_heroes), 2)
            score = hero_mmr + (map_bonus * 10) + matchup_advantage
            if score > best_score:
                best_score = score
                best_pick = hero
                best_player = player
                best_reason = f"MMR {hero_mmr:.2f}, Map Bonus {map_bonus:+.2f}%, Matchup Advantage {matchup_advantage:+.2f}, Role: {role}"
    if best_player in available_players:
        available_players.remove(best_player)
    return [(best_player, best_pick, best_reason)], available_players, available_heroes, picked_heroes, team_roles


def execute_draft_phase(draft_data):
    print(f"\nDraft for {draft_data['team_1_name']} vs {draft_data['team_2_name']}\n")
    print(f"{'Order':<6}\t{'Type':<6}\t{'Team':<25}\t{'Player':<20}\t{'Hero':<15}\t{'Reason'}")
    print("=" * 180)
    remaining_picks = sum(1 for pick in DRAFT_ORDER if pick[0] == "Pick")
    hero_config = utils.load_hero_config()
    team_roles = {draft_data["team_1_name"]: {"Tank": 0, "Healer": 0, "Offlaner": 0, "Assassin": 0},
                  draft_data["team_2_name"]: {"Tank": 0, "Healer": 0, "Offlaner": 0, "Assassin": 0}}
    enemy_has_offlaner = False
    pair_starts = {6, 8, 12, 14}
    i = 0
    while i < len(DRAFT_ORDER):
        draft_type, order = DRAFT_ORDER[i]
        team_name = draft_data["team_1_name"] if order in FIRST_PICK_SLOTS else draft_data["team_2_name"]
        enemy_team = draft_data["team_2_name"] if team_name == draft_data["team_1_name"] else draft_data["team_1_name"]
        team_tags = draft_data["available_players_team_1"] if team_name == draft_data["team_1_name"] else draft_data["available_players_team_2"]
        ally = set(draft_data["team_1_picked_heroes"].values()) if team_name == draft_data["team_1_name"] else set(draft_data["team_2_picked_heroes"].values())
        enemy = set(draft_data["team_2_picked_heroes"].values()) if team_name == draft_data["team_1_name"] else set(draft_data["team_1_picked_heroes"].values())
        if team_roles[enemy_team]["Offlaner"] > 0:
            enemy_has_offlaner = True
        if draft_type == "Ban":
            enemy_mmr = draft_data["enemy_player_mmr_data"] if team_name == draft_data["team_1_name"] else draft_data["friendly_player_mmr_data"]
            ban, reason, draft_data["banned_heroes"], draft_data["available_heroes"] = select_best_ban_with_reason(
                enemy_mmr, draft_data["hero_winrates_by_map"], draft_data["hero_matchup_data"],
                draft_data["banned_heroes"], draft_data["available_heroes"], draft_data["enemy_team_data"],
                draft_data["map_name"], ally, enemy
            )
            draft_data["draft_log"].append((order, "Ban", team_name, ban, reason))
            print(f"{order:<6}\tBan   \t{team_name:<25}\t{'-':<20}\t{ban:<15}\t{reason}")
            i += 1
        elif draft_type == "Pick":
            # Check if this order starts a paired pick round
            if order in pair_starts:
                pair_picks, team_tags, draft_data["available_heroes"], draft_data["picked_heroes"], team_roles[team_name] = \
                    select_best_pair_pick_with_reason(team_tags,
                        draft_data["friendly_player_mmr_data"] if team_name == draft_data["team_1_name"] else draft_data["enemy_player_mmr_data"],
                        draft_data["available_heroes"], draft_data["picked_heroes"], draft_data["banned_heroes"],
                        draft_data["hero_winrates_by_map"], draft_data["hero_matchup_data"], draft_data["map_name"],
                        ally, enemy, team_roles[team_name], hero_config, enemy_has_offlaner)
                if pair_picks is not None:
                    for pick in pair_picks:
                        p_order = DRAFT_ORDER[i][1]  # use the current order for this pick
                        draft_data["draft_log"].append((p_order, "Pick", team_name, pick[0], pick[1], pick[2]))
                        if team_name == draft_data["team_1_name"]:
                            draft_data["team_1_picked_heroes"][pick[0]] = pick[1]  # store only the hero name
                        else:
                            draft_data["team_2_picked_heroes"][pick[0]] = pick[1]
                        print(f"{p_order:<6}\tPick  \t{team_name:<25}\t{pick[0]:<20}\t{pick[1]:<15}\t{pick[2]}")
                        i += 1  # increment for each pick in the pair
                else:
                    i += 1
            else:
                # Normal single pick round
                picks, team_tags, draft_data["available_heroes"], draft_data["picked_heroes"], team_roles[team_name] = \
                    select_best_pick_with_reason(team_tags,
                        draft_data["friendly_player_mmr_data"] if team_name == draft_data["team_1_name"] else draft_data["enemy_player_mmr_data"],
                        draft_data["available_heroes"], draft_data["picked_heroes"], draft_data["banned_heroes"],
                        draft_data["hero_winrates_by_map"], draft_data["hero_matchup_data"], draft_data["map_name"],
                        ally, enemy, remaining_picks, team_roles[team_name], hero_config, enemy_has_offlaner)
                remaining_picks -= len(picks)
                for player, pick, pr in picks:
                    if pick in draft_data["picked_heroes"]:
                        continue
                    draft_data["picked_heroes"].add(pick)
                    if team_name == draft_data["team_1_name"]:
                        draft_data["team_1_picked_heroes"][player] = pick
                    else:
                        draft_data["team_2_picked_heroes"][player] = pick
                    draft_data["draft_log"].append((order, "Pick", team_name, player, pick, pr))
                    print(f"{order:<6}\tPick  \t{team_name:<25}\t{player:<20}\t{pick:<15}\t{pr}")
                i += 1
        else:
            i += 1



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


def select_best_ban_with_reason(enemy_player_mmr_data, hero_winrates_by_map, hero_matchup_data, banned_heroes, available_heroes, enemy_team_data, map_name, ally_picked_heroes,
                                enemy_picked_heroes):
    """Selects the best hero to ban and formats numeric values correctly at their source."""
    best_ban = None
    best_score = -1
    best_reason = ""

    for player, heroes in enemy_player_mmr_data.items():
        if "Storm League" not in heroes:
            continue  # Skip players without Storm League data

        for hero, stats in heroes["Storm League"].items():
            if hero in banned_heroes or hero not in available_heroes:
                continue  # Skip already banned or unavailable heroes

            hero_mmr = round(stats.get("mmr", 2000), 2)  # ✅ Round before storing
            map_bonus = round(hero_winrates_by_map.get(map_name, {}).get(hero, {}).get("win_rate", 50) - 50, 2)
            matchup_advantage = round(utils.calculate_matchup_advantage(hero, hero_matchup_data, ally_picked_heroes, enemy_picked_heroes), 2)
            top_player, top_mmr, mmr_drop = get_enemy_top_mmr_drop(hero, enemy_player_mmr_data, enemy_picked_heroes)

            score = hero_mmr + (map_bonus * 10) + matchup_advantage + (mmr_drop * 2)

            if score > best_score:
                best_score = score
                best_ban = hero
                best_reason = f"MMR {hero_mmr}, Map Bonus {map_bonus:+.2f}%, Matchup Advantage {matchup_advantage:+.2f}, {top_player} forced to drop {round(mmr_drop, 2)} MMR"

    if not best_ban:
        raise ValueError("❌ No valid hero found for banning! Debug the enemy hero data and ban logic.")

    banned_heroes.add(best_ban)
    available_heroes.discard(best_ban)

    return best_ban, best_reason, banned_heroes, available_heroes


def draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name,
          timeframe_type="major", timeframe="2.47"):
    """Runs the draft process, predicting bans and picks intelligently."""

    draft_data = initialize_draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe_type, timeframe)
    execute_draft_phase(draft_data)
    utils.print_final_teams(draft_data)

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
