import feedparser
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from html import unescape


class KoreaRSSManager:
    def __init__(self):
        # Korea.kr RSS feeds
        self.rss_feeds = [
            "https://www.korea.kr/rss/policy.xml",
            "https://www.korea.kr/rss/president.xml", 
            "https://www.korea.kr/rss/cabinet.xml"
        ]
        self.processed_articles_file = 'processed_articles.json'
    
    def _parse_article_key(self, link):
        """Parse article link to create unique key"""
        try:
            # Remove CDATA if present
            if link.startswith('<![CDATA[') and link.endswith(']]>'):
                link = link[9:-3].strip()
            
            # Extract page type and news ID dynamically
            # Pattern: extract everything between last '/' and '.do', and newsId value
            # Examples:
            # https://www.korea.kr/briefing/stateCouncilView.do?newsId=148945654&call_from=rsslink
            # https://www.korea.kr/news/policyNewsView.do?newsId=148945904&call_from=rsslink
            # https://www.korea.kr/news/healthView.do?newsId=148945548&call_from=rsslink
            
            # Extract page type (between last '/' and '.do')
            page_type_match = re.search(r'/([^/]+)\.do', link)
            page_type = page_type_match.group(1) if page_type_match else 'unknown'
            
            # Extract newsId (between 'newsId=' and '&' or end of string)
            news_id_match = re.search(r'newsId=(\d+)(?:&|$)', link)
            news_id = news_id_match.group(1) if news_id_match else None
            
            if news_id:
                return f"{page_type}_{news_id}"
            else:
                # If no newsId found, use hash of the link
                import hashlib
                return f"{page_type}_{hashlib.md5(link.encode()).hexdigest()[:8]}"
            
        except Exception as e:
            print(f"Error parsing article key from {link}: {e}")
            import hashlib
            return f"error_{hashlib.md5(link.encode()).hexdigest()[:8]}"
    
    def _load_processed_articles(self):
        """Load processed articles from file"""
        try:
            if os.path.exists(self.processed_articles_file):
                with open(self.processed_articles_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            print(f"Error loading processed articles: {e}")
            return set()
    
    def _save_processed_articles(self, processed_keys):
        """Save processed article keys to file"""
        try:
            with open(self.processed_articles_file, 'w', encoding='utf-8') as f:
                json.dump(list(processed_keys), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving processed articles: {e}")
    
    def get_rss_articles(self, num_articles=5):
        """Get articles from Korea.kr RSS feeds with duplicate checking"""
        try:
            # Load processed articles
            processed_keys = self._load_processed_articles()
            print(f"[DEBUG] Loaded {len(processed_keys)} processed article keys")
            
            all_articles = []
            new_processed_keys = processed_keys.copy()
            
            for rss_url in self.rss_feeds:
                print(f"[DEBUG] Fetching from RSS: {rss_url}")
                
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries:
                    if len(all_articles) >= num_articles:
                        break
                        
                    # Extract title (remove CDATA)
                    title = entry.title
                    if title.startswith('<![CDATA[') and title.endswith(']]>'):
                        title = title[9:-3].strip()
                    
                    # Extract description and clean HTML
                    description = entry.description if hasattr(entry, 'description') else ''
                    if description.startswith('<![CDATA[') and description.endswith(']]>'):
                        description = description[9:-3].strip()
                    
                    # Extract link
                    link = entry.link if hasattr(entry, 'link') else ''
                    if link.startswith('<![CDATA[') and link.endswith(']]>'):
                        link = link[9:-3].strip()
                    
                    # Parse article key for duplicate checking
                    article_key = self._parse_article_key(link)
                    print(f"[DEBUG] Article key: {article_key}")
                    
                    # Check if already processed
                    if article_key in processed_keys:
                        print(f"[DEBUG] Skipping duplicate article: {title[:50]}... (key: {article_key})")
                        continue
                    
                    # Clean description from HTML tags
                    clean_description = self.clean_html_content(description)
                    
                    article_data = {
                        'title': title,
                        'description': clean_description,
                        'link': link,
                        'source': rss_url,
                        'key': article_key
                    }
                    
                    all_articles.append(article_data)
                    new_processed_keys.add(article_key)
                    print(f"[DEBUG] Added new article: {title[:50]}... (key: {article_key})")
                
                if len(all_articles) >= num_articles:
                    break
            
            # Save updated processed keys
            if new_processed_keys != processed_keys:
                self._save_processed_articles(new_processed_keys)
                print(f"[DEBUG] Saved {len(new_processed_keys)} processed article keys")
            
            return all_articles[:num_articles]
            
        except Exception as e:
            print(f"Error fetching RSS feeds: {e}")
            return []
    
    def clean_html_content(self, html_content):
        """Clean HTML content and extract meaningful text"""
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['img', 'a', 'script', 'style']):
                element.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
            text = re.sub(r'\[.*?\]', '', text)  # Remove [content] patterns
            text = unescape(text)  # Decode HTML entities
            text = text.strip()
            
            # Limit length
            if len(text) > 1500:
                text = text[:1500] + "..."
            
            return text
            
        except Exception as e:
            print(f"Error cleaning HTML content: {e}")
            return html_content
    
    def get_full_article_content(self, url):
        """Get full content from an article URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find article content with Korea.kr specific selectors
            content_selectors = [
                '.article_body',
                '.news_content',
                '.cont_inner',
                '.view_content',
                '.article_view',
                '.content_area',
                '.news_view',
                'article',
                '.content'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(strip=True)
                    break
            
            # If no specific content found, try body text
            if not content:
                content = soup.get_text()
            
            # Clean up the content
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:  # Filter out very short lines
                    cleaned_lines.append(line)
            
            # Limit content length
            content = ' '.join(cleaned_lines)
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            return content
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return ""


def test_korea_rss():
    """Test function for Korea RSS functionality"""
    print("Testing Korea RSS functionality...")
    
    rss_manager = KoreaRSSManager()
    
    # Test getting RSS articles
    articles = rss_manager.get_rss_articles(3)
    print(f"Found {len(articles)} articles:")
    
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. Title: {article['title']}")
        print(f"   Description: {article['description'][:100]}...")
        print(f"   Link: {article['link']}")
        print(f"   Key: {article['key']}")
        print(f"   Source: {article['source']}")
        
        # Test getting full content
        if article['link']:
            print(f"   Testing full content fetch...")
            content = rss_manager.get_full_article_content(article['link'])
            print(f"   Full content length: {len(content)} characters")
            if content:
                print(f"   Content preview: {content[:100]}...")
    
    # Test duplicate checking by running again
    print("\n" + "="*50)
    print("Testing duplicate checking...")
    print("Running RSS fetch again to test duplicate detection:")
    
    articles2 = rss_manager.get_rss_articles(3)
    print(f"Second run found {len(articles2)} new articles (should be 0 if all were duplicates)")
    
    print("\nKorea RSS test completed!")


if __name__ == "__main__":
    test_korea_rss()