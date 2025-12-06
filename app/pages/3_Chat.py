import streamlit as st
from openai import OpenAI
import time

st.set_page_config(page_title="Chat - 요약해줘", layout="wide")

# ------------------------
# API KEY
# ------------------------
if "user_api_key" not in st.session_state or not st.session_state.user_api_key:
    st.error("먼저 1_FileUpload 페이지에서 API Key를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=st.session_state.user_api_key)

# ------------------------
# 파일 확인
# ------------------------
if "uploaded_content" not in st.session_state or st.session_state.uploaded_content is None:
    st.warning("학습 자료가 업로드되지 않았습니다. 1_FileUpload에서 파일 또는 링크를 등록하세요.")
    st.stop()

uploaded_content = st.session_state.uploaded_content


# ------------------------
# VectorStore 생성/검증
# ------------------------
def setup_vector_store():
    if "vectorstore_id" in st.session_state:
        try:
            client.vector_stores.retrieve(st.session_state.vectorstore_id)
            return st.session_state.vectorstore_id
        except:
            st.warning("기존 VectorStore가 서버에 존재하지 않아 새로 생성합니다.")
            st.session_state.pop("vectorstore_id")

    st.info("업로드된 자료 기반으로 VectorStore를 생성합니다...")

    with st.spinner("처리 중..."):

        # 1) Create Vector Store
        vs = client.vector_stores.create(name="Yoyakhaejo_RAG_Store")
        st.session_state.vectorstore_id = vs.id

        # 2) 파일 업로드 (purpose 변경!)
        if isinstance(uploaded_content, str):
            uploaded_file = client.files.create(
                file=uploaded_content.encode(),
                purpose="assistants"  # FIXED
            )
        else:
            uploaded_file = client.files.create(
                file=(uploaded_content.name, uploaded_content, "application/octet-stream"),
                purpose="assistants"  # FIXED
            )

        # 3) 벡터스토어 연결 + embedding
        client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vs.id,
            files=[uploaded_file.id]
        )

    st.success("Vector Store 준비 완료.")
    return st.session_state.vectorstore_id


vectorstore_id = setup_vector_store()


# ------------------------
# Chat Section
# ------------------------
st.title("AI 학습 도우미 챗봇")
st.write("업로드한 강의자료를 기반으로 질문해보세요.")

if "messages" not in st.session_state:
    st.session_state.messages = []


# 기존 메시지 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


query = st.chat_input("질문을 입력하세요.")

if query:
    st.chat_message("user").write(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("답변 생성 중..."):

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

        answer = response.output_text

        st.chat_message("assistant").write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


# ------------------------
# RESET
# ------------------------
if st.button("대화 초기화"):
    st.session_state.pop("messages", None)
    st.session_state.pop("vectorstore_id", None)
    st.experimental_rerun()
