from data_collection.scraper import scraper as sc
import pandas as pd

if __name__ == "__main__":
    driver = sc.create_new_driver()
    links = sc.scrape_fragrance_links(driver)
    print('Number of links:', len(links))

    all_data = []
    for link in links:
        fragrance_data = sc.scrape_fragrance_data(link, driver)
        all_data.append(fragrance_data)

    df = pd.DataFrame(all_data)
    df.to_csv("fragrance-data.csv")  # Save the data to CSV
    driver.quit()

    print('Dataset saved as CSV file')
