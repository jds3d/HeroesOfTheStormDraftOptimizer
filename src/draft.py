import utils  # ✅ Import utils as a package
import load_data
import interface
import ban
import pick

DRAFT_ORDER = [
    ("Ban", 1), ("Ban", 2), ("Ban", 3), ("Ban", 4),
    ("Pick", 5), ("Pick", 6), ("Pick", 7), ("Pick", 8), ("Pick", 9),
    ("Ban", 10), ("Ban", 11),
    ("Pick", 12), ("Pick", 13), ("Pick", 14), ("Pick", 15), ("Pick", 16)
]

FIRST_PICK_SLOTS = {1, 3, 5, 8, 9, 11, 14, 15}


def execute_draft_phase(draft_data, user_input_enabled=True):
    """Executes the draft process, allowing optional manual input for both teams while displaying suggestions."""

    if user_input_enabled:
        interface.print_available_heroes(draft_data["available_heroes"], draft_data["hero_roles"], draft_data["picked_heroes"], draft_data["banned_heroes"])

    print("\n🔹 STARTING DRAFT 🔹\n" + "=" * 120 + f"\n{'Order':<6} {'Type':<6} {'Team':<25} {'Player':<20} {'Hero':<15} {'Score':<10} {'Reason'}\n" + "=" * 120)

    for draft_type, order in DRAFT_ORDER:
        team_name = draft_data["team_1_name"] if (order in FIRST_PICK_SLOTS) == (first_pick_team == 1) else draft_data["team_2_name"]

        if draft_type == "Ban":
            ban.execute_ban_phase(order, team_name, user_input_enabled, draft_data)
        elif draft_type == "Pick":
            pick.execute_pick_phase(order, team_name, user_input_enabled, draft_data)


def draft(timeframe_type="major", timeframe="2.47"):
    """Runs the draft process, allowing full automation or manual enemy input."""

    while True:
        mode = input("Choose draft mode: (1) Full Mock Draft, (2) Live Draft with Manual Input: ").strip()
        if mode in {"1", "2"}:
            user_input_enabled = (mode == "2")
            break
        print("❌ Invalid input. Enter 1 or 2.")

    draft_data = load_data.load_and_initialize_draft(timeframe_type, timeframe)
    execute_draft_phase(draft_data, user_input_enabled)

    utils.print_final_draft(draft_data, user_input_enabled)

    utils.save_to_pickle(draft_data["draft_log"], f"draft_{map_name}.pkl")
    return draft_data["draft_log"]


if __name__ == "__main__":

    # ✅ Load team configuration
    import team_config
    team_1_name = team_config.team_1_name
    team_1_tags = team_config.team_1_tags
    team_2_name = team_config.team_2_name
    team_2_tags = team_config.team_2_tags
    map_name = team_config.map_name

    # ✅ Prompt for first pick team
    while True:
        first_pick_team = input(f"Which team has first pick? (1 = {team_1_name}, 2 = {team_2_name}): ").strip()
        if first_pick_team in {"1", "2"}:
            first_pick_team = int(first_pick_team)
            break
        print("Invalid input. Please enter 1 or 2.")

    # ✅ Run the draft
    # draft_log = draft(timeframe_type="major", timeframe="2.55")
    draft_log = draft(timeframe_type="minor", timeframe="2.55.9.93640")
