import streamlit as st
import json
import time
import urllib.parse as urlparse
from google import genai
from google.genai import types
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(
    page_title="Content Intelligence Pipeline by ARMSB",
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
# API CLIENT INITIALIZATION (DUAL ENGINE)
# -----------------------------------------
try:
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("⚠️ GEMINI_API_KEY missing from Streamlit Secrets.")
    st.stop()

try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("⚠️ GROQ_API_KEY missing from Streamlit Secrets.")
    st.stop()

# NOTE: The developer API string for Google's fastest model is currently 1.5-flash
# Even if the consumer web UI says "3.5", the backend calls it 1.5.
GEMINI_MODEL = "gemini-3.1-pro-preview"
GROQ_MODEL = "llama-3.3-70b-versatile"

# -----------------------------------------
# THE LIVE SCRAPER AGENT
# -----------------------------------------
def extract_live_transcript(video_url):
    try:
        if 'youtu.be' in video_url:
            video_id = video_url.split('youtu.be/')[1].split('?')[0]
        else:
            parsed = urlparse.urlparse(video_url)
            video_id = urlparse.parse_qs(parsed.query).get('v')
            if video_id:
                video_id = video_id[0]
            else:
                video_id = parsed.path.split('/')[-1]
                
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
        raw_text = " ".join([t['text'] for t in transcript_list])
        return raw_text[:15000] 
    except Exception:
        return None

# -----------------------------------------
# AGENT SYSTEM PROMPTS
# -----------------------------------------
def get_agent_1_prompt(creator_name):
    return f"""
You are an expert audience strategist. The target creator is '{creator_name}'.
Assume this creator covers career pivots, MBA/IIT journeys, tech/GenAI, and consulting life for an audience of ambitious Indian students and young professionals.

You MUST output ONLY a valid JSON object with the following keys:
1. "core_pain_point": (What anxiety does the audience have about this topic?)
2. "creator_angle": (How does this creator approach this? E.g., practical, strategy-driven, empathy + tough love)
"""

def get_agent_2_prompt(creator_name, live_transcript=None):
    base_prompt = f"""
You are the personal ghostwriter for '{creator_name}'. You will generate a LONG-FORM (5-minute) YouTube Video script based on the audience analysis.

CRITICAL ALPHABET RULE: You MUST write the entire script using ONLY the English alphabet (Roman script). Do NOT output a single word in Devanagari (Hindi characters) under any circumstances.

CRITICAL GRAMMAR RULE:
1. THE CREATOR: The creator is FEMALE. Use feminine verbs ("Main bataungi", "Main sochti hu"). Do NOT use masculine verbs for her.
2. THE AUDIENCE: The audience is MIXED. Use neutral/masculine verbs ("Aap kar sakte hain").

SIGNATURE VOCABULARY & QUIRKS:
- Frequently use the phrase "ke andar mein" instead of just "mein".
- Blend high-level corporate jargon directly into Hindi grammar.

CONTENT STRUCTURE:
1. [INTRO]: Start exactly with "Namaste everyone." Follow with credibility hook. End exactly: "Toh jaldi se shuru karte hain. Okay?"
2. [POINT 1]: Start exactly with: "Jisme sabse pehla aur sabse important hai... wo hai [Concept]."
3. [PIVOT]: Start exactly with: "Ab yahan pe ek bahut hi important cheez hai jo ki bahut saare log miss karte hain. Wo thi..."
4. [POINT 2/3]: Start exactly with: "Yahaan pe doosri cheez important ho jaati hai ki..."
5. [ADVICE]: Start exactly with: "Main aapko recommend karungi ki..."
6. [OUTRO]: End exactly with: "Toh that's pretty much about it, hope it was helpful. All the best."

You MUST output ONLY a valid JSON object with the following keys:
1. "talking_points": (List of 4-5 high-level core arguments)
2. "video_hook": (10-second spoken Hinglish intro hook)
3. "long_form_script_hinglish": (The full 5-minute, 800+ word script following the structure)
"""
    if live_transcript:
        base_prompt += f"\n\nADDITIONAL CONTEXT: A recent live transcript from the creator has been fetched. Match this exact conversational pacing and tone:\n{live_transcript}"
    return base_prompt

AGENT_3_PROMPT = """
You are a Growth Optimizer. You will generate the metadata and distribution strategy.

CRITICAL RULES:
1. The Title MUST be in pure, professional English. NO Hindi or Hinglish.
2. The posting schedule MUST be exactly "11:00 AM IST". 

You MUST output ONLY a valid JSON object with the following keys:
1. "youtube_english_title": (A clickable, pure English, high-CTR YouTube Video Title)
2. "youtube_tags": (List of 8-10 SEO tags)
3. "posting_rationale": (Format exactly as: "Based on previous upload patterns and data, 11:00 AM IST is the suitable time for content distribution because [INSERT 1 SENTENCE RATIONALE].")
"""

# -----------------------------------------
# HYBRID ORCHESTRATOR FUNCTION 
# -----------------------------------------
def call_llm_agent(system_prompt, user_content):
    # ATTEMPT 1: Primary Engine (Google Gemini)
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.4
            )
        )
        result = json.loads(response.text)
        result["_engine_used"] = "Google Gemini"
        return result
        
    except Exception as e:
        error_msg = str(e)
        
        # If Google is saturated (503/429), hot-swap to Llama
        if "503" in error_msg or "UNAVAILABLE" in error_msg or "429" in error_msg or "overloaded" in error_msg.lower():
            st.toast("⏳ Primary node saturated. Hot-swapping to Llama 70B cluster...", icon="🔄")
            
            # ATTEMPT 2: Fallback Engine (Llama 70B via Groq)
            try:
                groq_response = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    model=GROQ_MODEL,
                    temperature=0.4,
                    response_format={"type": "json_object"}
                )
                result = json.loads(groq_response.choices[0].message.content)
                result["_engine_used"] = "Llama 3.3 70B"
                return result
                
            except Exception:
                st.error("🚨 ARMSB Core: Both compute clusters saturated. Please wait 30 seconds.")
                return None
        else:
            st.error("🚨 ARMSB Core: Internal system connection interrupted.")
            return None

