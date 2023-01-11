import json
import logging
import re
from urllib.parse import urljoin

import requests
import wptools
from bs4 import BeautifulSoup


# Enter wiki page -> Scrape tables -> For each table row, get the link to the team -> Enter team page -> Get stadium infobox

def get_city_name(href):
    url = urljoin('https://en.wikipedia.org', href)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    logging.debug(f'Getting city name for {url}')
    pattern = re.compile(r'city of \w')
    return soup.find(pattern).text.strip('city of').strip()


def get_stadium(href):
    url = urljoin('https://en.wikipedia.org', href)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    title = soup.find('h1').text
    logging.debug(f'Getting stadium for {title}')
    p = wptools.page(title).get_parse()
    if p.data['infobox'] is not None:
        stadium = p.data['infobox'].get('ground')
        capacity = p.data['infobox'].get('capacity')
        return stadium, capacity
    return None, None


def get_wiki_tables(soup: BeautifulSoup):
    tables = soup.find_all('table', class_='sortable')
    clubs = []
    for table in tables:
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if not tds:
                continue
            rows = [td.text.strip() for td in tds]
            logging.debug(f'Rows: {rows}')
            club_name = ''
            city = ''
            stadium = ''
            capacity = ''
            if len(rows) > 2:
                club_name = rows[1]
                url = tds[1].find('a').get('href')
                stadium, capacity = get_stadium(url)
                if len(rows) == 3:
                    city = rows[2]
                else:
                    city = get_city_name(url)
            else:
                club_name = rows[0]
                city = rows[1]
                url = tds[0].find('a').get('href')
                stadium, capacity = get_stadium(url)
            clubs.append({
                'name': club_name,
                'city': city,
                'stadium_name': stadium,
                'stadium_capacity': capacity,
            })

    return clubs


def get_countries(soup: BeautifulSoup):
    h2 = soup.find_all('h2')
    countries = [h.get_text().replace("[edit]", "") for h in h2 if
                 h.get_text().replace("[edit]", "") not in ["Contents", "External links", "See also",
                                                            "League ranking", "References", "Current champions",
                                                            "Navigation menu"]]
    return countries


def scrape_wiki_pages():
    urls = [
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_CAF_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_AFC_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_UEFA_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_CONCACAF_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_OFC_countries',
        'https://en.wikipedia.org/wiki/List_of_top-division_football_clubs_in_CONMEBOL_countries',
    ]
    data = []
    for url in urls:
        logging.debug(f'Getting {url}')
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        countries = get_countries(soup)
        logging.debug(f'Countries: {countries}')
        clubs = get_wiki_tables(soup)
        for country, club in zip(countries, clubs):
            data.append({
                'name': country,
                'clubs': clubs
            })

    with open('data.json', 'w') as fp:
        json.dump(data, fp)


logging.basicConfig(filename='clubs.log', encoding='utf-8', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('Started')
scrape_wiki_pages()
