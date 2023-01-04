import discord
import requests
import numpy.random as random

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

print(randomImg(2))