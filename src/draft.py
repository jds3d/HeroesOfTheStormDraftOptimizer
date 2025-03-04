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


def draft(team_1_tags, team_2_tags, team_1_name, team_2_name, first_pick_team, map_name,
          timeframe_type="major", timeframe="2.47"):
    """Runs the draft process, allowing full automation or manual enemy input."""

    while True:
        mode = input("Choose draft mode: (1) Full Mock Draft, (2) Live Draft with Manual Input: ").strip()
        if mode in {"1", "2"}:
            user_input_enabled = (mode == "2")
            break
        print("❌ Invalid input. Enter 1 or 2.")

    draft_data = load_data.load_and_initialize_draft(team_1_tags, team_2_tags, team_1_name, team_2_name, first_pick_team, map_name, timeframe_type, timeframe)
    execute_draft_phase(draft_data, user_input_enabled)

    utils.print_final_draft(draft_data, user_input_enabled)

    utils.save_to_pickle(draft_data["draft_log"], f"draft_{map_name}.pkl")
    return draft_data["draft_log"]


if __name__ == "__main__":
    # Our team - Came From Behind
    our_team_name = "Came From Behind"
    our_team_tags = ["HuckIt#1840", "topgun707#1875", "beachyman#1138", "mrhustler#1686", "mojoe#11242"]
    # our_team_tags = ["HuckIt#1840", "topgun707#1875", "papichulo#12352", "mrhustler#1686", "mojoe#11242"]

    # Enemy team - Fancy Flightless Fowl
    enemy_team_name = "Fancy Flightless Fowl"
    # enemy_team_tags = ["Alfie#1948", "Silverbell#11333", "AngryPanda#12178", "GingiBoi#1791", "XxLuNaTiCxX#11820"]
    enemy_team_tags = ["Alfie#1948", "Batmang#11255", "Silverbell#11333", "GingiBoi#1791", "Stefwithanf#1470"]  # Valkrye#11330
    # enemy_team_tags = ["Yarrface#1948", "Batmang#11255", "AngryPanda#12178", "GingiBoi#1791", "Stefwithanf#1470"]  # Valkrye#11330

    # Map selection
    # map_name = "Garden of Terror"
    # map_name = "Sky Temple"
    # map_name = "Battlefield of Eternity"
    map_name = "Braxis Holdout"
    # map_name = "Volskaya Temple"
    # map_name = "Alterac Pass"

    # Default first_pick_team to 1 for now (1 = Came From Behind, 2 = Fancy Flightless Fowl)
    # first_pick_team = 1
    # Uncomment below for interactive selection:
    while True:
        first_pick_team = input("Which team has first pick? (1 = Came From Behind, 2 = Fancy Flightless Fowl): ").strip()
        if first_pick_team in {"1", "2"}:
            first_pick_team = int(first_pick_team)
            break
        print("Invalid input. Please enter 1 or 2.")

    # Run the draft
    draft_log = draft(our_team_tags, enemy_team_tags, our_team_name, enemy_team_name, first_pick_team, map_name, timeframe="2.55")
