import discord
import requests
import numpy.random as random
import dotenv
import os
import asyncio
import json

#===============================================================================
# Randomizing Manga
#===============================================================================

def randomMangas(difficulty):
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

    mangaTitles = []
    while len(mangaTitles) < 4:

        startOffset = (difficulty-1)*250
        endOffset = difficulty*250
        offset = random.randint(startOffset, endOffset)

        r = requests.get(
            f"{base_url}/manga",
            params={
                **{
                    "limit": 1,
                    "offset": offset,
                    "includedTags[]": included_tag_ids,
                    "excludedTags[]": excluded_tag_ids,
                    "originalLanguage[]": ["ja"],
                },
                **final_order_query,
            },
        )

        data = r.json()['data']
        manga = data[0]
        
        if 'en' in manga['attributes']['title']:
            mangaTitle = manga['attributes']['title']['en']
        elif 'ja' in manga['attributes']['title']:
            mangaTitle = manga['attributes']['title']['ja']
        elif 'ko' in manga['attributes']['title']:
            mangaTitle = manga['attributes']['title']['ko']
        else:
            print('No valid title, retrying...')
            return (None, None)

        if mangaTitle in mangaTitles:
            continue
        else:
            mangaTitles.append(mangaTitle)
        
        if len(mangaTitles) == 1:
            manga_id = manga['id']

    return manga_id, mangaTitles


def randomMangaWithMAL(malUsers):

    with open('data.json') as f:
        data = json.load(f)

    mdexLst = []
    for username in malUsers:
        mdexLst.extend(data['mal'][username])

    mdexLstIdxes = random.choice(len(mdexLst), 4, replace=False)

    mangaTitles = []
    for i in range(4):
        manga_id, mangaTitle = mdexLst[mdexLstIdxes[i]]
        mangaTitles.append(mangaTitle)

        if i == 0:
            correct_manga_id = manga_id

    f.close()
    return correct_manga_id, mangaTitles

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

def randomImg(difficulty, malUsers):

    if malUsers != []:
        manga_id, mangaTitles = randomMangaWithMAL(malUsers)
        fullURLs = randomPages(manga_id)
        while fullURLs == None:
            manga_id, mangaTitles = randomMangaWithMAL(malUsers)
            fullURLs = randomPages(manga_id)
        return fullURLs, mangaTitles
    else:
        manga_id, mangaTitles = randomMangas(difficulty)
        while manga_id == None:
            manga_id, mangaTitles = randomMangas(difficulty)
        fullURLs = randomPages(manga_id)
        while fullURLs == None:
            manga_id, mangaTitles = randomMangas(difficulty)
            fullURLs = randomPages(manga_id)
        return fullURLs, mangaTitles

#===============================================================================
# Starting up bot
#===============================================================================

bot = discord.Bot()

@bot.event
async def on_ready():
    setAllRoundsOutOfProgress()
    print(f'We have logged in as {bot.user}')

#===============================================================================
# Embeds/Buttons
#===============================================================================

# returns difficulty name given difficulty
def difficultyName(difficulty):
    if difficulty == 1:
        return 'Easy'
    elif difficulty == 2:
        return 'Normal'
    elif difficulty == 3:
        return 'Hard'
    elif difficulty == 4:
        return 'Harder'
    elif difficulty == 5:
        return 'Insane'

async def startEmbed(ctx, difficulty, malUsers):
    startEmbed = discord.Embed(
        title="Starting round in 3 seconds...",
        color=discord.Colour.yellow(),
    )
    difficultyLevel = difficultyName(difficulty)

    if malUsers == []:
        value = f'Difficulty: **{difficultyLevel}**'
    else:
        value = f'From **{",".join(malUsers)}** MyAnimeList list(s)'


    startEmbed.add_field(name='Settings', value=value)

    await ctx.respond(embed=startEmbed)

async def panelEmbed(ctx, fullURL, mangaTitle):
    panelEmbed = discord.Embed(
        title="Random Manga Panel",
        description="Guess the correct manga!",
        color=discord.Colour.greyple(),
    )

    panelEmbed.set_image(url=fullURL)
    await asyncio.sleep(3)
    # panelEmbed.set_footer(text=mangaTitle)  # putting correct manga as embed footer
    await ctx.respond(embed=panelEmbed)

