import discord
import requests
import numpy.random as random
import dotenv
import os
import asyncio

def randomMangas(offset):
    base_url = "https://api.mangadex.org"

    included_tag_names = []
    excluded_tag_names = []
    tags = requests.get(
        f"{base_url}/manga/tag"
    ).json()
    included_tag_ids = [
        tag["id"]
        for tag in tags["data"]
        if tag["attributes"]["name"]["en"]
        in included_tag_names
    ]
    excluded_tag_ids = [
        tag["id"]
        for tag in tags["data"]
        if tag["attributes"]["name"]["en"]
        in excluded_tag_names
    ]

    order = {"rating": "desc", "followedCount": "desc"}
    # order = {'followedCount': "desc"}
    final_order_query = dict()
    # { "order[rating]": "desc", "order[followedCount]": "desc" }
    for key, value in order.items():
        final_order_query[f"order[{key}]"] = value

    r = requests.get(
        f"{base_url}/manga",
        params={
            **{
                "limit": 100,
                "offset": offset,
                "includedTags[]": included_tag_ids,
                "excludedTags[]": excluded_tag_ids,
                "originalLanguage[]": ["ja"],
            },
            **final_order_query,
        },
    )

    data = r.json()['data']
    mangas = random.choice(data, 4, replace=False)
    mangaTitles = []
    for manga in mangas:
        if 'en' in manga['attributes']['title']:
            mangaTitle = manga['attributes']['title']['en']
        elif 'ja' in manga['attributes']['title']:
            mangaTitle = manga['attributes']['title']['ja']
        else:
            print('No english/japanese title, retrying...')
            return (None, None)
        mangaTitles.append(mangaTitle)
    manga_id = mangas[0]['id']

    return manga_id, mangaTitles

def randomPages(manga_id):

    fullURLs = []
    while len(fullURLs) < 3:
        
        base_url = "https://api.mangadex.org"
        r = requests.get(
            f"{base_url}/manga/{manga_id}/feed",
            params={"translatedLanguage[]": ["en"]},
        )

        chapter_ids = [chapter["id"] for chapter in r.json()["data"]]
        if len(chapter_ids) == 0:
            print('No valid chapters, retrying...')
            return None
        chapter_id = random.choice(chapter_ids)

        r = requests.get(f"{base_url}/at-home/server/{chapter_id}")
        r_json = r.json()

        if "baseUrl" not in r_json:
            print('baseUrl not in r_json, retrying...')
            return None

        host = r_json["baseUrl"]
        chapter_hash = r_json["chapter"]["hash"]
        data = r_json["chapter"]["data"]
        # data_saver = r_json["chapter"]["dataSaver"]

        if len(data) <= 1:
            print('Chapter has 0 pages, retrying...')
            return None
            
        randomPageIdx = random.randint(0, len(data)-1)
        
        fullURL = f'{host}/data/{chapter_hash}/{data[randomPageIdx]}'
        fullURLs.append(fullURL)

    return fullURLs

def randomImg(difficulty):

    manga_id, mangaTitles = randomMangas(difficulty)
    while manga_id == None:
        manga_id, mangaTitles = randomMangas(difficulty)
    fullURLs = randomPages(manga_id)
    while fullURLs == None:
        manga_id, mangaTitles = randomMangas(difficulty)
        fullURLs = randomPages(manga_id)
    return fullURLs, mangaTitles


bot = discord.Bot(command_prefix='$')

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")

def shortenTitles(mangaTitles):
    for i in range(len(mangaTitles)):
        mangaTitle = mangaTitles[i]
        if len(mangaTitle) > 80:
            mangaTitles[i] = mangaTitle[:77] + '...'
    return mangaTitles

async def startEmbed(ctx):
    startEmbed = discord.Embed(
        title="Starting round in 5 seconds...",
        color=discord.Colour.yellow(),
    )
    await ctx.send(embed=startEmbed)

