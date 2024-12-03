from dotenv import load_dotenv
import os
import discord
import boto3
import json
from botocore.exceptions import ClientError, BotoCoreError
from datetime import datetime
from textwrap import dedent
from climbing_stats import (
    validate_climbing_grade,
    update_climbing_stats,
    grade_to_number,
    generate_stats_summary,
)
from dynamo_functions import (
    is_emoji_free,
    test_aws_connection,  # None / Returns "RockData" Dynamo.db table
    check_user_exists,  # discord user id / boolean
    check_and_create_user,  # Discord id, Dynamo table / boolean, dictionary item (existing or new)
)

# TODO: turn table name into a changeable variable.  Put in .env
# TODO: Adjust DynamoDB storage structure to be less disgusting
# TODO:  Be inclusive rather than exclusive for data validation
# TODO: Add readme
# TODO: Add some kind of rolling average
# TODO: Find way to make no DISCORD_GUILD necessary.  Make it a default connect to any server.
# TODO: Make function to check if user_id is in "RockData" exists now.  TODO RETROFIT.  Return True or False
""" TODO: If bad data gets into dynamo, it will prevent all bot operations except deletehistory from occuring.
It completely corrupts the data for update_climbing_stats and rocktracker command"""
# TODO: Add way to delete specific entries so if data gets corrupted last entry can be deleted.  Or if 5.1 gets added it can be removed.
# TODO: Investigate why grade_to_numbers runs once for each unique difficulty grade tracked.
# TODO: Put /rocktracker in markdown font for discord notification
# TODO: $$$$ input in difficulty broke data
# TODO: 5 in difficulty input broke code.
# TODO: Get channel by name and not ID
"""
Inputs that broke code...
Difficulty:  $$$$
Difficulty:  5
Difficulty:  a
Sends: -1 (didn't break code, but still incorrect).
Difficulty:  test 5.8v
"""

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
##############################

# Set up Discord bot
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


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

    is_valid, error_message = is_emoji_free(difficulty)
    if not is_valid:
        await interaction.response.send_message(error_message)
        return

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
        print("No user exists.")
        return await interaction.response.send_message("No data to kill, master... :(")


# Start the bot
client.run(TOKEN)
