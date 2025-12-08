# utils.py
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from urllib.parse import urlparse, parse_qs

def extract_youtube_video_id(url: str):
    """
    다양한 형태의 유튜브 URL에서 video_id 추출
    """
    parsed = urlparse(url)

    # https://youtu.be/VIDEOID
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")

    # https://www.youtube.com/watch?v=VIDEO_ID
    if parsed.hostname and "youtube.com" in parsed.hostname:
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]

    return None


def get_youtube_transcript(url: str):
    """
    list_transcripts()가 없는 구버전 youtube-transcript-api에서도 안전하게 작동하도록 작성한 함수.
    언어 우선순위: 한국어 → 영어 → 자동 생성
    """

    video_id = extract_youtube_video_id(url)
    if not video_id:
        return None, "유효한 유튜브 URL이 아닙니다."

    # 우선순위: 한국어, 영어
    lang_priority = [
        ['ko'],      # 한국어
        ['ko', 'ko-KR'],
        ['en'],      # 영어
        ['en', 'en-US'],
    ]

    # 1) 먼저 언어 기반으로 시도
    for langs in lang_priority:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
            text = " ".join([item["text"] for item in transcript])
            return text, None
        except NoTranscriptFound:
            continue
        except TranscriptsDisabled:
            return None, "해당 영상은 자막이 비활성화되어 있습니다."
        except Exception:
            continue

    # 2) 자동 생성(auto-generated) 자막 시도
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # auto-generated 중 ko, en 우선
        for lang in ["ko", "en"]:
            try:
                generated = transcript_list.find_generated_transcript([lang])
                data = generated.fetch()
                text = " ".join([item["text"] for item in data])
                return text, None
            except:
                continue
    except:
        pass  # list_transcripts가 없는 환경에서는 여기로 옴 → 무시

    # 3) 어떤 방식도 실패
    return None, "해당 영상에서 이용 가능한 자막을 찾을 수 없습니다."
