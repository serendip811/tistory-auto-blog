import os
import json
from datetime import datetime
from korea_rss import KoreaRSSManager
from openai_blog import OpenAIBlogGenerator
from tistory_poster import TistoryPoster
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TistoryAutoBlog:
    def __init__(self):
        self.max_articles = 1
        
        # Initialize components
        self.rss_manager = KoreaRSSManager()
        self.blog_generator = OpenAIBlogGenerator()
        self.tistory_poster = TistoryPoster()
    
    def run(self, prompt_only=False):
        """Main execution function"""
        print(f"Starting Tistory Auto Blog at {datetime.now()}")
        
        if prompt_only:
            print("*** PROMPT TEST MODE - Will generate prompts only and exit ***")
        
        # Get articles from Korea RSS feeds
        articles = self.rss_manager.get_rss_articles(self.max_articles)
        if not articles:
            print("No articles found")
            return
        
        print(f"Found {len(articles)} articles")
        
        # If prompt_only mode, just generate and show prompts
        if prompt_only:
            for i, article_data in enumerate(articles, 1):
                print(f"\n{'='*80}")
                print(f"PROMPT {i}/{len(articles)}: {article_data['title']}")
                print(f"Article link: {article_data['link']}")
                print(f"{'='*80}")
                
                # Get full article content if available
                full_content = ""
                if article_data['link']:
                    print(f"Fetching full content from: {article_data['link']}")
                    full_content = self.rss_manager.get_full_article_content(article_data['link'])
                    if full_content:
                        print(f"Full content fetched: {len(full_content)} characters")
                    else:
                        print("Failed to fetch full content, using description")
                        full_content = article_data['description']
                else:
                    full_content = article_data['description']
                
                # Prepare data for blog generation
                keyword_data = {
                    'keyword': article_data['title'],
                    'source_url': article_data['link']
                }
                news_contents = [full_content] if full_content else []
                
                # Generate and display prompt only
                prompt = self.blog_generator.get_prompt_only(keyword_data, news_contents)
                print("\n[GENERATED PROMPT]:")
                print(prompt)
                print(f"\n{'='*80}")
            
            print(f"\nPrompt test completed - Generated {len(articles)} prompts")
            return
        
        # Normal execution mode
        # Setup browser once for all articles
        driver = None
        login_success = False
        
        try:
            driver = self.tistory_poster.setup_chrome_driver()
            login_success = self.tistory_poster.login_to_tistory(driver)
            
            if not login_success:
                print("Failed to login to Tistory")
                return
            
            print("Successfully logged in to Tistory")
            
            # Process each article
            for i, article_data in enumerate(articles, 1):
                print(f"\n{'='*50}")
                print(f"Processing article {i}/{len(articles)}: {article_data['title']}")
                print(f"Article link: {article_data['link']}")
                
                # Get full article content if available
                full_content = ""
                if article_data['link']:
                    print(f"Fetching full content from: {article_data['link']}")
                    full_content = self.rss_manager.get_full_article_content(article_data['link'])
                    if full_content:
                        print(f"Full content fetched: {len(full_content)} characters")
                    else:
                        print("Failed to fetch full content, using description")
                        full_content = article_data['description']
                else:
                    full_content = article_data['description']
                
                # Prepare data for blog generation
                keyword_data = {
                    'keyword': article_data['title'],
                    'source_url': article_data['link']
                }
                news_contents = [full_content] if full_content else []
                
                print(f"Content prepared for blog generation: {len(news_contents)} items")
                
                # Generate blog post using OpenAI (or dummy data)
                use_openai = True  # Set to True to use OpenAI, False for dummy data
                blog_post = self.blog_generator.generate_blog_post(keyword_data, news_contents, use_openai)
                print(f"Generated blog post: {blog_post['title']}")
                
                # Post to Tistory
                if self.tistory_poster.post_to_tistory(driver, blog_post['title'], blog_post['body'], blog_post['tags']):
                    print(f"✅ Successfully posted article {i}: {article_data['title']}")
                else:
                    print(f"❌ Failed to post article {i}: {article_data['title']}")
                
                # Add delay between posts to avoid rate limiting
                if i < len(articles):
                    print("Waiting 5 seconds before next post...")
                    import time
                    time.sleep(5)
                
        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            if driver:
                driver.quit()
        
        print(f"\nTistory Auto Blog completed - Processed {len(articles)} articles")


def test_individual_components():
    """Test individual components separately"""
    print("=== Testing Individual Components ===")
    
    # Test Korea RSS
    print("\n1. Testing Korea RSS...")
    rss_manager = KoreaRSSManager()
    articles = rss_manager.get_rss_articles(2)
    if articles:
        print(f"✅ Korea RSS working: Found {len(articles)} articles")
        print(f"First article: {articles[0]['title']}")
    else:
        print("❌ Korea RSS not working")
    
    # Test OpenAI Blog Generator
    print("\n2. Testing OpenAI Blog Generator...")
    blog_generator = OpenAIBlogGenerator()
    test_keyword = {'keyword': '테스트키워드', 'news_urls': []}
    test_news = ['테스트 뉴스 내용']
    blog_post = blog_generator.generate_blog_post(test_keyword, test_news, use_openai=False)
    if blog_post and blog_post['title']:
        print(f"✅ Blog Generator working: {blog_post['title'][:50]}...")
    else:
        print("❌ Blog Generator not working")
    
    # Test Tistory Poster (setup only)
    print("\n3. Testing Tistory Poster Setup...")
    try:
        tistory_poster = TistoryPoster()
        driver = tistory_poster.setup_chrome_driver()
        if driver:
            print("✅ Tistory Poster setup working")
            driver.quit()
        else:
            print("❌ Tistory Poster setup not working")
    except Exception as e:
        print(f"❌ Tistory Poster setup error: {e}")
    
    print("\n=== Component Tests Completed ===")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_individual_components()
    elif len(sys.argv) > 1 and sys.argv[1] == "prompt":
        try:
            bot = TistoryAutoBlog()
            bot.run(prompt_only=True)
        except Exception as e:
            print(f"Fatal error: {e}")
    else:
        try:
            bot = TistoryAutoBlog()
            bot.run()
        except Exception as e:
            print(f"Fatal error: {e}")