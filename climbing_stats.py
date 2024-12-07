from datetime import datetime


x = 0


def difficulty_validation(
    difficulty: str, sends: int, removing: bool
) -> tuple[bool, str]:
    print("... validating data w/ difficulty_validation")
    VALID_GRADES = [
        # Sport/Trad grades without letters
        "5.5",
        "5.6",
        "5.7",
        "5.8",
        "5.9",
        "5.10",
        "5.11",
        "5.12",
        "5.13",
        "5.14",
        "5.15",
        "5.16",
        "5.17",
        # Sport/Trad grades with letters
        "5.5a",
        "5.5b",
        "5.5c",
        "5.5d",
        "5.6a",
        "5.6b",
        "5.6c",
        "5.6d",
        "5.7a",
        "5.7b",
        "5.7c",
        "5.7d",
        "5.8a",
        "5.8b",
        "5.8c",
        "5.8d",
        "5.9a",
        "5.9b",
        "5.9c",
        "5.9d",
        "5.10a",
        "5.10b",
        "5.10c",
        "5.10d",
        "5.11a",
        "5.11b",
        "5.11c",
        "5.11d",
        "5.12a",
        "5.12b",
        "5.12c",
        "5.12d",
        "5.13a",
        "5.13b",
        "5.13c",
        "5.13d",
        "5.14a",
        "5.14b",
        "5.14c",
        "5.14d",
        "5.15a",
        "5.15b",
        "5.15c",
        "5.15d",
        "5.16a",
        "5.16b",
        "5.16c",
        "5.16d",
        "5.17a",
        "5.17b",
        "5.17c",
        "5.17d",
        # Boulder grades
        "V0",
        "V1",
        "V2",
        "V3",
        "V4",
        "V5",
        "V6",
        "V7",
        "V8",
        "V9",
        "V10",
        "V11",
        "V12",
        "V13",
        "V14",
        "V15",
        "V16",
        "V17",
    ]

    if removing == False:
        if difficulty in VALID_GRADES:
            if sends > 0:
                return True, difficulty
            else:
                return False, "Bad input, try a number > 0"
        else:
            return False, "Bad input, try 5.5, 5.5a, 5.5b ... or V1, V2, V3 ... etc"
    if removing == True:
        if difficulty in VALID_GRADES:
            if sends <= 0:
                return True, difficulty
            else:
                return False, "Bad input, use a number less than 0"
        else:
            return False, "Bad input, try 5.5, 5.5a, 5.5b ... or V1, V2, V3 ... etc"


def update_climbing_stats(user_data, difficulty, sends):
    print("... updating climber stats w/ update_climbing_stats")
    if "climbing_data" not in user_data:
        user_data["climbing_data"] = {}

    diff_key = str(difficulty)
    if diff_key in user_data["climbing_data"]:
        new_total = user_data["climbing_data"][diff_key] + sends  # <- Add this line
        if new_total <= 0:  # <- Add this line
            del user_data["climbing_data"][diff_key]  # <- Add this line
            return user_data  # <- Add this line
        user_data["climbing_data"][diff_key] = new_total  # <- Add this line
    else:
        if sends <= 0:  # <- Add this line
            return user_data  # <- Add this line
        user_data["climbing_data"][diff_key] = sends

    user_data["last_updated"] = str(datetime.now())
    return user_data


"""
display_sort converts difficulty grade to numbers so they can be sorted cleanly
in the display.  5.xx grades come before V grades
"""


def display_sort(grade):
    print("... sorting data points w/ display_sort")
    grade = grade.strip().lower()

    if grade.startswith("v"):
        try:
            v_number = grade[1:].strip()
            return float(v_number) + 500
        except ValueError:
            raise ValueError(f"Invalid V-grade format: {grade}")

    if "." not in grade and grade.startswith("5"):
        grade = f"{grade[0]}.{grade[1:]}"

    # Handle letter grades
    letter_value = 0
    if grade.endswith("d"):
        letter_value = 0.4
    elif grade.endswith("c"):
        letter_value = 0.3
    elif grade.endswith("b"):
        letter_value = 0.2
    elif grade.endswith("a"):
        letter_value = 0.1

    base = grade.split("a")[0].split("b")[0].split("c")[0].split("d")[0]
    major, minor = base.split(".")
    return -1 * (
        float(major) * 100 + float(minor) + letter_value
    )  # Negative for reverse sort


def generate_stats_summary(user_data):
    summary = "\n📊 Your Updated Climbing Stats 📊\n```"
    if not user_data.get("climbing_data"):
        return summary + "\nNo climbs recorded yet!```"

    sorted_difficulties = sorted(
        user_data["climbing_data"].items(), key=lambda x: display_sort(x[0])
    )

    for _, (diff, sends) in enumerate(sorted_difficulties):
        summary += f"\n{diff:<6} {sends:>3} sends"

    total_sends = sum(sends for _, sends in sorted_difficulties)
    summary += f"\n\nTotal Sends: {total_sends}```"
    return summary
