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
# TODO: Adjust guild under on ready to be applicable to all servers rather than just yours. Get personal server out of code
# TODO: Fix 5.10 showing as 5.1
# TODO: Add readme
# TODO: Add some kind of rolling average
# TODO: Make function to check if user_id is in "RockData" exists now.  TODO RETROFIT.  Return True or False
# TODO: Replace manual entries of server guild ID with .env extracted data.  You'll only have to hardcode one variable.
# TODO: Do I need os.getenv variables below since I have the MyDynamoFunctions.py file?

# Load environment variables
load_dotenv()

# Debug prints for AWS credentials
aws_access = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")


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


def update_climbing_stats(user_data, difficulty, sends):
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


def generate_stats_summary(user_data):
    # Generate a formatted summary of user's climbing statistics.
    summary = "\n📊 Your Updated Climbing Stats 📊\n"

    if not user_data.get("climbing_data"):
        return summary + "\nNo climbs recorded yet!"

    sorted_difficulties = sorted(
        user_data["climbing_data"].items(), key=lambda x: float(x[0])
    )

    for diff, sends in sorted_difficulties:
        summary += f"\n{diff}: {sends} sends"

    total_sends = sum(sends for _, sends in sorted_difficulties)
    summary += f"\n\nTotal Sends: {total_sends}"

    return summary


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1309552643089240155))
    channel = client.get_channel(1309552643089240158)
    await channel.send("Ready to remember, boss!")


@tree.command(
    name="rocktracker",
    description="Keeps a tally of climbs you've sent.",
    guild=discord.Object(id=1309552643089240155),
)
async def climb_tracker(interaction, difficulty: float, sends: int):
    user_id = str(interaction.user.id)

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
    name="savedclimbs",
    description="View your climbing log.",
    guild=discord.Object(id=1309552643089240155),
)
async def saved_climbs(interaction):
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
    name="resetdata",
    description="Get a clean slate!",
    guild=discord.Object(id=1309552643089240155),
)
async def reset_data(interaction):
    user_id = interaction.user.id

    exists = check_user_exists(user_id, table)

    if exists == True:
        table.delete_item(Key={"id": str(user_id)})
        return await interaction.response.send_message("Data destroyed! :D")
    else:
        return await interaction.response.send_message("No data to kill, master... :(")


# Start the bot
client.run(TOKEN)
