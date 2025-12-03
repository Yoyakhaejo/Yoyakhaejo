# app/pages/4_MakingQuiz.py
import streamlit as st
import openai
import tempfile
import os
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

# 빠른 유효성 검사: API Key 및 업로드 자료 존재 확인
if not st.session_state["user_api_key"]:
    st.warning("⚠️ 먼저 왼쪽 설정에서 OpenAI API Key를 입력해주세요!")
    st.stop()

if st.session_state["uploaded_content"] is None:
    st.warning("📂 먼저 '강의 자료 업로드' 페이지에서 자료를 업로드해주세요!")
    st.stop()

content_type = st.session_state["content_type"]
st.info(f"업로드된 자료 유형: **{content_type}**")

# --- 보조: 업로드된 자료에서 텍스트를 뽑아오는 함수 ---
def extract_text_from_uploaded():
    data = st.session_state["uploaded_content"]
    ctype = st.session_state["content_type"]

    # 텍스트 직접 입력 (string)
    if ctype == "text":
        return data

    # 유튜브 링크
    if ctype == "youtube":
        return f"유튜브 영상 URL: {data}\n(영상의 자막/요약을 기반으로 퀴즈를 만들어주세요.)"

    # 파일(PDF/PPT 등)
    if ctype in ("pdf", "ppt", "pptx"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ctype}") as tmp:
                tmp.write(data.getbuffer())
                tmp_path = tmp.name
            return (
                f"파일 경로: {tmp_path}\n"
                "※ 현재는 파일 경로만 전달합니다. 텍스트 추출은 업로드 단계에서 처리해주세요."
            )
        except Exception as e:
            return f"파일 처리 중 오류: {e}"

    return "알 수 없는 자료 형식입니다."

material_text = extract_text_from_uploaded()

# 퀴즈 옵션 설정
st.subheader("🎯 생성할 퀴즈 설정")
quiz_type = st.selectbox(
    "문제 유형",
    ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"],
)
difficulty = st.select_slider("난이도", ["쉬움", "보통", "어려움"], value="보통")

st.markdown("---")

st.write("버튼을 누르면 OpenAI ChatCompletion API를 호출하여 퀴즈를 생성합니다.")

# 실제 퀴즈 생성 버튼
if st.button("🚀 퀴즈 생성하기"):
    try:
        # openai 구버전 방식 — 세션에 키만 설정하면 됨
        openai.api_key = st.session_state["user_api_key"]

        # 프롬프트 구성
        prompt = f"""
아래 강의자료를 바탕으로 {quiz_type} 퀴즈를 생성해줘.
난이도: {difficulty}

--- 강의자료 ---
{material_text}
-----------------

요구사항:
- 객관식이면 보기 4개 포함
- 각 문제마다 '정답:' 으로 정답을 명시
- 가능한 한 간결하고 명확한 문제 문장으로 작성
- 출력은 사람이 읽기 쉬운 텍스트 형식으로 해줘
"""

        with st.spinner("AI가 퀴즈를 생성하고 있습니다..."):

            # ChatCompletion (openai==1.3.0 완전 호환)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )

            # 응답 텍스트 추출
            quiz_text = (
                response["choices"][0]["message"]["content"]
                if "choices" in response and len(response["choices"]) > 0
                else str(response)
            )

            # 화면 출력 + 저장
            st.success("퀴즈 생성이 완료되었습니다!")
            st.markdown("### 📘 생성된 퀴즈")
            st.code(quiz_text, language="text")
            st.session_state["generated_quiz"] = quiz_text

    except Exception as exc:
        st.error("퀴즈 생성 중 오류가 발생했습니다. 콘솔 로그를 확인하세요.")
        st.exception(exc)
        print("=== OpenAI 호출 예외 ===")
        traceback.print_exc()

# 생성된 퀴즈가 있으면 다운로드 버튼 제공
if st.session_state.get("generated_quiz"):
    st.download_button(
        "🔽 퀴즈 다운로드 (.txt)",
        st.session_state["generated_quiz"],
        file_name="generated_quiz.txt",
        mime="text/plain",
    )