async def panelEmbed(ctx, offset, fullURL, mangaTitle):
    description = f'Random Page from Top {offset+1}-{offset+101} Manga'

    panelEmbed = discord.Embed(
        title="Cap 1",
        description=description,
        color=discord.Colour.greyple(),
    )
    panelEmbed.set_image(url=fullURL)
    # panelEmbed.set_footer(text=mangaTitle) # answer
    await ctx.response.defer()
    await asyncio.sleep(5)
    await ctx.followup.send(embed=panelEmbed)

async def buttons(ctx, mangaTitles):
    correctManga = mangaTitles[0]
    random.shuffle(mangaTitles)
    lostPlayers = set()
    isWinner = []

    class MyView(discord.ui.View):

        async def changeButtonColors(self, state, interaction=None):
            for child in self.children:
                child.disabled = True
                if child.label != correctManga:
                    child.style = discord.ButtonStyle.secondary
                elif state == 'win':
                    child.style = discord.ButtonStyle.success
                elif state == 'loss':
                    child.style = discord.ButtonStyle.danger
            if state == 'win':
                serverGuildIDs.remove(ctx.guild.id)
                await self.gameWin(interaction)
            elif state == 'loss':
                serverGuildIDs.remove(ctx.guild.id)
                await ctx.respond(f'No one got the correct answer! The correct answer was {correctManga}.')
            await self.message.edit(view=self)

        async def gameWin(self, interaction):
            if isWinner != []:
                await interaction.response.defer()
            else:
                isWinner.append(interaction.user)
                await ctx.respond(f'{interaction.user} has won!')

        async def buttonPressResponse(self, button, interaction):
            # correct choice -- game ends
            if button.label == correctManga:
                await self.changeButtonColors('win', interaction)
            # incorrect choice
            else:
                lostPlayers.add(interaction.user)
                await interaction.response.send_message("Sorry, that is the wrong answer!", ephemeral=True)

        async def on_timeout(self):
            if isWinner != []:
                return
            await self.changeButtonColors('loss')
            
        async def repeatedButtonPress(self, interaction):
            try:
                await interaction.response.defer()
            except discord.errors.InteractionResponded:
                pass

        async def buttonInteraction(self, button, interaction):
            if interaction.user in lostPlayers or isWinner != []:
                await self.repeatedButtonPress(interaction)
            else:
                await self.buttonPressResponse(button, interaction)
                await self.repeatedButtonPress(interaction)

        @discord.ui.button(label=mangaTitles[0], row=0, style=discord.ButtonStyle.primary)
        async def first_button_callback(self, button, interaction):
            await self.buttonInteraction(button, interaction)

        @discord.ui.button(label=mangaTitles[1], row=1, style=discord.ButtonStyle.primary)
        async def second_button_callback(self, button, interaction):
            await self.buttonInteraction(button, interaction)

        @discord.ui.button(label=mangaTitles[2], row=2, style=discord.ButtonStyle.primary)
        async def third_button_callback(self, button, interaction):
            await self.buttonInteraction(button, interaction)

        @discord.ui.button(label=mangaTitles[3], row=3, style=discord.ButtonStyle.primary)
        async def fourth_button_callback(self, button, interaction):
            await self.buttonInteraction(button, interaction)
        
    await ctx.send(view=MyView(timeout=10))

serverGuildIDs = set()

@bot.command(description='Play an image game')
@discord.option(
    "offset",
    description="Enter the offset",
    default=0,
    min_value=0,
    max_value=1000)

async def pg(ctx, offset : int):

    if ctx.guild.id in serverGuildIDs:
        await ctx.respond('A game is already in progress!')
        return

    serverGuildIDs.add(ctx.guild.id)

    try:
        fullURLs, mangaTitles = randomImg(offset)

        mangaTitles = shortenTitles(mangaTitles)
        correctManga = mangaTitles[0]
        fullURL = fullURLs[0]

        await startEmbed(ctx)
        await panelEmbed(ctx, offset, fullURL, correctManga)
        await buttons(ctx, mangaTitles)

    except:
        serverGuildIDs.remove(ctx.guild.id)
        await ctx.respond('Round failed, please try again!')


dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
bot.run(token)