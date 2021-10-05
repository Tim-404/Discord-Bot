import random
import json
import discord
from discord.ext import commands

cleanup_delay = 5
dft_ante = 5
dft_init_balance = 50
status = {
    'pending': 0,
    'bet': 1,
    'stand': 2,
    'call': 3,
    'fold': 4,
    'bust': 5
}

card_dict = {
    1: ':regional_indicator_a:',
    2: ':two:',
    3: ':three:',
    4: ':four:',
    5: ':five:',
    6: ':six:',
    7: ':seven:',
    8: ':eight:',
    9: ':nine:',
    10: ':keycap_ten:',
    11: ':regional_indicator_j:',
    12: ':regional_indicator_q:',
    13: ':regional_indicator_k:'
}
blackjack_card_value = {
            1: 11,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
            6: 6,
            7: 7,
            8: 8,
            9: 9,
            10: 10,
            11: 10,
            12: 10,
            13: 10
        }

class Games(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    def cmds(self, pfx):
        cmd_str = 'Games'
        cmd_str += f'\n\t{pfx}[game_list|games]\n\t\tlists the following games\n'
        cmd_str += f'\n\t{pfx}blackjack <init_balance> <ante> <players>'
        cmd_str += f'\n\t*{pfx}[end|stop|end_game]\n\t\tends any of the above games in the channel\n'
        cmd_str += f'\n\t{pfx}[minesweeper|ms] [width]x[height] [# of bombs|bomb percentage]\n'
        return cmd_str

    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Games are ready.')
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        for channel_id in info:
            info = map_presets(info, channel_id)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        for channel in guild.text_channels:
            info = map_presets(info, channel.id)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        for channel in guild.text_channels:
            del info[str(channel.id)]
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)

    #commands
    @commands.command(aliases=['games'])    #TODO: poker?
    async def game_list(self, ctx):
        await ctx.send(f'```Games:\n\tBlackjack\n\tMinesweeper```')

    @commands.command()
    async def ante(self, ctx, amount : int):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        info[str(ctx.channel.id)]['ante'] = amount
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)
        await ctx.message.delete()
        await ctx.send(f':white_check_mark: Ante for card games set to: ${amount}')

    @ante.error
    async def ante_error(self, ctx, error):
        await (await ctx.send(f':exclamation:Enter the ante for all card games.\nUsage: `{ctx.prefix}ante <amount>`'))

    @commands.command()
    async def init_balance(self, ctx, amount : int):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        info[str(ctx.channel.id)]['init_balance'] = amount
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)
        await ctx.message.delete()
        await ctx.send(f':white_check_mark: Starting balance for card games set to: ${amount}')

    @init_balance.error
    async def init_balance_error(self, ctx, error):
        await (await ctx.send(f':exclamation:Enter the amount of money that players start with for all card games.\nUsage: `{ctx.prefix}init_balance <amount>`'))

    @commands.command(aliases=['end', 'stop'])
    async def end_game(self, ctx):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        if not game_active(ctx, info):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:There are no games running in this channel.')).delete(delay=cleanup_delay)
            return
        info = map_presets(info, ctx.channel.id)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)
        await ctx.message.delete()
        await ctx.send(':white_check_mark: Game ended.')
        
    @commands.command()
    async def blackjack(self, ctx, *, players):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        if game_active(ctx, info):
            await ctx.message.delete(delay=cleanup_delay/2)
            await (await ctx.send(':exclamation:Game in progress.')).delete(delay=cleanup_delay/2)
            return
        player_list = players.split(' ')
        
        info = setup_game(ctx, info, 'blackjack', player_list, info[str(ctx.channel.id)]['init_balance'])
        info = blackjack_start(ctx, info)
        info = calc_score(ctx, info, 'blackjack')
        
        embed = blackjack_display(ctx, info)
        await ctx.message.delete()
        info = await new_display(ctx, info, embed)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)

        for player in player_list:
            card = card_dict[info[str(ctx.channel.id)]['players'][player]['hand'][0]]
            embed = discord.Embed(title='Blackjack')
            embed.add_field(name='First Card', value=card)
            await get_member_from_mention(ctx, player).send(embed=embed)

    @blackjack.error
    async def blackjack_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.CommandInvokeError):
            await (await ctx.send(f':exclamation:Mention the players that want to participate.\nUsage: `{ctx.prefix}blackjack <init_balance> <ante> @player1 @player2 @player3 ...`')).delete(delay=2*cleanup_delay)

    @commands.command()
    async def bet(self, ctx, amount : int):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        if not game_active(ctx, info, 'blackjack'):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:Blackjack is not running.')).delete(delay=cleanup_delay)
            return
        if not found_player(ctx, info, ctx.author.mention):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:You are not in the game.')).delete(delay=cleanup_delay)
            return
        if player_status(ctx, info) == status['bust'] or player_status(ctx, info) == status['fold'] or not round_active(ctx, info) or (player_status(ctx, info) == status['bet'] and info[str(ctx.channel.id)]['players'][ctx.author.mention]['wager'] == highest_wager(ctx, info)):
            await ctx.message.delete()
            return

        #TODO: issue
        info = bet(ctx, info, amount)
        info[str(ctx.channel.id)]['players'][ctx.author.mention]['status'] = status['bet']
        info, embed = round_sweep(ctx, info)
        await ctx.message.delete()
        await display(ctx, info, embed)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)

    @commands.command()
    async def call(self, ctx):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        if not game_active(ctx, info, 'blackjack'):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:Blackjack is not running.')).delete(delay=cleanup_delay)
            return
        if not found_player(ctx, info, ctx.author.mention):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:You are not in the game.')).delete(delay=cleanup_delay)
            return
        if player_status(ctx, info) == status['bust'] or player_status(ctx, info) == status['fold'] or not round_active(ctx, info):
            await ctx.message.delete()
            return

        info = call(ctx, info)
        info[str(ctx.channel.id)]['players'][ctx.author.mention]['status'] = status['call']
        info, embed = round_sweep(ctx, info)
        await ctx.message.delete()
        await display(ctx, info, embed)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)

    @commands.command()
    async def fold(self, ctx):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        if not game_active(ctx, info, 'blackjack'):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:Blackjack is not running.')).delete(delay=cleanup_delay)
            return
        if not found_player(ctx, info, ctx.author.mention):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:You are not in the game.')).delete(delay=cleanup_delay)
            return
        if player_status(ctx, info) == status['fold'] or player_status(ctx, info) == status['bust']or not round_active(ctx, info):
            await ctx.message.delete()
            return

        info[str(ctx.channel.id)]['players'][ctx.author.mention]['status'] = status['fold']
        info, embed = round_sweep(ctx, info)
        await ctx.message.delete()
        await display(ctx, info, embed)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)

    @commands.command()
    async def hit(self, ctx):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        if not game_active(ctx, info, 'blackjack'):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:Blackjack is not running.')).delete(delay=cleanup_delay)
            return
        if not found_player(ctx, info, ctx.author.mention):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:You are not in the game.')).delete(delay=cleanup_delay)
            return
        if info[str(ctx.channel.id)]['players'][ctx.author.mention]['status'] != status['pending'] or not round_active(ctx, info):
            await ctx.message.delete()
            return

        info = deal(ctx, info, ctx.author.mention)
        info = calc_score(ctx, info, 'blackjack')
        info, embed = round_sweep(ctx, info)
        await ctx.message.delete()
        await display(ctx, info, embed)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)

    @commands.command()
    async def stand(self, ctx):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        if not game_active(ctx, info, 'blackjack'):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:Blackjack is not running.')).delete(delay=cleanup_delay)
            return
        if not found_player(ctx, info, ctx.author.mention):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:You are not in the game.')).delete(delay=cleanup_delay)
            return
        if player_status(ctx, info) == status['fold'] or player_status(ctx, info) == status['bust'] or not round_active(ctx, info):
            await ctx.message.delete()
            return

        info[str(ctx.channel.id)]['players'][ctx.author.mention]['status'] = status['stand']
        info, embed = round_sweep(ctx, info)
        await ctx.message.delete()
        await display(ctx, info, embed)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)
        
    @commands.command(aliases=['ms'])
    async def minesweeper(self, ctx, widthxheight, bombs):
        max_len = 1900  # discord limit
        tile_len = 11   # emoji length
        time_lim = 300  # time limit for performance issues

        width, height = widthxheight.split('x')
        w = int(width)
        h = int(height)
        if bombs.endswith('%'):
            bombs = float(bombs.rstrip('%')) / 100
            bombs = w * h * bombs
        bombs = max(int(bombs), 0)

        if w < 1 or h < 1:
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:Those are not valid grid dimensions.')).delete(delay=cleanup_delay)
            return
        if w * h < bombs:
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:There are too many bombs for the grid.')).delete(delay=cleanup_delay)
            return

        grid = [[0 for x in range(w)] for y in range(h)]
        b = 0
        while b < bombs:    # set bombs
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            if grid[y][x] != -1:
                grid[y][x] = -1
                b += 1
                for i in range(-1, 2):  # set numbers of surrounding tiles
                    for j in range(-1, 2):
                        if (i != 0 or j != 0) and x + i >= 0 and x + i < w and y + j >= 0 and y + j < h and grid[y + j][x + i] != -1:
                            grid[y + j][x + i] += 1
        
        await ctx.message.delete()
        await (await ctx.send(f':exclamation:The grid will be deleted in {time_lim} seconds to prevent lag.\n**Grid**: {w}x{h}\t**Bombs**: {bombs}')).delete(delay=time_lim)
        grid_dict = {
            -1: '||:bomb:||',
            0: '||:zero:||',
            1: '||:one:||',
            2: '||:two:||',
            3: '||:three:||',
            4: '||:four:||',
            5: '||:five:||',
            6: '||:six:||',
            7: '||:seven:||',
            8: '||:eight:||'
        }
        grid_str = ''
        for r in range(h):
            for c in range(w):
                grid_str += grid_dict.get(grid[r][c])
            if len(grid_str) + tile_len * w > max_len and r + 1 < h:
                await (await ctx.send(grid_str)).delete(delay=time_lim)
                grid_str = ''
            else:
                grid_str += '\n'
        await (await ctx.send(grid_str)).delete(delay=time_lim)

    @minesweeper.error
    async def mnswpr_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.CommandInvokeError):
            await (await ctx.send(f'Enter a grid size and the amount of bombs.\nUsage: `{ctx.prefix}minesweeper [width]x[height] [# of bombs|bomb percentage]`')).delete(delay=2*cleanup_delay)

    @commands.command()
    async def next(self, ctx):
        with open('cogs\\game_status.json', 'r') as f:
            info = json.load(f)
        if not game_active(ctx, info, 'blackjack'):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:Blackjack is not running.')).delete(delay=cleanup_delay)
            return
        if not found_player(ctx, info, ctx.author.mention):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:You are not in the game.')).delete(delay=cleanup_delay)
            return
        if round_active(ctx, info):
            await ctx.message.delete(delay=cleanup_delay)
            await (await ctx.send(':exclamation:The current round is still active.')).delete(delay=cleanup_delay)
            return

        if info[str(ctx.channel.id)]['game'] == 'blackjack':
            info = blackjack_start(ctx, info)
            info = calc_score(ctx, info, 'blackjack')
            embed = blackjack_display(ctx, info)
            await ctx.message.delete()
            await display(ctx, info, embed)

            for player in info[str(ctx.channel.id)]['players']:
                card = card_dict[info[str(ctx.channel.id)]['players'][player]['hand'][0]]
                embed = discord.Embed(title='Blackjack')
                embed.add_field(name='First Card', value=card)
                await get_member_from_mention(ctx, player).send(embed=embed)
        with open('cogs\\game_status.json', 'w') as f:
            json.dump(info, f, indent=4)

