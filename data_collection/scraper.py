import csv
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup

# Function to scrape the main fragrance list
def scrape_fragrance_links(driver):
    base_url = 'https://www.wikiparfum.com'
    links_scraped = []
    links_count = 0  # Track the number of links scraped

    driver.get('https://www.wikiparfum.com/en/fragrances')

    while True:
        time.sleep(2)  # Wait for the page to load

        # Scrape the current items
        items = driver.find_elements(By.CSS_SELECTOR,
                                     'div.col-span-4.sm\\:col-span-2.md\\:col-span-4.lg\\:col-span-3.xl\\:col-span-2')

        if not items:
            break  # Break the loop if no items are found

        for item in items:
            link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
            if link not in links_scraped:  # Avoid duplicate links
                links_scraped.append(link)
                links_count += 1

        print(f'Page scraped, found {len(items)} items. Total links scraped: {links_count}')

        # Save to CSV every 500 links
        if links_count % 500 == 0:
            print(f"Saving CSV with {links_count} links...")
            save_to_csv(links_scraped)

        # Check if we need to wait due to request limit (simulated here)
        if links_count % 100 == 0:  # Adjust this as needed
            print("Waiting due to rate-limiting or request limit...")
            time.sleep(5)  # Wait for 5 seconds (adjust as needed)

        # Click the "Load More" button
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[text()='Load more']")))

            button = driver.find_element(By.XPATH, "//button[text()='Load more']")

            # Force click the "Load More" button, regardless of its disabled state
            driver.execute_script("arguments[0].click();", button)  # Bypass the disabled state

            print("Clicked 'Load more' button.")

        except Exception as e:
            print("No more items to load or error occurred:", e)
            break  # Exit if the button is not found or another error occurs

    # Save to CSV after the loop if links were collected
    if links_scraped:
        print(f"Final saving CSV with {links_count} links...")
        save_to_csv(links_scraped)

    return links_scraped


# Function to save links to CSV file
def save_to_csv(links_scraped):
    """ Save the scraped links to a CSV file """
    with open('fragrance_links.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Fragrance Link"])
        for link in links_scraped:
            writer.writerow([link])


# Create new Selenium WebDriver
def create_new_driver():
    # Initialize the Selenium WebDriver
    service = Service(r"C:\Users\admin\Documents\fragrances\chromedriver.exe")

    # Set options for Chrome
    options = webdriver.ChromeOptions()

    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(service=service, options=options)
    return driver


# Function to scrape data from individual fragrance pages
def scrape_fragrance_data(lnk, driver):
    driver.get(lnk)

    # Give the page time to load (if necessary)
    WebDriverWait(driver, 10)
    # Get the page source and parse it with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    brand = soup.find('h6', class_='uppercase text-14 md:text-labLarge').text.strip()
    name = soup.find('h1', class_='text-h1Mobile md:text-h1 font-secondary mt-6 mb-1.5').text.strip()
    desc = soup.find('span', class_='text-16 md:text-18 font-light markdown').text.strip()
    meta_tag = soup.find('meta', {'name': 'description'}).get('content')
    ingredients_start = meta_tag.find("made from") + len("made from ")
    ingredients_string = meta_tag[ingredients_start:]
    ingredients = [ingredient.strip() for ingredient in ingredients_string.split(',')]
    ings = []
    for ingredient in ingredients:
        sub_ingredients = [sub.strip() for sub in ingredient.split('/')]
        ings.extend(sub_ingredients)

    # Locate the <dt> for "Concepts" and find the next <dl> element
    concepts_dl = soup.find('dt', string='Concepts').find_next('dl')
    # Fetch concepts directly from the located <dl> tag
    concepts = [concept.strip().strip(',') for concept in concepts_dl.get_text(strip=True).split(',')]

    return {'Brand': brand, 'Name': name, 'Description': desc, 'Notes': ings, 'Concepts': concepts}


# Function to save new data to the database
def save_new_to_database(df):
    engine = create_engine('sqlite:///fragrance_db.sqlite')  # Change as needed
    with engine.connect() as conn:
        for index, row in df.iterrows():
            # Check if the record already exists
            query = text("SELECT COUNT(*) FROM fragrances WHERE Name = :name")
            count = conn.execute(query, {'name': row['Name']}).scalar()
            if count == 0:
                # Insert new record if it doesn't exist
                insert_query = text("INSERT INTO fragrances (Name, Price) VALUES (:name, :price)")
                conn.execute(insert_query, {'name': row['Name'], 'price': row['Price']})
