from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote, quote
from google.cloud import storage

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///links.db'
db = SQLAlchemy(app)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.Date, default=datetime.date.today)

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def sanitize_url(url):
    """Create a filename-safe version of a URL."""
    parsed_url = urlparse(url)
    sanitized = quote(parsed_url.netloc + parsed_url.path, safe='')
    return sanitized

def get_author_name(url):
    """Extracts the author's name from the URL."""
    path = urlparse(url).path.strip('/')
    author_name = path.split('/')[-1]
    return unquote(author_name)

def save_new_links(url, new_links, old_links, bucket_name):
    """Saves new links to the database and uploads them to GCS."""
    author_name = get_author_name(url)
    filename = f"{author_name}_{datetime.datetime.now().strftime('%Y-%m-%d')}_new_links.txt"
    with open(filename, 'w') as file:
        for link in sorted(new_links - old_links):
            date_posted = datetime.date.today()
            new_link = Link(url=link, author=author_name, date_posted=date_posted)
            db.session.add(new_link)
            file.write(f"{link}\n")
    db.session.commit()
    # Upload file to GCS
    upload_to_gcs(bucket_name, filename, filename)

def scrape_and_store(bucket_name, url_list):
    """Scrapes and stores new links."""
    for url in url_list:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            new_links = set(link.get('href') for link in links if link.get('href') is not None)
            old_links = set(link.url for link in Link.query.filter_by(author=get_author_name(url)).all())
            real_new_links = new_links - old_links
            if real_new_links:
                save_new_links(url, new_links, old_links, bucket_name)

def schedule_scraping():
    bucket_name = 'ldrlinks-bucket1'
    url_list = [
        # Your URL list here
    ]
    scrape_and_store(bucket_name, url_list)

scheduler = BackgroundScheduler()
scheduler.add_job(func=schedule_scraping, trigger="interval", days=1)
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/links', methods=['GET'])
def links():
    author = request.args.get('author')
    date = request.args.get('date', datetime.date.today().isoformat())
    links_query = Link.query.filter_by(author=author) if author else Link.query
    links_query = links_query.filter(Link.date_posted == datetime.datetime.fromisoformat(date).date())
    links = links_query.all()
    return jsonify([{'author': link.author, 'url': link.url, 'date_posted': link.date_posted.isoformat()} for link in links])

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
