import streamlit as st
from openai import OpenAI

st.title("연습 문제 생성하기")

# 1페이지에서 저장된 content와 apiKey 사용
content = st.session_state.get("content")
api_key = st.session_state.get("apiKey")

if not content:
    st.warning("먼저 자료를 업로드해주세요.")
    st.stop()

if not api_key:
    st.warning("API Key가 필요합니다.")
    st.stop()

client = OpenAI(api_key=api_key)

if st.button("연습 문제 생성"):
    with st.spinner("AI가 문제를 생성하고 있습니다..."):
        prompt = f"""
다음 자료로 연습문제를 만들어줘.

자료:
{content}

요구사항:
- 객관식 3문제
- 서술형 2문제
- JSON 형식으로 반환
"""

        response = client.responses.create(
            model="gpt-4.1",
            input=prompt
        )

        quiz = response.output_text
        st.json(quiz)