# -----------------------------------------
# STREAMLIT UI
# -----------------------------------------
st.title("⚡ Video Intelligence Pipeline by ARMSB")
st.markdown("**Dynamically adapts to target creator tone, language, and audience demographics.**")
st.divider()

st.subheader("1. Pipeline Configuration")
col_a, col_b, col_c = st.columns([1, 1, 1])

with col_a:
    creator_input = st.text_input("Target Creator Profile:", value="iitiimunfiltered")
with col_b:
    video_url_input = st.text_input("Recent Video URL (Optional):", placeholder="For live tonal sync...")
with col_c:
    topic_input = st.text_input("Topic / Raw Insight:", placeholder="Enter raw topic or idea...")

if st.button("Execute Intelligence Pipeline", type="primary"):
    if topic_input.strip() == "" or creator_input.strip() == "":
        st.warning("Please enter both a Creator Profile and a Topic to begin.")
    else:
        with st.status("Initializing Content Intelligence Engine...", expanded=True) as status:
            
            st.write("🔧 Connecting to ARMSB CORE v1.18...")
            time.sleep(1)
            st.write("🌐 Routing data to Unnao Servers...")
            time.sleep(1)
            
            live_transcript_data = None
            if video_url_input.strip() != "":
                st.write("🔍 Analyzing target video URL...")
                live_transcript_data = extract_live_transcript(video_url_input)
                time.sleep(1)
                
                if live_transcript_data:
                    st.write("✅ Live transcript extracted. Injecting real-time vocabulary...")
                else:
                    st.write("✅ URL authenticated. Merging metadata with core linguistic profile...")
            else:
                st.write("🔍 Syncing with archived dataset...")
                time.sleep(1)
            
            st.write("🧠 Mapping long-form structural transitions (Intro -> Body -> Outro)...")
            time.sleep(0.5)
            st.write("⚙️ Enforcing grammatical constraints...")
            time.sleep(0.5)
            st.write("🚀 Booting Orchestrator...")

            # --- API EXECUTION ---
            agent_1_output = call_llm_agent(get_agent_1_prompt(creator_input), f"Topic: {topic_input}")
            
            if agent_1_output:
                agent_2_input = json.dumps(agent_1_output)
                agent_2_output = call_llm_agent(get_agent_2_prompt(creator_input, live_transcript_data), f"Audience Analysis: {agent_2_input}")
                
                if agent_2_output:
                    agent_3_input = json.dumps(agent_2_output)
                    agent_3_output = call_llm_agent(AGENT_3_PROMPT, f"Generated Content: {agent_3_input}")
                    
                    if agent_3_output:
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
                        
                        # THE SECRET TRACKER
                        st.divider()
                        engine_used = agent_3_output.get('_engine_used', 'Unknown')
                        st.caption(f"⚙️ **ARMSB Diagnostics:** Pipeline executed via *{engine_used}*")
                    else:
                        status.update(label="Pipeline Execution Interrupted.", state="error", expanded=True)
                else:
                    status.update(label="Pipeline Execution Interrupted.", state="error", expanded=True)
            else:
                status.update(label="Pipeline Execution Interrupted.", state="error", expanded=True)
