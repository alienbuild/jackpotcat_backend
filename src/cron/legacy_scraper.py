import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

BASE_URL = "https://www.lottery.co.uk"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "lottery_results.json")

def initialize_output_file():
    """Clear the contents of the JSON file."""
    with open(OUTPUT_FILE, 'w') as f:
        f.write('[]')  # Initialize with an empty array

def remove_ordinal_suffix(date_str):
    """Remove ordinal suffixes like '16th' from a date string."""
    import re
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', date_str)

def parse_jackpot(jackpot_str):
    """Convert jackpot string (e.g., '£4,026,427') to an integer."""
    import re
    if not jackpot_str:
        return 0  # Default to 0 if the jackpot is missing
    cleaned = re.sub(r'[^\d]', '', jackpot_str)
    return int(cleaned)

def scrape_year_results(year_url):
    results = []
    try:
        response = requests.get(year_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Locate the table
        table = soup.find('table', class_='table lotto mobFormat')
        if not table:
            print(f"No table found on {year_url}")
            return []

        # Iterate through the rows in the table directly
        rows = table.find_all('tr')[1:]  # Skip the header row
        for row in rows:
            try:
                # Extract the draw date
                date_td = row.find_all('td')[0]
                date_str = date_td.find('a').text.strip()
                date_str = remove_ordinal_suffix(date_str)
                draw_date = datetime.strptime(date_str, "%A %d %B %Y").strftime("%Y-%m-%d")

                # Extract the numbers
                results_td = row.find_all('td')[1]
                numbers = [int(div.text.strip()) for div in results_td.find_all('div', class_='result')]
                main_numbers = numbers[:-1]
                bonus_ball = numbers[-1]

                # Extract the jackpot
                jackpot_td = row.find_all('td')[2]
                jackpot_strong = jackpot_td.find('strong')
                jackpot_str = jackpot_strong.text.strip() if jackpot_strong else None
                jackpot = parse_jackpot(jackpot_str)

                # Append the result
                results.append({
                    "draw_date": draw_date,
                    "numbers": main_numbers,
                    "bonus_ball": bonus_ball,
                    "jackpot": jackpot
                })
            except Exception as e:
                print(f"Error parsing row: {e}")
    except Exception as e:
        print(f"Error scraping year URL {year_url}: {e}")
    return results

def get_lottery_results(archive_url):
    all_results = []
    try:
        # Initialize the output file
        initialize_output_file()

        response = requests.get(archive_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract year links
        year_links = soup.select('ul.bullet li a')
        year_urls = [BASE_URL + link['href'] for link in year_links]

        print(f"Found year URLs: {year_urls}")

        # Scrape results for each year
        for year_url in year_urls:
            print(f"Scraping year: {year_url}")
            year_results = scrape_year_results(year_url)
            all_results.extend(year_results)

        # Save all results to JSON
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(all_results, f, indent=4)
        print(f"Scraping complete. Results saved to {OUTPUT_FILE}.")

    except Exception as e:
        print(f"Error occurred during scraping: {e}")

if __name__ == "__main__":
    archive_url = f"{BASE_URL}/lotto/results/archive-2024"
    get_lottery_results(archive_url)
