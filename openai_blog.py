import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenAIBlogGenerator:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            print("[WARNING] OPENAI_API_KEY not found - will use dummy data only")
            self.openai_client = None
    
    def _prepare_news_summary(self, news_contents):
        """Prepare news content summary for prompt"""
        news_summary = ""
        for i, content in enumerate(news_contents, 1):
            if content:
                news_summary += f"뉴스 {i}:\n{content}\n\n"
        return news_summary.strip()
    
    def _create_prompt(self, keyword_data, news_contents):
        """Create unified prompt for OpenAI"""
        news_summary = self._prepare_news_summary(news_contents)
        
        prompt = f"""다음은 현재 트렌드 키워드 "{keyword_data['keyword']}"에 대한 최신 뉴스 내용입니다.

{news_summary}

---

아래 뉴스 내용을 바탕으로 마크다운 형식의 블로그 글을 작성해주세요.

---

✳️ 아래는 주제 유형별로 자주 사용되는 블로그 구성 예시입니다.  
뉴스 내용을 파악하여 가장 적절한 구성을 참고해 자유롭게 글을 작성해주세요.
적절한 구성이 없다면 4단계의 적절한 구조문으로 작성해주세요.

**[정책/지원금형]**
- ## 정책 소개
- ## 지원 대상 및 혜택
- ## 신청 방법
- ## 마무리

**[재난/사회 이슈형]**
- ## 이슈 개요
- ## 현재 상황
- ## 전문가 의견
- ## 대응 방법 및 마무리

**[트렌드/소비 뉴스형]**
- ## 트렌드 소개
- ## 원인 분석
- ## 산업/시장 반응
- ## 전망 및 마무리

**[통계/리포트형]**
- ## 통계 요약
- ## 수치 해석
- ## 의미 있는 포인트
- ## 정리 및 시사점

**[기술/AI 뉴스형]**
- ## 기술 개요
- ## 핵심 기능
- ## 업계 반응
- ## 전망 및 활용 팁

---

📌 작성 조건:
- 제목은 50자 이내의 클릭 유도형으로 작성
- 본문은 800~1200자 분량의 정보성 콘텐츠
- 마크다운 문법(##, **, -, > 등) 활용
- 마지막 줄에는 관련 해시태그 5개를 붙여주세요 (예: `#소상공인 #정책지원`)

글 구성은 위 템플릿을 참고하되, 뉴스 성격에 맞게 유연하게 조정해주세요.
정확하고 객관적인 정보를 제공하되, 읽기 쉽고 흥미로운 글로 작성해주세요.

마크다운 문법을 사용하세요:
- 제목: ## (큰 제목), ### (소제목)
- 강조: **굵게**, *기울임*
- 목록: - 또는 1. 2. 3.
- 인용: > 인용문
- 링크: [텍스트](URL)
- 줄바꿈: 빈 줄로 단락 구분

응답 형식을 반드시 아래와같이 지켜주세요.
응답형식
제목: [제목]
본문: [마크다운 형식 본문]
태그: [태그1, 태그2, 태그3, 태그4, 태그5]
"""

        print(f"prompt : {prompt}")
        
        return prompt
    
    def get_prompt_only(self, keyword_data, news_contents):
        """Return only the prompt without calling OpenAI API"""
        return self._create_prompt(keyword_data, news_contents)
    
    def _parse_openai_response(self, content):
        """Parse OpenAI response to extract title, body, and tags"""
        print(f"[DEBUG] Parsing OpenAI response...")
        lines = content.split('\n')
        print(f"[DEBUG] Total lines in response: {len(lines)}")
        
        title = ""
        body = ""
        tags = ""
        
        current_section = None
        line_count = 0
        body_started = False
        
        for line in lines:
            line_count += 1
            original_line = line
            line = line.strip()
            
            if line.startswith('제목:'):
                title = line.replace('제목:', '').strip()
                current_section = 'title'
                print(f"[DEBUG] Line {line_count}: Found title section: '{title}'")
            elif line.startswith('본문:'):
                body = line.replace('본문:', '').strip()
                current_section = 'body'
                body_started = True
                print(f"[DEBUG] Line {line_count}: Found body section start: '{body}'")
            elif line.startswith('태그:') or line.startswith('해시태그:'):
                tags = line.replace('태그:', '').replace('해시태그:', '').strip()
                current_section = 'tags'
                print(f"[DEBUG] Line {line_count}: Found tags section: '{tags}'")
            elif current_section == 'body' and line:
                body += '\n' + line
                if line_count <= 5:  # Only log first few lines to avoid spam
                    print(f"[DEBUG] Line {line_count}: Adding to body: '{line[:50]}...'")
            elif current_section == 'tags' and line:
                tags += ' ' + line
                print(f"[DEBUG] Line {line_count}: Adding to tags: '{line}'")
            # Handle case where OpenAI doesn't use "본문:" prefix
            elif title and not body_started and line and not line.startswith('#') and len(line) > 10:
                # Skip empty lines and start collecting body content after title
                if not body:
                    current_section = 'body'
                    body_started = True
                    print(f"[DEBUG] Line {line_count}: Auto-starting body section: '{line[:50]}...'")
                body += '\n' + line if body else line
            elif title and body_started and line:
                # Continue adding to body
                if line.startswith('태그:') or line.startswith('해시태그:'):
                    tags = line.replace('태그:', '').replace('해시태그:', '').strip()
                    current_section = 'tags'
                    print(f"[DEBUG] Line {line_count}: Found tags section: '{tags}'")
                else:
                    body += '\n' + line
            elif line and line_count <= 10:  # Log unmatched lines only for first 10 lines
                print(f"[DEBUG] Line {line_count}: Unmatched line (section='{current_section}'): '{line[:50]}...'")
        
        # Clean up
        body = body.strip()
        tags = tags.strip()
        
        # Extract hashtags if tags is empty but hashtags exist in body
        if not tags and body:
            import re
            hashtag_matches = re.findall(r'#\w+', body)
            if hashtag_matches:
                tags = ', '.join([tag.replace('#', '') for tag in hashtag_matches[:5]])
                print(f"[DEBUG] Extracted hashtags from body: '{tags}'")
        
        print(f"[DEBUG] Final parsing results:")
        print(f"[DEBUG] - Title: '{title}' (empty: {not title})")
        print(f"[DEBUG] - Body length: {len(body)} (empty: {not body})")
        print(f"[DEBUG] - Tags: '{tags}' (empty: {not tags})")
        
        return title, body, tags
    
    def _create_fallback_content(self, keyword_data, news_contents):
        """Create fallback content when OpenAI fails or isn't available"""
        news_summary = self._prepare_news_summary(news_contents)
        
        title = f"{keyword_data['keyword']} 최신 소식 - 놓치면 안 되는 핵심 정보"
        
        body = f"""## {keyword_data['keyword']}에 대한 최신 뉴스

{keyword_data['keyword']}에 대한 최신 뉴스를 정리해드립니다.

### 주요 뉴스 내용

{news_summary}

### 마무리

{keyword_data['keyword']}는 현재 많은 관심을 받고 있는 키워드입니다. 앞으로도 관련 동향을 지속적으로 주시해 보겠습니다."""
        
        tags = f"{keyword_data['keyword']}, 뉴스, 트렌드, 최신정보, 이슈"
        
        return title, body, tags
    
    def _create_dummy_content(self, keyword_data):
        """Create dummy content for testing"""
        title = f"{keyword_data['keyword']} 최신 트렌드 완전 분석! 놓치면 안 되는 핵심 정보"
        
        body = f"""## {keyword_data['keyword']}란 무엇인가?

최근 **{keyword_data['keyword']}**가 많은 관심을 받고 있습니다. 이번 포스팅에서는 {keyword_data['keyword']}에 대한 모든 것을 자세히 알아보겠습니다.

### 1. {keyword_data['keyword']}의 주요 특징

{keyword_data['keyword']}는 현재 많은 사람들이 주목하고 있는 키워드입니다. 다양한 관점에서 분석해보면 다음과 같은 특징들을 발견할 수 있습니다:

- 높은 검색량과 관심도
- 다양한 미디어에서의 언급 증가
- 사회적 파급효과

### 2. 왜 {keyword_data['keyword']}가 주목받고 있을까?

최근 트렌드를 분석해보면 *{keyword_data['keyword']}*가 주목받는 이유를 쉽게 찾을 수 있습니다. 소셜미디어와 뉴스에서 언급되는 빈도가 크게 증가했습니다.

> "트렌드는 시대의 흐름을 반영합니다. {keyword_data['keyword']}의 급상승은 현재 우리 사회의 관심사를 보여주는 지표입니다."

### 3. {keyword_data['keyword']} 관련 최신 정보

실시간으로 업데이트되는 {keyword_data['keyword']} 관련 정보들을 정리해보았습니다:

1. **주요 뉴스 동향**: 관련 기사 및 보도 증가
2. **소셜미디어 반응**: 네티즌들의 다양한 의견과 반응
3. **전문가 분석**: 해당 분야 전문가들의 견해

### 4. 마무리

{keyword_data['keyword']}에 대한 관심이 계속 증가하고 있는 만큼, 관련 동향을 지속적으로 주시할 필요가 있습니다. 앞으로도 {keyword_data['keyword']}와 관련된 **유용한 정보**들을 지속적으로 업데이트하겠습니다.

[더 자세한 정보 보기](#)"""
        
        tags = f"{keyword_data['keyword']}, 트렌드, 최신정보, 핫이슈, 분석"
        
        return title, body, tags
    
    def generate_blog_post(self, keyword_data, news_contents, use_openai=True):
        """Generate blog post using OpenAI API or fallback to dummy data"""
        print(f"[DEBUG] Generating blog post for keyword: {keyword_data['keyword']}")
        print(f"[DEBUG] News contents count: {len(news_contents)}")
        print(f"[DEBUG] Using OpenAI: {use_openai and self.openai_client is not None}")
        
        # If OpenAI is disabled or not available, use dummy data
        if not use_openai or not self.openai_client:
            if not news_contents:
                # No news content, use dummy data
                title, body, tags = self._create_dummy_content(keyword_data)
            else:
                # Has news content, use fallback format
                title, body, tags = self._create_fallback_content(keyword_data, news_contents)
        else:
            # Try to use OpenAI
            try:
                prompt = self._create_prompt(keyword_data, news_contents)
                
                # Call OpenAI API
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "당신은 한국어 블로그 포스트를 작성하는 전문 작가입니다. 뉴스 내용을 바탕으로 정확하고 흥미로운 블로그 포스트를 마크다운 형식으로 작성해주세요. 마크다운 문법을 정확히 사용하여 가독성 높은 포스트를 작성하세요."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                
                # Parse response
                content = response.choices[0].message.content
                print(f"[DEBUG] OpenAI raw response length: {len(content)} characters")
                print(f"[DEBUG] OpenAI raw response preview:\n{content[:500]}...")
                
                title, body, tags = self._parse_openai_response(content)
                
                print(f"[DEBUG] Parsed title: '{title}' (length: {len(title) if title else 0})")
                print(f"[DEBUG] Parsed body: '{body[:100] if body else 'None'}...' (length: {len(body) if body else 0})")
                print(f"[DEBUG] Parsed tags: '{tags}' (length: {len(tags) if tags else 0})")
                
                # Validate parsed content
                if not title or not body:
                    print("[DEBUG] OpenAI response parsing failed, using fallback")
                    print(f"[DEBUG] Title empty: {not title}, Body empty: {not body}")
                    
                    # Save raw response for debugging
                    try:
                        with open("openai_response_debug.txt", "w", encoding="utf-8") as f:
                            f.write(f"=== RAW RESPONSE ===\n{content}\n\n")
                            f.write(f"=== PARSED RESULTS ===\n")
                            f.write(f"Title: '{title}'\n")
                            f.write(f"Body: '{body}'\n")
                            f.write(f"Tags: '{tags}'\n")
                        print("[DEBUG] Raw response saved to openai_response_debug.txt")
                    except Exception as save_error:
                        print(f"[DEBUG] Could not save debug file: {save_error}")
                    
                    title, body, tags = self._create_fallback_content(keyword_data, news_contents)
                    
            except Exception as e:
                print(f"[DEBUG] Error generating blog post with OpenAI: {e}")
                title, body, tags = self._create_fallback_content(keyword_data, news_contents)
        
        print(f"[DEBUG] Generated title: {title}")
        print(f"[DEBUG] Generated body length: {len(body)}")
        print(f"[DEBUG] Generated tags: {tags}")
        
        return {
            'title': title,
            'body': body,
            'tags': tags
        }