async def buttons(ctx, mangaTitles):
    correctManga = mangaTitles[0]
    random.shuffle(mangaTitles)
    lostPlayers = set()
    isWinner = []

    # initializing button class
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
                setRoundOutOfProgress(ctx)
                await self.roundWin(interaction)
            elif state == 'loss':
                setRoundOutOfProgress(ctx)
                await ctx.respond(f'No one got the correct answer! The correct answer was **{correctManga}**.')
            await self.message.edit(view=self)

        async def roundWin(self, interaction):
            if isWinner != []:
                await interaction.response.defer()
            else:
                isWinner.append(interaction.user)
                updateScore(interaction)
                username = str(interaction.user)
                await ctx.respond(f'**{username}** has won!')

        async def buttonPressResponse(self, button, interaction):
            # correct choice -- round ends
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

#===============================================================================
# Updating playing guilds / leaderboard
#===============================================================================

def isRoundInProgress(ctx):
    with open('data.json') as f:
        data = json.load(f)

    isRoundInProgress = ctx.guild.id in data["playingGuilds"]
    f.close()
    return isRoundInProgress

def setRoundInProgress(ctx):
    with open('data.json') as f:
        data = json.load(f)

    data["playingGuilds"].append(ctx.guild.id)

    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    f.close()

def setRoundOutOfProgress(ctx):
    with open('data.json') as f:
        data = json.load(f)

    if ctx.guild.id in data["playingGuilds"]:
        data["playingGuilds"].remove(ctx.guild.id)

    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    f.close()

def setAllRoundsOutOfProgress():
    with open('data.json') as f:
        data = json.load(f)

    data["playingGuilds"] = []

    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    f.close()

def updateScore(interaction):
    with open('data.json') as f:
        data = json.load(f)

    user = str(interaction.user)
    if user not in data["score"]:
        data["score"][user] = 1
    else:
        data["score"][user] += 1

    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    f.close()

#===============================================================================
# Bot commands
#===============================================================================

def checkForValidMALs(myAnimeLists):

    with open('data.json') as f:
        data = json.load(f)

    malLists = myAnimeLists.split(',')
    for i in range(len(malLists)):
        username = (malLists[i].strip()).lower()

        if username not in data['mal']:
            
            f.close()
            return ('No user', username)
        mdexLst = data['mal'][username]

        if len(mdexLst) < 4:
            
            f.close()
            return ('Not enough manga', username)

        malLists[i] = username

    f.close()
    return malLists

# parsing manga titles that are > 80 characters
def shortenTitles(mangaTitles):
    for i in range(len(mangaTitles)):
        mangaTitle = mangaTitles[i]
        if len(mangaTitle) > 80:
            mangaTitles[i] = mangaTitle[:77] + '...'
    return mangaTitles

@bot.command(description='Play a manga guessing game.')
@discord.option(
    "difficulty",
    description="Enter the difficulty",
    default=1,
    min_value=1,
    max_value=5)
@discord.option(
    "mal",
    description="MyAnimeList usernames (seperated by commas)",
    default="",
)

async def pg(ctx, difficulty : int, mal : str):

    if isRoundInProgress(ctx):
        await ctx.respond('A round is already in progress!')
        return

    setRoundInProgress(ctx)

    malUsers = []
    if mal != "":
        malUsers = checkForValidMALs(mal)
        if isinstance(malUsers, tuple):
            error, username = malUsers
            if error == 'No user':
                await ctx.respond(f"{username}'s list on MyAnimeList has not been synced yet. Use the `sync` command to syncronize the list.")
                setRoundOutOfProgress(ctx)
                return
            elif error == 'Not enough manga':
                await ctx.respond(f"{username}'s list does not have enough manga!")
                setRoundOutOfProgress(ctx)
                return

    try:
        await startEmbed(ctx, difficulty, malUsers)

        fullURLs, mangaTitles = randomImg(difficulty, malUsers)

        mangaTitles = shortenTitles(mangaTitles)
        correctManga = mangaTitles[0]
        fullURL = fullURLs[0]

        
        await panelEmbed(ctx, fullURL, correctManga)
        await buttons(ctx, mangaTitles)

    except:
        setRoundOutOfProgress(ctx)
        print('Error occurred, please try again.')

