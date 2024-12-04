"""
Changes ~~~
-moved print statement to aws connection function
-created difficulty_validation function
-removed validate_climbing_grade
-adjusted display_sort to put hardest grades at top and account for letter difficulties
-Made UI summary even and more readable with discord code block
-Updated UI rocktracker message
-Made DISCORD_GUILD global.  Specific guild ID not required
-Changed bot messages and terminal debug messages
-Prevented 0's and negative numbers from being entered in sends
-added remove_climb command that will not register and hasn't been tested.
"""

from dotenv import load_dotenv
import os
import discord
from climbing_stats import (
    difficulty_validation,
    update_climbing_stats,
    generate_stats_summary,
)
from dynamo_functions import (
    test_aws_connection,  # None / Returns TABLE Dynamo.db table
    check_user_exists,  # discord user id / boolean
    check_and_create_user,  # Discord id, Dynamo table / boolean, dictionary item (existing or new)
)

# TODO: Add readme
# TODO: Add some kind of rolling average
# TODO: Is channel necessary?
# TODO: Delete entries by adding -1 to the difficulty.  Make data validation remove entries with 0 or less.  Get command to register and test it
# TODO: Add /help documentation
# TODO: Investigate why display_sort runs once for each unique difficulty grade tracked.
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
remove_command = "remove_climb"  # name of bot command


# Load environment variables
load_dotenv()

DISCORD_CHANNEL = int(os.getenv("DISCORD_CHANNEL"))

# Try to create table connection
try:
    table = test_aws_connection()
except Exception as e:
    print(f"Failed to establish initial AWS connection: {str(e)}")

# Set up Discord bot
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    print("Executing on_ready...")
    await tree.sync()
    channel = client.get_channel(DISCORD_CHANNEL)
    await channel.send("Ready to remember, boss!")


@tree.command(
    name=tracker,
    description="Keeps a tally of climbs you've sent.\n"
    + "  Difficulties range from 5.5 - 5.17d \n"
    + "and V0 - V17.  \n",
)
async def climb_tracker(interaction, difficulty: str, sends: int):

    print("Executing " + tracker + "...")
    user_id = str(interaction.user.id)
    removing = False
    data_valid, difficulty = difficulty_validation(difficulty, sends, removing)
    if data_valid == True:
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
    else:
        message = difficulty
        await interaction.response.send_message(message)


@tree.command(
    name=history,
    description="View your climbing log.",
)
async def saved_climbs(interaction):
    print("Executing " + history + "...")
    user_id = str(interaction.user.id)

    try:
        exists, user_data = check_and_create_user(user_id, table)
        if exists:
            message = generate_stats_summary(user_data)
        else:
            message = (
                "No climbing record found! Use "
                + "`/rocktracker`"
                + " to start logging your climbs."
            )
    except Exception as e:
        print(f"Error in saved_climbs: {str(e)}")
        message = "Sorry, there was an error retrieving your climbing record."

    await interaction.response.send_message(message)


@tree.command(
    name=delete,
    description="Get a clean slate!",
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


print("Before Tree")


@tree.command(
    name=remove_command,
    description="Remove climbs from your history",
)
async def remove_climb(interaction, difficulty: str, sends: int):
    print("in funk")
    print("Executing " + remove_command + "...")
    user_id = str(interaction.user.id)
    removing = True
    data_valid, difficulty = difficulty_validation(difficulty, sends, removing)
    if data_valid == True:
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
    else:
        message = difficulty
        await interaction.response.send_message(message)


# Start the bot
client.run(TOKEN)
