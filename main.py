import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from pytrends.request import TrendReq
import openai
import requests
from bs4 import BeautifulSoup


class TistoryAutoBlog:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.tistory_cookie = os.getenv('TISTORY_COOKIE')
        self.used_keywords_file = 'used_keywords.json'
        self.max_keywords = 10
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not self.tistory_cookie:
            raise ValueError("TISTORY_COOKIE environment variable is required")
        
        openai.api_key = self.openai_api_key
        
    def load_used_keywords(self):
        """Load previously used keywords from file"""
        try:
            with open(self.used_keywords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_used_keywords(self, keywords):
        """Save used keywords to file"""
        with open(self.used_keywords_file, 'w', encoding='utf-8') as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
    
    def get_google_trends_keywords(self, num_keywords=5):
        """Get trending keywords from Google Trends"""
        try:
            pytrends = TrendReq(hl='ko', tz=540)
            trending_searches = pytrends.trending_searches(pn='south_korea')
            
            used_keywords = self.load_used_keywords()
            
            # Filter out used keywords
            new_keywords = []
            for keyword in trending_searches.values.flatten():
                if keyword not in used_keywords and len(new_keywords) < num_keywords:
                    new_keywords.append(keyword)
            
            return new_keywords
        except Exception as e:
            print(f"Error fetching Google Trends: {e}")
            return []
    
    def get_news_articles(self, keyword, num_articles=3):
        """Get news articles related to the keyword"""
        try:
            search_url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            news_items = soup.find_all('div', class_='news_area')[:num_articles]
            
            for item in news_items:
                title_elem = item.find('a', class_='news_tit')
                summary_elem = item.find('div', class_='news_dsc')
                
                if title_elem and summary_elem:
                    articles.append({
                        'title': title_elem.get_text().strip(),
                        'summary': summary_elem.get_text().strip()
                    })
            
            return articles
        except Exception as e:
            print(f"Error fetching news articles: {e}")
            return []
    
    def generate_blog_post(self, keyword, news_articles):
        """Generate blog post using OpenAI"""
        try:
            news_context = ""
            if news_articles:
                news_context = "\n\n관련 뉴스 정보:\n"
                for i, article in enumerate(news_articles, 1):
                    news_context += f"{i}. {article['title']}\n{article['summary']}\n\n"
            
            prompt = f"""
            '{keyword}'를 주제로 한 SEO 최적화된 블로그 글을 작성해주세요.
            
            다음 조건을 반드시 지켜주세요:
            1. 제목은 클릭을 유도하는 매력적인 제목으로 작성
            2. 본문은 1500자 이상으로 작성
            3. 키워드를 자연스럽게 적절히 분산 배치
            4. 소제목을 활용하여 가독성 향상
            5. 실용적이고 유용한 정보 제공
            6. 마지막에 관련 키워드 태그 5개 이상 제안
            
            {news_context}
            
            응답 형식:
            제목: [제목]
            본문: [본문 내용]
            태그: [태그1, 태그2, 태그3, ...]
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 SEO 최적화된 블로그 글을 작성하는 전문가입니다. 한국어로 자연스럽고 유용한 콘텐츠를 작성해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse the response
            lines = content.split('\n')
            title = ""
            body = ""
            tags = ""
            
            current_section = ""
            for line in lines:
                if line.startswith('제목:'):
                    title = line.replace('제목:', '').strip()
                    current_section = "title"
                elif line.startswith('본문:'):
                    current_section = "body"
                    body = line.replace('본문:', '').strip()
                elif line.startswith('태그:'):
                    tags = line.replace('태그:', '').strip()
                    current_section = "tags"
                elif current_section == "body" and line.strip():
                    body += "\n" + line
            
            return {
                'title': title or f"{keyword}에 대한 최신 트렌드 분석",
                'body': body or f"{keyword}에 대한 상세한 분석과 정보를 제공합니다.",
                'tags': tags or keyword
            }
            
        except Exception as e:
            print(f"Error generating blog post: {e}")
            return {
                'title': f"{keyword}에 대한 최신 트렌드 분석",
                'body': f"{keyword}에 대한 상세한 분석과 정보를 제공합니다.",
                'tags': keyword
            }
    
    def setup_chrome_driver(self):
        """Setup Chrome WebDriver with headless mode"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    
    def login_to_tistory(self, driver):
        """Login to Tistory using cookies"""
        try:
            driver.get("https://www.tistory.com")
            
            # Parse and add cookies
            cookies = json.loads(self.tistory_cookie)
            for cookie in cookies:
                driver.add_cookie(cookie)
            
            # Refresh to apply cookies
            driver.refresh()
            time.sleep(3)
            
            return True
        except Exception as e:
            print(f"Error logging in to Tistory: {e}")
            return False
    
    def post_to_tistory(self, driver, title, content, tags):
        """Post content to Tistory blog"""
        try:
            # Navigate to write page - you need to replace 'yourblog' with your actual blog name
            blog_url = "https://yourblog.tistory.com/manage/newpost/"
            driver.get(blog_url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "title"))
            )
            
            # Enter title
            title_input = driver.find_element(By.ID, "title")
            title_input.clear()
            title_input.send_keys(title)
            
            # Enter content
            # Switch to HTML mode for better content handling
            html_mode_btn = driver.find_element(By.CSS_SELECTOR, "button[data-mode='html']")
            html_mode_btn.click()
            time.sleep(2)
            
            content_textarea = driver.find_element(By.ID, "content")
            content_textarea.clear()
            content_textarea.send_keys(content)
            
            # Add tags
            if tags:
                tag_input = driver.find_element(By.ID, "tagText")
                tag_input.clear()
                tag_input.send_keys(tags)
            
            # Publish the post
            publish_btn = driver.find_element(By.CSS_SELECTOR, "button[data-action='publish']")
            publish_btn.click()
            
            # Wait for confirmation
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "confirm"))
            )
            
            return True
            
        except Exception as e:
            print(f"Error posting to Tistory: {e}")
            return False
    
    def run(self):
        """Main execution function"""
        print(f"Starting Tistory Auto Blog at {datetime.now()}")
        
        # Get trending keywords
        keywords = self.get_google_trends_keywords(self.max_keywords)
        if not keywords:
            print("No new keywords found")
            return
        
        print(f"Found {len(keywords)} new keywords: {keywords}")
        
        # Process the first keyword
        keyword = keywords[0]
        print(f"Processing keyword: {keyword}")
        
        # Get news articles
        news_articles = self.get_news_articles(keyword)
        print(f"Found {len(news_articles)} news articles")
        
        # Generate blog post
        blog_post = self.generate_blog_post(keyword, news_articles)
        print(f"Generated blog post: {blog_post['title']}")
        
        # Setup browser and post to Tistory
        driver = None
        try:
            driver = self.setup_chrome_driver()
            
            if self.login_to_tistory(driver):
                if self.post_to_tistory(driver, blog_post['title'], blog_post['body'], blog_post['tags']):
                    print("Successfully posted to Tistory")
                    
                    # Save used keyword
                    used_keywords = self.load_used_keywords()
                    used_keywords.append(keyword)
                    self.save_used_keywords(used_keywords)
                    print(f"Saved keyword: {keyword}")
                else:
                    print("Failed to post to Tistory")
            else:
                print("Failed to login to Tistory")
                
        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            if driver:
                driver.quit()
        
        print("Tistory Auto Blog completed")


if __name__ == "__main__":
    try:
        bot = TistoryAutoBlog()
        bot.run()
    except Exception as e:
        print(f"Fatal error: {e}")