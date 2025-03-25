import interface
import utils


def execute_pick_phase(order, team_name, user_input_enabled, DRAFT_DATA):
    """Handles picking heroes, prioritizing critical selections and role enforcement with suggested picks and reasons."""

    team_tags = utils.get_available_players(DRAFT_DATA, team_name)

    # ✅ Now passing `order` to enforce pick timing restrictions
    pick_suggestions = select_best_pick_with_reason(DRAFT_DATA, team_name, order, num_suggestions=5)

    if not user_input_enabled:
        selected_score, selected_player, selected_hero, selected_role, reason = pick_suggestions[0][1:]
    else:
        # ✅ Provide suggestions before user input with reasons
        formatted_suggestions = [f"{p[3]}, Player: {p[2]}, {p[5]})" for p in pick_suggestions]
        print("\nSuggested Picks:\n", "\n".join(formatted_suggestions))

        selected_index = interface.select_hero_interactive(
            f"Enter pick for {team_name} (suggested: {formatted_suggestions[0]}):",
            DRAFT_DATA["available_heroes"],
            DRAFT_DATA["hero_roles"],
            DRAFT_DATA["picked_heroes"],
            DRAFT_DATA["banned_heroes"],
            [p[3] for p in pick_suggestions]
        )

        if selected_index in [p[3] for p in pick_suggestions]:  # If selected hero is in suggestions
            selected_pick = next(p for p in pick_suggestions if p[3] == selected_index)
            selected_score, selected_player, selected_hero, selected_role, reason = selected_pick[1:]
        else:  # If user entered a different hero
            selected_hero = selected_index  # Assign hero name directly
            selected_player = None  # Prompt for player separately
            selected_score, reason = None, None
            # Get the role(s) of the manually selected hero
            selected_roles = DRAFT_DATA["hero_roles"].get(selected_hero, ["Unknown"])
            selected_role = selected_roles[0]  # Default to the first listed role

        # If no player was auto-selected, ask the user to pick one
        import difflib

        # If no player was auto-selected, ask the user to pick one
        if selected_player is None:
            print(f"\nAvailable Players for {team_name}: {', '.join(team_tags)}")

            while True:
                selected_input = input(f"Which player on {team_name} is picking {selected_hero}? ").strip()

                # Find all matches where the input uniquely identifies a player
                possible_matches = [player for player in team_tags if player.lower().startswith(selected_input.lower())]

                if len(possible_matches) == 1:  # If exactly one match, use it
                    selected_player = possible_matches[0]
                    break
                elif len(possible_matches) > 1:  # If ambiguous, ask again
                    print(f"Ambiguous selection. Matches: {', '.join(possible_matches)}. Please enter more characters.")
                else:  # No matches found
                    print("Invalid player. Please enter a valid team member or more characters.")

    # ✅ Update DRAFT_DATA correctly
    team_tags.remove(selected_player)
    DRAFT_DATA["picked_heroes"].add(selected_hero)
    DRAFT_DATA["available_heroes"].remove(selected_hero)

    if selected_role in DRAFT_DATA["required_roles"]:
        DRAFT_DATA["team_roles"][team_name][selected_role] += 1  # ✅ Update role count only when a hero is actually picked

    if team_name == DRAFT_DATA["team_1_name"]:
        DRAFT_DATA["team_1_picked_heroes"][selected_player] = selected_hero
    else:
        DRAFT_DATA["team_2_picked_heroes"][selected_player] = selected_hero

    DRAFT_DATA["draft_log"].append((order, "Pick", team_name, selected_player, selected_hero, selected_score, reason))
    print(f"{order:<6} Pick  {team_name:<25} {selected_player:<20} {selected_hero:<15} {selected_score if selected_score is not None else 'N/A':<10} {reason if reason else 'No reason provided'}")



