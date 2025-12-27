import streamlit as st
from agent import PharmacyAgent

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="AI Pharmacist Assistant",
    page_icon="💊",
    layout="centered"
)

st.title("💊 AI Pharmacist Assistant")
st.caption("Real-time pharmacy agent – Home Assignment")

# --------------------------------------------------
# Session State Initialization
# --------------------------------------------------
if "agent" not in st.session_state:
    st.session_state.agent = PharmacyAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# Display Chat History
# --------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------
# User Input
# --------------------------------------------------
prompt = st.chat_input("How can I help you today?")
if not prompt:
    st.stop()

# Add user message
st.session_state.messages.append({"role": "user", "content": prompt})
with st.chat_message("user"):
    st.markdown(prompt)

# --------------------------------------------------
# Assistant Response (Streaming)
# --------------------------------------------------
with st.chat_message("assistant"):
    response_placeholder = st.empty()
    full_response = ""

    with st.status("Processing request...", expanded=True) as status:
        try:
            stream = st.session_state.agent.chat_with_streaming(
                prompt,
                st.session_state.messages
            )
            first_chunk = True
            for chunk in stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # סינון קריאות כלים - זה מה שימנע את ה-JSON המכוער על המסך
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    continue
                    
                if delta.content:
                    full_response += delta.content
                    response_placeholder.markdown(full_response + "▌")

            status.update(
                label="Done",
                state="complete",
                expanded=False
            )

        except Exception as e:
            status.update(
                label="Error",
                state="error",
                expanded=True
            )
            st.error(f"Unexpected error: {e}")

    response_placeholder.markdown(full_response)

# Save assistant message
st.session_state.messages.append(
    {"role": "assistant", "content": full_response}
)
