import time
import re
import unicodedata

STRIKETHROUGH = "~"  # ✅ Strikethrough formatting without ANSI (Windows-compatible)
RESET = ""  # ✅ No reset needed
BOLD = ""  # ✅ No bold needed


def normalize_hero_name(name):
    """Normalize hero names by removing diacritics, punctuation, and spaces."""
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^\w\s]", "", name)
    return name.lower().replace(" ", "")


def get_formatted_hero_list(available_heroes, hero_roles, picked_heroes, banned_heroes):
    """Generates a formatted list of heroes grouped by role, with strikethrough for picked/banned heroes."""

    role_prefixes = {
        "Tank": "T", "Healer": "H", "Offlaner": "O",
        "Ranged Assassin": "R", "Melee Assassin": "M", "Other": "X"
    }
    role_categories = {key: [] for key in role_prefixes}
    hero_index_map = {}

    for hero in sorted(available_heroes | picked_heroes | banned_heroes):
        roles = hero_roles.get(hero, ["Other"])
        if isinstance(roles, str):
            roles = [roles]

        role_found = False
        for role in roles:
            if role == "Bruiser":
                role_categories["Offlaner"].append(hero)
                role_found = True
            elif role in role_categories:
                role_categories[role].append(hero)
                role_found = True

        if not role_found:
            role_categories["Other"].append(hero)

    hero_display_list = {role: [] for role in role_prefixes}

    for role, heroes in role_categories.items():
        prefix = role_prefixes[role]
        for idx, hero in enumerate(heroes, start=1):
            hero_code = f"{prefix}{idx}"
            hero_index_map[hero_code.lower()] = hero
            display_name = hero

            # ✅ Strikethrough formatting for picked/banned heroes (using ~)
            if hero in picked_heroes or hero in banned_heroes:
                display_name = f"{STRIKETHROUGH}{display_name}{STRIKETHROUGH}"

            hero_display_list[role].append(f"{hero_code}: {display_name}")

    return hero_display_list, hero_index_map


def select_hero_interactive(prompt, available_heroes, hero_roles, picked_heroes, banned_heroes, suggestions):
    """Prompts the user for hero selection with the top 5 suggestions. Pressing Enter defaults to the top suggestion."""

    _, hero_index_map = get_formatted_hero_list(available_heroes, hero_roles, picked_heroes, banned_heroes)

    # ✅ Show top 5 suggestions inline
    suggestion_text = ", ".join(suggestions[:5]) if suggestions else "No suggestions available"

    print(f"\n{prompt}")

    while True:
        choice = input("➤ Select hero (or press Enter for default): ").strip()

        # ✅ Default to top suggested pick if Enter is pressed
        if choice == "" and suggestions:
            return suggestions[0].split(" ")[0]

        # ✅ Match by hero code (e.g., T1, H2)
        if choice.lower() in hero_index_map:
            return hero_index_map[choice.lower()]

        # ✅ Match by exact name (case insensitive, ignores punctuation/diacritics)
        normalized_choice = normalize_hero_name(choice)
        normalized_hero_map = {normalize_hero_name(h): h for h in available_heroes}

        if normalized_choice in normalized_hero_map:
            return normalized_hero_map[normalized_choice]

        print("\n❌ Invalid choice. Please select a valid code, hero name, or press Enter for the default.")


def select_player_interactive(prompt, available_players):
    """Prompts the user to select a player from the available team members."""

    print(f"\n{prompt}")
    player_options = {str(i + 1): player for i, player in enumerate(available_players)}

    for num, player in player_options.items():
        print(f"{num}: {player}")

    while True:
        choice = input("Enter the number corresponding to the player: ").strip()

        if choice in player_options:
            return player_options[choice]

        print("❌ Invalid input. Please enter a valid number from the list.")


def print_hero_list(hero_display_list):
    """Print heroes in organized columns by role."""

    role_order = ["Tank", "Healer", "Offlaner", "Ranged Assassin", "Melee Assassin", "Other"]
    column_width = 25  # Adjust width to align columns properly

    # ✅ Print headers
    header = "".join(f"{role:<{column_width}}" for role in role_order)
    print(header)
    print("=" * len(header))

    # ✅ Print rows by taking the longest list as the max number of rows
    max_rows = max(len(hero_display_list[role]) for role in role_order)

    for i in range(max_rows):
        row = []
        for role in role_order:
            row.append(hero_display_list[role][i] if i < len(hero_display_list[role]) else "")
        print("".join(f"{col:<{column_width}}" for col in row))


def print_available_heroes(available_heroes, hero_roles, picked_heroes, banned_heroes):
    """Prints the available hero list once at the start of the draft."""
    print("\n" + "=" * 120 + "\n🔹 AVAILABLE HEROES 🔹\n" + "=" * 120)
    hero_display_list, _ = get_formatted_hero_list(available_heroes, hero_roles, picked_heroes, banned_heroes)
    print_hero_list(hero_display_list)
