from dotenv import load_dotenv
import os
import discord
from discord import app_commands

load_dotenv()  # Load variables from .env file
TOKEN = os.getenv("TOKEN")  # Read a specific variable


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1309552643089240155))


@tree.command(
    name="rocktracker",
    description="Keeps a tally of climbs you've sent.",
    guild=discord.Object(id=1309552643089240155),
)
async def first_command(interaction):
    print(interaction)
    await interaction.response.send_message(
        "Input difficulty grading e.g. 5.10, 5.11, 5.12"
    )


client.run(TOKEN)
