import streamlit as st
from openai import OpenAI
from pprint import pprint

# ------------------------
# Streamlit Page Config
# ------------------------
st.set_page_config(page_title="Chat - 요약해줘", layout="wide")

# ------------------------
# Check API Key
# ------------------------
if "user_api_key" not in st.session_state or st.session_state.user_api_key == "":
    st.error(" 먼저 1_FileUpload 페이지에서 API Key를 입력해주세요!")
    st.stop()

# OpenAI Client
client = OpenAI(api_key=st.session_state.user_api_key)

# ------------------------
# VectorStore 확인
# ------------------------
if "vectorstore_id" not in st.session_state:
    st.warning(" 아직 벡터스토어가 생성되지 않았습니다. 먼저 2_VectorStore 페이지에서 자료를 임베딩하세요.")
    st.stop()

vectorstore_id = st.session_state.vectorstore_id

# ------------------------
# 메시지 저장 공간 (대화 유지)
# ------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "developer", "content": "You are a helpful assistant."}]

st.title(" AI 학습 도우미 챗봇")
st.markdown("업로드한 강의자료 기반으로 질문해보세요.")

# ------------------------
# 이전 메시지 표시
# ------------------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

# ------------------------
# 사용자 입력
# ------------------------
query = st.chat_input("무엇이 궁금한가요?")

if query:

    # 메시지 저장
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message("user").write(query)

    # ------------------------
    #  벡터스토어 기반 검색 + 응답 생성
    # ------------------------

    with st.spinner("답변 생성 중..."):
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                *st.session_state.messages,
                {
                    "role": "system",
                    "content": f"사용자는 {vectorstore_id} 벡터스토어에 저장된 학습 자료를 기반으로 학습 중입니다. 질문에 대해 가능한 한 업로드된 자료에서 근거하여 답변하세요."
                }
            ],
            extra_body={
                "vector_store_query": {"vector_store_ids": [vectorstore_id], "query": query}
            }
        )

        answer = response.choices[0].message.content

        # 화면 출력
        st.chat_message("assistant").write(answer)

        # 저장
        st.session_state.messages.append({"role": "assistant", "content": answer})

# ------------------------
# Reset Option
# ------------------------
if st.button(" 대화 초기화"):
    st.session_state.messages = [{"role": "developer", "content": "You are a helpful assistant."}]
    st.experimental_rerun()
