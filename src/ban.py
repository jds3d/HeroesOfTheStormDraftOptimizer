import utils
import interface


def execute_ban_phase(order, team_name, user_input_enabled, DRAFT_DATA):
    """Handles banning heroes, allowing manual input when enabled, with suggested bans and reasons."""

    if not user_input_enabled:
        score, score_drop, ban, player, hero_mmr, map_bonus, synergy_score, counter_score, reason = get_ban_suggestions(DRAFT_DATA, team_name, num_suggestions=1)[0]
        reason = f"Score: {score:.2f}, Banning {ban} forces {player} to choose another option."
    else:
        # ✅ Provide suggestions before user input with reasons
        ban_suggestions = get_ban_suggestions(DRAFT_DATA, team_name, num_suggestions=5)
        # (score, score_drop, hero, player, hero_mmr, map_bonus, synergy_score, counter_score, reason))
        formatted_suggestions = [f"{b[2]} (Reason: {b[8]})" for b in ban_suggestions]
        print("\nSuggested Bans:\n" + "\n".join(formatted_suggestions))

        selected_ban = interface.select_hero_interactive(
            f"Round {order}: Enter {team_name}'s ban.  Suggestions:",
            DRAFT_DATA["available_heroes"],
            DRAFT_DATA["hero_roles"],
            DRAFT_DATA["picked_heroes"],
            DRAFT_DATA["banned_heroes"],
            formatted_suggestions
        )
        if selected_ban in [s[2] for s in ban_suggestions]:
            score, score_drop, ban, player, hero_mmr, map_bonus, synergy_score, counter_score, reason = ban_suggestions[0]  # Default to best suggestion
        else:
            ban = selected_ban
            score, reason = 0, "Manual input"

    # ✅ Move DRAFT_DATA modifications here to avoid removing multiple heroes at once
    DRAFT_DATA["banned_heroes"].add(ban)
    DRAFT_DATA["available_heroes"].remove(ban)
    DRAFT_DATA["draft_log"].append((order, "Ban", team_name, ban, score, reason))

    print(f"{order:<6} Ban   {team_name:<25} {'-':<20} {ban:<15} {score:<10.2f} {reason}")


def get_ban_suggestions(DRAFT_DATA, team_name, num_suggestions=1):
    """Returns a list of the top `num_suggestions` ban options based on impact, ranked by MMR, map bonus, and matchup advantage."""
    # ✅ Ensure we are banning against the correct team
    if team_name == DRAFT_DATA["team_1_name"]:
        # team 1 is banning
        enemy_mmr_data = DRAFT_DATA["team_2_player_mmr_data"]
        enemy_picked_heroes = set(DRAFT_DATA["team_2_picked_heroes"].values())
        available_players = utils.get_available_players(DRAFT_DATA, DRAFT_DATA["team_2_name"])
        enemy_team_name = DRAFT_DATA["team_2_name"]

    else:
        # team 2 is banning
        enemy_mmr_data = DRAFT_DATA["team_1_player_mmr_data"]
        enemy_picked_heroes = set(DRAFT_DATA["team_1_picked_heroes"].values())
        available_players = utils.get_available_players(DRAFT_DATA, DRAFT_DATA["team_1_name"])
        enemy_team_name = DRAFT_DATA["team_1_name"]

    # ✅ Exclude already picked, banned, and forbidden heroes
    excluded_heroes = enemy_picked_heroes | DRAFT_DATA["banned_heroes"]
    available_heroes = DRAFT_DATA["available_heroes"] - excluded_heroes

    player_hero_pool_sizes = utils.get_hero_player_pool_sizes(DRAFT_DATA, enemy_team_name)

    # ✅ Determine max pool size to scale the boost
    max_pool_size = max(player_hero_pool_sizes.values(), default=1)
    candidates = []
    for player, player_data in enemy_mmr_data.items():
        if player not in available_players:
            # don't ban heroes for players that picked already.
            continue

        hero_scores = []
        for hero in available_heroes:
            if "Storm League" not in player_data or hero not in player_data["Storm League"]:
                continue  # ✅ Skip if this player never played the hero

            stats = player_data["Storm League"][hero]

            hero_mmr = round(stats.get("mmr", 2000), 2)
            map_bonus = round(DRAFT_DATA["hero_winrates_by_map"].get(DRAFT_DATA["map_name"], {}).get(hero, {}).get("win_rate", 50) - 50, 2)
            synergy_score = round(utils.calculate_allied_synergy_score(DRAFT_DATA, hero, team_name), 2)
            counter_score = round(utils.calculate_enemy_countering_score(DRAFT_DATA, hero, team_name), 2)

            score = hero_mmr + (map_bonus * 50) + (synergy_score * 25) + (counter_score * 25)

        # ✅ Store top hero scores
            hero_scores.append((score, hero, player, hero_mmr, map_bonus, synergy_score, counter_score))

        hero_scores.sort(reverse=True, key=lambda x: x[0])

        # ✅ Apply a **boost** to players with smaller hero pools
        hero_pool_size = player_hero_pool_sizes.get(player, 0)
        score, hero, player, hero_mmr, map_bonus, synergy_score, counter_score = hero_scores[0]

        second_best_score = hero_scores[1][0] if len(hero_scores) > 1 else 2000
        pool_boost = (1 - (hero_pool_size / max_pool_size)) * 200  # pool boost ranges up to the multiplicative factor (comparable to mmr drop).
        score_drop = score - second_best_score + pool_boost

        reason = f"Score: {score:.2f}, Score Drop: {score_drop:.2f}, MMR {hero_mmr:.2f}, Map Bonus {map_bonus:+.2f}%, Synergy {synergy_score:+.2f}, Counter {counter_score:+.2f}, Pool Boost: {pool_boost:.2f}, Next option for {player}: {hero_scores[1][1]}"
        candidates.append((score, score_drop, hero, player, hero_mmr, map_bonus, synergy_score, counter_score, reason))

    # ✅ Sort and return the top `num_suggestions`

    ban_suggestions = candidates[:num_suggestions]

    return ban_suggestions
