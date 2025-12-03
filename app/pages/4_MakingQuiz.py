import streamlit as st
from openai import OpenAI
import tempfile
import os

# 페이지 설정
st.set_page_config(page_title="퀴즈 생성 - 요약해줘", layout="wide")

# --- Session State 기본값 ---
st.session_state.setdefault('user_api_key', '')
st.session_state.setdefault('uploaded_content', None)
st.session_state.setdefault('content_type', None)

# --- UI ---
st.title("📝 AI 기반 연습 문제 생성")
st.markdown("업로드된 강의자료를 기반으로 퀴즈를 생성합니다.")

# --- API Key 체크 ---
if not st.session_state['user_api_key']:
    st.warning("⚠️ 먼저 왼쪽 설정에서 OpenAI API Key를 입력해주세요!")
    st.stop()

# --- 업로드 자료 체크 ---
if st.session_state['uploaded_content'] is None:
    st.warning("📂 먼저 '강의 자료 업로드' 페이지에서 자료를 업로드해주세요!")
    st.stop()

content_type = st.session_state['content_type']
st.info(f"업로드된 자료 유형: **{content_type}**")

# --- 텍스트 추출 ---
def extract_text_from_uploaded():
    data = st.session_state['uploaded_content']
    ctype = st.session_state['content_type']

    if ctype == 'text':
        return data

    if ctype == 'youtube':
        return f"다음 유튜브 강의 요약 후 퀴즈 생성:\n{data}"

    if ctype in ['pdf', 'ppt', 'pptx']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ctype}") as tmp:
            tmp.write(data.getbuffer())
            tmp_path = tmp.name
        
        return f"강의자료 파일({ctype}): {tmp_path}"

    return "알 수 없는 자료 형식"

material_text = extract_text_from_uploaded()

# --- 퀴즈 옵션 ---
st.subheader("🎯 생성할 퀴즈 형태")

quiz_type = st.selectbox(
    "문제 유형", ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"]
)

difficulty = st.select_slider(
    "난이도", ["쉬움", "보통", "어려움"], value="보통"
)

# --- 버튼 ---
if st.button("🚀 퀴즈 생성하기"):

    # 🟩 여기에서만 OpenAI() 초기화!
    client = OpenAI(api_key=st.session_state['user_api_key'])

    prompt = f"""
    아래 강의자료를 기반으로 {quiz_type} 퀴즈를 생성해줘.
    난이도: {difficulty}

    ----- 강의자료 -----
    {material_text}
    ---------------------

    문제 번호, 보기, 정답을 명확하게 포함해줘.
    """

    with st.spinner("AI가 퀴즈를 생성하고 있습니다..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "너는 교육용 퀴즈 생성 전문가다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            quiz_output = response.choices[0].message["content"]

            st.success("퀴즈 생성 완료!")
            st.markdown("### 📘 생성된 퀴즈")
            st.write(quiz_output)

        except Exception as e:
            st.error(f"오류 발생: {e}")
