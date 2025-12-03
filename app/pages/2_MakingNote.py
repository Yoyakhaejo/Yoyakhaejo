import streamlit as st

st.title("2. 강의노트 만들기")
st.write("업로드한 자료를 요약해서 강의노트를 생성하는 페이지입니다.")

# openai 패키지 임포트 (설치 안 되어 있으면 안내 메시지)
try:
    from openai import OpenAI
except ImportError:
    st.error("⚠️ openai 패키지가 설치되어 있지 않습니다.\n\n"
             "터미널에서 아래 명령을 실행해서 먼저 설치해 주세요.\n\n"
             "    pip install openai")
    st.stop()

api_key = st.session_state.get("api_key")
vector_store_id = st.session_state.get("lecture_vector_store_id")

# 1번 페이지에서 아직 세팅을 안 했을 때
if not api_key or not vector_store_id:
    st.info(
        "아직 1번 페이지에서 API Key 입력과 강의자료 업로드가 완료되지 않았습니다.\n"
        "먼저 1번 페이지에서:\n"
        "1) OpenAI API Key 입력\n"
        "2) 강의자료 업로드 → vector_store_id 저장\n"
        "을 한 뒤 다시 돌아와 주세요."
    )
else:
    client = OpenAI(api_key=api_key)

    def generate_lecture_notes_from_vector_store(client, vector_store_id):
        system_prompt = (
            "너는 대학 강의를 정리해 주는 조교야.\n"
            "첨부된 강의자료(슬라이드, PDF 등)를 기반으로 다음 형식의 강의노트를 만들어줘.\n\n"
            "1. 강의 개요\n"
            "   - 이 강의의 주제 한 줄 요약\n"
            "   - 강의에서 다루는 핵심 질문/목표\n\n"
            "2. 핵심 개념 정리\n"
            "   - 개념 1: 정의 + 중요 포인트\n"
            "   - 개념 2: 정의 + 중요 포인트\n"
            "   - … (필요한 만큼)\n\n"
            "3. 예시 및 응용\n"
            "   - 강의에서 나온 대표 예시나 사례 정리\n"
            "   - 학생이 실무/현실에서 어떻게 써먹을 수 있는지\n\n"
            "4. 강의 체크리스트\n"
            "   - 복습할 때 스스로 물어볼 만한 질문 3~5개\n\n"
            "문장은 한국어로, 너무 장황하지 않게 A4 1~2장 분량 느낌으로 정리해줘."
        )

        response = client.responses.create(
            model="gpt-4o-mini",  # 1번 페이지에서 쓰는 모델 이름과 맞춰줘
            input=[
                {"role": "developer", "content": system_prompt},
                {
                    "role": "user",
                    "content": "위 형식에 맞춰 업로드된 강의자료 전체를 요약해서 강의노트를 작성해줘.",
                },
            ],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": 20,
            }],
            temperature=0.3,
        )

        return response.output_text

    st.write("버튼을 누르면 1번에서 업로드한 강의자료를 기반으로 강의노트를 자동으로 생성합니다.")

    if st.button("📚 강의노트 생성하기"):
        with st.spinner("강의노트를 생성하는 중입니다..."):
            notes = generate_lecture_notes_from_vector_store(client, vector_store_id)

        st.subheader("✅ 생성된 강의노트")
        st.text_area("강의노트", value=notes, height=400)

        st.session_state["lecture_notes"] = notes
        st.success("강의노트가 생성되어 세션에 저장되었습니다!")
