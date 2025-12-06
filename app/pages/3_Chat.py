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
# API KEY 확인
# ------------------------
api_key = st.session_state.get("user_api_key", "")
if not api_key:
    st.error("먼저 1_FileUpload 페이지에서 API Key를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=api_key)

# ------------------------
# 파일 확인
# ------------------------
uploaded_content = st.session_state.get("uploaded_content", None)
content_type = st.session_state.get("content_type", None)

if uploaded_content is None or content_type is None:
    st.warning("학습 자료가 업로드되지 않았습니다. 1_FileUpload에서 파일 또는 링크를 등록하세요.")
    st.stop()

# ------------------------
# 업로드된 자료에서 텍스트 추출
# ------------------------
def extract_text_from_pdf(file_bytes):
    """PDF 파일에서 텍스트 추출"""
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
    """
    업로드된 자료의 타입에 따라 텍스트 추출
    """
    if content_type == "text":
        return uploaded_content
    
    elif content_type == "youtube":
        return f"""
유튜브 강의 링크: {uploaded_content}

참고: 실제 영상에 직접 접근할 수는 없으나, 
사용자가 이 강의를 시청했다고 가정하고 대화하겠습니다.
"""
    
    elif content_type == "pdf":
        try:
            pdf_text = extract_text_from_pdf(uploaded_content.getvalue())
            return pdf_text[:8000]  # 토큰 제한을 위해 처음 8000자 사용
        except Exception as e:
            return f"PDF 텍스트 추출 실패: {str(e)}"
    
    elif content_type in ("ppt", "pptx"):
        return f"""
파일명: {uploaded_content.name if hasattr(uploaded_content, 'name') else 'unknown'}
파일 타입: PowerPoint 프레젠테이션

참고: 현재 앱에서는 PPT 파일의 원문 추출이 제한되어 있습니다.
일반적인 대학 강의 슬라이드 형식을 기반으로 대화하겠습니다.
"""
    
    elif content_type in ("mp4", "mov", "avi"):
        return f"""
파일명: {uploaded_content.name if hasattr(uploaded_content, 'name') else 'unknown'}
파일 타입: 비디오 파일

참고: 영상 파일의 자동 텍스트 추출은 지원되지 않습니다.
영상 내용에 대해 질문하시면 일반적인 지식을 바탕으로 답변하겠습니다.
"""
    
    else:
        return f"알 수 없는 자료 형식입니다. (type: {content_type})"


material_text = extract_material_text(uploaded_content, content_type)


# ------------------------
# Chat Section
# ------------------------
st.title("AI 학습 도우미 챗봇")
st.write("업로드한 강의자료를 기반으로 질문해보세요.")
st.info(f"📚 현재 자료 유형: **{content_type}**")

# 대화 초기화 버튼 (상단)
if st.button("🔄 대화 초기화", use_container_width=False):
    st.session_state.pop("messages", None)
    st.rerun()

st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []


# 기존 메시지 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


query = st.chat_input("질문을 입력하세요.")

if query:
    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("답변 생성 중..."):
        try:
            # 시스템 프롬프트
            system_prompt = f"""
너는 대학 강의 자료 학습을 돕는 AI 튜터이다.
사용자가 업로드한 강의 자료를 기반으로 정확하고 친절하게 답변해줘.

강의 자료 내용:
---
{material_text}
---

다음 규칙을 지켜줘:
1. 강의 자료의 내용을 우선으로 참고해서 답변해
2. 강의 자료에 없는 내용이면 일반 지식으로 보충 설명해
3. 항상 한국어로 답변해
4. 명확하고 이해하기 쉽게 설명해
5. 필요하면 예시를 들어서 설명해
6. 너무 긴 답변보다는 핵심을 먼저 말하고 필요하면 추가 설명해
"""

            # OpenAI Chat Completions API 호출
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *[{"role": msg["role"], "content": msg["content"]} 
                      for msg in st.session_state.messages[:-1]],  # 이전 대화 포함
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=1500,
            )

            answer = response.choices[0].message.content

            # 어시스턴트 답변 표시
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

        except Exception as e:
            st.error(f"답변 생성 중 오류 발생: {str(e)}")
