import streamlit as st
import html

st.title("3. 채팅하기")

from openai import OpenAI


def init_state():
	if "api_key" not in st.session_state:
		st.session_state["api_key"] = None
	if "lecture_vector_store_id" not in st.session_state:
		st.session_state["lecture_vector_store_id"] = None
	if "lecture_notes" not in st.session_state:
		st.session_state["lecture_notes"] = None
	if "chat_history" not in st.session_state:
		# list of dicts: {role: 'user'|'assistant', 'content': '...'}
		st.session_state["chat_history"] = []


init_state()


api_key = st.session_state.get("api_key")
vector_store_id = st.session_state.get("lecture_vector_store_id")

if api_key is None:
	st.error("❗ 먼저 1번 페이지에서 OpenAI API Key를 입력해 주세요.")
	st.stop()

client = OpenAI(api_key=api_key)


def generate_response(client, user_message, history, vector_store_id=None):
	# Prepare system prompt explaining role and use of uploaded materials
	system_prompt = (
		"너는 대학생을 도와 공부 효율을 높여주는 친절한 튜터야.\n"
		"사용자가 업로드한 강의자료를 참고해서 답변을 주고, 필요하면 예시와 복습 체크리스트를 제공해줘.\n"
		"짧고 명확하게, 핵심을 우선으로 한국어로 답변해줘."
	)

	# Build input messages from history (keep recent history)
	messages = [
		{"role": "developer", "content": system_prompt},
	]

	# include last N messages to maintain context
	recent = history[-10:] if history else []
	for m in recent:
		role = m.get("role")
		content = m.get("content")
		if role in ("user", "assistant"):
			messages.append({"role": role, "content": content})

	# finally add this user message
	messages.append({"role": "user", "content": user_message})

	# Call OpenAI Responses API; include file_search tool if vector store exists
	kwargs = {
		"model": "gpt-4o-mini",
		"input": messages,
		"temperature": 0.2,
	}

	if vector_store_id:
		kwargs["tools"] = [
			{
				"type": "file_search",
				"vector_store_ids": [vector_store_id],
				"max_num_results": 10,
			}
		]

	resp = client.responses.create(**kwargs)
	return resp.output_text


# Layout: chat area (scrollable) + fixed-ish input at bottom
chat_area = st.container()
with chat_area:
	# height set so that input below appears fixed visually; messages scroll inside
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

	st.markdown(chat_box, unsafe_allow_html=True)


# Input area
st.write("")
cols = st.columns([8, 1])
with cols[0]:
	user_input = st.text_input("메시지를 입력하세요", key="chat_input", placeholder="질문을 입력하고 Enter 또는 전송 버튼을 누르세요")
with cols[1]:
	send = st.button("전송")

def handle_send():
	text = st.session_state.get("chat_input", "").strip()
	if not text:
		return
	# append user message
	st.session_state["chat_history"].append({"role": "user", "content": text})

	# generate assistant response
	try:
		with st.spinner("AI가 답변을 생성하는 중입니다..."):
			reply = generate_response(client, text, st.session_state["chat_history"], vector_store_id)
	except Exception as e:
		reply = "죄송합니다. 응답 생성 중 오류가 발생했습니다. 나중에 다시 시도해 주세요."
		st.error(f"오류: {e}")

	st.session_state["chat_history"].append({"role": "assistant", "content": reply})
	# clear input
	st.session_state["chat_input"] = ""


if send:
	handle_send()

# Also handle Enter key (Streamlit triggers form submission differently); offer a small button above
if st.session_state.get("chat_history"):
	# simple instruction
	st.info("위 스크롤 영역을 사용해 대화를 확인하세요. 입력창은 항상 하단에 있습니다.")