def test_openai_blog():
    """Test function for OpenAI blog generation"""
    print("Testing OpenAI blog generation...")
    
    # Test data
    keyword_data = {
        'keyword': '테스트 키워드',
        'source_url': 'http://example.com/news1'
    }
    
    news_contents = [
        "이것은 첫 번째 뉴스 내용입니다. 테스트 키워드에 대한 중요한 정보를 담고 있습니다.",
        "이것은 두 번째 뉴스 내용입니다. 테스트 키워드의 최신 동향을 다룹니다."
    ]
    
    blog_generator = OpenAIBlogGenerator()
    
    # Test prompt generation
    print("\n1. Testing prompt generation...")
    prompt = blog_generator.get_prompt_only(keyword_data, news_contents)
    print(f"Prompt length: {len(prompt)} characters")
    print(f"Prompt preview:\n{prompt[:200]}...")
    
    # Test with dummy data (OpenAI disabled)
    print("\n2. Testing with dummy data...")
    result = blog_generator.generate_blog_post(keyword_data, news_contents, use_openai=False)
    print(f"Title: {result['title']}")
    print(f"Body length: {len(result['body'])} characters")
    print(f"Tags: {result['tags']}")
    print(f"Body preview:\n{result['body'][:200]}...")
    
    # Test with OpenAI (if API key is available)
    print("\n3. Testing with OpenAI...")
    try:
        result = blog_generator.generate_blog_post(keyword_data, news_contents, use_openai=True)
        print(f"Title: {result['title']}")
        print(f"Body length: {len(result['body'])} characters")
        print(f"Tags: {result['tags']}")
        print(f"Body preview:\n{result['body'][:200]}...")
    except Exception as e:
        print(f"OpenAI test failed: {e}")
    
    print("\nOpenAI blog generation test completed!")


if __name__ == "__main__":
    test_openai_blog()