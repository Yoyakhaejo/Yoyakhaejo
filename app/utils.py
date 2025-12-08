# utils.py
import re
from urllib.parse import urlparse, parse_qs

# import inside try so we can show better error messages if library missing
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception as e:
    # If the import fails, we'll raise later when function is used.
    YouTubeTranscriptApi = None
    _import_error = e

def extract_video_id(url: str):
    """
    유튜브 URL에서 video id(11자리) 추출
    """
    if not url:
        return None
    parsed = urlparse(url)
    # youtu.be/ID
    if parsed.hostname and parsed.hostname.endswith("youtu.be"):
        return parsed.path.lstrip("/")
    # youtube.com/watch?v=ID or other params
    qs = parse_qs(parsed.query)
    if "v" in qs:
        return qs["v"][0]
    # embed URL
    m = re.search(r"embed/([a-zA-Z0-9_-]{11})", url)
    if m:
        return m.group(1)
    # fallback: try to find 11-char id anywhere
    m2 = re.search(r"([a-zA-Z0-9_-]{11})", url)
    if m2:
        return m2.group(1)
    return None

def get_youtube_transcript(url: str):
    """
    유튜브 URL을 입력받아 자막 텍스트를 반환하는 함수
    반환: (text_or_None, error_message_or_None)
    여러 버전의 youtube_transcript_api를 지원하도록 폴백 로직 포함.
    """
    if YouTubeTranscriptApi is None:
        return None, f"youtube_transcript_api 라이브러리를 import할 수 없습니다: {_import_error}"

    video_id = extract_video_id(url)
    if not video_id:
        return None, "유효한 유튜브 URL이 아닙니다."

    errors = []  # 각 방식별 예외 메시지 모음 (디버깅용)
    # 1) 최신 권장 방식: list_transcripts -> find_transcript -> fetch
    try:
        if hasattr(YouTubeTranscriptApi, "list_transcripts"):
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            # 언어 우선순위: 한국어 -> 영어 -> 자동 생성 한국어 -> 자동 생성 영어
            # find_transcript / find_generated_transcript 사용 시각화
            for lang in ["ko", "en"]:
                try:
                    t = transcripts.find_transcript([lang])
                    data = t.fetch()
                    text = " ".join([item.get("text", "") for item in data])
                    return text, None
                except Exception as e:
                    errors.append(f"find_transcript({lang}) 실패: {e}")
            # 자동 생성 자막 시도
            try:
                t = transcripts.find_generated_transcript(["ko", "en"])
                data = t.fetch()
                text = " ".join([item.get("text", "") for item in data])
                return text, None
            except Exception as e:
                errors.append(f"find_generated_transcript 실패: {e}")
        else:
            errors.append("YouTubeTranscriptApi.list_transcripts 없음")
    except Exception as e:
        errors.append(f"list_transcripts 호출 중 예외: {e}")

    # 2) 구버전/다른 시그니처: get_transcript(video_id, languages=[...])
    try:
        if hasattr(YouTubeTranscriptApi, "get_transcript"):
            try:
                # languages 인자 지원하는 경우
                data = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko", "en"])
                if data:
                    text = " ".join([item.get("text", "") for item in data])
                    return text, None
            except TypeError:
                # get_transcript는 있지만 languages 인자를 못받는 경우
                data = YouTubeTranscriptApi.get_transcript(video_id)
                if data:
                    text = " ".join([item.get("text", "") for item in data])
                    return text, None
            except Exception as e:
                errors.append(f"get_transcript 호출 실패: {e}")
        else:
            errors.append("YouTubeTranscriptApi.get_transcript 없음")
    except Exception as e:
        errors.append(f"get_transcript 시도 중 예외: {e}")

    # 3) 또 다른 후보 함수명: get_transcripts / get_transcript_list 등 (있으면 시도)
    alt_names = ["get_transcripts", "getTranscript", "get_transcript_list"]
    for name in alt_names:
        try:
            fn = getattr(YouTubeTranscriptApi, name, None)
            if callable(fn):
                try:
                    data = fn(video_id)
                    if data:
                        # data가 dict나 list 형식일 수 있음
                        if isinstance(data, dict) and "transcript" in data:
                            entries = data["transcript"]
                        else:
                            entries = data
                        text = " ".join([item.get("text", "") for item in entries])
                        return text, None
                except Exception as e:
                    errors.append(f"{name} 호출 실패: {e}")
        except Exception as e:
            errors.append(f"{name} 확인 중 예외: {e}")

    # 4) 최종 폴백: 직접 HTTP 요청을 시도하거나, 에러 메시지 반환
    # (여기서는 직접 요청은 구현하지 않고 상세 에러 메시지를 반환)
    err_msg = "자막을 가져오지 못했습니다. 시도한 방식들의 오류:\n" + "\n".join(errors)
    return None, err_msg