# general info
def adjust_ante_and_balance(ctx, info):
    if info[str(ctx.channel.id)]['ante'] > info[str(ctx.channel.id)]['init_balance']:
        info[str(ctx.channel.id)]['ante'] = dft_ante
        info[str(ctx.channel.id)]['init_balance'] = dft_init_balance
    return info

async def display(ctx, info, embed):
    message = await ctx.channel.fetch_message(info[str(ctx.channel.id)]['display_id'])
    await message.edit(embed=embed)

def found_player(ctx, info, player):
    return player in info[str(ctx.channel.id)]['players']

def game_active(ctx, info, game=''):
    if game == '':
        return info[str(ctx.channel.id)]['game'] != game
    return info[str(ctx.channel.id)]['game'] == game

def get_member_from_mention(ctx, player):
    return ctx.guild.get_member(int(player.strip('<@>')))

def map_defaults(info, channel_id):
    info[str(channel_id)] = {
        'ante': dft_ante,
        'init_balance': dft_init_balance,
        'game': '',
        'players': {}
    }
    return info

def map_presets(info, channel_id):    # aka clear_game
    ante = dft_ante if 'ante' not in info[str(channel_id)] else info[str(channel_id)]['ante']
    init_balance = dft_init_balance if 'init_balance' not in info[str(channel_id)] else info[str(channel_id)]['init_balance']
    info[str(channel_id)] = {
        'ante': ante,
        'init_balance': init_balance,
        'game': '',
        'players': {}
    }
    return info

