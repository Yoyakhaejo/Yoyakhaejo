import streamlit as st
from openai import OpenAI
import tempfile
import os

# 페이지 설정
st.set_page_config(page_title="퀴즈 생성 - 요약해줘", layout="wide")

# --- 1. 필수 Session State 확인 ---
if 'user_api_key' not in st.session_state:
    st.session_state['user_api_key'] = ''
if 'uploaded_content' not in st.session_state:
    st.session_state['uploaded_content'] = None
if 'content_type' not in st.session_state:
    st.session_state['content_type'] = None

# --- 2. 상단 안내 ---
st.title("📝 AI 기반 연습 문제 생성")
st.markdown("업로드된 강의자료를 기반으로 퀴즈를 생성합니다.")

# --- 3. API Key 확인 ---
if not st.session_state['user_api_key']:
    st.warning("⚠️ 먼저 왼쪽 설정에서 OpenAI API Key를 입력해주세요!")
    st.stop()

# 클라이언트 준비
client = OpenAI(api_key=st.session_state['user_api_key'])

# --- 4. 업로드된 자료 확인 ---
if st.session_state['uploaded_content'] is None:
    st.warning("📂 먼저 '강의 자료 업로드' 페이지에서 자료를 업로드해주세요!")
    st.stop()

content_type = st.session_state['content_type']
st.info(f"업로드된 자료 유형: **{content_type}**")

# --- 5. 자료에서 사용할 텍스트 추출 ---
def extract_text_from_uploaded():
    data = st.session_state['uploaded_content']
    ctype = st.session_state['content_type']

    # 텍스트 직접 입력
    if ctype == 'text':
        return data

    # 유튜브 링크
    if ctype == 'youtube':
        return f"다음 유튜브 강의 내용을 요약하여 퀴즈를 만들어줘: {data}"

    # PDF/PPT 등 파일 처리
    if ctype in ['pdf', 'ppt', 'pptx']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ctype}") as tmp:
            tmp.write(data.getbuffer())
            tmp_path = tmp.name
        
        return (
            f"다음 강의자료 파일({ctype})을 기반으로 퀴즈를 만들어줘.\n"
            f"파일 경로: {tmp_path}"
        )

    return "알 수 없는 자료 유형입니다."

material_text = extract_text_from_uploaded()

# --- 6. 퀴즈 옵션 선택 ---
st.subheader("🎯 생성할 퀴즈 형태 선택")

quiz_type = st.selectbox(
    "생성할 문제 유형을 선택하세요",
    ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"]
)

difficulty = st.select_slider(
    "난이도",
    options=["쉬움", "보통", "어려움"],
    value="보통"
)

# --- 7. 퀴즈 생성 ---
if st.button("🚀 퀴즈 생성하기"):
    with st.spinner("AI가 퀴즈를 생성하는 중입니다..."):

        prompt = f"""
        아래 강의자료를 기반으로 {quiz_type}의 퀴즈를 생성해줘.
        난이도는 {difficulty} 수준으로.

        --- 강의자료 내용 ---
        {material_text}
        ---------------------

        문제는 번호를 붙이고, 보기와 정답을 명확하게 포함해서 작성해줘.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "넌 강의자료 기반 교육용 퀴즈 생성 전문 AI야."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            quiz_output = response.choices[0].message.content

            st.success("퀴즈 생성이 완료되었습니다!")
            st.markdown("### 📘 생성된 퀴즈")
            st.write(quiz_output)

        except Exception as e:
            st.error(f"오류 발생: {e}")
