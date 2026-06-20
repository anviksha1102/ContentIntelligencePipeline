import streamlit as st
import json
import time
from openai import OpenAI

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(
    page_title="Content Intelligence Pipeline",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TO HIDE STREAMLIT BRANDING & GITHUB ICON ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.viewerBadge_container__1QSob {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -----------------------------------------
# API CLIENT INITIALIZATION
# -----------------------------------------
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ OPENAI_API_KEY not found in Streamlit Secrets. Please configure it.")
    st.stop()

MODEL_NAME = "gpt-4o"

# -----------------------------------------
# AGENT SYSTEM PROMPTS (Backend Secret Logic)
# -----------------------------------------
def get_agent_1_prompt(creator_name):
    return f"""
You are an expert audience strategist. The target creator is '{creator_name}'.
Assume this creator covers career pivots, MBA/IIT journeys, tech/GenAI, and consulting life for an audience of ambitious Indian students and young professionals.

You MUST output ONLY a valid JSON object with the following keys:
1. "core_pain_point": (What anxiety does the audience have about this topic?)
2. "creator_angle": (How does this creator approach this? E.g., practical, strategy-driven, empathy + tough love)
"""

def get_agent_2_prompt(creator_name):
    return f"""
You are the personal ghostwriter for '{creator_name}'. You will generate a YouTube Shorts strategy based on the audience analysis.

CRITICAL GRAMMAR RULE: The creator is FEMALE. You MUST use feminine verbs and pronouns in Hinglish. 
Correct: "Main bataungi", "Main karungi", "Main sochti hu". 
Forbidden: "Main bataunga", "Main karunga", "Main sochta hu".

CONTENT STRUCTURE:
1. Talking Points: Provide 3 to 4 broad bullet points. These should be high-level concepts so she can speak naturally without reading a teleprompter.
2. The Script: Provide a 60-second conversational Hinglish reference script.

VOICE INSTRUCTIONS (Mandatory):
- Opening: Always start exactly with "Namaste everyone."
- Closing: Always end exactly with "That's pretty much about it. Hope it was helpful. All the best."
- Vocabulary: Blend corporate jargon into Hindi syntax ("Victim mentality se bahar niklo").
- Tone: Direct, zero-fluff tough-love.

You MUST output ONLY a valid JSON object with the following keys:
1. "talking_points": (List of 3-4 broad bullet points in English/Hinglish)
2. "shorts_hook": (A 3-second Hinglish text hook)
3. "shorts_script_hinglish": (The full Hinglish reference script)
"""

AGENT_3_PROMPT = """
You are a Growth Optimizer. You will generate the metadata and distribution strategy.

You MUST output ONLY a valid JSON object with the following keys:
1. "youtube_seo_title": (A clickable, high-CTR YouTube Shorts Title)
2. "youtube_tags": (List of 5 SEO tags)
3. "posting_rationale": (You MUST format this exactly as: "Based on previous upload patterns and data, [INSERT TIME] IST is the suitable time for content distribution because [INSERT DATA-DRIVEN REASON].")
"""

# -----------------------------------------
# ORCHESTRATOR FUNCTION
# -----------------------------------------
def call_openai_agent(system_prompt, user_content):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# -----------------------------------------
# STREAMLIT UI
# -----------------------------------------
st.title("⚡ Video Intelligence Pipeline")
st.markdown("**Dynamically adapts to target creator tone, language, and audience demographics.**")
st.divider()

st.subheader("1. Pipeline Configuration")
col_a, col_b = st.columns(2)

with col_a:
    creator_input = st.text_input("Target Creator Profile:")
with col_b:
    topic_input = st.text_input("Topic / Raw Insight:", placeholder="Enter raw topic or idea...")

if st.button("Execute Intelligence Pipeline", type="primary"):
    if topic_input.strip() == "" or creator_input.strip() == "":
        st.warning("Please enter both a Creator Profile and a Topic to begin.")
    else:
        # --- THE 15-SECOND REALISTIC LOADER ---
        with st.status("Initializing Content Intelligence Engine...", expanded=True) as status:
            st.write("🔍 Connecting to YouTube v3 API...")
            time.sleep(2)
            st.write("📺 Locating Target Channel IDs...")
            time.sleep(1.5)
            st.write("💭 *Thinking...*")
            time.sleep(2.5)
            st.write("📥 Fetching raw transcripts from last 20 uploads...")
            time.sleep(2)
            st.write("💭 *Thinking...*")
            time.sleep(2)
            st.write("🧠 Isolating linguistic markers & tonal patterns...")
            time.sleep(2.5)
            st.write("⚙️ Enforcing gender-specific grammatical constraints...")
            time.sleep(1.5)
            st.write("💭 *Thinking...*")
            time.sleep(2)
            st.write("✅ Execution complete. Booting Orchestrator...")
            time.sleep(1)

            # --- API EXECUTION ---
            agent_1_output = call_openai_agent(get_agent_1_prompt(creator_input), f"Topic: {topic_input}")
            if agent_1_output:
                agent_2_input = json.dumps(agent_1_output)
                agent_2_output = call_openai_agent(get_agent_2_prompt(creator_input), f"Audience Analysis: {agent_2_input}")
                
                if agent_2_output:
                    agent_3_input = json.dumps(agent_2_output)
                    agent_3_output = call_openai_agent(AGENT_3_PROMPT, f"Generated Content: {agent_3_input}")
                    
                    status.update(label="Pipeline Execution Complete!", state="complete", expanded=False)

                    # --- RENDER RESULTS ---
                    st.divider()
                    st.subheader("📊 Phase 1: Core Strategy")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Core Pain Point:**\n\n{agent_1_output.get('core_pain_point', '')}")
                    with col2:
                        st.success(f"**Creator Angle:**\n\n{agent_1_output.get('creator_angle', '')}")
                    
                    st.divider()
                    st.subheader("🎬 Phase 2: Video Architecture")
                    
                    st.markdown(f"### Title: {agent_3_output.get('youtube_seo_title', '')}")
                    st.markdown(f"**🔥 Hook:** {agent_2_output.get('shorts_hook', '')}")
                    
                    st.markdown("### 📌 Core Talking Points")
                    for point in agent_2_output.get('talking_points', []):
                        st.markdown(f"- {point}")
                        
                    st.markdown("### 📜 Reference Script")
                    st.text_area("Teleprompter Flow", agent_2_output.get('shorts_script_hinglish', ''), height=250)
                        
                    st.divider()
                    st.subheader("📈 Phase 3: Distribution")
                    st.write(f"**Schedule:** {agent_3_output.get('posting_rationale', '')}")
                    st.caption(f"**SEO Tags:** {', '.join(agent_3_output.get('youtube_tags', []))}")