async def new_display(ctx, info, embed):
    id = (await ctx.send(embed=embed)).id
    info[str(ctx.channel.id)]['display_id'] = id
    return info

def player_status(ctx, info):
    return info[str(ctx.channel.id)]['players'][ctx.author.mention]['status']

def store_game(ctx, info, game, player_list):
    info[str(ctx.channel.id)]['game'] = game
    for player in player_list:
        info[str(ctx.channel.id)]['players'][player] = {}
    return info

# general game func
def ante_in(ctx, info, amount):
    info = bet(ctx, info, amount)
    return info

def bet(ctx, info, amount):
    if amount > info[str(ctx.channel.id)]['players'][ctx.author.mention]['balance']:
        amount = info[str(ctx.channel.id)]['players'][ctx.author.mention]['balance']
    info[str(ctx.channel.id)]['players'][ctx.author.mention]['balance'] -= amount
    info[str(ctx.channel.id)]['players'][ctx.author.mention]['wager'] += amount
    info[str(ctx.channel.id)]['pot'] += amount
    return info

def calc_score(ctx, info, game):
    if game == 'blackjack':
        for player in info[str(ctx.channel.id)]['players']:
            info[str(ctx.channel.id)]['players'][player]['score'] = 0
            for card in info[str(ctx.channel.id)]['players'][player]['hand']:
                info[str(ctx.channel.id)]['players'][player]['score'] += blackjack_card_value[card]
            while info[str(ctx.channel.id)]['players'][player]['ace_buffer'] > 0 and info[str(ctx.channel.id)]['players'][player]['score'] > 21:
                info[str(ctx.channel.id)]['players'][player]['score'] -= 10
            if info[str(ctx.channel.id)]['players'][player]['score'] > 21:
                info[str(ctx.channel.id)]['players'][player]['status'] = status['bust']
    print(info[str(ctx.channel.id)]['players'][player]['score'])
    return info

