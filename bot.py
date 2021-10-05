import random
import json
import discord
from discord.ext import commands

dft_cmd_pfx = '/'
TOKEN = 'NzM3ODc1OTQ2NDAwMzgyOTk4.XyDuhg.vzVMrNIRbCTsDAqJd0dxbyDtgno'
client_activity = 'the game of life'
cleanup_delay = 5

def get_prefix(client, message):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]

client = commands.Bot(command_prefix=get_prefix)

#events
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game(client_activity))
    print('Bot is ready.')

@client.event
async def on_guild_join(guild):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)
    prefixes[str(guild.id)] = dft_cmd_pfx
    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

@client.event
async def on_guild_remove(guild):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)
    prefixes.pop(str(guild.id))
    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

@client.event
async def on_member_join(member):
    print(f'{member} has joined the server.')

@client.event
async def on_member_remove(member):
    print(f'{member} has left the server.')

@client.event
async def on_command_error(ctx, error):
    await ctx.message.delete(delay=cleanup_delay)   # All invalid commands are deleted after a certain amount of time
    if isinstance(error, commands.CheckFailure):
        print(f'Restricted command call by {ctx.author} was denied.\n')
        await (await ctx.send(':x: Invalid permissions.')).delete(delay=cleanup_delay)
    elif isinstance(error, commands.CommandNotFound):
        await (await ctx.send(f':exclamation:Invalid command. Do {ctx.prefix}help for a command list.')).delete(delay=cleanup_delay)
    else:
        print(f'{error.__class__}\n{error}\n')

#commands
@client.command(aliases=['cmd', 'command', 'commands'])
async def cmds(ctx):
    await ctx.message.delete()
    pfx = ctx.prefix
    cmd_str = 'Default:'
    cmd_str += f'\n\t{pfx}[cmd|cmds|command|commands]\n\t\tshows this message\n'
    cmd_str += f'\n\t{pfx}[pfx|cmd_pfx|prefix|new_prefix] <prefix>\n\t\tchanges the command prefix\n'
    cmd_str += f'\n\t{pfx}help\n\t\tthis without descriptions\n'
    cmd_str += f'\n\t{pfx}[extensions|extension|ext]\n\t\tprints available extensions\n'
    cmd_str += f'\n\t{pfx}load <ext>'
    cmd_str += f'\n\t{pfx}unload <ext>'
    cmd_str += f'\n\t{pfx}reload <ext>\n\t\tloads, unloads and reloads an extension, respectively\n'
    cmd_str += f'\n\t{pfx}ping\n\t\treturns latency\n'
    cmd_str += f'\n\t{pfx}[8ball|_8ball] <question>\n\t\tyes or no questions work best\n'
    for cog in client.cogs:
        cmd_str += f'\n\n{client.get_cog(cog).cmds(pfx)}'
    await ctx.send(f'```{cmd_str}```')

@client.command(aliases=['pfx', 'cmd_pfx', 'prefix', 'commandprefix', 'command_prefix', 'changeprefix'])
@commands.has_permissions(administrator=True)
async def new_prefix(ctx, pfx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)
    prefixes[str(ctx.guild.id)] = pfx
    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)
    await ctx.message.delete()
    await ctx.send(f':white_check_mark: Command prefix set to: {pfx}')

@new_prefix.error
async def new_prefix_error(ctx, error):
    await (await ctx.send(f':exclamation:Please specify a new prefix\nUsage: `{ctx.prefix}[pfx|cmd_pfx|prefix|new_prefix] <prefix>`')).delete(delay=2*cleanup_delay)

@client.command(aliases=['ext', 'extension'])
async def extensions(ctx):
    await ctx.message.delete()
    await ctx.send(f'```Extensions:\n\tGames\n\tModerator\n\nLoad and unload the extensions as shown below:\n\t{ctx.prefix}[load|import] <ext>\n\t{ctx.prefix}unload <ext>```')

@client.command(aliases=['import'])
@commands.has_permissions(manage_roles=True)
async def load(ctx, ext):
    ext = ext.lower()
    client.load_extension(f'cogs.{ext}')
    await ctx.message.delete()
    await ctx.send(f':white_check_mark: {ctx.author.name} has loaded {ext}.')

@load.error
async def load_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        report = ':exclamation:Please specify which extension to load.'
    elif isinstance(error, commands.CommandInvokeError):
        report = ':x: Extension invalid or already loaded.'
    await (await ctx.send(f'{report}\nUsage: `{ctx.prefix}[load|import] <ext>`')).delete(delay=cleanup_delay)

@client.command()
@commands.has_permissions(manage_roles=True)
async def unload(ctx, ext):
    ext = ext.lower()
    client.unload_extension(f'cogs.{ext}')
    await ctx.message.delete()
    await ctx.send(f':white_check_mark: {ctx.author.name} has unloaded {ext}.')

@unload.error
async def unload_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        report = ':exclamation:Please specify which extension to unload.'
    elif isinstance(error, commands.CommandInvokeError):
        report = ':x: Extension invalid or already unloaded.'
    await (await ctx.send(f'{report}\nUsage: `{ctx.prefix}unload <ext>`')).delete(delay=cleanup_delay)

@client.command()
async def reload(ctx, ext):
    ext = ext.lower()
    client.reload_extension(f'cogs.{ext}')
    await ctx.message.delete()
    await ctx.send(f':white_check_mark: {ctx.author.name} has reloaded {ext}')

@reload.error
async def reload_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        report = ':exclamation:Please specify which extension to reload.'
    elif isinstance(error, commands.CommandInvokeError):
        report = ':x: Extension invalid or is unloaded. Try loading it.'
    await (await ctx.send(f'{report}\nUsage: `{ctx.prefix}reload <ext>`')).delete(delay=cleanup_delay)

@client.command(aliases=['latency'])
async def ping(ctx):
    await ctx.message.delete()
    await ctx.send(f"{ctx.author.name}'s latency: {round(client.latency * 1000)}ms")

@client.command(aliases=['8ball', 'random'])
async def _8ball(ctx, *, question):
    responses = ['Yes.', 
                 'No.', 
                 'Absolutely!',
                 'Certainly not.',
                 'Of course.',
                 'That is uncertain.',
                 'It depends.',
                 'Without a doubt.',
                 "Don't count on it.",
                 'Very doubtful.',
                 'Outlook not so good.']
    await ctx.message.delete()
    await ctx.send(f"{ctx.author.name}'s Question: {question}\nAnswer: {random.choice(responses)}")

@_8ball.error
async def _8ball_error(ctx, error):
    await (await ctx.send(f':exclamation:Ask a question.\nUsage: `{ctx.prefix}[_8ball|8ball|random] <question>`')).delete(delay=cleanup_delay)

client.load_extension('cogs.moderator')
client.load_extension('cogs.games')
client.run(TOKEN)