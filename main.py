from dotenv import load_dotenv
import os  # Discord.py
import discord  # Discord.py
import boto3  # Dynamo
import json  # Dynamo
from botocore.exceptions import ClientError  # Dynamo
from datetime import datetime  # Dynamo
from discord import app_commands  # Discord.py
from textwrap import dedent  # etc

### TO DO ###
#  make DynamoDB connection.  imports should be ready
#  All data needs to be manipulated from the user data base
#  Initalize new dictionary when user is new
#  Send data and pull data for final results

load_dotenv()  # Load variables from .env file
TOKEN = os.getenv("TOKEN")  # Read a specific variable


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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
    x = difficulty
    y = sends


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
