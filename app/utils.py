from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def get_youtube_transcript(url):
    """
    유튜브 URL을 입력받아 자막 텍스트를 반환하는 함수
    성공 시: (텍스트, None) 반환
    실패 시: (None, 에러메시지) 반환
    """
    try:
        # -------------------------
        # 1. URL에서 video_id 추출
        # -------------------------
        parsed_url = urlparse(url)
        video_id = None

        if parsed_url.hostname == "youtu.be":
            video_id = parsed_url.path[1:]
        else:
            video_id = parse_qs(parsed_url.query).get("v", [None])[0]

        if not video_id:
            return None, "유효하지 않은 유튜브 URL입니다."

        # -----------------------------------------
        # 2. transcript 리스트 가져오기 (신버전 API)
        # -----------------------------------------
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

        # 언어 우선순위: 한국어 → 영어
        for lang in ["ko", "en"]:
            try:
                t = transcripts.find_transcript([lang])
                data = t.fetch()  # 실제 자막 가져오기
                text = " ".join([item["text"] for item in data])
                return text, None
            except:
                pass  # 해당 언어 없음 → 다음 언어 시도

        # -------------------------
        # 3. 자동 생성 자막 fallback
        # -------------------------
        try:
            t = transcripts.find_generated_transcript(["ko", "en"])
            data = t.fetch()
            text = " ".join([item["text"] for item in data])
            return text, None
        except:
            return None, "사용 가능한 자막(수동/자동)이 없습니다."

    except Exception as e:
        return None, f"자막을 가져올 수 없습니다. (자막 없음 또는 접근 제한됨): {e}"
