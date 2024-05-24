import feedparser
import re
import time
import requests
import sqlite3
import argparse
from bs4 import BeautifulSoup
from datetime import datetime
from utils import Utils


config = Utils.read_config('/user/config.ini', 'common')

# List of RSS feed URLs
rss_feeds = config.get("rss_feeds").split(' | ')

# List of strings to search for
search_strings = config.get("search_strings").split(' | ')

# Discord webhook URL
discord_webhook_url = config.get("webhook_url")

# Compile search strings into regular expressions with wildcards and case-insensitivity
search_patterns = [re.compile(f".*{re.escape(s)}.*", re.IGNORECASE) for s in search_strings]

def init_db():
    """Initialize SQLite database and create table if not exists."""
    conn = sqlite3.connect('/user/notified_entries.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS notified_entries (entry_id TEXT PRIMARY KEY)''')
    conn.commit()
    return conn, cursor

def clear_db(conn, cursor):
    """Clear the database entries."""
    cursor.execute("DELETE FROM notified_entries")
    conn.commit()
    print("Database cleared.")

def fetch_feed(url):
    """Fetch and parse the RSS feed from the given URL."""
    return feedparser.parse(url)

def check_entry(entry):
    """Check if any of the search patterns match the entry title or description."""
    for pattern in search_patterns:
        if pattern.search(entry.title) or pattern.search(entry.description):
            return True
    return False

def html_to_markdown(html):
    """Convert HTML tags in the given text to Markdown format."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Convert <strong> tags to ** for bold
    for strong_tag in soup.find_all('strong'):
        strong_tag.insert_before('**')
        strong_tag.insert_after('**')
        strong_tag.unwrap()

    # Convert <a> tags to Markdown links
    for a_tag in soup.find_all('a'):
        markdown_link = f"[{a_tag.text}]({a_tag['href']})"
        a_tag.replace_with(markdown_link)
    
    return soup.get_text(separator="").strip()

def send_discord_notification(entry, website_name):
    """Send a notification to Discord via webhook."""
    description_text = html_to_markdown(entry.description)
    message = {
        "username": "RSS-NOTIFY",
        "embeds": [
            {
                "title": entry.title,
                "url": entry.link,
                "description": description_text,
                "author": {
                    "name": entry.get("author", "Unknown Author"),
                    "url": entry.link
                },
                "footer": {
                    "text": website_name
                },
                "timestamp": datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').isoformat()
            }
        ]
    }
    response = requests.post(discord_webhook_url, json=message)
    if response.status_code == 204:
        print(f"Notification sent: {entry.title}")
    else:
        print(f"Failed to send notification: {response.status_code} {response.text}")

def check_feeds(feeds, cursor, conn):
    """Recursively check a list of RSS feeds for matching entries."""
    for url in feeds:
        print(f"Checking feed: {url}")
        feed = fetch_feed(url)
        website_name = feed.feed.title if 'title' in feed.feed else 'Unknown Website'
        for entry in feed.entries:
            entry_id = entry.id if 'id' in entry else entry.link
            cursor.execute("SELECT 1 FROM notified_entries WHERE entry_id = ?", (entry_id,))
            if check_entry(entry) and cursor.fetchone() is None:
                send_discord_notification(entry, website_name)
                cursor.execute("INSERT INTO notified_entries (entry_id) VALUES (?)", (entry_id,))
                conn.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="RSS Feed Checker with Discord Notifications")
    parser.add_argument('--clear', action='store_true', help='Clear the database entries')
    args = parser.parse_args()

    conn, cursor = init_db()

    if args.clear:
        clear_db(conn, cursor)
    else:
        try:
            timer = float(config.get('timer', '3600'))  # Default value is 10 if not found
            while True:
                check_feeds(rss_feeds, cursor, conn)
                print(f"Waiting {timer}sec for the next check...")
                time.sleep(timer)  # Wait for 1 hour before checking again
        finally:
            conn.close()
