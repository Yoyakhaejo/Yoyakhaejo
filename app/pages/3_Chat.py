import streamlit as st
st.set_option("client.showErrorDetails", True)
import html

st.title("3. 채팅하기")

from openai import OpenAI


def init_state():
	if "user_api_key" not in st.session_state:
		st.session_state["user_api_key"] = None
	if "uploaded_content" not in st.session_state:
		st.session_state["uploaded_content"] = None
	if "content_type" not in st.session_state:
		st.session_state["content_type"] = None
	if "chat_history" not in st.session_state:
		# list of dicts: {role: 'user'|'assistant', 'content': '...'}
		st.session_state["chat_history"] = []


init_state()


def build_user_input(uploaded_content, content_type: str) -> str:
	"""
	`1_FileUpload.py`와 동일한 방식으로 업로드된 내용을 모델에 보낼 텍스트로 변환합니다.
	- text: 업로드한 텍스트 전체를 그대로 사용
	- youtube: URL을 전달하고 실제 영상 접근이 불가능함을 명시
	- file: 파일명과 확장자를 전달하여 일반적인 강의 자료라고 가정하도록 함
	"""
	if not uploaded_content:
		return ""

	if content_type == "text":
		return (
			"다음 텍스트는 한 편의 강의 내용을 옮겨 적은 것이다. 이 텍스트 전체를 기반으로 답변에 참고해줘.\n\n"
			f"{uploaded_content}"
		)

	if content_type == "youtube":
		return (
			"사용자가 아래 유튜브 링크의 강의를 들었다고 가정하자. 실제 영상이나 자막에 직접 접근할 수는 없지만, 일반적인 대학 강의 구성을 바탕으로 답변해줘.\n\n"
			f"유튜브 URL: {uploaded_content}\n\n"
			"※ 실제 영상 내용은 알 수 없으므로, 너무 구체적인 숫자/예시는 피하고 전형적인 강의 구조에 맞춰 정리해줘."
		)

	# 파일(PDF/PPT/영상 등)
	file_name = getattr(uploaded_content, "name", str(uploaded_content))
	ext = "알수없음"
	try:
		if isinstance(file_name, str) and "." in file_name:
			ext = file_name.split(".")[-1]
	except Exception:
		ext = "알수없음"

	return (
		"사용자가 대학 강의자료 파일을 업로드했다. 실제 파일 내용을 직접 읽을 수는 없으므로, 일반적인 대학 강의 슬라이드/자료라고 가정하고 답변해줘.\n\n"
		f"파일 이름: {file_name}\n"
		f"파일 타입(확장자): {ext}\n\n"
		"※ 실제 슬라이드 내용을 모르는 상태이므로, 과도하게 구체적인 예시는 피하고, 대학생 대상의 일반적인 강의 구조에 맞춰 답변해줘."
	)


# 1_FileUpload 페이지에서 저장된 API Key와 파일을 받아 업데이트
user_api_key = st.session_state.get("user_api_key")
uploaded_content = st.session_state.get("uploaded_content")
content_type = st.session_state.get("content_type")

if user_api_key is None or user_api_key == "":
	st.error("❗ 먼저 1번 페이지에서 OpenAI API Key를 입력해 주세요.")
	st.stop()

# Warn if no content uploaded (but still allow chat to proceed)
if not uploaded_content:
	st.error("❌ 1번 페이지에서 먼저 다음 중 하나를 선택하여 업로드해 주세요:\n- 📄 파일 업로드 (PDF, PPT, 영상)\n- ▶️ 유튜브 링크\n- 📝 텍스트 직접 입력\n\n자료 업로드 후 채팅을 진행할 수 있습니다.")
	st.stop()

client = OpenAI(api_key=user_api_key)


