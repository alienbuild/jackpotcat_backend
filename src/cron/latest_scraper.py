import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import json

BASE_URL = "https://www.lottery.co.uk/lotto/results"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "lottery_results.json")

def parse_latest_results():
    """Fetch and parse the latest lottery results."""
    response = requests.get(BASE_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Locate the latest results
    result_box = soup.find('div', class_='resultBox')
    if not result_box:
        raise Exception("Could not find resultBox on the page.")

    # Extract draw date
    header = result_box.find('div', class_='latestHeader lotto')
    date_str = header.find('span', class_='smallerHeading').text.strip()
    date_str = remove_ordinal_suffix(date_str)
    draw_date = datetime.strptime(date_str, "%d %B %Y").strftime("%Y-%m-%d")

    # Extract numbers
    number_divs = result_box.find_all('div', class_='result lotto-ball floatLeft')
    numbers = [int(div.text.strip()) for div in number_divs]

    # Extract bonus ball
    bonus_ball_div = result_box.find('div', class_='result lotto-bonus-ball floatLeft')
    bonus_ball = int(bonus_ball_div.text.strip())

    # Extract jackpot
    jackpot_span = result_box.find('span', class_='resultJackpot')
    jackpot = parse_jackpot(jackpot_span.text.strip()) if jackpot_span else 0

    return {
        "draw_date": draw_date,
        "numbers": numbers,
        "bonus_ball": bonus_ball,
        "jackpot": jackpot
    }

def remove_ordinal_suffix(date_str):
    """Remove ordinal suffixes like '16th' from a date string."""
    import re
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', date_str)

def parse_jackpot(jackpot_str):
    """Convert jackpot string (e.g., '£4,026,427') to an integer."""
    import re
    cleaned = re.sub(r'[^\d]', '', jackpot_str)
    return int(cleaned)

def check_and_save_results():
    """Continuously check for new results until they are available."""
    while True:
        try:
            latest_results = parse_latest_results()
            print(f"Latest results: {latest_results}")

            # Load existing results
            if os.path.exists(OUTPUT_FILE):
                with open(OUTPUT_FILE, 'r') as f:
                    existing_results = json.load(f)
            else:
                existing_results = []

            # Check if results are already saved
            if any(r['draw_date'] == latest_results['draw_date'] for r in existing_results):
                print(f"Results for {latest_results['draw_date']} are already saved.")
                break  # Exit the loop once results are saved

            # Save new results
            existing_results.append(latest_results)
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(existing_results, f, indent=4)
            print(f"Results saved successfully for {latest_results['draw_date']}.")

            break  # Exit the loop after saving results
        except Exception as e:
            print(f"Error checking for results: {e}")
            print("Retrying in 5 minutes...")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    print("Starting to check for latest results...")
    check_and_save_results()
