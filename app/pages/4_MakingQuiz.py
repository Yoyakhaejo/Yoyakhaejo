# app/pages/4_MakingQuiz.py
import streamlit as st
from openai import OpenAI
import tempfile
import traceback

# 페이지 설정
st.set_page_config(page_title="퀴즈 생성 - 요약해줘", layout="wide")

# --- Session state 기본값 보장 ---
st.session_state.setdefault("user_api_key", "")
st.session_state.setdefault("uploaded_content", None)
st.session_state.setdefault("content_type", None)
st.session_state.setdefault("generated_quiz", None)

st.title("📝 AI 기반 연습 문제 생성")
st.markdown("업로드된 강의자료를 바탕으로 AI가 연습 문제를 생성합니다.")

# 빠른 유효성 검사
if not st.session_state["user_api_key"]:
    st.warning("⚠️ 먼저 왼쪽 설정에서 OpenAI API Key를 입력해주세요!")
    st.stop()

if st.session_state["uploaded_content"] is None:
    st.warning("📂 먼저 '강의 자료 업로드' 페이지에서 자료를 업로드해주세요!")
    st.stop()

content_type = st.session_state["content_type"]
st.info(f"업로드된 자료 유형: **{content_type}**")

# --- 업로드 자료 텍스트 추출 ---
def extract_text_from_uploaded():
    data = st.session_state["uploaded_content"]
    ctype = st.session_state["content_type"]

    if ctype == "text":
        return data

    if ctype == "youtube":
        return f"유튜브 영상 URL: {data}\n(이 영상의 핵심 내용을 기반으로 퀴즈를 생성해줘.)"

    if ctype in ("pdf", "ppt", "pptx"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ctype}") as tmp:
                tmp.write(data.getbuffer())
                tmp_path = tmp.name
            return (
                f"파일 경로: {tmp_path}\n"
                "※ 현재는 텍스트 추출을 하지 않고 파일 경로만 전달합니다."
            )
        except Exception as e:
            return f"파일 처리 오류: {e}"

    return "알 수 없는 자료 형식입니다."

material_text = extract_text_from_uploaded()

# --- 퀴즈 옵션 ---
st.subheader("🎯 생성할 퀴즈 설정")
quiz_type = st.selectbox(
    "문제 유형", ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"],
)
difficulty = st.select_slider("난이도", ["쉬움", "보통", "어려움"], value="보통")

st.markdown("---")

st.write("버튼을 누르면 OpenAI Chat Completions API가 호출됩니다.")

# === 퀴즈 생성 ===
if st.button("🚀 퀴즈 생성하기"):
    try:
        # v1.x 전용 클라이언트
        client = OpenAI(api_key=st.session_state["user_api_key"])

        prompt = f"""
아래 강의자료를 바탕으로 {quiz_type} 퀴즈를 생성해줘.
난이도: {difficulty}

--- 강의자료 ---
{material_text}
------------------

요구사항:
- 객관식이면 보기 4개 포함
- 각 문제마다 '정답:' 으로 정답 명시
- 간결하고 명확한 문제 문장
- 사람이 읽기 쉬운 텍스트 형식
"""

        with st.spinner("AI가 퀴즈를 생성 중입니다..."):
            # v1.x 문법 — Chat Completions API
            response = client.chat.completions.create(
                model="gpt-4o-mini",   # 원하는 모델로 변경 가능
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )

            quiz_text = response.choices[0].message["content"]

            st.success("퀴즈 생성 완료!")
            st.markdown("### 📘 생성된 퀴즈")
            st.code(quiz_text, language="text")

            st.session_state["generated_quiz"] = quiz_text

    except Exception as exc:
        st.error("퀴즈 생성 중 오류가 발생했습니다. 콘솔을 확인하세요.")
        st.exception(exc)
        print("=== OpenAI 호출 오류 ===")
        traceback.print_exc()

# --- 다운로드 ---
if st.session_state.get("generated_quiz"):
    st.download_button(
        "🔽 퀴즈 다운로드 (.txt)",
        st.session_state["generated_quiz"],
        file_name="generated_quiz.txt",
        mime="text/plain",
    )
