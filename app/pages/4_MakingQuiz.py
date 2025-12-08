import streamlit as st
from openai import OpenAI
import tempfile
import traceback
import fitz  # PyMuPDF
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_youtube_transcript

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
# 업로드 자료 텍스트 추출 (이제 (text, error) 반환)
# -------------------------------
def extract_text_from_uploaded():
    """
    반환: (text_or_None, error_message_or_None)
    text_or_None: 실제 사용할 텍스트 (문제 생성에 쓸 수 있음)
    error_message_or_None: 문제가 있으면 문자열 반환 (예: "자막 없음")
    """
    data = st.session_state["uploaded_content"]
    ctype = st.session_state["content_type"]

    if ctype == "text":
        if not data or str(data).strip() == "":
            return None, "저장된 텍스트가 비어 있습니다."
        return data, None

    if ctype == "youtube":
        # utils.get_youtube_transcript()는 (script, error) 반환으로 가정
        script, error_msg = get_youtube_transcript(data)
        if error_msg:
            # 상세한 에러 메시지는 UI로 보여주고, 프롬프트에는 절대 포함하지 않음
            return None, f"유튜브 자막을 가져오지 못했습니다: {error_msg}"
        if not script or script.strip() == "":
            return None, "유튜브 자막이 비어있습니다."
        return script, None

    if ctype == "pdf":
        try:
            pdf_bytes = data.getvalue()
            text = extract_text_from_pdf(pdf_bytes)
            if not text or text.strip() == "":
                return None, "PDF에서 텍스트를 추출할 수 없거나 내용이 비어 있습니다."
            return text, None
        except Exception as e:
            return None, f"PDF 텍스트 추출 오류: {e}"

    if ctype in ("ppt", "pptx", "mp4", "mov", "avi"):
        # 현재는 추출 기능 미구현이므로 사용자에게 안내
        return None, f"{ctype} 파일은 현재 자동 텍스트 추출이 지원되지 않습니다. 텍스트를 직접 붙여넣거나 PDF로 변환해 업로드해주세요."

    return None, "알 수 없는 자료 형식입니다."


# material_text은 실제 텍스트 또는 None, 그리고 error_msg
material_text, material_error = extract_text_from_uploaded()

# 오류가 있으면 화면에 보여주고 더 이상 진행하지 않음
if material_error:
    st.error(f"자료 처리 문제: {material_error}")
    st.info("해결 방법 예시:\n• 영상의 자막(한국어/영어)이 있는지 확인\n• PDF의 경우 텍스트가 포함된 파일인지 확인\n• 또는 텍스트를 직접 붙여넣기(업로드 페이지)를 사용")
    st.stop()


# -------------------------------
# 퀴즈 옵션 UI
# -------------------------------
st.subheader("🎯 생성할 퀴즈 설정")
quiz_type = st.selectbox(
    "문제 유형", ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"],
)
difficulty = st.select_slider("난이도", ["쉬움", "보통", "어려움"], value="보통")
st.markdown("---")
st.write("버튼을 누르면 OpenAI Chat Completions API가 호출됩니다. (에러 메시지는 프롬프트에 포함되지 않습니다.)")


# ==========================================================
# 퀴즈 생성
# ==========================================================
if st.button("🚀 퀴즈 생성하기"):
    try:
        # OpenAI 클라이언트는 버튼 클릭 시점에만 생성
        client = OpenAI(api_key=st.session_state["user_api_key"])

        # 안전한 프롬프트: material_text(실제 콘텐츠)만 포함, 에러 텍스트는 절대 포함하지 않음
        prompt = f"""
아래 강의자료를 바탕으로 {quiz_type} 퀴즈를 생성해줘.
난이도: {difficulty}

--- 강의자료 (요약/본문) ---
{material_text}
------------------

출력 형식 규칙:
1. 문제 유형:
   - 객관식: 문제 + 보기 4개(A,B,C,D) + "//정답: 정답문자"
   - 단답형: 문제만 작성 후 반드시 별도 줄에 "//정답: 정답" 작성
   - 서술형: 문제 작성 후 별도 줄에 "//정답: 정답 내용"
   - 혼합형: 유형 섞어서 5문항
2. 문제 번호 포함 금지 (문제 앞에 "문제 1:" 같은 텍스트는 빼기)
3. 문제와 정답은 항상 별도 줄로 구분
4. 불필요한 안내 문구 금지
"""

        with st.spinner("AI가 퀴즈를 생성 중입니다..."):
            # 최신 SDK에서 chat completions 사용 형태에 따라 조정 가능
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500,
            )

            # 응답 추출
            quiz_text = response.choices[0].message.content
            st.session_state["generated_quiz"] = quiz_text

            st.success("퀴즈 생성 완료!")
            st.markdown("### 📘 생성된 퀴즈")

            # 문제/정답 분리 + UI 표시
            lines = quiz_text.split("\n")
            buffer = []
            question_count = 1

            for line in lines:
                if "//정답:" in line:
                    question = "\n".join(buffer).strip()
                    answer = line.replace("//정답:", "").strip()

                    st.write(f"**문제 {question_count}:**")
                    st.write(question)

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
