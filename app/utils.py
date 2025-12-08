# utils.py
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from urllib.parse import urlparse, parse_qs

def extract_youtube_video_id(url: str):
    """
    다양한 형태의 유튜브 URL에서 video_id만 정상적으로 추출하는 함수
    """
    parsed = urlparse(url)

    # https://youtu.be/VIDEOID
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")

    # https://www.youtube.com/watch?v=VIDEO_ID
    if "youtube.com" in parsed.hostname:
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]

    return None


def get_youtube_transcript(url: str):
    """
    유튜브 자막을 안정적으로 가져오는 함수.
    성공하면: (script_text, None)
    실패하면: (None, error_message)
    """

    # ---------------------------
    # 1) URL에서 video_id 추출
    # ---------------------------
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return None, "유효한 유튜브 URL이 아닙니다."

    # ---------------------------
    # 2) 가능한 모든 자막 목록 조회
    # ---------------------------
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    except TranscriptsDisabled:
        return None, "해당 영상은 자막이 비활성화되어 있습니다."
    except NoTranscriptFound:
        return None, "이 영상에는 제공 가능한 자막 트랙이 없습니다."
    except Exception as e:
        return None, f"자막 목록을 가져오는 중 오류가 발생: {e}"

    # ---------------------------
    # 3) 언어 우선순위대로 자막 가져오기
    # ---------------------------
    preferred_languages = ["ko", "ko-KR", "ko-KR-auto", "en", "en-US", "en-US-auto"]

    transcript_obj = None

    # 언어 우선순위 탐색
    for lang in preferred_languages:
        try:
            transcript_obj = transcript_list.find_transcript([lang])
            break
        except:
            continue

    # 자동 생성(auto-generated)도 허용
    if not transcript_obj:
        try:
            transcript_obj = transcript_list.find_generated_transcript(["ko", "en"])
        except:
            pass

    if not transcript_obj:
        # 아무 자막도 찾을 수 없음
        available_langs = [t.language_code for t in transcript_list]
        return None, f"지원되는 자막이 없습니다. 제공 언어 목록: {available_langs}"

    # ---------------------------
    # 4) 실제 자막 텍스트 다운로드
    # ---------------------------
    try:
        transcript_data = transcript_obj.fetch()
        script = " ".join([entry["text"] for entry in transcript_data]).strip()
        return script, None

    except Exception as e:
        return None, f"자막을 가져오는 과정에서 오류 발생: {e}"
