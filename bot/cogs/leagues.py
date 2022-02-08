import asyncio

from discord import Color, Embed, Member
from discord.ext.commands.converter import MemberConverter
from discord.ext import commands
import discord.ui

from pymongo.errors import CollectionInvalid

from config import client
from utils.timezones import get_timezone


class LeagueCog(commands.Cog):
    """Controls the creation of 'leagues'."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = client

    @commands.group()
    async def league(self, ctx: commands.Context) -> None:
        """No-op for allowing subcommands."""
        return

    @league.command(aliases=("information",))
    async def info(self, ctx: commands.Context, *, name: str) -> None:
        """
        Get information about a league via its name.
        Parameters:
            - name: The name of the league.
        """
        server_db = self.db[str(ctx.guild.id)]

        try:
            server_db[name]
        except CollectionInvalid:
            raise commands.BadArgument(f"Invalid league name: {name}")

        league_dict = server_db[name].find_one()

        league_embed = Embed(title=name, description="Information about the following league.", color=Color.green())

        league_embed.add_field(
            name="Owner",
            value=(await self.bot.fetch_user(league_dict["owner"])).mention,
            inline=False
        )

        league_embed.add_field(
            name="Members",
            value="\n".join((await self.bot.fetch_user(user)).mention for user in league_dict["leaderboard"].keys()),
            inline=False
        )

        await ctx.send(embed=league_embed)

    @league.command(aliases=("make",))
    async def create(self, ctx: commands.Context, *, name: str) -> None:
        """
        Creates a league.

        Parameters:
            - name: The name of the league.
        """
        server_db = self.db[str(ctx.guild.id)]
        league_col = server_db[name]
        league_dict = {
            "name": name, "owner": ctx.author.id, "leaderboard": {ctx.author.id: 0}, "jobs": {}, "latest": []
        }
        league_col.insert_one(league_dict)

        success_embed = Embed(
            title="League created",
            description=f"Your league, {name}, has been created!",
            color=Color.green()
        )
        await ctx.send(embed=success_embed)

    @league.command(aliases=("add",))
    async def invite(self, ctx: commands.Context, name: str, *, members: str) -> None:
        """
        Invites member(s) to a league.

        Parameters:
            - name: The name of the league (should be enclosed in double quotes, like "League name")
            - members: The members to add (should be separated by a space each, like @test @hi)
        """
        converter = MemberConverter()
        members = [await converter.convert(ctx, member) for member in members.split()]

        server_db = self.db[str(ctx.guild.id)]

        try:
            server_db[name]
        except CollectionInvalid:
            raise commands.BadArgument(f"Invalid league name: {name}")

        for member in members:
            user_col = server_db[str(member.id)]
            if not user_col.find_one():
                user_col.insert_one({"user": member.id, "invitations": []})

            user_dict = user_col.find_one()
            user_dict["invitations"].append(name)
            user_col.replace_one(user_col.find_one(), user_dict)

        newline_members = "\n".join(member.mention for member in members)
        success_embed = Embed(
            title="Invitations have been sent!",
            description=f"Invitations to the league {name!r} were sent to:\n"
                        f"{newline_members}",
            color=Color.green()
        )

        await ctx.send(embed=success_embed)

    @league.command(aliases=("rem",))
    async def remove(self, ctx: commands.Context, member: Member, *, name: str) -> None:
        server_db = self.db[str(ctx.guild.id)]

        try:
            server_db[name]
        except CollectionInvalid:
            raise commands.BadArgument(f"Invalid league name: {name}")

        league_col = server_db[name]
        league_dict = league_col.find_one()
        user_col = server_db[str(member.id)]

        if ctx.author.id != league_dict["owner"]:
            not_owner_embed = Embed(
                title="Are you trying to break me?",
                description=f"You aren't the owner of the league {name}!",
                color=Color.red()
            )
            await ctx.send(embed=not_owner_embed)
            return

        user_dict = user_col.find_one()

        if not user_dict:
            raise commands.BadArgument(f"{member.mention} is not setup for WxLeague yet.")

        if name not in user_dict["leagues"]:
            raise commands.BadArgument(f"{member.mention} is not in the league `{name}`!")

        del league_dict["leaderboard"][member.id]
        del user_dict["leagues"][user_dict["leagues"].index(name)]

        user_col.replace_one(user_col.find_one(), user_dict)
        league_col.replace_one(league_col.find_one(), league_dict)

        success_embed = Embed(
            title="Success!",
            description=f"{member.mention} was removed from the league {name}!",
            color=Color.green()
        )

        await ctx.send(embed=success_embed)


def setup(bot: commands.Bot):
    """Load the LeagueCog."""
    bot.add_cog(LeagueCog(bot))

