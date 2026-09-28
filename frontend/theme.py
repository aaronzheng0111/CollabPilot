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
  flex: 0 0 auto;
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

.cp-tool-line {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #8e8b82;
  padding: 2px 4px 2px 10px;
  margin: 2px 0 2px 4px;
  border-left: 2px solid #e6dfd8;
  background: transparent;
  line-height: 1.4;
}
.cp-tool-line code {
  background: transparent;
  color: #6c6a64;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 11px;
  padding: 0;
}
.cp-tool-line .cp-dot {
  width: 5px;
  height: 5px;
  background: #a09d96;
}
.cp-tool-meta { color: #a09d96; }
.cp-tool-line-running {
  color: #6c6a64;
  border-left-color: #e8a55a;
}
.cp-tool-line-running .cp-spinner {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
}
.cp-tool-line-running code {
  color: #3d3d3a;
}
.cp-tool-line-succeeded,
.cp-tool-line-succeeded code {
  color: #5db872;
}
.cp-tool-line-succeeded {
  border-left-color: #5db872;
}
.cp-tool-line-failed,
.cp-tool-line-failed code {
  color: #8e8b82;
}
.cp-tool-line-failed {
  border-left-color: #c64545;
}

/* Left main table + right chat share the same top edge in the 3:2 row.
   min-width:0 lets the flex column shrink so a wide glide canvas cannot
   push past the column and paint over the chat.
   gap:8px matches st.columns(..., gap=8) — a few pixels, not a gutter.
   :has(.st-key-cp-chat-frame) covers the case where st.empty() omits the
   table key class from the DOM. */
div[data-testid="stHorizontalBlock"]:has(.st-key-cp-main-table),
div[data-testid="stHorizontalBlock"]:has(.st-key-cp-chat-frame) {
  gap: 8px;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-cp-main-table) > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.st-key-cp-chat-frame) > div[data-testid="stColumn"] {
  min-width: 0;
  overflow-x: clip;
}
.st-key-cp-main-table,
.st-key-cp-chat-frame {
  margin-top: 0;
}
/* Host clips X so nothing paints over chat. Real H-scroll lives on
   .st-key-cp-table-scroll (idle catalog + search results). */
.st-key-cp-main-table {
  padding-top: 0;
  min-width: 0;
  max-width: 100%;
  overflow-x: clip;
  overflow-y: hidden;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-cp-chat-frame) > div[data-testid="stColumn"]:first-child {
  overflow-y: hidden;
}
/* One H-scroll bar on this container. Inner HTML table has fixed min-width
   (≥1600px / column sum) so scrollWidth > clientWidth; Glide is not used
   for the creator grid (it shrink-to-fits and never engages overflow-x). */