def call(ctx, info):
    high = highest_wager(ctx, info)
    current = info[str(ctx.channel.id)]['players'][ctx.author.mention]['wager']
    amount = high - current if high > current else 0
    info = bet(ctx, info, amount)
    return info

def deal(ctx, info, player, amount=1):
    for _ in range(amount):
        if info[str(ctx.channel.id)]['card_count'] == 0:
            print('The deck is empty.')
            break
        card = random.randint(1, info[str(ctx.channel.id)]['card_count'])
        deck_index = -1
        t = 0
        while t < card:
            deck_index += 1
            t += info[str(ctx.channel.id)]['deck'][deck_index]
        info[str(ctx.channel.id)]['players'][player]['hand'].append(deck_index + 1)
        info[str(ctx.channel.id)]['deck'][deck_index] -= 1
        info[str(ctx.channel.id)]['card_count'] -= 1
        if deck_index == 0:
            info[str(ctx.channel.id)]['players'][player]['ace_buffer'] += 1
    return info

def distr_chips(ctx, info, base):
    for player in info[str(ctx.channel.id)]['players']:
        info[str(ctx.channel.id)]['players'][player]['balance'] = base
    return info

def highest_wager(ctx, info):
    highest = 0
    for player in info[str(ctx.channel.id)]['players']:
        highest = max(highest, info[str(ctx.channel.id)]['players'][player]['wager'])
    return highest

def is_finished(ctx, info, player):
    action = info[str(ctx.channel.id)]['players'][player]['status']
    return (info[str(ctx.channel.id)]['players'][player]['wager'] == highest_wager(ctx, info) or info[str(ctx.channel.id)]['players'][player]['balance'] == 0) and (action == status['bet'] or action == status['call'] or action == status['stand'])

def opted_out(ctx, info, player):
    action = info[str(ctx.channel.id)]['players'][player]['status']
    return action == status['fold'] or action == status['bust']

def purge(ctx, info):
    info[str(ctx.channel.id)]['losers'] = []
    for player in info[str(ctx.channel.id)]['players']:
        if info[str(ctx.channel.id)]['players'][player]['balance'] <= 0:
            info[str(ctx.channel.id)]['losers'].append(info[str(ctx.channel.id)]['players'].pop(player))
    return info

def redeem(ctx, info, winner_list : list):
    total = 0
    for player in winner_list:
        total += info[str(ctx.channel.id)]['players'][player]['wager']
    for player in winner_list:
        winnings = info[str(ctx.channel.id)]['pot'] * float(info[str(ctx.channel.id)]['players'][player]['wager']) / total
        info[str(ctx.channel.id)]['players'][player]['balance'] += winnings
        info[str(ctx.channel.id)]['pot'] -= winnings
    return info

