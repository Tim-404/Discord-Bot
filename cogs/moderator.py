import random
import discord
from discord.ext import commands

cleanup_delay = 5

admin_whitelist = [
    516411039575965697, #me
    737875946400382998  #bot
]

funny_rejections = [
    "I wouldn't do that if I were you.",
    "That's not the answer.",
    'Stoopid.',
    'Are you sure?',
    'No.',
    "That won't work, no matter how much you try.",
    "You can't do that to yourself.",
    'Nope.',
    'Bruh.',
    ':x: Error. Self-deprecating actions prohibited.',
    "How 'bout no."
]

funny_bot_complaints = [
    "Hey! :pleading_face:",
    "That's not nice.",
    "Don't test my patience, mortal. :rage:",
    ":face_with_symbols_over_mouth:",
    "Your efforts are futile.",
    "Hold up.",
    ":white_check_mark: Task successfully failed.",
    "No thanks, I'm doing just fine.",
    "HO HO HO! You are on the naughty list now.",
    "AHem. :face_with_raised_eyebrow:"
]

class Moderator(commands.Cog):
    def __init__(self, client):
        self.client = client

    def cmds(self, pfx):
        cmd_str = 'Moderator'
        cmd_str += f'\n\t{pfx}kick <user>'
        cmd_str += f'\n\t{pfx}ban <user>'
        cmd_str += f'\n\t{pfx}unban <user>'
        cmd_str += f'\n\t{pfx}clear <# of messages>\n'
        return cmd_str

    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Moderator is ready.')

    #commands
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member : discord.Member, *, reason=None):
        if await auth_exe(ctx, member):
            await ctx.message.delete()
            await member.ban(reason=reason)
            await ctx.send(f':ballot_box_with_check: {member.name} is banned from the server.')

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            report = ':exclamation:Mention the user to ban.'
        elif isinstance(error, commands.BadArgument):
            report = ':exclamation:User not found.'
        await (await ctx.send(f'{report}\nUsage: `{ctx.prefix}ban <user>`')).delete(delay=cleanup_delay)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=1):
        await ctx.channel.purge(limit=amount+1)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await (await ctx.send(f':exclamation:Enter the amount of messages to delete.\nUsage: `{ctx.prefix}clear`')).delete(delay=cleanup_delay)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member : discord.Member, *, reason=None):
        if await auth_exe(ctx, member):
            await ctx.message.delete()
            await member.kick(reason=reason)
            await ctx.send(f':ballot_box_with_check: {member.name} has been kicked from the server.')

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            report = ':exclamation:Mention the user to kick.'
        elif isinstance(error, commands.BadArgument):
            report = ':exclamation:User not found.'
        await (await ctx.send(f'{report}\nUsage: `{ctx.prefix}kick <user>`')).delete(delay=cleanup_delay)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for banned_entry in banned_users:
            user = banned_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.message.delete()
                await ctx.guild.unban(user)
                await ctx.send(f':ballot_box_with_check: Unbanned {user}.')
                return
        await ctx.message.delete(delay=cleanup_delay)
        await (await ctx.send(':exclamation:User not found. Make sure to enter the name in this format:\n\tName#1234')).delete(delay=cleanup_delay)

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.CommandInvokeError):
            await (await ctx.send(f':exclamation:Enter a username in this format: Name#1234\nUsage: `{ctx.prefix}unban <user>`')).delete(delay=cleanup_delay)

async def auth_exe(ctx, member : discord.Member):
    if member is ctx.author:
        await ctx.send(f'{random.choice(funny_rejections)}')
        return False
    if member.id == admin_whitelist[1]:
        print(f'{ctx.author} attempted to call a moderator command on the bot.')
        await ctx.send(f'{random.choice(funny_bot_complaints)}')
        return False
    for admin in admin_whitelist:
        if member.id == admin:
            print(f'{ctx.author} attempted to call a moderator command on {member}.')
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(f':x: Invalid execution. {member.name} is immune to that command.')).delete(delay=cleanup_delay)
            return False
    return True

def setup(client):
    client.add_cog(Moderator(client))