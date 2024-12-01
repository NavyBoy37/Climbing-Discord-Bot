from datetime import datetime
from MyDynamoFunctions import (
    test_aws_connection,  # None / Returns "RockData" Dynamo.db table
    check_user_exists,  # discord user id / boolean
    check_and_create_user,  # Discord id, Dynamo table / boolean, dictionary item (existing or new)
)

x = 0


def validate_climbing_grade(grade: str) -> tuple[bool, str]:
    print("...validating data w/ validate_climbing_grade")
    """
    Validates if a climbing grade is in the correct format.
    Returns (is_valid, error_message).
    """
    # Check for empty or pure whitespace input
    if not grade or not grade.strip():
        return False, "Grade cannot be empty"

    # Strip whitespace and convert to lowercase for consistency
    grade = grade.strip().lower()

    # Check for any internal whitespace
    if " " in grade:
        return False, "Grade cannot contain spaces"

    # Check for multiple decimal points
    if grade.count(".") > 1:
        return False, "Grade cannot have multiple decimal points"

    # Handle V grades (bouldering)
    if grade.startswith("v"):
        try:
            v_grade = int(grade[1:])
            if 0 <= v_grade <= 17:  # Typical range for V grades
                return True, ""
            return False, "V grade must be between V0 and V17"
        except ValueError:
            return (
                False,
                "Invalid V grade format. Must be V followed by a number (e.g., V5)",
            )

    # Handle 5.xx grades (sport/trad climbing)
    try:
        # Convert "510a" format to "5.10a" format
        if grade.startswith("5") and "." not in grade:
            grade = f"{grade[0]}.{grade[1:]}"

        if not grade.startswith("5."):
            return False, "Grade must start with '5.' or be a V grade"

        # Split grade into numeric and letter parts
        base_grade = grade[2:].rstrip("abcd")
        letter_grade = grade[2 + len(base_grade) :]

        # Validate numeric part contains only digits
        if not base_grade.isdigit() and not base_grade.replace(".", "").isdigit():
            return (
                False,
                "Invalid grade format - must contain only numbers and optional a/b/c/d",
            )

        # Validate numeric part
        grade_num = float(base_grade)
        if not (5 <= grade_num <= 15):  # Typical range for sport/trad
            return False, "Grade must be between 5.5 and 5.15"

        # Validate letter grade
        if letter_grade and letter_grade not in ["a", "b", "c", "d"]:
            return False, "Letter grade must be a, b, c, or d"

        return True, ""

    except ValueError:
        return False, "Invalid grade format"


def update_climbing_stats(user_data, difficulty, sends):
    print("... updating climber stats w/ update_climbing_stats")
    """Update user's climbing statistics with new send data."""
    if "climbing_data" not in user_data:
        user_data["climbing_data"] = {}

    diff_key = str(difficulty)
    if diff_key in user_data["climbing_data"]:
        user_data["climbing_data"][diff_key] += sends
    else:
        user_data["climbing_data"][diff_key] = sends

    user_data["last_updated"] = str(datetime.now())
    return user_data


def grade_to_number(grade):
    # print("... validating data w/ grade_to_numbers")
    # Normalize input
    grade = grade.strip().lower()

    # Handle V grades
    if grade.startswith("v"):
        try:
            # Just take the number part after 'v'
            v_number = grade[1:].strip()
            return (
                float(v_number) + 500
            )  # Adding 500 to sort V grades after 5.xx grades
        except ValueError:
            raise ValueError(f"Invalid V-grade format: {grade}")

    # Handle 5.xx grades
    if "." not in grade and grade.startswith("5"):
        # Convert "510" to "5.10"
        grade = f"{grade[0]}.{grade[1:]}"

    base = grade.split("a")[0].split("b")[0].split("c")[0].split("d")[0]
    major, minor = base.split(".")
    return float(major) * 100 + float(minor)


def generate_stats_summary(user_data):
    print("... generating stats summary w/ generate_stats_summary")
    # Generate a formatted summary of user's climbing statistics.
    summary = "\n📊 Your Updated Climbing Stats 📊\n"

    if not user_data.get("climbing_data"):
        return summary + "\nNo climbs recorded yet!"

    sorted_difficulties = sorted(
        user_data["climbing_data"].items(), key=lambda x: grade_to_number(x[0])
    )

    for i, (diff, sends) in enumerate(sorted_difficulties):
        # Ensure we're using the original string format
        grade_display = diff  # This preserves the original "5.10" format
        summary += f"\n{grade_display}: {sends} sends"

        if i == len(sorted_difficulties) - 1:  # Check if this is the last iteration
            print("... validating data w/ grade_to_numbers x" + str(i + 1))

    total_sends = sum(sends for _, sends in sorted_difficulties)
    summary += f"\n\nTotal Sends: {total_sends}"

    return summary
