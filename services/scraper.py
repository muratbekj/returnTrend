import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class SimpleWebScraper:
    def __init__(self):
        self.rss_feeds = [
            'https://magazine.sebastianraschka.com/feed',
            'https://openai.com/news/rss.xml',
            'https://www.artificialintelligence-news.com/feed/rss/',
        ]

    def scrape_rss_feeds(self):
        """Scrape RSS feeds and return articles as dict"""
        articles = {}
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                source_name = feed.feed.get('title', 'Unknown')
                
                for entry in feed.entries[:3]:  # Get max 3 from each feed
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    link = entry.get('link', '')
                    
                    # Parse date
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                        else:
                            pub_date = datetime.now()
                    except:
                        pub_date = datetime.now()
                    
                    articles[title] = {
                        'summary': summary[:200],  # Limit summary length
                        'link': link,
                        'source': source_name,
                        'published_at': pub_date.isoformat()
                    }
                    
            except Exception as e:
                print(f"Error scraping {feed_url}: {e}")
                continue
        
        return articles

    def scrape_web_pages(self):
        """Scrape HTML pages for additional content"""
        articles = {}
        web_sources = [
            {
                'url': 'https://techcrunch.com/category/artificial-intelligence/',
                'title_selector': 'h2.post-block__title a',
                'summary_selector': '.post-block__content',
                'source_name': 'TechCrunch AI'
            }
        ]
        
        for source in web_sources:
            try:
                response = requests.get(source['url'], headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                soup = BeautifulSoup(response.content, 'html.parser')
                
                titles = soup.select(source['title_selector'])[:5]  # Get first 5
                
                for title_elem in titles:
                    title = title_elem.get_text().strip()
                    link = title_elem.get('href', '')
                    
                    # Try to get summary from same container
                    summary = ''
                    try:
                        summary_elem = title_elem.find_parent().find(source['summary_selector'])
                        if summary_elem:
                            summary = summary_elem.get_text().strip()[:300]
                    except:
                        pass
                    
                    articles[title] = {
                        'summary': summary,
                        'link': link,
                        'source': source['source_name'],
                        'published_at': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                print(f"Error scraping {source['url']}: {e}")
                continue
        
        return articles

    def get_all_articles(self):
        """Get all articles from RSS feeds and web pages"""
        print("Scraping RSS feeds...")
        rss_articles = self.scrape_rss_feeds()
        
        print("Scraping web pages...")
        web_articles = self.scrape_web_pages()
        
        # Combine both dictionaries
        all_articles = {**rss_articles, **web_articles}
        
        print(f"Total articles found: {len(all_articles)}")
        return all_articles

# Usage:
# scraper = SimpleWebScraper()
# articles = scraper.get_all_articles()