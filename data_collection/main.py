import os
import subprocess

# Define the path to dataset.csv
dataset_path = os.path.join(os.path.dirname(__file__), 'dataset.csv')

# Check if dataset.csv exists
if os.path.exists(dataset_path):
    print("Dataset found, no need to scrape.")
else:
    print("Dataset not found. Running scraper to collect data.")
    # Run the scraper's main.py using subprocess
    scraper_script = os.path.join(os.path.dirname(__file__), 'scraper', 'main.py')
    result = subprocess.run(['python', scraper_script], capture_output=True, text=True)

    # Output result of scraping
    if result.returncode == 0:
        print("Scraping completed successfully. Dataset created.")
    else:
        print("Scraping failed. Please check the scraper for issues.")
        print("Error output:", result.stderr)