.st-key-cp-table-scroll {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}
.cp-table-scroll-inline {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}
.st-key-cp-table-scroll .cp-table-inner,
.cp-table-scroll-inline .cp-table-inner {
  display: block;
  max-width: none;
  box-sizing: content-box;
  min-width: 1600px;
}
.st-key-cp-table-scroll .cp-creator-table,
.cp-table-scroll-inline .cp-creator-table {
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  font-size: 14px;
  line-height: 1.35;
  color: #252523;
  max-width: none;
  min-width: 1600px;
}
.st-key-cp-table-scroll .cp-creator-table th,
.st-key-cp-table-scroll .cp-creator-table td,
.cp-table-scroll-inline .cp-creator-table th,
.cp-table-scroll-inline .cp-creator-table td {
  box-sizing: border-box;
  padding: 8px;
  border-bottom: 1px solid #ebe6df;
  text-align: left;
  vertical-align: top;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: clip;
  /* Opaque so neighbor overflow cannot show through. */
  background: #faf9f5;
}
.st-key-cp-table-scroll .cp-creator-table th,
.cp-table-scroll-inline .cp-creator-table th {
  font-weight: 600;
  color: #3d3d3a;
  background: #f5f0e8;
  position: sticky;
  top: 0;
  z-index: 1;
}
/* Pinned identity columns: opaque so scrolled cells do not show through. */
.st-key-cp-table-scroll .cp-creator-table .cp-sticky-edge,
.cp-table-scroll-inline .cp-creator-table .cp-sticky-edge {
  box-shadow: 8px 0 10px -8px rgba(20, 20, 19, 0.45);
}
.st-key-cp-table-scroll .cp-creator-table tr.cp-row-selected td,
.cp-table-scroll-inline .cp-creator-table tr.cp-row-selected td {
  background: #e8a55a;
  color: #141413;
}
.st-key-cp-table-scroll .cp-creator-table tr.cp-row-selected td.cp-sticky-lead,
.cp-table-scroll-inline .cp-creator-table tr.cp-row-selected td.cp-sticky-lead {
  box-shadow: inset 5px 0 0 #141413;
  font-weight: 700;
}
.st-key-cp-table-scroll .cp-creator-table tr.cp-row-selected td.cp-sticky-edge.cp-sticky-lead,
.cp-table-scroll-inline .cp-creator-table tr.cp-row-selected td.cp-sticky-edge.cp-sticky-lead {
  box-shadow: inset 5px 0 0 #141413, 8px 0 10px -8px rgba(20, 20, 19, 0.45);
}
.st-key-cp-table-scroll .cp-creator-table .cp-td-contact,
.st-key-cp-table-scroll .cp-creator-table .cp-td-topics,
.st-key-cp-table-scroll .cp-creator-table .cp-td-audience_summary,
.st-key-cp-table-scroll .cp-creator-table .cp-td-region,
.cp-table-scroll-inline .cp-creator-table .cp-td-contact,
.cp-table-scroll-inline .cp-creator-table .cp-td-topics,
.cp-table-scroll-inline .cp-creator-table .cp-td-audience_summary,
.cp-table-scroll-inline .cp-creator-table .cp-td-region {
  white-space: nowrap;
}
/* Checkbox picker sits below the HTML table, never stacked on top of it. */
.st-key-cp-selection-picker {
  margin-top: 8px;
  max-width: 280px;
  position: relative;
  z-index: 0;
}
/* AppTest mirror dataframe: keep in DOM, hide from layout. */
.st-key-cp-table-mirror {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  border: 0 !important;
  opacity: 0 !important;
  pointer-events: none !important;
  z-index: -1 !important;
}
/* Compact pager: caption left, prev/next as small side-by-side buttons. */
.st-key-cp-table-pager {
  margin: 6px 0 2px;
  align-items: center;
}
.st-key-cp-table-pager [data-testid="stCaptionContainer"] {
  margin: 0;
  flex: 1 1 auto;
  min-width: 0;
}
.st-key-cp-table-pager [data-testid="stButton"] {
  width: auto;
  flex: 0 0 auto;
}
.st-key-cp-table-pager [data-testid="stButton"] button {
  min-height: 2rem;
  padding: 0.2rem 0.7rem;
  white-space: nowrap;
}
.st-key-cp-main-table .cp-table-empty,
.st-key-cp-main-table .cp-table-loading {
  font-size: 15px;
}
/* Side panel: viewport height (not % of short table column). */
.st-key-cp-chat-frame {
  position: sticky;
  top: 0.75rem;
  height: calc(100vh - 4.5rem);
  max-height: calc(100vh - 4.5rem);
  min-width: 0;
  background: #efe9de;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.st-key-cp-chat-frame > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-cp-chat-frame > div[data-testid="stVerticalBlockBorderWrapper"] > div {
  height: 100%;
  max-height: calc(100vh - 4.5rem);
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.cp-projects-label {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #8e8b82;
}
[data-testid="stSidebar"] .cp-projects-label {
  margin-top: 4px;
}
[data-testid="stSidebar"] button {
  font-size: 13px;
  text-align: left;
  line-height: 1.3;
  white-space: normal;
}
.st-key-cp-chat-thread {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.st-key-cp-chat-history {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  height: calc(100vh - 11rem) !important;
  max-height: calc(100vh - 11rem) !important;
}
.st-key-cp-chat-history [data-testid="stVerticalBlockBorderWrapper"],
.st-key-cp-chat-history [data-testid="stScrollToBottomContainer"] {
  overflow-y: auto !important;
  height: calc(100vh - 11rem) !important;
  max-height: calc(100vh - 11rem) !important;
}
.st-key-cp-chat-history [data-testid="stChatMessage"] {
  padding: 0.55rem 0.75rem;
  margin-bottom: 0.35rem;
}
.st-key-cp-chat-history button[kind="tertiary"],
.st-key-cp-chat-history [data-testid="stBaseButton-tertiary"] {
  font-size: 11px;
  color: #a09d96;
  min-height: 1.4rem;
  padding: 0 0.25rem;
}
.st-key-cp-chat-decisions {
  flex-shrink: 0;
  margin-top: 8px;
  padding: 10px 4px 4px;
  border-top: 1px solid #e6dfd8;
  background: #efe9de;
}
.st-key-cp-chat-decisions h4 {
  font-size: 15px;
  margin: 0 0 6px;
}
.st-key-cp-chat-composer {
  flex-shrink: 0;
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid #e6dfd8;
}
.st-key-cp-chat-composer [data-testid="stButton"] button {
  min-height: 2.4rem;
}

.st-key-cp-secondary {
  background: #efe9de;
  border-radius: 12px;
  padding: 24px;
}
.st-key-cp-secondary h4 { font-size: 18px; margin: 0 0 8px; }

.cp-table-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0 0 8px;
  padding: 12px;
  background: rgba(245, 240, 232, 0.92);
  border: 1px solid #e6dfd8;
  border-radius: 12px;
  color: #3d3d3a;
  font-size: 14px;
}
.cp-table-loading .cp-spinner { border-color: #a09d96; border-top-color: #e8a55a; }

.cp-table-empty {
  color: #6c6a64;
  background: #f5f0e8;
  border: 1px dashed #e6dfd8;
  border-radius: 12px;
  padding: 32px 16px;
  text-align: center;
}

.cp-pill {
  display: inline-block;
  border-radius: 9999px;
  background: #efe9de;
  color: #141413;
  font-size: 13px;
  line-height: 1;
  padding: 4px 10px;
  margin-left: 8px;
  vertical-align: middle;
}
.cp-pill code {
  background: transparent;
  color: inherit;
  padding: 0;
  font-family: "JetBrains Mono", ui-monospace, monospace;
}
.cp-pill-mock { background: #efe9de; color: #141413; }
.cp-pill-rule {
  background: #faf9f5;
  color: #3d3d3a;
  border: 1px solid #e6dfd8;
  margin-left: 8px;
}
.cp-pill-llm { background: #252320; color: #faf9f5; }
.cp-pill-mock-send { background: #f5f0e8; color: #6c6a64; }
.cp-pill-assumed { background: #e8a55a; color: #141413; }

.cp-pill-unknown { background: #e8a55a; color: #141413; margin: 0 8px 4px 0; }
.cp-pill-decision { background: #faf9f5; color: #141413; }
.cp-pill-mismatch { background: #e8a55a; color: #141413; margin: 0 8px 4px 0; }

/* 判断依据：product-mockup-card-dark */
.cp-evidence {
  background: #181715;
  color: #faf9f5;
  border-radius: 12px;
  padding: 20px;
  margin-top: 12px;
}
.cp-evidence-header { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.cp-evidence-header h3 { font-size: 18px; margin: 0; color: #faf9f5; }
.cp-evidence-reasons { margin: 12px 0 0; padding-left: 20px; font-size: 14px; line-height: 1.6; }
.cp-evidence-section {
  margin-top: 14px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a09d96;
}
.cp-evidence-item { margin-top: 8px; }
.cp-evidence-item code, .cp-evidence code {
  background: #1f1e1b;
  color: #faf9f5;
  border-radius: 6px;
  padding: 1px 6px;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 12px;
}
.cp-evidence-age { margin-left: 8px; font-size: 12px; color: #a09d96; }
.cp-evidence-text { margin: 4px 0 0; font-size: 13px; line-height: 1.5; color: #e8e0d2; }
.cp-evidence-muted { font-size: 13px; color: #a09d96; }
.cp-evidence-quote { margin: 12px 0 0; font-size: 13px; color: #e8a55a; border-left: 3px solid #e8a55a; padding-left: 12px; }
.cp-evidence-lock { margin-top: 10px; font-size: 13px; color: #e8e0d2; }

.cp-audience { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; margin-top: 8px; }
.cp-audience-cell { font-size: 13px; color: #e8e0d2; }
.cp-audience-label { display: block; font-size: 12px; color: #a09d96; }
.cp-pending-list { margin: 12px 0 20px; }
.cp-pending-list h4 { font-size: 18px; margin: 0 0 8px; }
.cp-pending-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #ebe6df;
  font-size: 14px;
}
.cp-pending-row:last-child { border-bottom: none; }
.cp-pending-reason { color: #252523; }

.cp-goal-card { margin-top: 16px; }
.cp-goal-header { display: flex; align-items: center; gap: 4px; margin-bottom: 8px; }
.cp-goal-header h3 { font-size: 18px; margin: 0; }
.cp-goal-row {
  display: flex;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #ebe6df;
  font-size: 14px;
}
.cp-goal-row:last-child { border-bottom: none; }
.cp-goal-label { flex: 0 0 88px; color: #6c6a64; }
.cp-goal-value { color: #252523; }
.cp-reason { color: #8e8b82; font-size: 12px; margin-left: 6px; }

.cp-draft-card {
  background: #efe9de;
  border-radius: 12px;
  padding: 16px 0 8px;
  margin-top: 8px;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: #f5f0e8;
  border-radius: 10px;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
  background: transparent;
  border: 1px solid #e6dfd8;
  border-radius: 10px;
}

/* coral only: 批准按钮由 theme.primaryColor；勾选框与输入框聚焦环 */
[data-testid="stCheckbox"] input:focus-visible,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stTextInput"] input:focus {
  border-color: #cc785c;
  box-shadow: 0 0 0 3px rgba(204, 120, 92, 0.15);
}
</style>
"""


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
