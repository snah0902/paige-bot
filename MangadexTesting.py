import requests
import os
import dotenv
import json
import numpy.random as random

dotenv.load_dotenv()
CLIENT_ID = str(os.getenv("CLIENT_ID"))

def myAnimeListRequest(mangaTitles, username, status):
    url = f'https://api.myanimelist.net/v2/users/{username}/mangalist?offset=0&limit=1000&status={status}'

    r = requests.get(url, headers = {'X-MAL-CLIENT-ID': CLIENT_ID})

    mangaList = r.json()['data']

    if 'error' in mangaList:
        return None

    for manga in mangaList:
        mangaTitle = manga['node']['title']
        mangaTitles.append(mangaTitle)

    return mangaTitles

def sync(username):

    mangaTitles=[]
    mangaTitles = myAnimeListRequest(mangaTitles, username, 'reading')
    if mangaTitles == None:
        print(f'{username} is not a valid username on MyAnimeList.')
    mangaTitles = myAnimeListRequest(mangaTitles, username, 'completed')
    if mangaTitles == None:
        print(f'{username} is not a valid username on MyAnimeList.')

    base_url = "https://api.mangadex.org"
    final_order_query = {'order[relevance]': 'desc'}

    mdexLst = []

    print(len(mangaTitles))

    i = 0
    for i in range(len(mangaTitles)):

        print(i)
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

    data['mal'][username] = mdexLst

    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

    f.close()

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

username = 'rtdrtd67'

sync(username)
malUsers = ['rtdrtd67']

# manga_id, mangaTitles = randomMangaWithMAL(malUsers)
# print(manga_id, mangaTitles)