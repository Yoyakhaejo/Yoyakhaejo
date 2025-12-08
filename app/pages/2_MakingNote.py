import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_youtube_transcript

st.title("2. 강의노트 만들기")
st.write("업로드한 자료를 요약해서 강의노트를 생성하는 페이지입니다.")

# -------------------------------------------------
# 0. httpx.Client 패치 (proxies 인자 무시용)
#    이전에 생기던 "unexpected keyword argument 'proxies'" 방지
# -------------------------------------------------
try:
    import httpx as _httpx

    _OriginalClient = _httpx.Client

    class _PatchedClient(_OriginalClient):
        def __init__(self, *args, **kwargs):
            # openai 내부에서 넘기는 proxies 인자를 무시
            kwargs.pop("proxies", None)
            super().__init__(*args, **kwargs)

    _httpx.Client = _PatchedClient

except Exception:
    # httpx가 없거나, 다른 이유로 실패해도 앱은 계속 동작하게 둔다.
    pass

# -------------------------------------------------
# 1. OpenAI 임포트
# -------------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    st.error(
        "⚠️ openai 패키지가 설치되어 있지 않습니다.\n\n"
        "requirements.txt 에 아래 항목이 있는지 확인하세요.\n\n"
        "    streamlit\n"
        "    openai\n"
        "    httpx\n"
    )
    st.stop()

# -------------------------------------------------
# 2. 1번 페이지에서 저장한 Session State 읽기
# -------------------------------------------------
api_key = st.session_state.get("user_api_key", "")
uploaded_content = st.session_state.get("uploaded_content", None)
content_type = st.session_state.get("content_type", None)

if not api_key or uploaded_content is None or content_type is None:
    st.info(
        "아직 1번 페이지에서 API Key 입력과 강의자료 업로드가 완료되지 않았습니다.\n\n"
        "먼저 1번 페이지(📂 강의 자료 업로드)에서:\n"
        "1) OpenAI API Key 입력\n"
        "2) 강의자료 업로드 (파일 / 유튜브 링크 / 텍스트 중 택1)\n"
        "을 완료한 뒤, 다시 이 페이지로 돌아와 주세요."
    )
    st.stop()

# -------------------------------------------------
# 3. 업로드 타입에 따라 user 메시지 생성
# -------------------------------------------------
def build_user_input(uploaded_content, content_type: str) -> str:
    """
    1번 페이지에서 저장한 uploaded_content와 content_type을 받아
    모델에 넘길 user 메시지 텍스트를 만들어준다.
    """

    # (1) 텍스트 직접 입력
    if content_type == "text":
        return (
            "다음 텍스트는 한 편의 강의 내용을 옮겨 적은 것이다.\n"
            "이 텍스트 전체를 기반으로 강의노트를 작성해줘.\n\n"
            f"{uploaded_content}"
        )

    # (2) 유튜브 링크
    if content_type == "youtube":
        # utils.py의 함수를 사용하여 자막 추출
        script, error_msg = get_youtube_transcript(uploaded_content)
        
        if error_msg:
            return f"오류 발생: {error_msg}\n(자막이 없는 영상이거나 유효하지 않은 링크입니다.)"
            
        return (
            "다음은 유튜브 강의 영상의 자막 스크립트이다.\n"
            "이 내용을 바탕으로 대학 강의노트 형식으로 정리해줘.\n"
            "참고: 영상 내용을 직접 볼 수 없으므로 자막에 의존하여 작성함.\n\n"
            f"--- 강의 자막 시작 ---\n{script}\n--- 강의 자막 끝 ---"
        )

    # (3) 파일(PDF/PPT/영상 등)
    file_name = getattr(uploaded_content, "name", "알 수 없는 파일명")
    return (
        "사용자가 대학 강의자료 파일을 업로드했다.\n"
        "현재 앱에서는 파일의 원문 텍스트를 직접 읽어오지는 못하지만,\n"
        "일반적인 대학 강의 슬라이드/자료라고 가정하고 강의노트를 작성해줘.\n\n"
        f"파일 이름: {file_name}\n"
        f"파일 타입(확장자): {content_type}\n\n"
        "※ 실제 슬라이드 내용을 모르는 상태이므로, 과도하게 구체적인 예시는 피하고,\n"
        "대학생 대상의 일반적인 강의 구조(개요-핵심 개념-예시/응용-체크리스트)에 맞게 작성해줘."
    )

# -------------------------------------------------
# 4. OpenAI Chat Completions API로 강의노트 생성
#    (responses.create 대신 chat.completions.create 사용)
# -------------------------------------------------
def generate_lecture_notes(api_key: str, uploaded_content, content_type: str) -> str:
    """
    OpenAI Chat Completions API를 이용해서 강의노트를 생성한다.
    """
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "너는 대학 강의를 정리해 주는 조교야.\n"
        "사용자가 업로드한 강의자료(텍스트, 유튜브 링크, PDF/PPT 등)를 기반으로 "
        "다음 형식의 강의노트를 만들어줘.\n\n"
        "1. 강의 개요\n"
        "   - 이 강의의 주제 한 줄 요약\n"
        "   - 강의에서 다루는 핵심 질문/목표\n\n"
        "2. 핵심 개념 정리\n"
        "   - 개념 1: 정의 + 중요 포인트\n"
        "   - 개념 2: 정의 + 중요 포인트\n"
        "   - … (필요한 만큼)\n\n"
        "3. 예시 및 응용\n"
        "   - 강의에서 나올 법한 대표 예시나 사례 정리\n"
        "   - 학생이 실무/현실에서 어떻게 써먹을 수 있는지\n\n"
        "4. 강의 체크리스트\n"
        "   - 복습할 때 스스로 물어볼 만한 질문 3~5개\n\n"
        "문장은 한국어로, 너무 장황하지 않게 A4 1~2장 분량 느낌으로 정리해줘."
    )

    user_input = build_user_input(uploaded_content, content_type)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # 모델은 필요하면 gpt-4o 등으로 변경 가능
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.3,
    )

    # chat.completions의 기본 출력 형식
    return completion.choices[0].message.content

# -------------------------------------------------
# 5. UI 안내 + 버튼
# -------------------------------------------------
if content_type != "text":
    st.info(
        "이 페이지에서는 1번에서 업로드한 강의자료를 바탕으로,\n"
        "① 강의 개요, ② 핵심 개념, ③ 예시와 응용, ④ 복습용 체크리스트를\n"
        "자동으로 정리해 ‘강의노트’ 형태로 만들어 줍니다.\n\n"
        "복잡한 강의 내용을 구조화해서 보여 주기 때문에\n"
        "복습, 시험 대비, 과제 정리용 요약본으로 바로 활용할 수 있습니다."
    )

st.write("버튼을 누르면 1번 페이지에서 업로드한 자료를 기반으로 강의노트를 자동으로 생성합니다.")

if st.button("📚 강의노트 생성하기"):
    try:
        with st.spinner("강의노트를 생성하는 중입니다..."):
            notes = generate_lecture_notes(api_key, uploaded_content, content_type)
    except Exception as e:
        st.error(f"강의노트 생성 중 오류가 발생했습니다:\n\n{e}")
    else:
        st.subheader("✅ 생성된 강의노트")
        st.text_area("강의노트", value=notes, height=400)

        st.session_state["lecture_notes"] = notes
        st.success("강의노트가 생성되어 세션에 저장되었습니다!")
