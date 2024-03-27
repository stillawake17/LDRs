import requests
from bs4 import BeautifulSoup

# The URL of the website you want to scrape
url = 'https://www.leicestermercury.co.uk/authors/hannah-richardson/'

# Send a GET request to the website
response = requests.get(url)

# Check if the website was successfully accessed
if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all hyperlinks in the page
    links = soup.find_all('a')
    
    # Extract href attributes from the <a> tags
    extracted_links = set(link.get('href') for link in links if link.get('href') is not None)
    
    # Store the links in a file for later use
    with open('links.txt', 'w') as file:
        for link in extracted_links:
            file.write(f"{link}\n")
            
    print(f"Found and stored {len(extracted_links)} links.")
else:
    print(f"Failed to access {url}")
