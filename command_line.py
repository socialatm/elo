import csv
import os
import argparse
from elo_logic import UfcEloCalculator

def print_elo_ranking(calculator, num_fighters, verbose=False):
    """Prints the Elo ranking to the console."""
    if not verbose:
        print("\n--- UFC Elo Rankings ---")
        for i, (fighter, elo) in enumerate(list(calculator.sorted_elo.items())[:num_fighters]):
            print(f"{i+1:2d}. {fighter:<25} {elo:.1f}")
    else:
        print("\n--- UFC Elo Rankings (Verbose) ---")
        header = (
            f"{'Rank':<5} | {'Fighter':<25} | {'Elo':>8} | {'Peak Elo':>9} | "
            f"{'Record':<10} | {'Streak':>6} | {'Avg Opp Elo':>12}"
        )
        print(header)
        print("-" * len(header))
        
        for i, (fighter, elo) in enumerate(list(calculator.sorted_elo.items())[:num_fighters]):
            record = (
                f"{calculator.number_of_wins.get(fighter, 0)}-"
                f"{calculator.number_of_losses.get(fighter, 0)}-"
                f"{calculator.number_of_draws.get(fighter, 0)}"
            )
            peak = calculator.peak_elo.get(fighter, 0)
            streak = calculator.unbeaten_streak.get(fighter, 0)
            sos = calculator.strength_of_schedule.get(fighter, 0)
            
            print(
                f"{i+1:<5} | {fighter:<25} | {elo:>8.1f} | {peak:>9.1f} | "
                f"{record:<10} | {streak:>6} | {sos:>12.1f}"
            )

def main():
    """Main execution function for the command-line tool."""
    parser = argparse.ArgumentParser(description="Ranks UFC fighters by the Elo-rating system")
    parser.add_argument("-n", "--number", type=int, default=15, help="Number of fighters to be displayed (default: %(default)s)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output with more columns")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "csv", "UFC_db.csv")

    # 1. Initialize the calculator (loads data from CSV)
    calculator = UfcEloCalculator(csv_path)

    # 2. Update with new fights from the web
    calculator.update_from_web()

    # 3. Calculate Elo ratings for all fights
    calculator.calculate_elo()

    # 4. Print the results based on user arguments
    print_elo_ranking(calculator, args.number, args.verbose)

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
    global new_fights
    global new_links
    global new_years
    global sorted_dictionary_updated
    nl = generate_ufc_stats_path()
    new_years = []
    new_links = []
    new_fights = []
    existing_urls = set(urls)
    new_links = [i for i in nl if i not in existing_urls]

    if len(new_links) > 0:
        for link in new_links:
            fight_results, event_year = scrapping(link)
            if fight_results and event_year:
                new_fights.append(fight_results)
                new_years.append(event_year)
                fights.extend(fight_results)
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

def print_last_items(dict_, x):
    cont = 1
    items = list(dict_.items())[-x:]
    for key, value in reversed(items):
        print(f"{cont}° - {key}: {value:.1f}")
        cont += 1

def print_last_items_verbose(x):
    cont = 1
    items = list(sorted_dictionary_updated.items())[-x:]
    print("Rank  | Fighter                  | Elo Rating | Peak Elo | Record   |Streak | Avg. Opp. Elo")
    print("------|--------------------------|------------|----------|----------|-------|--------------")
    for key, value in reversed(items):
        peak_elo_value = peak_elo[key] if key in peak_elo else "N/A"  # Handle cases where peak_elo is not available
        fighter_info = f"{cont}°".ljust(6) + "| " + key.ljust(25) + "| " + f"{value:.1f}".ljust(11) + "| " + \
                       f"{peak_elo_value:.1f}".ljust(9) + "| " + f"{number_of_wins[key]}-{number_of_losses[key]}-{number_of_draws[key]}".ljust(9) + "| " + \
                       f"{unbeaten_streak[key]}".ljust(6) + "| " + f"{strength_of_schedule[key]:.1f}"
        print(fighter_info)
        cont += 1

if args.verbose:
    print_last_items_verbose(args.N)
else:
    print_last_items(sorted_dictionary_updated, args.N)
