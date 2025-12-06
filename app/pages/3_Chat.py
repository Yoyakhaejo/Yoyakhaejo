import streamlit as st
from openai import OpenAI
import time


# ------------------------
# Page Configuration
# ------------------------
st.set_page_config(page_title="Chat - 요약해줘", layout="wide")


# ------------------------
# API KEY 확인
# ------------------------
if "user_api_key" not in st.session_state or not st.session_state.user_api_key:
    st.error("먼저 1_FileUpload 페이지에서 API Key를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=st.session_state.user_api_key)


# ------------------------
# 파일 확인
# ------------------------
if "uploaded_content" not in st.session_state or st.session_state.uploaded_content is None:
    st.warning("학습 자료가 업로드되지 않았습니다. 1_FileUpload에서 파일을 등록하세요.")
    st.stop()


# ------------------------
# 기존(혹은 외부) 벡터스토어 사용 (옵션 B)
# ------------------------
FIXED_VECTORSTORE_ID = "vs_6933e3094bc081918846e6bcaad5be21"

if "vectorstore_id" not in st.session_state:
    st.info("기존 벡터스토어를 사용하도록 설정합니다.")
    # 바로 고정 ID를 사용
    st.session_state.vectorstore_id = FIXED_VECTORSTORE_ID
    # (선택) 존재 여부 확인 시도
    try:
        vs_meta = client.vector_stores.retrieve(st.session_state.vectorstore_id)
        st.success(f"벡터스토어 사용: {vs_meta.id}")
    except Exception as e:
        st.warning(f"벡터스토어 조회 실패: {e} — 하지만 지정된 ID를 세션에 설정했습니다.")

vectorstore_id = st.session_state.vectorstore_id


# ------------------------
# 메시지 저장 (대화 유지)
# ------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


st.title("AI 학습 도우미 챗봇")
st.markdown("업로드된 강의자료 기반으로 질문해보세요.")


# ------------------------
# 이전 메시지 출력
# ------------------------
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


# ------------------------
# 사용자 입력
# ------------------------
query = st.chat_input("질문을 입력하세요.")

if query:

    st.chat_message("user").write(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("답변 생성 중..."):

        # ---------- RAG: Responses + file_search ----------
        response = client.responses.create(
            model="gpt-5-mini",
            input=query,
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [vectorstore_id]
                }
            ]
        )

        result = response.output_text
        st.chat_message("assistant").write(result)
        st.session_state.messages.append({"role": "assistant", "content": result})


# ------------------------
# Reset 버튼
# ------------------------
if st.button("대화 초기화"):
    st.session_state.messages = []
    st.experimental_rerun()
