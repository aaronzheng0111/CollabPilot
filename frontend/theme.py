import streamlit as st


CSS = """
<style>
h1, h2, h3 {
  font-weight: 400;
  letter-spacing: -0.3px;
}
h1 { font-size: 28px; }
h2, h3 { font-size: 22px; }

.cp-status {
  background: #181715;
  color: #faf9f5;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.cp-status code {
  background: transparent;
  color: #faf9f5;
  font-family: "JetBrains Mono", ui-monospace, monospace;
}
.cp-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #a09d96;
}
.cp-status-running .cp-dot { background: #e8a55a; }
.cp-status-succeeded .cp-dot { background: #5db872; }
.cp-status-failed .cp-dot { background: #c64545; }
.cp-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #a09d96;
  border-top-color: #e8a55a;
  border-radius: 9999px;
  animation: cp-spin 0.8s linear infinite;
}
@keyframes cp-spin { to { transform: rotate(360deg); } }

.st-key-cp-secondary {
  background: #efe9de;
  border-radius: 12px;
  padding: 24px;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: #f5f0e8;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
  background: transparent;
  border: 1px solid #e6dfd8;
}
</style>
"""


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
