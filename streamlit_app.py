import streamlit as st
from openai import OpenAI

# --- 글자 크기 및 스타일 커스텀 ---
st.markdown("""
    <style>
    .user-message, .assistant-message {
        font-size: 1.2rem !important;
        line-height: 1.7;
        font-family: "Pretendard", "Apple SD Gothic Neo", "Malgun Gothic", "sans-serif";
    }
    .stChatInputContainer textarea {
        font-size: 1.1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 유튜브 쇼츠 콘텐츠 생성기 챗봇")
st.write("주제, 타겟, 톤을 선택하고 쇼츠 핵심만 빠르게 받아보세요!")

openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")
if not openai_api_key:
    st.info("진행을 위해 API 키를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# 옵션 UI
mode = st.selectbox("모드를 선택하세요", ["유튜브 쇼츠 생성", "기본 대화"])
target = st.selectbox("🎯 타겟층", ["10대", "20대", "직장인", "엄마들", "전 연령"])
tone = st.selectbox("🎨 톤 앤 매너", ["유쾌한", "감성적인", "진지한", "믿음직한", "힙한", "깔끔한"])

# 옵션 변경 시 세션 리셋
reset_flag = False
if "mode_prev" not in st.session_state or st.session_state.mode_prev != mode:
    reset_flag = True
if "target_prev" not in st.session_state or st.session_state.target_prev != target:
    reset_flag = True
if "tone_prev" not in st.session_state or st.session_state.tone_prev != tone:
    reset_flag = True

if reset_flag or "messages" not in st.session_state:
    st.session_state.messages = []
    if mode == "유튜브 쇼츠 생성":
        # 시스템 프롬프트는 대화창에 표시하지 않고 messages에만 저장
        st.session_state.system_prompt = (
            f"너는 유튜브 쇼츠 콘텐츠 기획 전문가야. 타겟은 '{target}', 톤은 '{tone}'야.\n"
            "사용자가 주제를 입력하면 아래와 같은 형식으로만 출력해야 해. **절대 설명문, 장황한 문장, 서론/결론 없이!**\n"
            "각 항목(제목, 후킹 스크립트, 구성, 편집 포인트, 해시태그, 썸네일 문구)을 반드시 줄바꿈하여 출력할 것. (예시: 🎬 제목: ...\\n🧲 후킹 스크립트: ... ) 한 줄에 여러 항목을 쓰지 말 것.\n"
            "---\n"
            "🎬 **제목**: (짧고 강렬하게)\n"
            "🧲 **후킹 스크립트**: (첫 3초 시선 끌 멘트)\n"
            "📄 **콘텐츠 구성 (3단계)**: 1. ... 2. ... 3. ...\n"
            "✂️ **편집 포인트**: - 효과, 자막 등 핵심 2~3개\n"
            "🔖 **해시태그 (5개)**: #...\n"
            "🖼️ **썸네일 문구**: (짧고 임팩트 있게)\n"
            "---\n"
            "⚠️ 절대 한 줄로 작성하지 말고, 반드시 항목별로 줄바꿈해서 출력! 마크다운 템플릿을 어기면 다시 작성."
        )

    else:
        st.session_state.system_prompt = ""
    st.session_state.mode_prev = mode
    st.session_state.target_prev = target
    st.session_state.tone_prev = tone

# --- 줄바꿈 인식 마크다운 렌더 함수 ---
def render_markdown_with_newlines(text):
    st.markdown(
        f"<div class='assistant-message' style='white-space: pre-line'>{text}</div>",
        unsafe_allow_html=True
    )

# --- 기존 메시지(유저/어시스턴트만) 출력 ---
for message in st.session_state.get("messages", []):
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            render_markdown_with_newlines(message['content'])

# --- 사용자 입력 ---
if prompt := st.chat_input("주제를 입력하세요 (예: 아침 루틴, 공부법 등)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 실제 GPT 호출 메시지 배열 만들기 (system + 대화내역)
    full_messages = []
    if mode == "유튜브 쇼츠 생성" and st.session_state.system_prompt:
        full_messages.append({"role": "system", "content": st.session_state.system_prompt})
    full_messages.extend(st.session_state.messages)

    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=full_messages,
        stream=True,
    )
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- 답변 저장 ---
if st.session_state.get("messages") and st.session_state.messages[-1]["role"] == "assistant":
    last_response = st.session_state.messages[-1]["content"]
    st.download_button("💾 답변 저장하기", last_response, file_name="shorts_idea.txt")
