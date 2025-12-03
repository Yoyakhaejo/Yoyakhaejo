import streamlit as st
from openai import OpenAI

st.title("📘 자동 문제 생성기 (Making Quiz)")

client = OpenAI()

# 사용자 입력
st.write("요약된 내용을 기반으로 자동으로 연습문제를 생성합니다.")
content = st.text_area("문제 생성에 사용할 내용을 입력하세요:", height=300)

if st.button("문제 생성하기"):
    if not content.strip():
        st.error("내용을 입력해주세요.")
    else:
        with st.spinner("문제를 생성하는 중입니다..."):

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 학생을 위해 정확한 객관식 문제를 생성하는 보조 도구입니다."
                        },
                        {
                            "role": "user",
                            "content": f"다음 내용을 바탕으로 중학생 수준의 객관식 문제 5개를 만들어줘:\n\n{content}"
                        }
                    ],
                    max_tokens=1500
                )

                quiz = response.choices[0].message["content"]
                st.success("문제 생성 완료!")
                st.write(quiz)

            except Exception as e:
                st.error(f"오류 발생: {e}")
