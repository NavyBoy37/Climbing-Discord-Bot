from dotenv import load_dotenv
import os  # Discord.py
import discord  # Discord.py
import boto3  # Dynamo
import json  # Dynamo
from botocore.exceptions import ClientError  # Dynamo
from datetime import datetime  # Dynamo
from textwrap import dedent  # etc


# TODO: make DynamoDB connection.  imports should be ready
# TODO: All data needs to be manipulated from the user data base
# TODO: Initalize new dictionary when user is new
# TODO: Send data and pull data for final results
# TODO: Turn auto recommendations on in VSCode
# TODO: Adjust guild under on ready to be applicable to all servers rather than just yours.

# DynamoDB connection made below (to table)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("RockData")

load_dotenv()  # Load variables from .env file
TOKEN = os.getenv("TOKEN")  # Read a specific variable


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

#  Below are the Trees and async functions.  These are asynchronous functions that automatically run when / commands are run in the bot
#  That's why you don't see them called anywhere, it's built into discord.py.


#  Below tells Discord the status of the commands your bot offers and gives the go head when ready
#  Note that client.get_channel uses a chat channel ID rather than the server ID.
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1309552643089240155))
    channel = client.get_channel(1309552643089240158)
    await channel.send("Ready to remember, boss!")


#  Below creates the /rocktracker and links it to your discord ID
@tree.command(
    name="rocktracker",
    description="Keeps a tally of climbs you've sent.",
    guild=discord.Object(id=1309552643089240155),
)

#  Multi Variable input is established below.  difficulty and attempts are established variables and ready for work.
async def climb_tracker(interaction, difficulty: float, sends: int):
    user_id = interaction.user.id

    # TODO: Try to pull ID's dictionary from DyanmoDB table
    # TODO: if it isn't a key in the nested dictionary.
    # TODO: if ID is not in list, make a new ID in main Dictionary.  If it is, continue to next step.
    # TODO: Update shared dictionary with difficulty and sends values.  Use shared dictionary to update info for specific user in main dictionary.


#  Below will spit out your climbing log each time you enter a value
async def saved_climbs(interaction):
    print(interaction)
    await interaction.response.send_message(
        dedent(
            """
            5.8  -
            5.9  -
            5.10 -
            5.11 -
            5.12 -
            5.13 -
            """
        )
    )


client.run(TOKEN)