def reset_round(ctx, info):
    info[str(ctx.channel.id)]['round_in_play'] = True
    info[str(ctx.channel.id)]['deck'] = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
    info[str(ctx.channel.id)]['card_count'] = 52
    info[str(ctx.channel.id)]['pot'] = 0
    for player in info[str(ctx.channel.id)]['players']:
        info[str(ctx.channel.id)]['players'][player]['hand'] = []
        info[str(ctx.channel.id)]['players'][player]['wager'] = 0
        info[str(ctx.channel.id)]['players'][player]['status'] = status['pending']
    return info

def round_active(ctx, info):
    return info[str(ctx.channel.id)]['round_in_play']

def round_sweep(ctx, info): 
    for player in info[str(ctx.channel.id)]['players']:
        if not is_finished(ctx, info, player) and not opted_out(ctx, info, player):
            return info, blackjack_display(ctx, info)
    if info[str(ctx.channel.id)]['game'] == 'blackjack':
        winners = []
        former_balances = {}
        high_score = 0
        for player in info[str(ctx.channel.id)]['players']:
            if is_finished(ctx, info, player) and info[str(ctx.channel.id)]['players'][player]['score'] > high_score:
                high_score = info[str(ctx.channel.id)]['players'][player]['score']
        for player in info[str(ctx.channel.id)]['players']:
            if is_finished(ctx, info, player) and info[str(ctx.channel.id)]['players'][player]['score'] == high_score:
                print(1)
                winners.append(player)
                former_balances[player] = info[str(ctx.channel.id)]['players'][player]['balance']

        info = redeem(ctx, info, winners)

        info = purge(ctx, info)
        eliminated = info[str(ctx.channel.id)]['losers']

        embed = blackjack_display(ctx, info, False)
        s = 's' # pylint freaks out about not using these idk y :(
        _ = ''
        plyrs = 'players'
        bal = 'balance'
        if len(winners) > 0:
            header = f'Round Winner{s if len(winners) > 1 else _}:'
            for player in winners:
                header += f'\n{get_member_from_mention(ctx, player).display_name}: ${info[str(ctx.channel.id)][plyrs][player][bal] - former_balances[player]}'
            embed.description = header
        if len(eliminated) > 0:
            footer = f'Player{s if len(eliminated) > 1 else _} eliminated:'
            for player in eliminated:
                footer += f'\n{get_member_from_mention(ctx, player).display_name}'
            embed.set_footer(text=footer)

        info[str(ctx.channel.id)]['round_in_play'] = False
        return info, embed

def setup_game(ctx, info, game, player_list, base):
    info = adjust_ante_and_balance(ctx, info)
    info = store_game(ctx, info, game, player_list)
    info = distr_chips(ctx, info, base)
    return info

# blackjack
def blackjack_start(ctx, info):
    info = reset_round(ctx, info)
    info = ante_in(ctx, info, info[str(ctx.channel.id)]['ante'])
    for player in info[str(ctx.channel.id)]['players']:
        info[str(ctx.channel.id)]['players'][player]['ace_buffer'] = 0
        info = deal(ctx, info, player, 2)
    return info

def blackjack_display(ctx, info, hide_first=True):
    pot = info[str(ctx.channel.id)]['pot']
    embed = discord.Embed(title='Blackjack', description=f'Pot: ${pot}\nCall wager: ${highest_wager(ctx, info)}')
    for player in info[str(ctx.channel.id)]['players']:
        balance = info[str(ctx.channel.id)]['players'][player]['balance']
        wager = info[str(ctx.channel.id)]['players'][player]['wager']
        hand = ''
        hide = hide_first
        for card in info[str(ctx.channel.id)]['players'][player]['hand']:
            if hide and not info[str(ctx.channel.id)]['players'][player]['status'] == status['busted']:
                hand += ':shield:'
                hide = False
                continue
            hand += card_dict[card]
        action = list(status.keys())[list(status.values()).index(info[str(ctx.channel.id)]['players'][player]['status'])]
        player_info = f'Balance: ${balance}\nWager: ${wager}\nAction: {action}\n{hand}'
        stat = ':white_check_mark:' if is_finished(ctx, info, player) else ':x:' if opted_out(ctx, info, player) else ''
        header = f'{get_member_from_mention(ctx, player).display_name} {stat}'
        embed.add_field(name=header, value=player_info, inline=False)
    if info[str(ctx.channel.id)]['card_count'] == 0:
        embed.set_footer(text='The deck is empty.')
    return embed

def setup(client):
    client.add_cog(Games(client))