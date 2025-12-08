# utils.py
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def get_youtube_transcript(url):
    """
    유튜브 URL을 입력받아 자막 텍스트를 반환하는 함수
    성공 시: (텍스트, None) 반환
    실패 시: (None, 에러메시지) 반환
    """
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path[1:]
        else:
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]
        
        if not video_id:
            return None, "유효하지 않은 유튜브 URL입니다."

        # 자막 가져오기 (한국어 -> 영어 순)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        
        full_text = " ".join([entry['text'] for entry in transcript_list])
        return full_text, None

    except Exception as e:
        return None, f"자막을 가져올 수 없습니다. (영상에 자막이 없거나 접근 제한됨): {e}"