import streamlit as st
from openai import OpenAI
import tempfile
import traceback
import fitz  # PyMuPDF

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
# PDF 텍스트 추출 함수
# -------------------------------
def extract_text_from_pdf(file_bytes):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()
    return text


# -------------------------------
# 업로드 자료 텍스트 추출
# -------------------------------
def extract_text_from_uploaded():
    data = st.session_state["uploaded_content"]
    ctype = st.session_state["content_type"]

    if ctype == "text":
        return data
    if ctype == "youtube":
        return f"유튜브 영상 URL: {data}\n(이 영상의 핵심 내용을 기반으로 퀴즈를 생성해줘.)"
    if ctype == "pdf":
        try:
            return extract_text_from_pdf(data.getvalue())
        except Exception as e:
            return f"[PDF 추출 오류] {e}"
    if ctype in ("ppt", "pptx", "mp4", "mov", "avi"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ctype}") as tmp:
                tmp.write(data.getbuffer())
                tmp_path = tmp.name
            return f"파일 경로: {tmp_path}\n※ ppt/pptx/영상 파일은 내용 추출 기능이 없습니다."
        except:
            return "파일 처리 오류 발생."
    return "알 수 없는 자료 형식입니다."


material_text = extract_text_from_uploaded()


# -------------------------------
# 퀴즈 옵션 UI
# -------------------------------
st.subheader("🎯 생성할 퀴즈 설정")
quiz_type = st.selectbox(
    "문제 유형", ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"],
)
difficulty = st.select_slider("난이도", ["쉬움", "보통", "어려움"], value="보통")
st.markdown("---")
st.write("버튼을 누르면 OpenAI Chat Completions API가 호출됩니다.")


# ==========================================================
# 퀴즈 생성
# ==========================================================
if st.button("🚀 퀴즈 생성하기"):
    try:
        client = OpenAI(api_key=st.session_state["user_api_key"])

        # 문제 유형별 포맷 지시
        prompt = f"""
아래 강의자료를 바탕으로 {quiz_type} 퀴즈를 생성해줘.
난이도: {difficulty}

--- 강의자료 ---
{material_text}
------------------

출력 형식 규칙:
1. 문제 유형:
   - 객관식: 문제 + 보기 4개(A,B,C,D) + "//정답: 정답문자"
   - 단답형: 문제만 작성 후 반드시 별도 줄에 "//정답: 정답" 작성
   - 서술형: 문제 작성 후 별도 줄에 "//정답: 정답 내용"
   - 혼합형: 유형 섞어서 5문항
2. 문제 번호 포함: "문제 1:", "문제 2:" 등
3. 문제와 정답은 항상 별도 줄로 구분
4. 불필요한 안내 문구 금지
"""

        with st.spinner("AI가 퀴즈를 생성 중입니다..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500,
            )

            quiz_text = response.choices[0].message.content
            st.session_state["generated_quiz"] = quiz_text
            st.success("퀴즈 생성 완료!")
            st.markdown("### 📘 생성된 퀴즈")

            # -------------------------------
            # 문제/정답 분리 + 정답 클릭 표시(expander)
            # -------------------------------
            lines = quiz_text.split("\n")
            buffer = []
            question_count = 1

            for line in lines:
                if "//정답:" in line:
                    question = "\n".join(buffer).strip()
                    answer = line.replace("//정답:", "").strip()

                    # 문제는 항상 화면에 표시
                    st.write(f"**문제 {question_count}:**")
                    st.write(question)

                    # 정답만 expander로 숨기기
                    with st.expander("정답 보기", expanded=False):
                        st.success(answer)

                    buffer = []
                    question_count += 1
                else:
                    buffer.append(line)

    except Exception as exc:
        st.error("퀴즈 생성 중 오류가 발생했습니다.")
        st.exception(exc)
        traceback.print_exc()


# ==========================================================
# 다운로드 버튼
# ==========================================================
if st.session_state.get("generated_quiz"):
    st.download_button(
        "🔽 퀴즈 다운로드 (.txt)",
        st.session_state["generated_quiz"],
        file_name="generated_quiz.txt",
        mime="text/plain",
    )
