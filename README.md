# Tistory Auto Blog

매일 자동으로 구글 트렌드에서 인기 키워드를 수집하여 티스토리 블로그에 포스팅하는 자동화 시스템입니다.

## 주요 기능

- 구글 트렌드에서 실시간 인기 키워드 수집
- 네이버 뉴스에서 관련 기사 정보 수집
- OpenAI GPT-4를 활용한 SEO 최적화 블로그 글 생성
- 중복 키워드 방지 기능
- 티스토리 자동 포스팅
- GitHub Actions를 통한 완전 자동화

## 설정 방법

### 1. GitHub Repository 설정

1. GitHub에서 새 저장소를 생성합니다.
2. 이 코드를 저장소에 업로드합니다.

### 2. GitHub Secrets 설정

Repository Settings > Secrets and variables > Actions에서 다음 값들을 설정합니다:

- `OPENAI_API_KEY`: OpenAI API 키
- `TISTORY_COOKIE`: 티스토리 로그인 쿠키 (JSON 배열 형태)

### 3. 티스토리 쿠키 추출 방법

1. 크롬 브라우저에서 티스토리에 로그인
2. F12 → Application → Cookies → https://tistory.com
3. 모든 쿠키를 JSON 배열 형태로 복사:
```json
[
  {
    "name": "TSSESSION",
    "value": "your_session_value",
    "domain": ".tistory.com",
    "path": "/",
    "secure": true,
    "httpOnly": true
  }
]
```

### 4. 블로그 주소 수정

`main.py` 파일의 116번째 줄에서 `yourblog`를 실제 블로그 주소로 변경:

```python
blog_url = "https://yourblog.tistory.com/manage/newpost/"
```

## 실행 방법

### 자동 실행
- GitHub Actions가 매일 오전 9시(한국 시간)에 자동 실행

### 수동 실행
1. GitHub Repository > Actions > Tistory Auto Blog
2. "Run workflow" 버튼 클릭

### 로컬 실행
```bash
# 환경 변수 설정
export OPENAI_API_KEY="your_api_key"
export TISTORY_COOKIE='[{"name":"TSSESSION","value":"..."}]'

# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py
```

## 파일 구조

```
├── main.py                    # 메인 실행 파일
├── requirements.txt           # Python 의존성
├── used_keywords.json         # 사용된 키워드 저장 (자동 생성)
├── .github/
│   └── workflows/
│       └── blog_post.yml      # GitHub Actions 워크플로우
└── README.md                  # 프로젝트 설명
```

## 주요 특징

1. **중복 방지**: 이미 사용된 키워드는 `used_keywords.json`에 저장되어 재사용 방지
2. **뉴스 연동**: 네이버 뉴스에서 관련 기사 정보를 수집하여 더 풍부한 콘텐츠 생성
3. **SEO 최적화**: OpenAI를 활용한 검색 엔진 최적화 콘텐츠 생성
4. **완전 자동화**: GitHub Actions를 통한 스케줄링 및 자동 실행

## 문제 해결

- **크롬 드라이버 오류**: GitHub Actions에서 자동으로 최신 ChromeDriver를 설치
- **쿠키 만료**: 티스토리 쿠키가 만료되면 다시 추출하여 Secrets에 업데이트
- **API 제한**: OpenAI API 사용량 확인 및 요금 관리 필요

## 라이선스

MIT License