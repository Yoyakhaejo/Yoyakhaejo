# Streamlit + OpenAI Summarizer & Practice Generator

간단한 Streamlit 앱으로, 사용자가 업로드한 PDF/PPTX/MP4 혹은 웹페이지 링크에서 텍스트를 추출한 뒤 OpenAI API를 사용해 요약과 연습문제를 생성합니다.

## 사용법 (로컬)

1. 레포지토리 클론

```bash
git clone <이 리포지토리 URL>
cd streamlit-openai-summarizer-practice-repo
```

2. 의존성 설치

```bash
python -m venv venv
source venv/bin/activate   # mac/linux
venv\Scripts\activate    # windows
pip install -r requirements.txt
```

3. ffmpeg 설치 (moviepy가 필요로 함)

mac: `brew install ffmpeg`
윈도우/리눅스: 배포 방식에 맞게 설치

4. 앱 실행

```bash
streamlit run app.py
```

5. OpenAI API 키

앱 사이드바에서 `OpenAI API Key` 입력란에 키를 입력하거나, 환경변수 `OPENAI_API_KEY`로 설정하세요.

## 배포
- Streamlit Cloud 또는 다른 PaaS에 배포할 수 있습니다.

## 보안 메모
- API 키를 서버에 저장하지 마세요.
- 업로드 파일 삭제/검증을 추가하세요.
