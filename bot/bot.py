"""Main file where the bot runs from and loads extensions."""
from discord.ext import commands
from config import TOKEN


bot = commands.Bot(command_prefix="~", case_insensitive=True)

bot.load_extension("cogs.leagues")

bot.run(TOKEN)
