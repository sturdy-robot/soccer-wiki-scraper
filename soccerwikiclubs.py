import json
import requests
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def parse_club_data(session: aiohttp.ClientSession, url: str, name: str) -> dict | None:
    async with session.get(url) as resp:
        if resp.status != 200:
            return None
        logging.debug(f'Requesting: {url}')
        page = await resp.text()
        soup = BeautifulSoup(page, 'html.parser')
        rows = soup.find_all('p', class_='player-info-subtitle mb-2')
        manager, nickname, medium_name, short_name, year_founded, stadium, league, location, country = [
            row.text for row in rows
        ]
        manager = manager.replace('Manager:', '').strip()
        nickname = nickname.replace('Nickname:', '').strip()
        medium_name = medium_name.replace('Medium Name:', '').strip()
        short_name = short_name.replace('Short Name:', '').strip()
        year_founded = year_founded.replace('Year Founded:', '').strip()
        stadium = stadium.replace('Stadium:', '').strip()
        league = league.replace('League:', '').strip()
        location = location.replace('Location:', '').strip()
        country = country.replace('Country:', '').strip()

        return {
            "name": name,
            "manager": manager,
            "nickname": nickname,
            "medium_name": medium_name,
            "short_name": short_name,
            "year_founded": year_founded,
            "stadium": stadium,
            "league": league,
            "location": location,
            "country": country,
        }


async def combine_club_data(clubs: list[dict]) -> list[dict]:
    _clubs = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for club in clubs:
            club_id = club["ID"]
            logging.debug(f'{club_id}: {club["Name"]}')
            url = f'https://en.soccerwiki.org/squad.php?clubid={club_id}'
            tasks.append(asyncio.ensure_future(parse_club_data(session, url, club["Name"])))

        _clubs = await asyncio.gather(*tasks)

    _clubs = list(filter(lambda x: x is not None, _clubs))
    _clubs.sort(key=lambda x: x['country'])
    return _clubs


async def main():
    with open('soccerdata.json', 'r') as fp:
        data = json.load(fp)
        clubs = data['ClubData']
        _clubs = await combine_club_data(clubs)
        with open('clubs.json', 'w') as fw:
            json.dump(_clubs, fw)


if __name__ == '__main__':
    logging.basicConfig(filename='soccerwikilogs.log', filemode='w', encoding='utf-8', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    asyncio.run(main())
