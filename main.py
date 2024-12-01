from dotenv import load_dotenv
import os
import discord
import boto3
import json
from botocore.exceptions import ClientError, BotoCoreError
from datetime import datetime
from textwrap import dedent

from MyDynamoFunctions import (
    test_aws_connection,  # None / Returns "RockData" Dynamo.db table
    check_user_exists,  # discord user id / boolean
    check_and_create_user,  # Discord id, Dynamo table / boolean, dictionary item (existing or new)
)

# TODO: Adjust DynamoDB storage structure to be less disgusting
# TODO: Add readme
# TODO: Add some kind of rolling average
# TODO: Make function to check if user_id is in "RockData" exists now.  TODO RETROFIT.  Return True or False
""" TODO: If bad data gets into dynamo, it will prevent all bot operations except deletehistory from occuring.
It completely corrupts the data for update_climbing_stats and rocktracker command"""
# TODO: Add way to delete specific entries so if data gets corrupted last entry can be deleted.  Or if 5.1 gets added it can be removed.

"""
Below variables change names of bot commands
and associated print statements for terminal
"""
history = "climbhistory"  # name of bot command
delete = "profileannihilation"  # name of bot command
tracker = "rocktracker"  # name of bot command


# Load environment variables
load_dotenv()
DISCORD_GUILD = int(os.getenv("DISCORD_GUILD"))
DISCORD_CHANNEL = int(os.getenv("DISCORD_CHANNEL"))

# Try to create table connection
try:
    print("\nAttempting to establish AWS connection...")
    table = test_aws_connection()
except Exception as e:
    print(f"Failed to establish initial AWS connection: {str(e)}")


# Set up Discord bot
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


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
    print("... validating data w/ grade_to_numbers")
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

    for diff, sends in sorted_difficulties:
        # Ensure we're using the original string format
        grade_display = diff  # This preserves the original "5.10" format
        summary += f"\n{grade_display}: {sends} sends"

    total_sends = sum(sends for _, sends in sorted_difficulties)
    summary += f"\n\nTotal Sends: {total_sends}"

    return summary


@client.event
async def on_ready():
    print("Executing on_ready...")
    await tree.sync(guild=discord.Object(id=DISCORD_GUILD))
    channel = client.get_channel(DISCORD_CHANNEL)
    await channel.send("Ready to remember, boss!")


@tree.command(
    name=tracker,
    description="Keeps a tally of climbs you've sent.",
    guild=discord.Object(id=DISCORD_GUILD),
)
async def climb_tracker(interaction, difficulty: str, sends: int):
    print("Executing " + tracker + "...")
    user_id = str(interaction.user.id)

    # Validate and standardize the climbing grade first
    difficulty = difficulty.strip().lower()

    # Quick check for invalid letter grades
    if any(
        letter in difficulty
        for letter in "efghijklmnopqrstuvwxyz"
        if letter not in "abcdv"
    ):
        await interaction.response.send_message(
            "Invalid grade format: Only grades a, b, c, d, or v are allowed"
        )
        return

    # Try to convert/validate the grade

    try:
        exists, user_data = check_and_create_user(user_id, table)

        if exists:
            message = "Found your record! Processing your send...\n"
        else:
            message = "Created new climbing record for you!\n"

        # Update and save the user's climbing data
        updated_data = update_climbing_stats(user_data, difficulty, sends)
        table.put_item(Item=updated_data)

        # Generate and append statistics summary
        message += generate_stats_summary(updated_data)

    except Exception as e:
        print(f"Error in climb_tracker: {str(e)}")
        message = "Sorry, there was an error processing your climbing record."

    await interaction.response.send_message(message)


@tree.command(
    name=history,
    description="View your climbing log.",
    guild=discord.Object(id=DISCORD_GUILD),
)
async def saved_climbs(interaction):
    print("Executing " + history + "...")
    user_id = str(interaction.user.id)

    try:
        exists, user_data = check_and_create_user(user_id, table)
        if exists:
            message = generate_stats_summary(user_data)
        else:
            message = "No climbing record found! Use /rocktracker to start logging your climbs."
    except Exception as e:
        print(f"Error in saved_climbs: {str(e)}")
        message = "Sorry, there was an error retrieving your climbing record."

    await interaction.response.send_message(message)


@tree.command(
    name=delete,
    description="Get a clean slate!",
    guild=discord.Object(id=DISCORD_GUILD),
)
async def reset_data(interaction):
    print("Executing " + delete + "...")
    user_id = interaction.user.id

    exists = check_user_exists(user_id, table)

    if exists == True:
        table.delete_item(Key={"id": str(user_id)})
        print("User exists.  Deleting profile")
        return await interaction.response.send_message("Data destroyed! :D")
    else:
        print("No user exists.  Creating profile")
        return await interaction.response.send_message("No data to kill, master... :(")


# Start the bot
client.run(TOKEN)
