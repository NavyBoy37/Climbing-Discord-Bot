"""
Changes:
-Updated generate_stats_summary
The above changes are to introduce climbing difficulty averages
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
# TODO: Add color configurable "Gym Mode" to better represent V grades
# TODO: Add /help documentation
# TODO: Get date of entries with discord.py and add it to dynamo


"""
Below variables change names of bot commands
and associated print statements for terminal
"""
history = "climbhistory"  # name of bot command
delete = "profileannihilation"  # name of bot command
tracker = "rocktracker"  # name of bot command
remove_command = "remove"  # name of bot command


# Try to create table connection
try:
    table = test_aws_connection()
except Exception as e:
    print(f"Failed to establish initial AWS connection: {str(e)}")

# Set up Discord bot
load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    print("Executing on_ready...")
    await tree.sync()


@tree.command(
    name=tracker,
    description="Keeps a tally of climbs you've sent.\n"
    + "  Difficulties range from 5.5 - 5.17d \n"
    + "and V0 - V17.  \n",
)
async def climb_tracker(interaction, difficulty: str, sends: int):

    print("Executing " + tracker + "...")
    user_id = str(interaction.user.id)
    removing = (
        False  # adding and removing commands share the difficulty_validation function
    )
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


@tree.command(
    name=remove_command,
    description="Remove climbs from your history.  Input number < 0 (eg. -1, -2, ...)",
)
async def remove(interaction, difficulty: str, sends: int):
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


@tree.command(name="resetcommands", description="Clear and resync all bot commands")
async def reset_commands(interaction):
    if interaction.user.guild_permissions.administrator:
        await interaction.response.defer()

        # Clear global commands
        await client.http.bulk_upsert_global_commands(client.application_id, [])

        # Clear guild commands
        await client.http.bulk_upsert_guild_commands(
            client.application_id, interaction.guild_id, []
        )

        await tree.sync()
        await interaction.followup.send("Commands cleared and resynced!")
    else:
        await interaction.response.send_message("You need administrator permissions!")


# Start the bot
client.run(TOKEN)
