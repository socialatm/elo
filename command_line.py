import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
import os
import argparse 

parser = argparse.ArgumentParser(description="Ranks UFC fighters by the Elo-rating system")
parser.add_argument("-n", "--number", dest="N", type=int, default=15, help="Number of fighters to be displayed (default: %(default)s)")
args = parser.parse_args()

def generate_ufc_stats_path():
    response = requests.get(url="http://ufcstats.com/statistics/events/completed")
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find_all('a')
    all_ufc_events_stats = []
    for i in table:
        if 'UFC' in i.text or 'The Ultimate Fighter' in i.text:
            all_ufc_events_stats.append(i['href'])
    all_ufc_events_stats.reverse()
    return all_ufc_events_stats

def scrapping(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    ###checking if the event has happened

    happened = soup.find('i', class_="b-flag__text")
    try:
        if (happened.text == 'win' or happened.text == 'draw' or happened.text == 'nc'):

            table = soup.find_all('a', class_="b-link b-link_style_black")
            ufc_fight_results = [i.text.strip() for i in table]
            ufc_fight_results.reverse()

            year_ = soup.find('li', class_='b-list__box-list-item')
            year = year_.text.strip()[-4::]

            ###checking for draws or NC
            status = soup.find_all('i', class_="b-flag__text")
            status_list = []
            cont_draws = 2
            cont_nc = 2
            for i in status:
                if i.text == 'draw':
                    if cont_draws % 2 == 0:
                        status_list.append(i.text)
                        cont_draws += 1
                    else:
                        cont_draws += 1
                        pass
                elif i.text == 'nc':
                    if cont_nc % 2 == 0:
                        status_list.append(i.text)
                        cont_nc += 1
                    else:
                        cont_nc += 1
                else:

                    status_list.append(i.text)
            status_list.reverse()

            aux = 2
            cont = 0
            for i in status_list:
                ufc_fight_results.insert(aux+cont,i)
                aux += 2
                cont +=1

            return ufc_fight_results, year
    except AttributeError:
        return None, None
every_ufc_fight = []
urls = []
event_years = []
### RETURNS A LIST OF ALL FIGHTERS FROM THE SPECIFIED EVENT. (LOSER, WINNER, LOSER, WINNER, ...)

# Get the directory where the current script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the full path to the CSV file
csv_path = os.path.join(script_dir, "csv", "UFC_db.csv")

try:
    with open(csv_path, "r", newline='') as f:
        reader = csv.reader(f)
        link_check = 'No link available'
        instance = []
        # Skip header if it exists
        # next(reader, None) 
        for row in reader:
            if not row: continue # skip empty rows
            loser, winner, method, year, link = row

            urls.append(link)

            if link == link_check:
                instance.extend([loser, winner, method])
            else:
                if instance:
                    every_ufc_fight.append(instance)
                event_years.append(year)
                instance = [loser, winner, method]
                link_check = link
        if instance:
            event_years.append(year)
            every_ufc_fight.append(instance)
except FileNotFoundError:
    print(f"Warning: {csv_path} not found. Starting with an empty database.")

every_ufc_fight = every_ufc_fight[2:]
event_years = event_years[1:]
time = 0

'''
links = generate_ufc_stats_path()
for i in links:
    try:
        print(time)
        print(i)
        every_ufc_fight.append(scrapping(i))
        time += 1

    except:
        pass
'''
### UFC FIGHTS DATA BASE

fights = []
for i in every_ufc_fight:
    for e in i:
        fights.append(e)

''' ###GETTING EVERY EVENT'S YEAR !!!IMPORTANTE FOR MANUAL CHANGES
for i in urls:
    scrapping(i)
    event_years.append(year)
    print(len(event_years))
print(event_years)'''

every_event_year = []
def generate_ufc_fighters():
    fighter_set = set()
    for i in fights:
        if i not in {'win', 'nc', 'draw'}:
            fighter_set.add(i)
    return list(fighter_set)

starting_rating = 1200
k_factor = 32
elo = {}
peak_elo = {}
number_of_wins = {}
number_of_losses = {}
number_of_draws = {}
number_of_fights = {}
strength_of_schedule = {} 
peak_elo_year = {}
unbeaten_streak = {}
last_5_fights = {}

def generate_elo():
    all_fighters = generate_ufc_fighters()
    for i in all_fighters:
        elo.update({i:starting_rating})
        number_of_wins.update({i:0})
        number_of_losses.update({i:0})
        number_of_draws.update({i:0})
        number_of_fights.update({i:0})
        unbeaten_streak.update({i:0})
        peak_elo.update({i:starting_rating})
        peak_elo_year.update({i: 'Never achieved'})
        strength_of_schedule.update({i:0})
        last_5_fights.update({i:[0,0,0,0,0]})

    aux = 0
    cont = 0

    #print(fights)

    while (aux + 2) < len(fights):

        fighter_a = fights[aux]  ##loser
        fighter_b = fights[aux+1]  ##winner
        status = fights[aux + 2]
        
        strength_of_schedule[fighter_a] += elo[fighter_b]
        strength_of_schedule[fighter_b] += elo[fighter_a]

        if status == 'win':
            transformed_rating_a = 10**((elo[fighter_a])/400)
            transformed_rating_b = 10**((elo[fighter_b])/400)

            expected_win_a = transformed_rating_a/(transformed_rating_a + transformed_rating_b)
            expected_win_b = transformed_rating_b/(transformed_rating_a + transformed_rating_b)

            elo[fighter_a] += k_factor*(0 - expected_win_a)
            elo[fighter_b] += k_factor*(1 - expected_win_b)

            number_of_wins[fighter_b] += 1
            number_of_losses[fighter_a] += 1

            unbeaten_streak[fighter_b] += 1
            unbeaten_streak[fighter_a] = 0

            last_5_fights[fighter_a].append(k_factor*(0 - expected_win_a))
            last_5_fights[fighter_b].append(k_factor*(1 - expected_win_b))

        elif status == 'draw':
            elo[fighter_a] += k_factor*(0.5 - expected_win_a) 
            elo[fighter_b] += k_factor*(0.5 - expected_win_b)

            number_of_draws[fighter_b] += 1
            number_of_draws[fighter_a] += 1

            unbeaten_streak[fighter_b] += 1
            unbeaten_streak[fighter_a] += 1

            last_5_fights[fighter_a].append(k_factor*(0.5 - expected_win_a))
            last_5_fights[fighter_b].append(k_factor*(0.5 - expected_win_b))

        ### PEAK ELO
        if elo[fighter_b] > peak_elo[fighter_b]:
            peak_elo.update({fighter_b:elo[fighter_b]})
            peak_elo_year.update({fighter_b:every_event_year[cont]})
        if elo[fighter_a] > peak_elo[fighter_a]:
            peak_elo.update({fighter_a:elo[fighter_a]})
            peak_elo_year.update({fighter_a:every_event_year[cont]})

        number_of_fights[fighter_a] += 1
        number_of_fights[fighter_b] += 1

        aux += 3
        cont += 1
    global peak_elo_sorted
    global sorted_dictionary
    global sorted_strength_of_schedule

    for i in all_fighters:
            if number_of_fights[i] > 0:
                strength_of_schedule[i] = strength_of_schedule[i] / number_of_fights[i]

    sorted_strength_of_schedule = {k: v for k, v in sorted(strength_of_schedule.items(), key=lambda item: item[1])}
    peak_elo_sorted = {k: v for k, v in sorted(peak_elo.items(), key=lambda item: item[1])}
    sorted_dictionary = {k: v for k, v in sorted(elo.items(), key=lambda item: item[1])}
    return sorted_dictionary

def update():
    global sorted_dictionary_updated
    nl = generate_ufc_stats_path()
    existing_urls = set(urls)
    new_links = [i for i in nl if i not in existing_urls]

    if len(new_links) > 0:
        print(f"Found {len(new_links)} new event(s). Appending to CSV database...")
        # Open the CSV in append mode to add new fights
        with open(csv_path, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Process oldest new events first to maintain chronological order
            for link in reversed(new_links):
                fight_results, event_year = scrapping(link)
                if fight_results and event_year:
                    print(f"  - Scraping and writing data for: {link}")
                    # Update in-memory lists for the current script run
                    fights.extend(fight_results)
                    every_ufc_fight.append(fight_results)
                    event_years.append(event_year)
                    urls.append(link)

                    # Write each new fight to the CSV file
                    aux = 0
                    while (aux + 2) < len(fight_results):
                        loser, winner, method = fight_results[aux], fight_results[aux+1], fight_results[aux+2]
                        writer.writerow([loser, winner, method, event_year, link])
                        aux += 3
        print("CSV database update complete.")

    cont = 0
    for event in every_ufc_fight:
        number_of_events = int(len(event)/3)
        for i in range(number_of_events):
            every_event_year.append(event_years[cont])
        cont += 1

    generate_elo()
    sorted_dictionary_updated = {k: v for k, v in sorted(elo.items(), key=lambda item: item[1])}
    return sorted_dictionary_updated

update()

# load sorted_dictionary_updated into a DataFrame named display
display = pd.DataFrame(list(sorted_dictionary_updated.items()), columns=['Fighter', 'Elo Rating'])

# Add additional stats from the other dictionaries, similar to the verbose output
fighters = display['Fighter']
display['Peak Elo'] = fighters.map(peak_elo)
display['Record'] = fighters.map(lambda f: f"{number_of_wins[f]}-{number_of_losses[f]}-{number_of_draws[f]}")
display['Unbeaten Streak'] = fighters.map(unbeaten_streak)
display['Strength of Schedule'] = fighters.map(strength_of_schedule)

# Sort the DataFrame by Elo Rating in descending order to show the top fighters first
display = display.sort_values(by='Elo Rating', ascending=False)

# Set the fighter's name as the index and format the output
display = display.set_index('Fighter')
pd.options.display.float_format = '{:.1f}'.format

print(f"\nTop {args.N} fighters:")
print(display.head(args.N))
