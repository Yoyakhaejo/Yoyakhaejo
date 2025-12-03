import streamlit as st
from openai import OpenAI
import tempfile
import os

# 페이지 설정
st.set_page_config(page_title="퀴즈 생성 - 요약해줘", layout="wide")


# --- 1. Session State 초기화 ---
st.session_state.setdefault("user_api_key", "")
st.session_state.setdefault("uploaded_content", None)
st.session_state.setdefault("content_type", None)


# --- 2. UI 안내 ---
st.title("📝 AI 기반 연습 문제 생성")
st.markdown("업로드된 강의자료를 기반으로 AI가 퀴즈를 생성합니다.")


# --- 3. API Key 확인 ---
if not st.session_state["user_api_key"]:
    st.warning("⚠️ 먼저 왼쪽 설정에서 OpenAI API Key를 입력해주세요!")
    st.stop()


# --- 4. 업로드된 자료 확인 ---
if st.session_state["uploaded_content"] is None:
    st.warning("📂 먼저 '강의 자료 업로드' 페이지에서 자료를 업로드해주세요!")
    st.stop()

content_type = st.session_state["content_type"]
st.info(f"업로드된 자료 유형: **{content_type}**")


# --- 5. 텍스트 추출 함수 ---
def extract_text_from_uploaded():
    data = st.session_state["uploaded_content"]
    ctype = st.session_state["content_type"]

    # 텍스트 직접 입력
    if ctype == "text":
        return data

    # 유튜브
    if ctype == "youtube":
        return f"다음 유튜브 내용을 기반으로 퀴즈를 만들어줘:\n{data}"

    # PDF / PPT
    if ctype in ["pdf", "ppt", "pptx"]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ctype}") as tmp:
            tmp.write(data.getbuffer())
            tmp_path = tmp.name

        return (
            f"여기 강의자료 파일({ctype})이 있어. 이 파일 내용을 기반으로 퀴즈를 만들어줘.\n"
            f"파일 경로: {tmp_path}\n"
            "(파일 내용은 AI가 직접 접근할 수 없으므로 보통은 업로드 페이지에서 텍스트를 추출해 넘기는 방식을 사용합니다.)"
        )

    return "알 수 없는 자료 형식입니다."


material_text = extract_text_from_uploaded()


# --- 6. 퀴즈 옵션 선택 ---
st.subheader("🎯 생성할 퀴즈 설정")

quiz_type = st.selectbox(
    "문제 유형 선택",
    ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"],
)

difficulty = st.select_slider(
    "난이도 설정",
    ["쉬움", "보통", "어려움"],
    value="보통",
)


# --- 7. 퀴즈 생성 버튼 ---
if st.button("🚀 퀴즈 생성하기"):

    # 🔥 여기에서만 OpenAI() 생성해야 함 (Streamlit Cloud 호환)
    client = OpenAI(
        api_key=st.session_state["user_api_key"],
        base_url="https://api.openai.com/v1"
    )

    prompt = f"""
    아래 강의자료를 기반으로 {quiz_type} 퀴즈를 생성해줘.
    난이도는 {difficulty} 수준으로 해줘.

    --- 강의자료 내용 ---
    {material_text}
    ---------------------

    각 문제는 번호를 붙이고,
    객관식일 경우 보기를 포함하고,
    정답을 반드시 마지막에 명확하게 표시해줘.
    """

    with st.spinner("AI가 퀴즈를 생성하는 중입니다..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "너는 교육용 퀴즈 제작 전문가다."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            quiz_output = response.choices[0].message["content"]

            st.success("퀴즈 생성 완료! 🎉")
            st.markdown("### 📘 생성된 퀴즈")
            st.write(quiz_output)

        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
