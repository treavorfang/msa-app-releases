import requests
from bs4 import BeautifulSoup
import time
import json
import csv
import configparser
from pathlib import Path

# Constants
BASE_URL = "https://www.gsmarena.com/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class GSMArenaScraper:
    def __init__(self):
        self.brands = []
        self.selected_brands = []
        self.results = {}

    def get_all_brands(self):
        """Get all brands with device counts"""
        url = f"{BASE_URL}makers.php3"
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        brand_table = soup.find('table')
        for link in brand_table.find_all('a'):
            brand_text = link.text.strip()
            # Remove " devices" part and the count before it
            brand_name = brand_text.split(' devices')[0].strip()
            # If the brand name ends with numbers (device count), remove them
            import re
            brand_name = re.sub(r'\d+$', '', brand_name).strip()

            brand_url = BASE_URL + link['href']
            self.brands.append({
                'name': brand_name,         # Clean brand name
                'full_name': brand_text,    # Original with count
                'url': brand_url
            })
        
        self.brands.sort(key=lambda x: x['name'])

    def get_all_models(self, brand_url):
        """Get all models for a brand, including all pagination"""
        models = []
        page_url = brand_url

        while page_url:
            try:
                print(f"Processing page: {page_url}")
                response = requests.get(page_url, headers=HEADERS)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Get devices from makers section
                makers_div = soup.find('div', class_='makers')
                if makers_div:
                    for link in makers_div.find_all('a'):
                        model_name = link.find('strong').text.strip() if link.find('strong') else link.text.strip()
                        models.append(model_name)

                # Find the "next" page — works even if no class="pages-next"
                nav_pages = soup.find('div', class_='nav-pages')
                if nav_pages:
                    active_page = nav_pages.find('strong')  # current page number
                    if active_page:
                        next_link = active_page.find_next_sibling('a')
                        page_url = BASE_URL + next_link['href'] if next_link else None
                    else:
                        page_url = None
                else:
                    page_url = None

                time.sleep(0.5)

            except Exception as e:
                print(f"Error: {e}")
                break

        return models

    def display_brands(self):
        """Show interactive brand selection"""
        print("\nAvailable Brands:")
        for i, brand in enumerate(self.brands, 1):
            print(f"{i}. {brand['full_name']}")

    def select_brands(self):
        """Let user select brands"""
        selections = input("\nEnter brand numbers (comma separated) or 'all': ")
        if selections.lower() == 'all':
            self.selected_brands = self.brands
            return
        
        for num in selections.split(','):
            try:
                self.selected_brands.append(self.brands[int(num)-1])
            except (ValueError, IndexError):
                pass

    def scrape_selected(self):
        """Scrape selected brands"""
        total = len(self.selected_brands)
        for i, brand in enumerate(self.selected_brands, 1):
            print(f"\n[{i}/{total}] Scraping {brand['full_name']}...")
            models = self.get_all_models(brand['url'])
            self.results[brand['name']] = models
            print(f"Found {len(models)} devices")
            time.sleep(1)

    def save_results(self, format_choice='txt'):
        """Save in selected format"""
        filename = f"gsmarena_results.{format_choice}"
        if format_choice == 'txt':
            with open(filename, 'w', encoding='utf-8') as f:
                for brand, models in self.results.items():
                    f.write(f"[{brand}]\n")  # Use clean brand name without count
                    for model in models:
                        f.write(f"{model}\n")
                    f.write("\n")

        elif format_choice == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2)

        elif format_choice == 'ini':
            with open(filename, 'w', encoding='utf-8') as f:
                for brand, models in self.results.items():
                    f.write(f"[{brand}]\n")
                    for model in models:
                        f.write(f"{model}\n")
                    f.write("\n")

        elif format_choice == 'csv':
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Brand', 'Model'])
                for brand, models in self.results.items():
                    for model in models:
                        writer.writerow([brand, model])

        print(f"\nResults saved to {filename}")


    def choose_format(self):
        """Let user select output format"""
        print("\nSelect output format:")
        print("1. Text (.txt)")
        print("2. JSON (.json)")
        print("3. INI config (.ini)")
        print("4. CSV (Excel compatible)")
        
        choice = input("Enter format number (1-4): ")
        formats = {1: 'txt', 2: 'json', 3: 'ini', 4: 'csv'}
        return formats.get(int(choice), 'txt')

    def run(self):
        print("=== GSMArena Universal Scraper ===")
        print("Loading brand list...")
        self.get_all_brands()
        self.display_brands()
        self.select_brands()
        
        if not self.selected_brands:
            print("No brands selected!")
            return
        
        print(f"\nSelected {len(self.selected_brands)} brands:")
        for brand in self.selected_brands:
            print(f"- {brand['full_name']}")
        
        confirm = input("\nStart scraping? (y/n): ")
        if confirm.lower() != 'y':
            return
        
        self.scrape_selected()
        format_choice = self.choose_format()
        self.save_results(format_choice)

if __name__ == "__main__":
    scraper = GSMArenaScraper()
    scraper.run()