@bot.command(description="Forcefully stops the current round. Only use if bot is softlocked.")
async def forcestop(ctx):
    setRoundOutOfProgress(ctx)
    await ctx.respond(f'Current round has forcefully been stopped.')

@bot.command(description="Sends user's current score.")
async def score(ctx):
    with open('data.json') as f:
        data = json.load(f)
    
    user = str(ctx.user)

    if user not in data["score"]:
        f.close()
        await ctx.respond(f"{user} has gotten 0 manga correct!")

    else:
        score = data["score"][user]
        f.close()
        await ctx.respond(f"{user} has gotten {score} manga correct!")

@bot.command(description="Sends the bot's latency.")
async def ping(ctx):
    await ctx.respond(f"Pong! Latency is {bot.latency}")

@bot.command(description="Sends top players.")
async def top(ctx):

    leaderboardEmbed = discord.Embed(
            title="Top Players",
            color=discord.Colour.blurple(),
        )

    with open('data.json') as f:
        data = json.load(f)

    leaderboardList = []

    for user in data["score"]:
        score = data["score"][user]
        leaderboardList.append((score, user))

    leaderboardList.sort(reverse = True)

    leaderboard = ""
    for i in range(10):
        if i < len(leaderboardList):
            score, user = leaderboardList[i]
            leaderboard += f"\n`{i+1}` {user} `{score}`"
        else:
            leaderboard += f"\n`{i+1}` N/A `0`"

    f.close()

    leaderboardEmbed.add_field(name='Players', value=leaderboard)
    await ctx.respond(embed=leaderboardEmbed)

def myAnimeListRequest(mangaTitles, username, status):
    url = f'https://api.myanimelist.net/v2/users/{username}/mangalist?offset=0&limit=1000&status={status}'

    r = requests.get(url, headers = {'X-MAL-CLIENT-ID': CLIENT_ID})

    if 'data' not in r.json():
        return None

    mangaList = r.json()['data']

    if 'error' in mangaList:
        return None

    for manga in mangaList:
        mangaTitle = manga['node']['title']
        mangaTitles.append(mangaTitle)

    return mangaTitles

@bot.command(description='Sync MyAnimeList manga list.')
async def sync(ctx, username : str):
    await ctx.respond('The bot will DM you when sync is complete!')
    mangaTitles=[]
    mangaTitles = myAnimeListRequest(mangaTitles, username, 'reading')
    if mangaTitles == None:
        await ctx.respond(f'{username} is not a valid username on MyAnimeList.')
        return
    mangaTitles = myAnimeListRequest(mangaTitles, username, 'completed')
    if mangaTitles == None:
        await ctx.respond(f'{username} is not a valid username on MyAnimeList.')
        return 

    base_url = "https://api.mangadex.org"
    final_order_query = {'order[relevance]': 'desc'}

    mdexLst = []
    for i in range(len(mangaTitles)):

        mangaTitle = mangaTitles[i]
        r = requests.get(
            f"{base_url}/manga",
            params={
                **{
                    "limit": 1,
                    "title": mangaTitle,
                },
                **final_order_query,
                },
        )

        data = r.json()["data"]
        if data == []:
            continue
        manga = data[0]
        if manga['attributes']['originalLanguage'] != 'ja':
            continue
        manga_id = manga['id']
        if 'en' in manga['attributes']['title']:
            mangaTitle = manga['attributes']['title']['en']
        elif 'ja' in manga['attributes']['title']:
            mangaTitle = manga['attributes']['title']['ja']
        elif 'ko' in manga['attributes']['title']:
            mangaTitle = manga['attributes']['title']['ko']
        else:
            continue

        mdexLst.append((manga_id, mangaTitle))

    with open('data.json') as f:
        data = json.load(f)

    data['mal'][username.lower()] = mdexLst

    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

    f.close()

    user = ctx.author
    await user.send(f'Syncing is complete! You can now use `mal:{username}` as a parameter.')


# Tokens
dotenv.load_dotenv()
CLIENT_ID = str(os.getenv("CLIENT_ID"))
token = str(os.getenv("TOKEN"))
bot.run(token)
