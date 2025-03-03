import interface
import utils


def execute_pick_phase(order, team_name, user_input_enabled, DRAFT_DATA):
    """Handles picking heroes, prioritizing critical selections and role enforcement with suggested picks and reasons."""

    team_tags = DRAFT_DATA["available_players_team_1"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["available_players_team_2"]
    pick_suggestions = select_best_pick_with_reason(DRAFT_DATA, team_tags, team_name, num_suggestions=5)

    if not user_input_enabled:
        selected_score, selected_player, selected_pick, selected_role, reason = pick_suggestions[0][1:]
    else:
        # ✅ Provide suggestions before user input with reasons
        formatted_suggestions = [f"{p[3]} (Score: {p[1]:.2f}, Player: {p[2]})" for p in pick_suggestions]
        print("\nSuggested Picks:\n", "\n".join(formatted_suggestions))

        selected_pick = interface.select_hero_interactive(
            f"Enter pick for {team_name} (suggested: {formatted_suggestions[0]}):",
            DRAFT_DATA["available_heroes"],
            DRAFT_DATA["hero_roles"],
            DRAFT_DATA["picked_heroes"],
            DRAFT_DATA["banned_heroes"],
            [p[3] for p in pick_suggestions]
        )

        if selected_pick is not None and selected_pick in DRAFT_DATA["available_heroes"]:
            # ✅ Allow the user to select which player is picking this hero
            available_players = DRAFT_DATA["available_players_team_1"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["available_players_team_2"]

            selected_player = interface.select_player_interactive(f"Who picked {selected_pick}?", available_players)

            # ✅ Retrieve hero details from pick suggestions if available
            selected_data = next((entry for entry in pick_suggestions if entry[3] == selected_pick), None)

            if selected_data:
                score_drop, selected_score, _, _, selected_role, reason = selected_data
            else:
                # ✅ Default values if manually picked hero is not in the suggestions
                selected_score, score_drop, selected_role, reason = 0, 0, "Unknown", "Manual input"
        else:
            selected_data = pick_suggestions[0] if pick_suggestions else None

            if selected_data:
                score_drop, selected_score, selected_player, selected_pick, selected_role, reason = selected_data
            else:
                raise ValueError("❌ ERROR: No valid pick found in pick_suggestions.")

    # ✅ Update DRAFT_DATA correctly
    team_tags.remove(selected_player)
    DRAFT_DATA["picked_heroes"].add(selected_pick)
    DRAFT_DATA["available_heroes"].remove(selected_pick)

    if selected_role in DRAFT_DATA["required_roles"]:
        DRAFT_DATA["team_roles"][team_name][selected_role] += 1  # ✅ Update role count only when a hero is actually picked

    if team_name == DRAFT_DATA["team_1_name"]:
        DRAFT_DATA["team_1_picked_heroes"][selected_player] = selected_pick
    else:
        DRAFT_DATA["team_2_picked_heroes"][selected_player] = selected_pick

    DRAFT_DATA["draft_log"].append((order, "Pick", team_name, selected_player, selected_pick, selected_score, reason))
    print(f"{order:<6} Pick  {team_name:<25} {selected_player:<20} {selected_pick:<15} {selected_score:<10.2f} {reason}")


def select_best_pick_with_reason(DRAFT_DATA, available_players, team_name, num_suggestions=1, mmr_threshold=2700):
    """Selects the best `num_suggestions` hero picks while enforcing role limits."""

    required_roles = DRAFT_DATA["required_roles"]
    already_picked = len(DRAFT_DATA["team_1_picked_heroes"]) if team_name == DRAFT_DATA["team_1_name"] else len(DRAFT_DATA["team_2_picked_heroes"])
    remaining_picks = 5 - already_picked
    missing_roles = {r for r in required_roles if DRAFT_DATA["team_roles"][team_name].get(r, 0) == 0}

    team_mmr_data = DRAFT_DATA["team_1_player_mmr_data"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["team_2_player_mmr_data"]

    # ✅ Load role limits from hero_config.json
    role_limits = DRAFT_DATA.get("role_limits", {"Tank": 1})
    role_counts = DRAFT_DATA["team_roles"][team_name]

    candidates = []

    for player in available_players:
        hero_scores = []
        for hero, stats in team_mmr_data.get(player, {}).get("Storm League", {}).items():
            if hero in DRAFT_DATA["forbidden_heroes"] or hero not in DRAFT_DATA["available_heroes"] or hero in DRAFT_DATA["picked_heroes"] or hero in DRAFT_DATA["banned_heroes"]:
                continue

            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(DRAFT_DATA["hero_winrates_by_map"].get(DRAFT_DATA["map_name"], {}).get(hero, {}).get("win_rate", 50) - 50, 2)

            role_list = DRAFT_DATA["hero_roles"].get(hero, ["Unknown"])
            role = "Offlaner" if "Bruiser" in role_list else role_list[0]

            # ✅ Enforce role limits from config
            if role in role_limits and role_counts.get(role, 0) >= role_limits[role]:
                continue

            # ✅ If role enforcement is needed, filter to missing roles
            enforce_roles = remaining_picks == len(missing_roles)
            if enforce_roles and role not in missing_roles:
                continue

            matchup_advantage = round(utils.calculate_matchup_advantage(hero, DRAFT_DATA["hero_matchup_data"], set(DRAFT_DATA["team_1_picked_heroes"].values()), set(DRAFT_DATA["team_2_picked_heroes"].values())), 2)

            score = hero_mmr + (map_bonus * 10) + matchup_advantage
            hero_scores.append((score, hero, role, hero_mmr, map_bonus))

        hero_scores.sort(reverse=True, key=lambda x: x[0])

        if not hero_scores:
            continue

        best_score, best_hero, best_role, hero_mmr, map_bonus = hero_scores[0]
        second_best_score = hero_scores[1][0] if len(hero_scores) > 1 else 2000
        score_drop = best_score - second_best_score

        reason = f"Score: {best_score:.2f}, Score Drop: {score_drop:.2f}, MMR {hero_mmr:.2f}, Map Bonus {map_bonus:+.2f}%, Matchup Advantage {matchup_advantage:+.2f}, Role: {best_role}"

        candidates.append((score_drop, best_score, player, best_hero, best_role, reason))

    if not candidates:
        raise ValueError(f"❌ ERROR: No valid picks available for {team_name}. Check available heroes and players.")

    # ✅ Sort by score drop first, then total score, and return `num_suggestions`
    candidates.sort(reverse=True, key=lambda x: (x[0], x[1]))
    return candidates[:num_suggestions]


def get_top_pick_suggestions(DRAFT_DATA, team_name, num_suggestions=5):
    """Returns the top `num_suggestions` pick options by calling `select_best_pick_with_reason()`."""

    team_tags = DRAFT_DATA["available_players_team_1"] if team_name == DRAFT_DATA["team_1_name"] else DRAFT_DATA["available_players_team_2"]

    # ✅ Call `select_best_pick_with_reason()` to get ranked candidates
    candidates = select_best_pick_with_reason(team_tags, team_name, DRAFT_DATA, num_suggestions=num_suggestions)

    return candidates