def select_best_pick_with_reason(DRAFT_DATA, team_name, order, num_suggestions=1, mmr_threshold=2700):
    """Selects the best `num_suggestions` hero picks while enforcing role limits, pick timing restrictions, and slightly boosting smaller hero pools."""

    required_roles = DRAFT_DATA["required_roles"]
    already_picked = len(DRAFT_DATA["team_1_picked_heroes"]) if team_name == DRAFT_DATA["team_1_name"] else len(DRAFT_DATA["team_2_picked_heroes"])
    remaining_picks = 5 - already_picked
    missing_roles = {r for r in required_roles if DRAFT_DATA["team_roles"][team_name].get(r, 0) == 0}

    team_mmr_data = DRAFT_DATA["team_1_player_mmr_data"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["team_2_player_mmr_data"]

    # ✅ Load role limits and pick restrictions from hero_config
    role_limits = DRAFT_DATA.get("role_limits", {})
    role_pick_restrictions = DRAFT_DATA.get("role_pick_restrictions", {})
    hero_pick_restrictions = DRAFT_DATA.get("hero_pick_restrictions", {})

    role_counts = DRAFT_DATA["team_roles"][team_name]

    # ✅ Determine the current pick phase
    is_middle_or_late_pick = order >= 8
    is_late_pick = order >= 14

    available_players = utils.get_available_players(DRAFT_DATA, team_name)
    player_hero_pool_sizes = utils.get_hero_player_pool_sizes(DRAFT_DATA, team_name)

    # ✅ Determine max pool size to scale the boost
    max_pool_size = max(player_hero_pool_sizes.values(), default=1)

    candidates = []

    for player in available_players:
        hero_scores = []
        for hero, stats in team_mmr_data.get(player, {}).get("Storm League", {}).items():
            if hero in DRAFT_DATA["forbidden_heroes"] or hero not in DRAFT_DATA["available_heroes"] or hero in DRAFT_DATA["picked_heroes"] or hero in DRAFT_DATA["banned_heroes"]:
                continue

            role_list = DRAFT_DATA["hero_roles"].get(hero, ["Unknown"])
            role = "Offlaner" if "Bruiser" in role_list else role_list[0]

            # ✅ Enforce role limits from config
            if role in role_limits and role_counts.get(role, 0) >= role_limits[role]:
                continue

            # ✅ Enforce role pick timing restrictions
            if role in role_pick_restrictions:
                restriction = role_pick_restrictions[role]
                if restriction == "middle" and not is_middle_or_late_pick:
                    continue
                elif restriction == "late" and not is_late_pick:
                    continue

            # ✅ Enforce individual hero pick timing restrictions
            if hero in hero_pick_restrictions:
                restriction = hero_pick_restrictions[hero]
                if restriction == "middle" and not is_middle_or_late_pick:
                    continue
                elif restriction == "late" and not is_late_pick:
                    continue

            # ✅ If role enforcement is needed, filter to missing roles
            enforce_roles = remaining_picks == len(missing_roles)
            if enforce_roles and role not in missing_roles:
                continue

            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(DRAFT_DATA["hero_winrates_by_map"].get(DRAFT_DATA["map_name"], {}).get(hero, {}).get("win_rate", 50) - 50, 2)
            synergy_score = round(utils.calculate_allied_synergy_score(DRAFT_DATA, hero, team_name), 2)
            counter_score = round(utils.calculate_enemy_countering_score(DRAFT_DATA, hero, team_name), 2)

            # ✅ Apply a **boost** to players with smaller hero pools
            hero_pool_size = player_hero_pool_sizes.get(player, 0)

            score = hero_mmr + (map_bonus * 50) + (synergy_score * 25) + (counter_score * 25)
            hero_scores.append((score, hero, role, hero_mmr, map_bonus, synergy_score, counter_score))

        hero_scores.sort(reverse=True, key=lambda x: x[0])

        if not hero_scores:
            continue

        best_score, best_hero, best_role, hero_mmr, map_bonus, synergy_score, counter_score = hero_scores[0]
        second_best_score = hero_scores[1][0] if len(hero_scores) > 1 else 2000

        pool_boost = (1 - (hero_pool_size / max_pool_size)) * 500  # Boost ranges from 0 to 400
        score_drop = best_score - second_best_score + pool_boost

        reason = f"Score: {best_score:.2f}, Score Drop: {score_drop:.2f}, MMR {hero_mmr:.2f}, Map Bonus {map_bonus:+.2f}%, Synergy {synergy_score:+.2f}, Counter {counter_score:+.2f}, Pool Boost: {pool_boost:.2f}, Role: {best_role}"

        candidates.append((score_drop, best_score, player, best_hero, best_role, reason))

    if not candidates:
        raise ValueError(f"❌ ERROR: No valid picks available for {team_name}. Check available heroes and players.")

    # ✅ Sort by score drop first, then total score, and return `num_suggestions`
    candidates.sort(reverse=True, key=lambda x: (x[0], x[1]))
    return candidates[:num_suggestions]

