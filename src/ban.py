import utils
import interface


def execute_ban_phase(order, team_name, user_input_enabled, DRAFT_DATA):
    """Handles banning heroes, allowing manual input when enabled, with suggested bans and reasons."""

    if not user_input_enabled or team_name == DRAFT_DATA["team_1_name"]:
        score, ban, best_player = get_ban_suggestions(DRAFT_DATA, team_name, num_suggestions=1)[0]
        reason = f"Score: {score:.2f}, Banning {ban} forces {best_player} to choose another option."
    else:
        # ✅ Provide suggestions before user input with reasons
        ban_suggestions = get_ban_suggestions(DRAFT_DATA, team_name, num_suggestions=5)
        formatted_suggestions = [f"{b[1]} (Score: {b[0]:.2f}, Target: {b[2]})" for b in ban_suggestions]
        print("\nSuggested Bans:", ", ".join(formatted_suggestions))

        selected_index = interface.select_hero_interactive(
            f"Enter enemy ban {order} (suggested: {formatted_suggestions[0]}):",
            DRAFT_DATA["available_heroes"],
            DRAFT_DATA["hero_roles"],
            DRAFT_DATA["picked_heroes"],
            DRAFT_DATA["banned_heroes"],
            [b[1] for b in ban_suggestions]
        )

        ban = ban_suggestions[selected_index][1] if selected_index is not None else ban_suggestions[0][1]
        score, reason = 0, "Manual input"

    # ✅ Move DRAFT_DATA modifications here to avoid removing multiple heroes at once
    DRAFT_DATA["banned_heroes"].add(ban)
    DRAFT_DATA["available_heroes"].remove(ban)
    DRAFT_DATA["draft_log"].append((order, "Ban", team_name, ban, score, reason))

    print(f"{order:<6} Ban   {team_name:<25} {'-':<20} {ban:<15} {score:<10.2f} {reason}")


def get_ban_suggestions(DRAFT_DATA, team_name, num_suggestions=1):
    """Returns a list of the top `num_suggestions` ban options based on impact, ranked by MMR, map bonus, and matchup advantage."""

    ban_suggestions = []

    # ✅ Ensure we are banning against the correct team
    if team_name == DRAFT_DATA["team_1_name"]:
        team_2_mmr_data = DRAFT_DATA["team_2_player_mmr_data"]
        team_2_picked_heroes = set(DRAFT_DATA["team_2_picked_heroes"].values())
    else:
        team_2_mmr_data = DRAFT_DATA["team_1_player_mmr_data"]
        team_2_picked_heroes = set(DRAFT_DATA["team_1_picked_heroes"].values())

    # ✅ Exclude already picked, banned, and forbidden heroes
    excluded_heroes = team_2_picked_heroes | DRAFT_DATA["banned_heroes"] | DRAFT_DATA["forbidden_heroes"]
    available_heroes = DRAFT_DATA["available_heroes"] - excluded_heroes

    hero_winrates_by_map = DRAFT_DATA["hero_winrates_by_map"]
    hero_matchup_data = DRAFT_DATA["hero_matchup_data"]
    map_name = DRAFT_DATA["map_name"]
    team_1_picked_heroes = set(DRAFT_DATA["team_1_picked_heroes"].values()) if team_name == DRAFT_DATA["team_1_name"] else set(DRAFT_DATA["team_2_picked_heroes"].values())

    hero_scores = []

    for hero in available_heroes:
        best_score = 0
        best_player = "Unknown"
        second_best_hero = "Unknown"
        score_drop = 0

        for player, player_data in team_2_mmr_data.items():
            if "Storm League" not in player_data or hero not in player_data["Storm League"]:
                continue  # ✅ Skip if this player never played the hero

            stats = player_data["Storm League"][hero]
            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(hero_winrates_by_map.get(map_name, {}).get(hero, {}).get("win_rate", 50) - 50, 2)
            matchup_advantage = round(utils.calculate_matchup_advantage(hero, hero_matchup_data, team_1_picked_heroes, team_2_picked_heroes), 2)

            # ✅ Compute hero score
            score = hero_mmr + (map_bonus * 10) + matchup_advantage
            if score > best_score:
                best_score = score
                best_player = player

        # ✅ Store top hero scores
        if best_score > 0:
            hero_scores.append((best_score, hero, best_player))

    # ✅ Sort and return the top `num_suggestions`
    hero_scores.sort(reverse=True, key=lambda x: x[0])
    ban_suggestions = hero_scores[:num_suggestions]

    return ban_suggestions