def generate_response(client, user_message, history, uploaded_content=None, content_type=None):
	# Prepare system prompt explaining role and use of uploaded materials
	system_prompt = (
		"너는 대학생을 도와 공부 효율을 높여주는 친절한 튜터야.\n"
		"사용자가 업로드한 강의자료를 참고해서 답변을 주고, 필요하면 예시와 복습 체크리스트를 제공해줘.\n"
		"짧고 명확하게, 핵심을 우선으로 한국어로 답변해줘."
	)

	# Build input messages from history (keep recent history)
	messages = [
		{"role": "system", "content": system_prompt},
	]

	# include last N messages to maintain context
	recent = history[-10:] if history else []
	for m in recent:
		role = m.get("role")
		content = m.get("content")
		if role in ("user", "assistant"):
			messages.append({"role": role, "content": content})

	# If there is uploaded content and it's the first message in history, include context once
	if uploaded_content and len(history) == 1:
		uploaded_prompt = build_user_input(uploaded_content, content_type)
		if uploaded_prompt:
			# add as a user message so model can reference it
			messages.append({"role": "user", "content": uploaded_prompt})

	# finally add this user message (the actual question)
	messages.append({"role": "user", "content": user_message})

	# Call OpenAI Chat Completions API
	resp = client.chat.completions.create(
		model="gpt-4o-mini",
		messages=messages,
		temperature=0.2,
	)
	# Some SDK versions return the message differently; handle common shapes
	try:
		return resp.choices[0].message.content
	except Exception:
		# fallback to attribute used by older/newer SDKs
		return getattr(resp, "output_text", str(resp))


# Layout: chat area (scrollable) + fixed-ish input at bottom
# Use a placeholder so we can re-render the chat immediately when messages change
chat_placeholder = st.empty()

def render_chat():
	chat_html = []
	for msg in st.session_state["chat_history"]:
		role = msg.get("role")
		content = msg.get("content")
		safe_content = html.escape(content)
		if role == "user":
			chat_html.append(
				f"<div style='text-align:right; margin:8px 0;'>"
				f"<div style='display:inline-block; background:#DCF8C6; padding:10px 14px; border-radius:12px; max-width:80%;'>{safe_content}</div></div>"
			)
		else:
			chat_html.append(
				f"<div style='text-align:left; margin:8px 0;'>"
				f"<div style='display:inline-block; background:#F1F0F0; padding:10px 14px; border-radius:12px; max-width:80%;'>{safe_content}</div></div>"
			)

	# render within a scrollable box
	chat_box = """
	<div id='chatbox' style='height:60vh; overflow:auto; padding:12px; border:1px solid #e6e6e6; background:#ffffff; border-radius:8px;'>
	"""
	chat_box += "\n".join(chat_html)
	chat_box += "</div>"

	chat_placeholder.markdown(chat_box, unsafe_allow_html=True)

# initial render
render_chat()


# Input area (avoid modifying widget-backed session_state keys after creation)
st.write("")
cols = st.columns([8, 1])
with cols[0]:
	# use the return value of text_input (no direct session_state writes to the widget key)
	user_input = st.text_input("메시지를 입력하세요", placeholder="질문을 입력하고 Enter 또는 전송 버튼을 누르세요")
with cols[1]:
	send = st.button("전송")

def handle_send(text: str):
	text = (text or "").strip()
	if not text:
		return
	# append user message
	st.session_state["chat_history"].append({"role": "user", "content": text})

	# Immediately re-render chat so user's message appears before AI generation
	render_chat()

	# generate assistant response
	try:
		with st.spinner("AI가 답변을 생성하는 중입니다..."):
			reply = generate_response(client, text, st.session_state["chat_history"], uploaded_content, content_type)
	except Exception as e:
		reply = "죄송합니다. 응답 생성 중 오류가 발생했습니다. 나중에 다시 시도해 주세요."
		st.error(f"오류: {e}")

	# append assistant reply and re-render
	st.session_state["chat_history"].append({"role": "assistant", "content": reply})
	render_chat()


if send:
	handle_send(user_input)
	if st.session_state.get("chat_history"):
		st.info("위 스크롤 영역을 사용해 대화를 확인하세요. 입력창은 항상 하단에 있습니다.")