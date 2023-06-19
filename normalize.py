"""
Script to normalize data for Openfoot Manager

This grabs data from the clubs.json file that you get from the soccerwikiclubs.py and normalizes it to a format
that Openfoot Manager can use for definition files, or for a basic database of clubs.
"""
import logging
import json
import os
import re
import asyncio
import random
from soccerwikiclubs import main

FORMATION_STRINGS = [
    "3-4-3",
    "3-5-2",
    "3-6-1",
    "4-4-2",
    "4-3-3",
    "4-5-1",
    "5-4-1",
    "5-3-2",
]


def get_fifa_country_codes() -> dict:
    with open('fifa_country_codes.json', 'r') as fp:
        return json.load(fp)


def normalize_club_data(club: dict, country_codes: dict):
    stadium = club["stadium"]
    pattern = re.compile(r'\((\d+|\d{1,3}(,\d{3})*)(\.\d+)?\)')
    stadium_capacity = re.findall(pattern, stadium)
    if stadium_capacity:
        stadium_capacity = stadium_capacity[0][0]
        stadium = stadium.replace(f'({stadium_capacity})', '').strip()
        stadium_capacity = int(stadium_capacity.replace(',', '').strip())
    return {
        "name": club["name"],
        "country": country_codes[club["country"]],
        "location": club["location"],
        "stadium": stadium,
        "stadium_capacity": stadium_capacity,
        "default_formation": random.choice(FORMATION_STRINGS),
        "squads_def": {
            "mu": random.randint(45, 85),
            "sigma": random.randint(5, 35),
        }
    }


async def normalize():
    root = os.path.abspath(os.path.dirname(__file__))
    if not os.path.exists(os.path.join(root, 'clubs.json')):
        await main()

    _clubs = []
    with open('clubs.json', 'r') as fp:
        clubs = json.load(fp)

    for club in clubs:
        c = normalize_club_data(club, get_fifa_country_codes())
        _clubs.append(c)

    clubs.sort(key=lambda x: x['country'])

    with open('normalized.json', 'w') as fw:
        json.dump(_clubs, fw, indent=2)


if __name__ == '__main__':
    logging.basicConfig(filename='normalize.log', filemode='w', encoding='utf-8', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    asyncio.run(normalize())
