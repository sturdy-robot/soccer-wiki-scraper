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
from soccerwikiclubs import main


def normalize_club_data(club: dict):
    stadium = club["stadium"]
    pattern = re.compile(r'\((\d+|\d{1,3}(,\d{3})*)(\.\d+)?\)')
    stadium_capacity = re.findall(pattern, stadium)
    if stadium_capacity:
        stadium_capacity = stadium_capacity[0][0]
        stadium = stadium.replace(f'({stadium_capacity})', '').strip()
        stadium_capacity = int(stadium_capacity.replace(',', '').strip())
    return {
        "name": club["name"],
        "country": club["country"],
        "stadium": stadium,
        "stadium_capacity": stadium_capacity
    }


async def normalize():
    root = os.path.abspath(os.path.dirname(__file__))
    if not os.path.exists(os.path.join(root, 'clubs.json')):
        await main()

    _clubs = []
    with open('clubs.json', 'r') as fp:
        clubs = json.load(fp)

        for club in clubs:
            c = normalize_club_data(club)
            _clubs.append(c)

    with open('normalized.json', 'w') as fw:
        json.dump(_clubs, fw)


if __name__ == '__main__':
    logging.basicConfig(filename='normalize.log', filemode='w', encoding='utf-8', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    asyncio.run(normalize())
