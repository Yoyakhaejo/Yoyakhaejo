import streamlit as st

st.title("2. 강의노트 만들기")
st.write("업로드한 자료를 요약해서 강의노트를 생성하는 페이지입니다.")

# openai 패키지 임포트 (설치 안 되어 있으면 안내 메시지)
try:
    from openai import OpenAI
except ImportError:
    st.error(
        "⚠️ openai 패키지가 설치되어 있지 않습니다.\n\n"
        "터미널이나 requirements.txt 에서 아래를 설치해 주세요.\n\n"
        "    pip install openai\n"
    )
    st.stop()

# --- 1. 1번 페이지에서 저장해 둔 Session State 읽기 ---
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


# --- 2. 업로드 타입에 따라 user 메시지 생성 ---
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
        return (
            "사용자가 아래 유튜브 링크의 강의를 들었다고 가정하자.\n"
            "실제 영상이나 자막에 직접 접근할 수는 없지만, 일반적인 대학 강의 구성을 바탕으로\n"
            "해당 링크의 강의가 있다고 가정하고 강의노트를 작성해줘.\n\n"
            f"유튜브 URL: {uploaded_content}\n\n"
            "※ 실제 영상 내용은 알 수 없으므로, 너무 구체적인 숫자/예시는 피하고 "
            "전형적인 강의 구조에 맞춰 정리해줘."
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


def generate_lecture_notes(api_key: str, uploaded_content, content_type: str) -> str:
    """
    OpenAI Responses API를 이용해서 강의노트를 생성한다.
    여기서 client 생성까지 한 번에 처리하고, 문제가 생기면 에러 메시지를 반환.
    """
    # 1) 클라이언트 생성 (여기서 TypeError 터지는 걸 방어)
    try:
        client = OpenAI(api_key=api_key)
    except TypeError as e:
        # httpx 버전/환경 문제로 인한 TypeError 방어
        raise RuntimeError(
            "OpenAI 클라이언트 생성 중 오류가 발생했습니다. "
            "requirements.txt 에서 openai / httpx 버전을 다시 확인해 주세요.\n\n"
            f"원래 에러 메시지: {e}"
        )

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

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.3,
    )

    # Python SDK에서 제공하는 편의 프로퍼티
    return response.output_text


# --- 3. UI 안내 + 버튼 ---
if content_type != "text":
    st.warning(
        "현재 버전에서는 '📝 텍스트 직접 입력' 탭으로 붙여넣은 경우에 "
        "가장 정확한 강의노트를 생성할 수 있습니다.\n"
        "PDF/PPT/영상/유튜브 링크는 아직 자동으로 내용을 추출하지 않고, "
        "일반적인 강의 형식을 기준으로 노트를 만들어 줍니다."
    )

st.write("버튼을 누르면 1번 페이지에서 업로드한 자료를 기반으로 강의노트를 자동으로 생성합니다.")

if st.button("📚 강의노트 생성하기"):
    try:
        with st.spinner("강의노트를 생성하는 중입니다..."):
            notes = generate_lecture_notes(api_key, uploaded_content, content_type)
    except RuntimeError as e:
        # OpenAI 클라이언트 생성 오류 등
        st.error(str(e))
        st.stop()
    except Exception as e:
        # 기타 예기치 못한 오류
        st.error(f"강의노트 생성 중 예기치 못한 오류가 발생했습니다:\n\n{e}")
        st.stop()

    st.subheader("✅ 생성된 강의노트")
    st.text_area("강의노트", value=notes, height=400)

    st.session_state["lecture_notes"] = notes
    st.success("강의노트가 생성되어 세션에 저장되었습니다!")
