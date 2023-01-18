import json
import logging
import re
import uuid
# import asyncio
# import aiohttp
from typing import Tuple, Optional
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_city_name(href):
    url = urljoin('https://en.wikipedia.org', href)
    page = requests.get(url)
    if page.status_code == 404:
        return None
    soup = BeautifulSoup(page.text, 'html.parser')
    title = soup.find('h1').text
    logging.debug(f'Getting stadium for {title}')
    pattern = re.compile(r'city of \w')
    return soup.find(pattern).text.replace('city of', '').strip()


def get_stadium(href) -> Tuple[Optional[str], Optional[str]]:
    url = urljoin('https://en.wikipedia.org', href)
    page = requests.get(url)
    if page.status_code == 404:
        logging.debug(f"Page {url} not found")
        return None, None
    soup = BeautifulSoup(page.text, 'html.parser')
    title = soup.find('h1').text
    logging.debug(f'Getting stadium for {title}')
    infobox = soup.find('table', class_="infobox")
    if infobox:
        df = pd.read_html(str(infobox))[0]
        df.to_dict()
        try:
            stadium = df.loc[df[0].isin(['Ground', 'Stadium'])].to_dict('records')[0].get(1)
        except (IndexError, KeyError):
            stadium = None
        try:
            pattern = re.compile(r'(\b\d[\d,.]*\b)')
            capacity = df.loc[df[0] == 'Capacity'].to_dict('records')[0].get(1)
            capacity = int(re.match(pattern, capacity).group(1).replace(',', '').replace('.', '')) # Formatting the capacity and remove brackets
        except (IndexError, KeyError):
            capacity = None
    else:
        stadium, capacity = None, None
    logging.debug(f"**{title}**: Stadium: {stadium}, Capacity: {capacity}")
    return stadium, capacity


def get_wiki_tables(soup: BeautifulSoup, url) -> list[dict]:
    if url == 'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_UEFA_countries':
        tables = soup.find_all('table')
    else:
        tables = soup.find_all('table', class_='sortable')
    clubs = []
    for table in tables:
        # Wikipedia is a bitch for consistency
        if url == 'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_UEFA_countries':
            for th in table.find_all('th', scope="row"):
                for club in th:
                    club_name = club.text.replace('(C)', '').replace('(R)', '').replace('(O)', '').replace('(D)', '').strip()
                    try:
                        url = club.find('a').get('href')
                    except AttributeError:
                        city = None
                        stadium, capacity = None, None
                    else:
                        page = requests.get(url)
                        soup = BeautifulSoup(page.text, 'html.parser')
                        city = None
                        stadium, capacity = get_stadium(url)
                    if club_name not in ['Africa','Asia','Europe', 'North,Central Americaand the Caribbean', 'Oceania', 'South America']: # wikipedia has these things in the page. Need to filter them out
                        clubs.append({
                            'id': uuid.uuid4().int,
                            'name': club_name,
                            'city': city,
                            'stadium_name': stadium,
                            'stadium_capacity': capacity,
                        })
        else:
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if not tds:
                    continue
                rows = [td.text.replace('(C)', '').replace('(R)', '').replace('(O)').strip() for td in tds]
                logging.debug(f'Rows: {rows}')

                if rows[0] == '':
                    continue

                if len(rows) > 2:
                    if url == 'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_CAF_countries':
                        club_name = rows[0]
                    else:
                        club_name = rows[1]

                    try:
                        if url == 'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_CAF_countries':
                            urls = tds[0].find_all('a')
                        else:
                            urls = tds[1].find_all('a')
                        if len(urls) > 1:
                            url_ = urls[1].get('href')
                        else:
                            url_ = urls[0].get('href')
                        stadium, capacity = get_stadium(url_)
                    except (AttributeError, IndexError):
                        url_ = None
                        stadium, capacity = None, None

                    if len(rows) == 3:
                        city = rows[2]
                    else:
                        if url_ is None:
                            city = None
                        else:
                            city = get_city_name(url_)
                else:
                    club_name = rows[0]
                    city = rows[1]

                    try:
                        urls = tds[0].find_all('a')
                        if len(urls) > 1:
                            url_ = urls[1].get('href')
                        else:
                            url_ = urls[0].get('href')
                        stadium, capacity = get_stadium(url_)
                    except (AttributeError, IndexError):
                        stadium, capacity = None, None

            clubs.append({
                'id': uuid.uuid4().int,
                'name': club_name,
                'city': city,
                'stadium_name': stadium,
                'stadium_capacity': capacity,
            })

    return clubs


def get_countries(soup: BeautifulSoup, url):
    if url == 'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_UEFA_countries':
        h2 = soup.find_all('h3')
    else:
        h2 = soup.find_all('h2')
    countries = [h.get_text().replace("[edit]", "") for h in h2 if
                 h.get_text().replace("[edit]", "") not in ["Contents", "External links", "See also",
                                                            "League ranking", "References", "Current champions",
                                                            "Navigation menu"]]
    return countries


def get_url_data(url) -> list[dict]:
    data = []
    logging.debug(f'Getting {url}')
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    countries = get_countries(soup, url)
    logging.debug(f'Countries: {countries}')
    clubs = get_wiki_tables(soup, url)
    for country, club in zip(countries, clubs):
        data.append({
            'name': country,
            'clubs': clubs
        })
    return data


def get_region_data(url):
    pattern = re.compile(r'https:\/\/en.wikipedia.org\/wiki\/List_of_top-division_football_clubs_in_(\w+)_countries')
    region = re.match(pattern, url).group(1)
    d = get_url_data(url)
    r = {
        "name": region,
        "countries": d,
    }

    with open(f'{region.lower()}.json', 'w') as fp:
        json.dump(r, fp)

    return r


def scrape_wiki_pages():
    urls = [
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_CAF_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_AFC_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_UEFA_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_CONCACAF_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_OFC_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_CONMEBOL_countries',
    ]
    data = {
        "regions": []
    }
    for url in urls:
        d = get_region_data(url)
        data["regions"].append(d)

    with open('clubs/clubs.json', 'w') as fp:
        json.dump(data, fp)


logging.basicConfig(filename='clubs.log', filemode='w', encoding='utf-8', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('Started')
scrape_wiki_pages()
