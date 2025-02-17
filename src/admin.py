# Built-in
import asyncio
# 3rd-party
import discord
from discord.ext import commands
# Local
import constants
import gamedata
from localization import LOCALIZATION_DATA

loc = LOCALIZATION_DATA["commands"]["admin"]
GROUP_CHAT = LOCALIZATION_DATA["channels"]["texts"]["group-chat"]


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Commands for server admins only"""

        return ctx.author.guild_permissions.administrator

    @commands.command(
        name=loc["show_all"]["name"],
        aliases=loc["show_all"]["aliases"],
        description=loc["show_all"]["description"]
    )
    async def show_all(self, ctx):
        """Reveal all channels and disable sending messages"""

        for channel in ctx.guild.text_channels:
            asyncio.create_task(channel.edit(sync_permissions=True))
        await ctx.send("All channels revealed!")

    @commands.command(
        name=loc["wipe"]["name"],
        aliases=loc["wipe"]["aliases"],
        description=loc["wipe"]["description"]
    )
    async def wipe(self, ctx, *text_channels: discord.TextChannel):
        """Erases all messages and clears game data"""

        # Confirm command to user
        await ctx.send(loc["wipe"]["DeletingMessages"])

        # Wipe messages
        if not text_channels:
            text_channels = ctx.guild.text_channels
        for text_channel in text_channels:
            asyncio.create_task(text_channel.purge(limit=None))

        # Reset game data
        ctx.game.__init__(ctx.game.guild)

        # Console logging
        print(f'{constants.INFO_PREFIX}Wiped messages from server: "{ctx.guild.name}" (ID: {ctx.guild.id})')

    @commands.command(
        name=loc["reset_perms"]["name"],
        aliases=loc["reset_perms"]["aliases"],
        description=loc["reset_perms"]["description"]
    )
    async def reset_perms(self, ctx):
        """Resets channel permissions to the default (undoes !show_all)"""

        everyone = ctx.guild.default_role
        spectator = ctx.game.spectator_role

        for channel in ctx.guild.text_channels:
            # Clues channels
            if channel.name in LOCALIZATION_DATA["channels"]["clues"].values():
                asyncio.create_task(channel.set_permissions(
                    everyone,
                    view_channel=False,
                    send_messages=False
                ))
                asyncio.create_task(channel.set_permissions(spectator, view_channel=True))

                player = channel.name.split("-")[0].title()
                for role in ctx.guild.roles:
                    if role.name == player:
                        asyncio.create_task(channel.set_permissions(role, view_channel=True))

            # Channels that all players can send messages
            elif channel.name in [GROUP_CHAT, LOCALIZATION_DATA["channels"]["voicemails"]]:
                asyncio.create_task(channel.set_permissions(everyone, send_messages=False))
                for role in ctx.guild.roles:
                    if role.name.lower() in gamedata.CHARACTERS:
                        asyncio.create_task(channel.set_permissions(role, send_messages=True))

            # Private message channels
            elif channel.name in LOCALIZATION_DATA["channels"]["texts"].values() and channel.name != GROUP_CHAT:
                asyncio.create_task(channel.set_permissions(everyone, view_channel=False, send_messages=None))
                asyncio.create_task(channel.set_permissions(spectator, view_channel=True, send_messages=False))
                split_name = channel.name.split("-")
                player_a = split_name[0].title()
                player_b = split_name[1].title()
                for role in ctx.guild.roles:
                    if role.name in [player_a, player_b]:
                        asyncio.create_task(channel.set_permissions(role, view_channel=True))

    @commands.command(
        name=loc["reset_roles"]["name"],
        aliases=loc["reset_roles"]["aliases"],
        description=loc["reset_roles"]["description"]
    )
    async def reset_roles(self, ctx):
        # Removes character roles from everyone
        for member in ctx.guild.members:
            is_player = False
            if not member.bot:
                for role in member.roles:
                    if role.name.lower() in gamedata.CHARACTERS.keys():
                        await member.remove_roles(role)
                        is_player = True
                if is_player:
                    if member is ctx.guild.owner:
                        await ctx.send(loc["reset_roles"]["NoteAboutOwner"])
                    else:
                        await member.edit(nick=None)

    @commands.command(
        name=loc["reset"]["name"],
        aliases=loc["reset"]["aliases"],
        description=loc["reset"]["description"]
    )
    async def reset(self, ctx):
        """Complete server reset"""

        # Confirm command to user
        await ctx.send(loc["reset"]["ResettingServer"])

        # Console logging
        print(f'{constants.INFO_PREFIX}Resetting server: "{ctx.guild.name}" (ID: {ctx.guild.id})')

        # Erase all messages and reset channel permissions
        await asyncio.gather(self.wipe(ctx), self.reset_perms(ctx), self.reset_roles(ctx))


def setup(bot):
    bot.add_cog(Admin(bot))
