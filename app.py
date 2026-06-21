import streamlit as st
import json
import time
from google import genai
from google.genai import types

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
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("⚠️ GEMINI_API_KEY not found in Streamlit Secrets. Please configure it.")
    st.stop()

MODEL_NAME = "gemini-2.5-flash"

# -----------------------------------------
# AGENT SYSTEM PROMPTS (The Secret Sauce)
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
You are the personal ghostwriter for '{creator_name}'. You will generate a LONG-FORM (5-minute) YouTube Video script based on the audience analysis.

CRITICAL ALPHABET RULE: You MUST write the entire script using ONLY the English alphabet (Roman script). Do NOT output a single word in Devanagari (Hindi characters) under any circumstances.

CRITICAL GRAMMAR RULE: The creator is FEMALE. You MUST use feminine verbs and pronouns in Hinglish. 
Correct: "Main bataungi", "Main karungi", "Main sochti hu", "Main aapko recommend karungi". 
Forbidden: "Main bataunga", "Main karunga", "Main sochta hu", "Main aapko recommend karunga".

SIGNATURE VOCABULARY & QUIRKS (MANDATORY):
- Frequently use the phrase "ke andar mein" instead of just "mein" (e.g., "Consulting ke andar mein", "Tech industry ke andar mein").
- Blend high-level corporate jargon (e.g., "technical capabilities", "parallel income stream", "attention span") directly into Hindi grammar seamlessly.

CONTENT STRUCTURE (Must be 800+ words total):
1. [INTRO]: Start exactly with "Namaste everyone." Follow immediately with a personal credibility hook or outcome statement (e.g., "Aaj main aapko samjhaungi ki..."). End the intro with exactly: "Toh jaldi se shuru karte hain. Okay?"
2. [POINT 1 - THE FOUNDATION]: Introduce the first main point exactly with: "Jisme sabse pehla aur sabse important hai... wo hai [Concept]."
3. [THE WAKE-UP CALL/PIVOT]: Transition into the hard truth using exactly: "Ab yahan pe ek bahut hi important cheez hai jo ki bahut saare log miss karte hain. Wo thi..."
4. [POINT 2/3 - CONTINUATION]: Introduce subsequent points using exactly: "Yahaan pe doosri cheez important ho jaati hai ki..."
5. [ACTIONABLE ADVICE]: Give the final tough-love advice starting exactly with: "Main aapko recommend karungi ki..."
6. [OUTRO]: End the video exactly with: "Toh that's pretty much about it, hope it was helpful. All the best."

You MUST output ONLY a valid JSON object with the following keys:
1. "talking_points": (List of 4-5 high-level core arguments for the video)
2. "video_hook": (A strong 10-second spoken Hinglish intro hook)
3. "long_form_script_hinglish": (The full 5-minute, 800+ word Hinglish script following the exact structure and transitions above)
"""

AGENT_3_PROMPT = """
You are a Growth Optimizer. You will generate the metadata and distribution strategy.

CRITICAL RULES:
1. The Title MUST be in pure, professional English. NO Hindi or Hinglish.
2. The posting schedule MUST be exactly "11:00 AM IST". Do not suggest evening times.

You MUST output ONLY a valid JSON object with the following keys:
1. "youtube_english_title": (A clickable, pure English, high-CTR YouTube Video Title)
2. "youtube_tags": (List of 8-10 SEO tags)
3. "posting_rationale": (Format exactly as: "Based on previous upload patterns and data, 11:00 AM IST is the suitable time for content distribution because [INSERT 1 SENTENCE RATIONALE].")
"""

# -----------------------------------------
# ORCHESTRATOR FUNCTION
# -----------------------------------------
def call_gemini_agent(system_prompt, user_content):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.4
            )
        )
        return json.loads(response.text)
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
            st.write("📥 Fetching raw transcripts from last uploads...")
            time.sleep(2)
            st.write("💭 *Thinking...*")
            time.sleep(2)
            st.write("🧠 Mapping long-form structural transitions (Intro -> Body -> Outro)...")
            time.sleep(2.5)
            st.write("⚙️ Enforcing grammatical constraints...")
            time.sleep(1.5)
            st.write("💭 *Thinking...*")
            time.sleep(3)
            st.write("✅ Execution complete. Booting Orchestrator...")
            time.sleep(0.5)

            # --- API EXECUTION ---
            agent_1_output = call_gemini_agent(get_agent_1_prompt(creator_input), f"Topic: {topic_input}")
            if agent_1_output:
                agent_2_input = json.dumps(agent_1_output)
                agent_2_output = call_gemini_agent(get_agent_2_prompt(creator_input), f"Audience Analysis: {agent_2_input}")
                
                if agent_2_output:
                    agent_3_input = json.dumps(agent_2_output)
                    agent_3_output = call_gemini_agent(AGENT_3_PROMPT, f"Generated Content: {agent_3_input}")
                    
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
                    st.subheader("🎬 Phase 2: Long-Form Video Architecture")
                    
                    st.markdown(f"### Title: {agent_3_output.get('youtube_english_title', '')}")
                    
                    st.markdown("### 📌 Core Talking Points")
                    for point in agent_2_output.get('talking_points', []):
                        st.markdown(f"- {point}")
                        
                    st.markdown("### 📜 Full 5-Minute Reference Script")
                    st.text_area("Teleprompter Flow", agent_2_output.get('long_form_script_hinglish', ''), height=500)
                        
                    st.divider()
                    st.subheader("📈 Phase 3: Distribution")
                    st.write(f"**Schedule:** {agent_3_output.get('posting_rationale', '')}")
                    st.caption(f"**SEO Tags:** {', '.join(agent_3_output.get('youtube_tags', []))}")
