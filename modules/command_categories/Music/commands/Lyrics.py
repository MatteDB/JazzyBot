import bs4
import discord

from modules.base.command import Command
from urllib.parse import quote_plus


class Lyrics(Command):
    name = "lyrics"
    alts = ["subtitles"]
    oneliner = "Get lyrics for songs from Genius"
    help = "You can get lyrics for the currently playing song by just using `<prefix>lyrics`"
    examples = "`<prefix>`lyrics - While the bot is playing a song, this will pull up a list of 4 closest " \
               "matches\n`<prefix>lyrics shape of you` - Regardless of the bot's state, get 4 closest matches for the "\
               "lyrics of `shape of you`"
    options = "None"

    @staticmethod
    async def main(bot, message):
        noplayer = 0
        try:
            player = bot.players[message.server]
        except KeyError:
            noplayer = 1
        splitreq = False
        stripspace = ' '.join(message.content.split()[1:])
        if len(stripspace) < 2 and not noplayer:
            songname = player.current_entry['title']
        else:
            songname = stripspace
        headers = {'Authorization': 'Bearer ' + bot.config['genius_token']}
        async with bot.aioses.get("http://api.genius.com/search?q=" + quote_plus(songname), headers=headers) as resp:
            response = await resp.json()
        output = list()
        for a, b in enumerate(response['response']['hits'][:4], 1):
            output.append('{} {}'.format(a, b['result']['full_title']))
        if not output:
            if songname == player.current_entry['title']:
                msg = "No lyrics found! Try typing the name in manually."
            else:
                msg = "No lyrics found!"
            await message.channel.send(msg)
            return
        outputlist = '\n'.join(map(str, output))
        outputlist = '```Markdown\n' + outputlist + '\n' + "#Choose the appropriate result number or type 'exit' to " \
                                                           "leave the menu\n" + '```'
        sent_msg = await message.channel.send(outputlist, delete_after=None)

        def check(m):
            return m.author == message.author and m.channel == message.channel

        while True:
            response_msg = await bot.wait_for('message', check=check, timeout=30)
            if response_msg.content.lower() == 'exit':
                await sent_msg.delete()
                return
            try:
                chosen_number = int(response_msg.content) - 1
                chosen_song = response.json()['response']['hits'][chosen_number]['result']['url']
                break
            except IndexError:
                em = discord.Embed(title=':exclamation: Invalid choice', colour=0xff3a38)
                await message.channel.send(embed=em)
                continue
            except ValueError:
                em = discord.Embed(title=':exclamation: Invalid choice', description="Please input a number "
                                                                                     "corresponding with the list",
                                   colour=0xff3a38)
                await message.channel.send(embed=em)
                continue

        await sent_msg.delete()
        async with bot.aioses.get(chosen_song) as resp:
            legit_lyrics = await resp.text()
        alphabetsoup = bs4.BeautifulSoup(legit_lyrics)
        lyrics = [a.text for a in alphabetsoup.select('div.lyrics p')][0]
        counter = 0
        for x in lyrics:
            counter += 1
            if counter >= 1800:
                splitreq = True
        if splitreq:
            lyrics1 = lyrics[:1800]
            remaininglen = len(lyrics) - 1800
            lyrics2 = lyrics[remaininglen:]
            await message.channel.send(lyrics1)
            await message.channel.send(lyrics2)
        else:
            await message.channel.send(lyrics)
