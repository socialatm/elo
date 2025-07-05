import requests
from bs4 import BeautifulSoup
import csv
import os

STARTING_RATING = 1200
K_FACTOR = 32

class UfcEloCalculator:
    """
    A class to handle loading, updating, and calculating UFC fighter Elo ratings.
    """
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.fights = []
        self.urls = set()
        self.event_years = []
        self.every_event_year = []

        # Fighter stats dictionaries
        self.elo = {}
        self.peak_elo = {}
        self.number_of_wins = {}
        self.number_of_losses = {}
        self.number_of_draws = {}
        self.number_of_fights = {}
        self.strength_of_schedule = {}
        self.peak_elo_year = {}
        self.unbeaten_streak = {}
        self.last_5_fights = {}

        # Sorted results
        self.sorted_elo = {}
        self.sorted_peak_elo = {}
        self.sorted_strength_of_schedule = {}

        # New data from web scrape
        self.new_fights = []
        self.new_links = []
        self.new_years = []

        self._load_from_csv()

    def _load_from_csv(self):
        """Loads the initial fight database from the CSV file."""
        try:
            with open(self.csv_path, "r", newline='') as f:
                reader = csv.reader(f)
                all_events = {}
                for row in reader:
                    if not row: continue
                    loser, winner, method, year, link = row
                    if link not in all_events:
                        all_events[link] = {'year': year, 'fights': []}
                    all_events[link]['fights'].extend([loser, winner, method])

                for link, data in all_events.items():
                    self.urls.add(link)
                    self.event_years.append(data['year'])
                    self.fights.extend(data['fights'])
                    
                    num_fights_in_event = len(data['fights']) // 3
                    self.every_event_year.extend([data['year']] * num_fights_in_event)

        except FileNotFoundError:
            print(f"Warning: {self.csv_path} not found. Starting with an empty database.")

    def _generate_ufc_stats_path(self):
        """Generates a list of all completed UFC event URLs."""
        try:
            response = requests.get(url="http://ufcstats.com/statistics/events/completed", timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find_all('a', href=lambda href: href and 'event-details' in href)
            all_ufc_events_stats = [i['href'] for i in table if 'UFC' in i.text or 'The Ultimate Fighter' in i.text]
            all_ufc_events_stats.reverse()
            return all_ufc_events_stats
        except requests.RequestException as e:
            print(f"Error fetching event list: {e}")
            return []

    def _scraping(self, url):
        """Scrapes a single event page for fight results."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            happened = soup.find('i', class_="b-flag__text")
            if not (happened and (happened.text == 'win' or happened.text == 'draw' or happened.text == 'nc')):
                return None, None

            table = soup.find_all('a', class_="b-link b-link_style_black")
            ufc_fight_results = [i.text.strip() for i in table]
            ufc_fight_results.reverse()

            year_ = soup.find('li', class_='b-list__box-list-item')
            year = year_.text.strip()[-4:]

            status_tags = soup.find_all('i', class_="b-flag__text")
            status_list = [tag.text for i, tag in enumerate(status_tags) if tag.text in ('win', 'draw', 'nc') and i % 2 == 0]
            status_list.reverse()

            final_results = []
            for i in range(0, len(ufc_fight_results), 2):
                final_results.extend([ufc_fight_results[i], ufc_fight_results[i+1], status_list[i//2]])

            return final_results, year
        except (requests.RequestException, AttributeError, IndexError) as e:
            print(f"Error scraping {url}: {e}")
            return None, None

    def update_from_web(self):
        """Finds and scrapes new events not present in the local database."""
        print("Checking for new events...")
        all_event_links = self._generate_ufc_stats_path()
        self.new_links = [link for link in all_event_links if link not in self.urls]

        if not self.new_links:
            print("No new events found. Database is up to date.")
            return

        print(f"Found {len(self.new_links)} new events. Scraping...")
        for link in self.new_links:
            fight_results, event_year = self._scraping(link)
            if fight_results and event_year:
                self.new_fights.append(fight_results)
                self.new_years.append(event_year)
                self.fights.extend(fight_results)
                num_fights_in_event = len(fight_results) // 3
                self.every_event_year.extend([event_year] * num_fights_in_event)
        print("Scraping complete.")

    def calculate_elo(self):
        """Calculates Elo ratings for all fighters based on the full fight history."""
        print("Calculating Elo ratings...")
        fighter_set = {f for f in self.fights if f not in {'win', 'nc', 'draw'}}

        for fighter in fighter_set:
            self.elo[fighter] = STARTING_RATING
            self.peak_elo[fighter] = STARTING_RATING
            self.number_of_wins[fighter] = 0
            self.number_of_losses[fighter] = 0
            self.number_of_draws[fighter] = 0
            self.number_of_fights[fighter] = 0
            self.strength_of_schedule[fighter] = 0
            self.peak_elo_year[fighter] = 'N/A'
            self.unbeaten_streak[fighter] = 0
            self.last_5_fights[fighter] = []

        for i in range(0, len(self.fights), 3):
            fighter_a = self.fights[i]
            fighter_b = self.fights[i+1]
            status = self.fights[i+2]
            event_idx = i // 3

            # Ensure fighters exist in dicts, for late additions
            for f in [fighter_a, fighter_b]:
                if f not in self.elo: # Should not happen with pre-population, but safe
                    # Initialize new fighter
                    self.elo[f], self.peak_elo[f] = STARTING_RATING, STARTING_RATING
                    self.number_of_wins[f], self.number_of_losses[f], self.number_of_draws[f] = 0, 0, 0
                    self.number_of_fights[f], self.strength_of_schedule[f], self.unbeaten_streak[f] = 0, 0, 0
                    self.peak_elo_year[f] = 'N/A'
                    self.last_5_fights[f] = []

            self.strength_of_schedule[fighter_a] += self.elo[fighter_b]
            self.strength_of_schedule[fighter_b] += self.elo[fighter_a]

            transformed_rating_a = 10**(self.elo[fighter_a] / 400)
            transformed_rating_b = 10**(self.elo[fighter_b] / 400)
            expected_win_a = transformed_rating_a / (transformed_rating_a + transformed_rating_b)
            expected_win_b = 1 - expected_win_a

            if status == 'win':
                score_a, score_b = 0, 1
                self.number_of_losses[fighter_a] += 1
                self.number_of_wins[fighter_b] += 1
                self.unbeaten_streak[fighter_a] = 0
                self.unbeaten_streak[fighter_b] += 1
            elif status == 'draw':
                score_a, score_b = 0.5, 0.5
                self.number_of_draws[fighter_a] += 1
                self.number_of_draws[fighter_b] += 1
                self.unbeaten_streak[fighter_a] += 1
                self.unbeaten_streak[fighter_b] += 1
            else: # NC or other
                score_a, score_b = 0.5, 0.5 # Treat as a draw for Elo, but don't update records

            elo_change_a = K_FACTOR * (score_a - expected_win_a)
            elo_change_b = K_FACTOR * (score_b - expected_win_b)

            self.elo[fighter_a] += elo_change_a
            self.elo[fighter_b] += elo_change_b

            if status != 'nc':
                self.last_5_fights[fighter_a].append(elo_change_a)
                self.last_5_fights[fighter_b].append(elo_change_b)

            self.number_of_fights[fighter_a] += 1
            self.number_of_fights[fighter_b] += 1

            current_year = self.every_event_year[event_idx]
            if self.elo[fighter_a] > self.peak_elo[fighter_a]:
                self.peak_elo[fighter_a] = self.elo[fighter_a]
                self.peak_elo_year[fighter_a] = current_year
            if self.elo[fighter_b] > self.peak_elo[fighter_b]:
                self.peak_elo[fighter_b] = self.elo[fighter_b]
                self.peak_elo_year[fighter_b] = current_year

        for fighter in fighter_set:
            if self.number_of_fights[fighter] > 0:
                self.strength_of_schedule[fighter] /= self.number_of_fights[fighter]

        self.sorted_elo = {k: v for k, v in sorted(self.elo.items(), key=lambda item: item[1], reverse=True)}
        self.sorted_peak_elo = {k: v for k, v in sorted(self.peak_elo.items(), key=lambda item: item[1], reverse=True)}
        self.sorted_strength_of_schedule = {k: v for k, v in sorted(self.strength_of_schedule.items(), key=lambda item: item[1], reverse=True)}
        print("Elo calculation complete.")