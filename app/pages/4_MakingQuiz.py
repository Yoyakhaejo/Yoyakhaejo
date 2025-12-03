# app/pages/4_MakingQuiz.py
import streamlit as st
from openai import OpenAI
import tempfile
import os
import traceback

# 페이지 설정
st.set_page_config(page_title="퀴즈 생성 - 요약해줘", layout="wide")

# --- Session state 기본값 보장 ---
st.session_state.setdefault("user_api_key", "")
st.session_state.setdefault("uploaded_content", None)
st.session_state.setdefault("content_type", None)
st.session_state.setdefault("generated_quiz", None)

st.title("📝 AI 기반 연습 문제 생성")
st.markdown("업로드된 강의자료를 바탕으로 AI가 연습 문제를 생성합니다.")

# 빠른 유효성 검사: API Key 및 업로드 자료 존재 확인
if not st.session_state["user_api_key"]:
    st.warning("⚠️ 먼저 왼쪽 설정에서 OpenAI API Key를 입력해주세요!")
    st.stop()

if st.session_state["uploaded_content"] is None:
    st.warning("📂 먼저 '강의 자료 업로드' 페이지에서 자료를 업로드해주세요!")
    st.stop()

content_type = st.session_state["content_type"]
st.info(f"업로드된 자료 유형: **{content_type}**")

# --- 보조: 업로드된 자료에서 텍스트를 뽑아오는 함수 (간단한 기본 버전) ---
def extract_text_from_uploaded():
    data = st.session_state["uploaded_content"]
    ctype = st.session_state["content_type"]

    # 텍스트 직접 입력 (string)
    if ctype == "text":
        return data

    # 유튜브 링크 (간단히 링크를 포함한 지시문으로 처리)
    if ctype == "youtube":
        return f"유튜브 영상 URL: {data}\n(영상의 자막/요약을 기반으로 퀴즈를 만들어주세요.)"

    # 파일(PDF/PPT 등)은 스트림릿 UploadedFile 객체인 경우가 많음
    if ctype in ("pdf", "ppt", "pptx"):
        try:
            # 임시 파일로 저장 (추후 텍스트 추출 모듈로 변환 가능)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ctype}") as tmp:
                tmp.write(data.getbuffer())
                tmp_path = tmp.name
            return (
                f"파일 경로: {tmp_path}\n"
                "※ 참고: 현재는 파일 경로로만 전달합니다. 실제 텍스트를 AI에 넘기려면 "
                "업로드 단계에서 PDF->텍스트 추출을 수행해 주세요."
            )
        except Exception as e:
            return f"파일 처리 중 예외 발생: {e}"

    return "알 수 없는 자료 형식입니다."

material_text = extract_text_from_uploaded()

# 퀴즈 옵션 설정
st.subheader("🎯 생성할 퀴즈 설정")
quiz_type = st.selectbox(
    "문제 유형",
    ["객관식 5문항", "단답형 5문항", "서술형 3문항", "혼합형 5문항"],
)
difficulty = st.select_slider("난이도", ["쉬움", "보통", "어려움"], value="보통")

st.markdown("---")

# 설명(사용자에게 짧게 안내)
st.write("버튼을 누르면 OpenAI Responses API를 호출하여 퀴즈를 생성합니다. 호출은 버튼 클릭 시에만 발생합니다.")

# 실제 퀴즈 생성 버튼
if st.button("🚀 퀴즈 생성하기"):
    try:
        # 1) 버튼 클릭 시점에만 OpenAI 클라이언트 생성 (Streamlit 재실행 안전)
        client = OpenAI(api_key=st.session_state["user_api_key"])

        # 2) 프롬프트 구성
        prompt = f"""
아래 강의자료를 바탕으로 {quiz_type} 퀴즈를 생성해줘.
난이도: {difficulty}

--- 강의자료 ---
{material_text}
-----------------

요구사항:
- 객관식이면 보기 4개 포함
- 각 문제마다 '정답:' 으로 정답을 명시
- 가능한 한 간결하고 명확한 문제 문장으로 작성
- 출력은 사람이 읽기 쉬운 텍스트 형식으로 해줘
"""

        with st.spinner("AI가 퀴즈를 생성하고 있습니다..."):
            # 3) Responses API 호출 (현재 권장 API)
            # 공식 문서에서 Responses API 사용을 권장함. (클라이언트 인스턴스 사용 방식)
            # 참고: response 객체의 텍스트는 response.output_text 속성이나 output 배열에서 추출 가능
            response = client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                temperature=0.7,
                max_output_tokens=1500,
            )

            # 4) 응답 텍스트 추출 (안전하게 여러 케이스 처리)
            quiz_text = None
            # 1) 편의 속성이 있으면 사용
            if hasattr(response, "output_text") and response.output_text:
                quiz_text = response.output_text
            else:
                # 2) output 구조에서 텍스트 추출 시도
                try:
                    # response.output -> list of items; 각 item.content -> list, 각 content[0].text 등
                    outputs = getattr(response, "output", None)
                    if outputs and len(outputs) > 0:
                        # 여러 content 타입이 있을 수 있어 안전하게 순회
                        pieces = []
                        for out_item in outputs:
                            for c in out_item.get("content", []):
                                # content element may be dict with 'text' or 'type'...
                                if isinstance(c, dict):
                                    text_val = c.get("text") or c.get("markdown") or c.get("content")
                                    if text_val:
                                        pieces.append(text_val)
                                elif isinstance(c, str):
                                    pieces.append(c)
                        quiz_text = "\n".join(pieces) if pieces else None
                except Exception:
                    quiz_text = None

            # 3) 최종 안전장치: 그래도 없으면 raw repr 전달
            if not quiz_text:
                quiz_text = str(response)

            # 5) 화면 출력 및 session_state 저장
            st.success("퀴즈 생성이 완료되었습니다!")
            st.markdown("### 📘 생성된 퀴즈")
            st.code(quiz_text, language="text")
            st.session_state["generated_quiz"] = quiz_text

    except Exception as exc:
        # 에러는 사용자에게 친절히 출력하고 상세 로그는 콘솔(서버)에 남김
        st.error("퀴즈 생성 중 오류가 발생했습니다. 콘솔 로그를 확인하세요.")
        st.exception(exc)
        # 내부 로그도 찍어둔다 (개발중에만)
        print("=== OpenAI 호출 예외 ===")
        traceback.print_exc()

# 생성된 퀴즈가 있으면 바로 보기/다운로드 옵션 제공
if st.session_state.get("generated_quiz"):
    st.download_button(
        "🔽 퀴즈 다운로드 (.txt)",
        st.session_state["generated_quiz"],
        file_name="generated_quiz.txt",
        mime="text/plain",
    )
