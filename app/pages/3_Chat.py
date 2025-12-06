import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF
import tempfile

st.set_page_config(page_title="Chat - 요약해줘", layout="wide")

# --- Session state 기본값 보장 ---
st.session_state.setdefault("user_api_key", "")
st.session_state.setdefault("uploaded_content", None)
st.session_state.setdefault("content_type", None)


# ------------------------
# 페이지 제목과 설명 (항상 표시)
# ------------------------
st.title("AI 학습 도우미 챗봇")
st.write("업로드한 학습자료를 기반으로 질문하세요. 아래 입력이 완료되면 챗봇이 활성화됩니다.")
st.divider()



# ------------------------
# API KEY 확인 (타이틀 아래에서 검증)
# ------------------------
api_key = st.session_state.get("user_api_key", "")
if not api_key:
    st.error("🚨 API Key가 없습니다. 1_FileUpload 페이지에서 OpenAI API Key를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=api_key)


# ------------------------
# 업로드 파일 확인 (API Key 통과 후)
# ------------------------
uploaded_content = st.session_state.get("uploaded_content", None)
content_type = st.session_state.get("content_type", None)

if uploaded_content is None or content_type is None:
    st.warning("⚠ 아직 학습 자료가 업로드되지 않았습니다. 1_FileUpload에서 파일 또는 링크를 등록하세요.")
    st.stop()


# ------------------------
# 자료 → 텍스트 변환 함수
# ------------------------
def extract_text_from_pdf(file_bytes):
    text = ""
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
            for page_num, page in enumerate(pdf):
                text += f"--- Page {page_num + 1} ---\n"
                text += page.get_text()
                text += "\n"
    except Exception as e:
        text = f"[PDF 추출 오류] {str(e)}"
    return text


def extract_material_text(uploaded_content, content_type: str) -> str:

    if content_type == "text":
        return uploaded_content
    
    elif content_type == "youtube":
        return f"""
📌 유튜브 링크: {uploaded_content}

⚠ 영상 내용은 직접 접근할 수 없으므로 일반적인 유튜브 강의 형식을 기반으로 답변합니다.
"""
    
    elif content_type == "pdf":
        try:
            pdf_text = extract_text_from_pdf(uploaded_content.getvalue())
            return pdf_text[:8000]  # 토큰 제한 고려
        except Exception as e:
            return f"PDF 추출 실패: {str(e)}"
    
    elif content_type in ("ppt", "pptx"):
        return "⚠ PPT 파일 자동 텍스트 추출은 아직 지원되지 않습니다. 슬라이드 내용을 기반으로 응답하겠습니다."
    
    elif content_type in ("mp4", "mov", "avi"):
        return "⚠ 영상 파일은 자동 분석이 불가능합니다. 영상 내용을 질문해주시면 일반적 내용을 바탕으로 답변합니다."

    return "알 수 없는 자료 형식입니다."


material_text = extract_material_text(uploaded_content, content_type)

st.info(f"📚 현재 자료 유형: **{content_type}**")


# ------------------------
# 초기화 버튼
# ------------------------
if st.button("대화 초기화"):
    st.session_state.pop("messages", None)
    st.rerun()

st.divider()


# ------------------------
# 대화 기억 공간
# ------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


# 이전 메시지 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])



# ------------------------
# 질문 처리
# ------------------------
query = st.chat_input("질문을 입력하세요.")

if query:
    with st.chat_message("user"):
        st.markdown(query)

    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("답변 생성 중..."):

        system_prompt = f"""
너는 사용자가 업로드한 강의 자료 기반으로 학습을 돕는 AI 튜터이다.

자료 내용:
---
{material_text}
---

규칙:
1. 강의 자료 내용 → 우선 이용
2. 없을 경우 일반 지식으로 보완
3. 한국어로 답변
4. 명확 · 친절 · 짧게
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *st.session_state.messages,
            ],
            max_tokens=1500,
            temperature=0.7
        )

        answer = response.choices[0].message.content

        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
