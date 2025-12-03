import streamlit as st
from openai import OpenAI

# OpenAI 클라이언트 생성
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📘 자동 퀴즈 생성기")
st.write("텍스트를 입력하면 문장 분석 후 퀴즈 5개를 만들어줍니다.")
st.write("각 문항의 정답은 기본적으로 숨겨져 있으며 클릭하면 볼 수 있습니다.")


# ------------------------------------------------
# 1) 사용자 입력
# ------------------------------------------------
input_text = st.text_area("요약할 자료 또는 본문을 입력하세요", height=250)

generate_btn = st.button("퀴즈 만들기", type="primary")


# ------------------------------------------------
# 2) 버튼 클릭 시 퀴즈 생성
# ------------------------------------------------
if generate_btn:

    if not input_text.strip():
        st.warning("먼저 텍스트를 입력해주세요!")
        st.stop()

    with st.spinner("⚙️ 퀴즈를 생성하는 중입니다..."):

        prompt = f"""
다음 내용을 바탕으로 객관식/주관식이 섞인 퀴즈 5개를 만들어줘.
각 문제마다 마지막 줄에 "//정답: ~" 형식으로 정답을 작성해줘.

본문:
{input_text}
"""

        # ✨ OpenAI 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )

        quiz_text = response.choices[0].message.content


    # ------------------------------------------------
    # 3) 화면에 퀴즈 표시 (정답 숨김 기능)
    # ------------------------------------------------
    st.subheader("📗 생성된 퀴즈")

    lines = quiz_text.split("\n")
    plain_text_for_download = ""

    for line in lines:

        # 정답 포함된 줄 처리
        if "//정답:" in line:
            question = line.split("//정답:")[0].strip()
            answer = line.split("//정답:")[1].strip()

            # Streamlit expander 로 정답 숨기기
            with st.expander(question):
                st.write("정답:", answer)

            # 다운로드용 텍스트에도 반영
            plain_text_for_download += f"{question} - 정답: {answer}\n"

        else:
            # 문제 설명 또는 번호 줄
            if line.strip():
                st.write(line)

            plain_text_for_download += line + "\n"


    # ------------------------------------------------
    # 4) 다운로드 버튼
    # ------------------------------------------------
    st.subheader("📥 퀴즈 다운로드")

    st.download_button(
        label="퀴즈 다운로드.txt",
        data=plain_text_for_download,
        file_name="quiz.txt",
        mime="text/plain"
    )
