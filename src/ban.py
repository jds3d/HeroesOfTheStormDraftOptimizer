import utils
import interface


def execute_ban_phase(order, team_name, user_input_enabled, DRAFT_DATA):
    """Handles banning heroes, allowing manual input when enabled, with suggested bans and reasons."""

    if not user_input_enabled:
        score, ban, player, hero_mmr, map_bonus, synergy_score, counter_score = get_ban_suggestions(DRAFT_DATA, team_name, num_suggestions=1)[0]
        reason = f"Score: {score:.2f}, Banning {ban} forces {player} to choose another option."
    else:
        # ✅ Provide suggestions before user input with reasons
        ban_suggestions = get_ban_suggestions(DRAFT_DATA, team_name, num_suggestions=5)
        formatted_suggestions = [f"{b[1]} (Score: {b[0]:.2f}, Target: {b[2]})" for b in ban_suggestions]
        print("\nSuggested Bans:\n" + "\n".join(formatted_suggestions))

        selected_ban = interface.select_hero_interactive(
            f"Enter enemy ban {order} or pick any available hero:",
            DRAFT_DATA["available_heroes"],
            DRAFT_DATA["hero_roles"],
            DRAFT_DATA["picked_heroes"],
            DRAFT_DATA["banned_heroes"],
            formatted_suggestions
        )

        if selected_ban in DRAFT_DATA["available_heroes"]:
            ban = selected_ban
            score, reason = 0, "Manual input"
        else:
            score, ban, player, hero_mmr, map_bonus, synergy_score, counter_score = ban_suggestions[0]  # Default to best suggestion
            score2, ban2, player2, hero_mmr2, map_bonus2, synergy_score2, counter_score2 = ban_suggestions[1]  # Default to best suggestion
            reason = f"Score: {score:.2f}, Banning {ban} forces {player} to choose another option. {hero_mmr=}, {map_bonus=}, {synergy_score=}, {counter_score=}"

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
    hero_scores = []

    for hero in available_heroes:
        best_score = 0
        best_player = "Unknown"

        for player, player_data in team_2_mmr_data.items():
            if "Storm League" not in player_data or hero not in player_data["Storm League"]:
                continue  # ✅ Skip if this player never played the hero

            stats = player_data["Storm League"][hero]

            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(DRAFT_DATA["hero_winrates_by_map"].get(DRAFT_DATA["map_name"], {}).get(hero, {}).get("win_rate", 50) - 50, 2)
            synergy_score = round(utils.calculate_allied_synergy_score(hero, DRAFT_DATA["hero_matchup_data"], set(DRAFT_DATA["team_1_picked_heroes"].values()), set(DRAFT_DATA["team_2_picked_heroes"].values())), 2)
            counter_score = round(utils.calculate_enemy_countering_score(hero, DRAFT_DATA["hero_matchup_data"], set(DRAFT_DATA["team_1_picked_heroes"].values()), set(DRAFT_DATA["team_2_picked_heroes"].values())), 2)

            score = hero_mmr + (map_bonus * 50) + (synergy_score * 25) + (counter_score * 25)

            # ✅ Compute hero score
            if score > best_score:
                best_score = score
                best_player = player

        # ✅ Store top hero scores
        if best_score > 0:
            hero_scores.append((best_score, hero, best_player, hero_mmr, map_bonus, synergy_score, counter_score))

    # ✅ Sort and return the top `num_suggestions`
    hero_scores.sort(reverse=True, key=lambda x: x[0])
    ban_suggestions = hero_scores[:num_suggestions]

    return ban_suggestions
