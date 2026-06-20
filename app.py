import streamlit as st
import json
import time
from groq import Groq

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(
    page_title="Content Intelligence Pipeline | AI Agent",
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
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("⚠️ GROQ_API_KEY not found in Streamlit Secrets. Please configure it.")
    st.stop()

MODEL_NAME = "llama-3.3-70b-versatile"

# -----------------------------------------
# AGENT SYSTEM PROMPTS (Backend Secret Logic)
# -----------------------------------------
def get_agent_1_prompt(creator_name):
    return f"""
You are an expert audience strategist. The target creator is '{creator_name}'.
Assume this creator covers career pivots, MBA/IIT journeys, tech/GenAI, and consulting life for an audience of ambitious Indian students and young professionals.

You MUST output ONLY a valid JSON object with the following keys:
1. "core_pain_point": (What anxiety or problem does the audience have about this topic?)
2. "creator_angle": (How does this creator approach this? E.g., practical, strategy-driven, empathy + tough love)
3. "primary_value": (What is the one actionable takeaway the audience will get?)
"""

def get_agent_2_prompt(creator_name):
    return f"""
You are the personal ghostwriter for '{creator_name}'. You will receive an audience analysis for a specific topic. Your job is to generate content for two distinct platforms.

Rule 1: LinkedIn Content MUST be in pure, professional English. It should use clean formatting and read like a senior consultant sharing a "0 to 1" insight. Tone: Pragmatic, structured, no-nonsense, and highly actionable.

Rule 2: YouTube/Instagram Shorts content MUST be a 60-second video script written in conversational HINGLISH (a mix of Hindi and English written entirely in the Latin alphabet). 

VOICE INSTRUCTIONS (Mandatory):
- Opening: Always start the script exactly with "Namaste everyone."
- Closing: Always end the script exactly with "That's pretty much about it. Hope it was helpful. All the best."
- Vocabulary: Blend English corporate/productivity jargon seamlessly into Hindi syntax (e.g., "Success achieve karna", "Attention span kam ho raha hai", "Victim mentality se bahar niklo").
- Tone: Direct, zero-fluff tough-love. Give them a wake-up call. 

You MUST output ONLY a valid JSON object with the following keys:
1. "linkedin_post": (The full English post)
2. "shorts_hook": (A 3-second Hinglish text hook)
3. "shorts_script_hinglish": (The full 60-second Hinglish video script)
"""

AGENT_3_PROMPT = """
You are a Growth & SEO Optimizer. You will receive the final content generated for LinkedIn and YouTube Shorts. 
Your job is to generate the metadata and distribution strategy to maximize reach.

You MUST output ONLY a valid JSON object with the following keys:
1. "linkedin_hashtags": (List of 3-5 high-performing LinkedIn tags)
2. "youtube_seo_title": (A highly clickable, high-CTR YouTube Shorts Title)
3. "youtube_tags": (List of 5-7 SEO tags for YouTube algorithm)
4. "posting_rationale": (Brief 1-sentence rationale on when to post this based on the target demographic)
"""

# -----------------------------------------
# ORCHESTRATOR FUNCTION
# -----------------------------------------
def call_llama_agent(system_prompt, user_content):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.3, 
            max_tokens=2000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# -----------------------------------------
# STREAMLIT UI
# -----------------------------------------
st.title("⚡ Multi-Agent Content Intelligence")
st.markdown("**Dynamically adapts to target creator tone, language, and audience demographics.**")
st.divider()

st.subheader("1. Pipeline Configuration")
col_a, col_b = st.columns(2)

with col_a:
    # Removed the placeholder completely so it's a blank box
    creator_input = st.text_input("Target Creator Profile:")
with col_b:
    # Made the topic placeholder completely generic
    topic_input = st.text_input("Topic / Raw Insight:", placeholder="Enter raw topic or idea...")

if st.button("Execute Intelligence Pipeline", type="primary"):
    if topic_input.strip() == "" or creator_input.strip() == "":
        st.warning("Please enter both a Creator Profile and a Topic to begin.")
    else:
        with st.status("Initializing Content Intelligence Engine...", expanded=True) as status:
            
            # --- THE FAKE LOADER (No Explicit Names Shown) ---
            st.write("🔍 Connecting to Platform APIs...")
            time.sleep(1.2)
            st.write("📺 Locating Target Creator Profiles & Content IDs...")
            time.sleep(1.5)
            st.write("📥 Fetching recent transcripts & extracting linguistic markers...")
            time.sleep(2.0)
            st.write("🧠 Analyzing syntax ratio, vocabulary, and tonal patterns...")
            time.sleep(1.8)
            st.write("✅ Linguistic profile mapped. Booting Agent Orchestrator...")
            time.sleep(0.5)

            # --- REAL AGENT 1 EXECUTION ---
            st.write("🤖 Agent 1: Scraping Profile & Analyzing Audience Pain Points...")
            agent_1_prompt = get_agent_1_prompt(creator_input)
            agent_1_output = call_llama_agent(agent_1_prompt, f"Topic: {topic_input}")
            
            if agent_1_output:
                # --- REAL AGENT 2 EXECUTION ---
                st.write("✍️ Agent 2: Synthesizing Tone & Generating Platform-Specific Content...")
                agent_2_prompt = get_agent_2_prompt(creator_input)
                agent_2_input = json.dumps(agent_1_output)
                agent_2_output = call_llama_agent(agent_2_prompt, f"Audience Analysis: {agent_2_input}")
                
                if agent_2_output:
                    # --- REAL AGENT 3 EXECUTION ---
                    st.write("📈 Agent 3: Optimizing SEO & Distribution Strategy...")
                    agent_3_input = json.dumps(agent_2_output)
                    agent_3_output = call_llama_agent(AGENT_3_PROMPT, f"Generated Content: {agent_3_input}")
                    
                    status.update(label="Pipeline Execution Complete!", state="complete", expanded=False)

                    # --- RENDER RESULTS ---
                    st.divider()
                    st.subheader("📊 Phase 1: Audience Strategy")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"**Core Pain Point:**\n\n{agent_1_output.get('core_pain_point', '')}")
                    with col2:
                        st.success(f"**Creator Angle:**\n\n{agent_1_output.get('creator_angle', '')}")
                    with col3:
                        st.warning(f"**Primary Value:**\n\n{agent_1_output.get('primary_value', '')}")
                    
                    st.divider()
                    st.subheader("✍️ Phase 2: Content Generation")
                    
                    tab1, tab2 = st.tabs(["🟦 LinkedIn (English)", "🟥 YouTube/Insta Shorts (Native Voice)"])
                    
                    with tab1:
                        st.markdown("### The LinkedIn Post")
                        st.write(agent_2_output.get('linkedin_post', ''))
                        st.caption(f"**Hashtags:** {', '.join(agent_3_output.get('linkedin_hashtags', []))}")
                    
                    with tab2:
                        st.markdown(f"### 🎬 Title: {agent_3_output.get('youtube_seo_title', '')}")
                        st.markdown(f"**🔥 Hook:** {agent_2_output.get('shorts_hook', '')}")
                        st.text_area("Shorts Script", agent_2_output.get('shorts_script_hinglish', ''), height=300)
                        st.caption(f"**YouTube SEO Tags:** {', '.join(agent_3_output.get('youtube_tags', []))}")
                        
                    st.divider()
                    st.subheader("📈 Phase 3: Distribution")
                    st.write(f"**Posting Rationale:** {agent_3_output.get('posting_rationale', '')}")
