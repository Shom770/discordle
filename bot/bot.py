"""Main file where the bot runs from and loads extensions."""
from disnake.ext import commands
from config import TOKEN


bot = commands.Bot(command_prefix="~", case_insensitive=True)

bot.run(TOKEN)
