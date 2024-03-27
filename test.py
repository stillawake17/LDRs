import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

def scrape_author_links(url):
    if not url.endswith('/'):
        url += '/'
        
    path = urlparse(url).path.strip('/')
    author_name = path.split('/')[-1]
    
    author_name = unquote(author_name)
    if not author_name:
        author_name = "unknown_author"
    
    filename = f"{author_name}.txt".replace('/', '_').replace('\\', '_')
    
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        extracted_links = set(link.get('href') for link in links if link.get('href') is not None)
        
        with open(filename, 'w') as file:
            for link in extracted_links:
                file.write(f"{link}\n")
        print(f"Found and stored {len(extracted_links)} links in {filename}.")
    else:
        print(f"Failed to access {url}")

def process_url_list(url_list):
    for url in url_list:
        scrape_author_links(url)


# List of URLs to process
url_list = [
    'https://www.leicestermercury.co.uk/authors/hannah-richardson',
    'https://www.somersetlive.co.uk/authors/john-wimperis/',
    # Add more URLs as needed
]

process_url_list(url_list)
