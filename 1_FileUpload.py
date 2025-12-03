import streamlit as st
import os

# 페이지 설정 (가장 윗부분에 위치해야 함)
st.set_page_config(page_title="강의자료 업로드 - 요약해줘", layout="wide")

# --- 1. Session State 초기화 (데이터 영구 저장을 위한 설정) ---
# API Key가 없으면 초기화
if 'user_api_key' not in st.session_state:
    st.session_state['user_api_key'] = ''

# 업로드된 컨텐츠 내용이 없으면 초기화
if 'uploaded_content' not in st.session_state:
    st.session_state['uploaded_content'] = None

# 컨텐츠의 타입 (pdf, youtube, text 등)
if 'content_type' not in st.session_state:
    st.session_state['content_type'] = None

# --- 2. 사이드바: API Key 입력 (전역 설정) ---
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 비밀번호 형태로 입력받음
    api_input = st.text_input(
        "OpenAI API Key를 입력하세요", 
        type="password",
        value=st.session_state['user_api_key'], # 기존 값이 있다면 유지
        help="입력하신 키는 다른 페이지(퀴즈 생성 등)에서도 계속 사용됩니다."
    )
    
    # 입력값이 변경되면 session_state에 저장
    if api_input:
        st.session_state['user_api_key'] = api_input
        st.success("API Key가 저장되었습니다! ✅")
    else:
        st.warning("API Key를 입력해주세요.")

# --- 3. 메인 화면: 자료 업로드 ---
st.title("📂 강의 자료 업로드")
st.markdown("강의 노트를 만들고 싶은 자료를 업로드해주세요. (PDF, PPT, 영상, 텍스트 등)")

# 탭을 사용하여 입력 방식을 구분
tab1, tab2, tab3 = st.tabs(["📄 파일 업로드", "▶️ 유튜브 링크", "📝 텍스트 직접 입력"])

# --- Tab 1: 파일 업로드 (PDF, PPT, 영상 파일) ---
with tab1:
    uploaded_file = st.file_uploader(
        "강의 자료 파일 선택", 
        type=['pdf', 'ppt', 'pptx', 'mp4', 'mov', 'avi'],
        help="PDF, PPT, 또는 영상 파일을 업로드하세요."
    )

    if uploaded_file is not None:
        # 파일 확장자 확인
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        # 버튼을 눌러야 처리가 확정되도록 (불필요한 리로드 방지)
        if st.button("파일 업로드 확정", key="btn_file"):
            # 실제 파일 처리 로직은 여기서 (예: 텍스트 추출 함수 호출)
            # 여기서는 예시로 파일 객체 자체를 저장합니다.
            st.session_state['uploaded_content'] = uploaded_file
            st.session_state['content_type'] = file_ext.replace('.', '') # pdf, pptx 등
            st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다!")

# --- Tab 2: 유튜브 링크 ---
with tab2:
    youtube_url = st.text_input("유튜브 영상 주소 (URL) 입력")
    
    if youtube_url:
        st.video(youtube_url) # 영상 미리보기
        
        if st.button("유튜브 링크 확정", key="btn_youtube"):
            st.session_state['uploaded_content'] = youtube_url
            st.session_state['content_type'] = 'youtube'
            st.success("유튜브 링크가 저장되었습니다! 분석 준비 완료.")

# --- Tab 3: 텍스트 직접 입력 ---
with tab3:
    raw_text = st.text_area("강의 내용 텍스트 붙여넣기", height=300)
    
    if raw_text:
        if st.button("텍스트 저장", key="btn_text"):
            st.session_state['uploaded_content'] = raw_text
            st.session_state['content_type'] = 'text'
            st.success("텍스트가 저장되었습니다.")

# --- 5. 다음 단계로 넘어가기 안내 ---
if st.session_state['uploaded_content'] and st.session_state['user_api_key']:
    st.info("모든 준비가 완료되었습니다! 왼쪽 메뉴에서 '강의노트 생성' 또는 '퀴즈 풀기' 페이지로 이동하세요.")