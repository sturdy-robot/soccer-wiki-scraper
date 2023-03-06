from tabulate import tabulate
from operator import itemgetter
import pandas as pd
import requests
import pycountry
from textwrap import dedent
from bs4 import BeautifulSoup


page = requests.get("https://en.wikipedia.org/wiki/2018_FIFA_World_Cup_squads")
soup = BeautifulSoup(page.text, 'html.parser')
h3 = soup.find_all('h3')
country_names = [h.text.replace('[edit]', '').strip() for h in h3[:32]]
table_soup = soup.find_all('table', class_='sortable')

tables = pd.read_html(str(table_soup))
table_index = 0
while table_index < 32:
    table = tables[table_index][['No.', 'Pos.', 'Player', 'Caps', 'Club']]
    players = table.values.tolist()
    fmt_pl = []
    for player in players:
        player_name = player[2].replace('(captain)', '(c)')
        player_pos = 0
        if player[1] == "DF":
            player_pos = 1
        elif player[1] == "MF":
            player_pos = 2
        elif player[1] == "FW":
            player_pos = 3
        formatted_players = [f'({player[0]:02})', player_pos, f'{player_name}', f'##', f'{player[3]}', f'{player[4]}\n']
        fmt_pl.append(formatted_players)

    fmt_pl.sort(key=itemgetter(1))
    for i, fmt in enumerate(fmt_pl):
        if fmt[1] == 0:
            fmt_pl[i][1] = "GK"
        elif fmt[1] == 1:
            fmt_pl[i][1] = "DF"
        elif fmt[1] == 2:
            fmt_pl[i][1] = "MF"
        elif fmt[1] == 3:
            fmt_pl[i][1] = "FW"
    country_name = country_names[table_index]
    file_country_name = country_name.lower().replace(' ', '-')
    country_code = ''
    country_official_code = ''
    if country_name == 'England':
        country_code = 'en'
        country_official_code = 'ENG'
    elif country_name == 'Wales':
        country_code = 'wal'
        country_official_code = 'WAL'
    elif country_name == 'Germany':
        country_name = 'Deutschland'
        country_code = 'de'
        country_official_code = 'GER'
        file_country_name = 'deutschland'
    elif country_name == 'Spain':
        country_name = 'España'
        country_code = 'es'
        country_official_code = 'ESP'
        file_country_name = 'espana'
    else:
        cc = pycountry.countries.search_fuzzy(country_name)[0]
        country_code = cc.alpha_2.lower()
        country_official_code = cc.alpha_3
    with open(f'squads/{country_code}-{file_country_name}.txt', 'w') as f:
        f.write(dedent(f"""
        ##############################
        # {country_name} ({country_official_code}) 
        #   - {len(fmt_pl)} players
        \n"""))
        f.write(tabulate(fmt_pl, tablefmt='plain', numalign='right'))
    table_index += 1