import discord
import requests
import numpy.random as random
import dotenv
import os

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
    final_order_query = dict()
    # { "order[rating]": "desc", "order[followedCount]": "desc" }
    for key, value in order.items():
        final_order_query[f"order[{key}]"] = value

    if difficulty == 'easy':
        offset = 0
    elif difficulty == 'medium':
        offset = 100
    elif difficulty == 'hard':
        offset = 200

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
        mangaTitles.append(manga['attributes']['title'])
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

        if len(data) == 0:
            print('Chapter has 0 pages, retrying...')
            return None
            
        randomPageIdx = random.randint(0, len(data)-1)
        
        fullURL = f'{host}/data/{chapter_hash}/{data[randomPageIdx]}'
        fullURLs.append(fullURL)

    return fullURLs

def randomImg(difficulty):

    manga_id, mangaTitles = randomMangas(difficulty)
    fullURLs = randomPages(manga_id)
    while fullURLs == None:
        manga_id, mangaTitles = randomMangas(difficulty)
        fullURLs = randomPages(manga_id)
    return fullURLs, mangaTitles


bot = discord.Bot()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command()
async def hello(ctx, name: str = None):
    name = name or ctx.author.name
    await ctx.respond(f"bruh {name}!")

@bot.command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")


play = bot.create_group("play", "Generate random image")

@bot.slash_command(description='Play an image game')
@discord.option(
    "difficulty",
    description="Enter the difficulty",
    choices=['easy', 'medium', 'hard'],
    default='easy')

async def pg(ctx, difficulty : str):

    fullURLs, mangaTitles = randomImg(difficulty)
    fullURL = fullURLs[0]

    if difficulty == 'easy':
        description = "Random Page from Top 1-100 Manga"
    elif difficulty == 'medium':
        description = "Random Page from Top 101-200 Manga"
    elif difficulty == 'hard':
        description = "Random Page from Top 201-300 Manga"

    embed = discord.Embed(
        title="Cap 1",
        description=description,
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )
    embed.set_image(url=fullURL)
    embed.set_footer(text=mangaTitles[0])
    await ctx.respond(embed=embed)

dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
bot.run(token)