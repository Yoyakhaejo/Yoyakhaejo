import streamlit as st
from openai import OpenAI
import tempfile
import traceback
import fitz  # PyMuPDF (PDF 텍스트 추출용)

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


# -------------------------------
# 🔵 PDF 텍스트 추출 함수
# -------------------------------
def extract_text_from_pdf(file_bytes):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()
    return text


# -------------------------------
# 🔵 업로드 자료 텍스트 추출
# -------------------------------
def extract_text_from_uploaded():
    data = st.session_state["uploaded_content"]
    ctype = st.session_state["content_type"]

    # 텍스트 입력
    if ctype == "text":
        return data

    # 유튜브 링크
    if ctype == "youtube":
        return (
            f"유튜브 영상 URL: {data}\n"
            "(이 영상을 분석해 핵심 내용을 기반으로 연습문제를 생성해줘.)"
        )

    # PDF 파일
    if ctype == "pdf":
        try:
            return extract_text_from_pdf(data.getvalue())
        except Exception as e:
            return f"[PDF 추출 오류] {e}"

    # 기타 파일 (ppt, pptx 등)
    # 여기서는 임시 파일 경로 전달
    if ctype in ("ppt", "pptx", "mp4", "mov", "avi"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ctype}") as tmp:
                tmp.write(data.getbuffer())
                tmp_path = tmp.name
            return (
                f"파일 경로: {tmp_path}\n"
                "※ 현재 ppt/pptx/영상 파일은 내용 추출 기능이 없습니다. 파일 정보를 참고하여 문제를 생성해주세요."
            )
        except:
            return "파일 처리 오류 발생."

    return "알 수 없는 자료 형식입니다."


# 변환된 자료 텍스트
material_text = extract_text_from_uploaded()


# -------------------------------
# 🔵 퀴즈 옵션 UI
# -------------------------------
st.subheader("🎯 생성할 퀴즈 설정")
quiz_type = st.selectbox(
    "문제 유형", ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"],
)
difficulty = st.select_slider("난이도", ["쉬움", "보통", "어려움"], value="보통")

st.markdown("---")


# ==========================================================
# 🔵 퀴즈 생성
# ==========================================================
if st.button("🚀 퀴즈 생성하기"):
    try:
        client = OpenAI(api_key=st.session_state["user_api_key"])

        prompt = f"""
아래 강의자료를 바탕으로 {quiz_type} 퀴즈를 생성해줘.
난이도: {difficulty}

--- 강의자료 ---
{material_text}
------------------

출력 형식 규칙(반드시 지켜라):
- 각 문제는 "문제 1:" 이런 형식으로 시작
- 객관식이면 보기 4개 포함
- 마지막 줄은 반드시 "//정답: 정답내용" 형식으로 끝낼 것
- 불필요한 설명, 사과문, 안내문 금지
- PDF를 못 읽는다는 문구는 절대 출력하지 마라
"""

        with st.spinner("AI가 퀴즈를 생성 중입니다..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )

            quiz_text = response.choices[0].message.content
            st.session_state["generated_quiz"] = quiz_text

            st.success("퀴즈 생성 완료!")
            st.markdown("### 📘 생성된 퀴즈")

            # -------------------------------
            # 정답 숨김 기능
            # -------------------------------
            lines = quiz_text.split("\n")
            buffer = []

            for line in lines:
                if "//정답:" in line:
                    q = "\n".join(buffer).strip()
                    a = line.replace("//정답:", "").strip()

                    with st.expander(q):
                        st.success(f"정답: {a}")

                    buffer = []
                else:
                    buffer.append(line)

    except Exception as exc:
        st.error("퀴즈 생성 중 오류가 발생했습니다.")
        st.exception(exc)
        traceback.print_exc()


# ==========================================================
# 🔵 다운로드 버튼
# ==========================================================
if st.session_state.get("generated_quiz"):
    st.download_button(
        "🔽 퀴즈 다운로드 (.txt)",
        st.session_state["generated_quiz"],
        file_name="generated_quiz.txt",
        mime="text/plain",
    )
