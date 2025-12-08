# utils.py
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from urllib.parse import urlparse, parse_qs

def get_youtube_transcript(url):
    """
    유튜브 URL을 입력받아 자막 텍스트를 반환.
    성공: (text, None)
    실패: (None, error_msg)
    """
    try:
        # --- 1. 영상 ID 파싱 ---
        parsed_url = urlparse(url)
        if parsed_url.hostname == "youtu.be":
            video_id = parsed_url.path[1:]
        else:
            video_id = parse_qs(parsed_url.query).get("v", [None])[0]

        if not video_id:
            return None, "유효하지 않은 YouTube URL입니다."

        # --- 2. 자막 목록 확인 ---
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        except Exception:
            return None, "해당 영상에서 이용 가능한 자막이 없습니다."

        # --- 3. 언어 우선순위: 한국어 → 영어 → 자동생성(en) ---
        preferred_langs = ["ko", "ko-KR", "en", "en-US"]

        transcript = None
        for lang in preferred_langs:
            try:
                transcript = transcripts.find_transcript([lang])
                break
            except:
                continue

        # 자동생성(en) 시도
        if transcript is None:
            try:
                transcript = transcripts.find_generated_transcript(["en"])
            except:
                return None, "해당 영상은 자막이 없거나 자동생성 자막도 지원되지 않습니다."

        # --- 4. 자막 추출 ---
        script_entries = transcript.fetch()
        text = " ".join([entry["text"] for entry in script_entries])

        return text, None

    except Exception as e:
        return None, f"예상치 못한 오류: {e}"
