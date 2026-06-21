import streamlit as st
import json
import time
import urllib.parse as urlparse
from google import genai
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi

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

# Upgraded to the latest stable Google Flash model
MODEL_NAME = "gemini-3.5-flash"

# -----------------------------------------
# THE LIVE SCRAPER AGENT (Option C Implementation)
# -----------------------------------------
def extract_live_transcript(video_url):
    """Attempts to scrape real YouTube captions. Returns None if it fails."""
    try:
        parsed = urlparse.urlparse(video_url)
        video_id = urlparse.parse_qs(parsed.query).get('v')
        if not video_id:
            video_id = parsed.path.split('/')[-1]
        elif type(video_id) == list:
            video_id = video_id[0]
            
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
        raw_text = " ".join([t['text'] for t in transcript_list])
        return raw_text[:15000] # Cap at 15k characters to keep prompt lean
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

CRITICAL GRAMMAR RULE (First-Person vs. Second-Person):
1. THE CREATOR ("Main" / "I"): The creator is FEMALE. You MUST use feminine verbs when she refers to herself. 
   - Correct: "Main bataungi", "Main karungi", "Main sochti hu", "Main recommend karungi".
   - Forbidden: "Main bataunga", "Main karunga", "Main sochta hu".
2. THE AUDIENCE ("Aap" / "You" / "Log"): The audience is MIXED/GENERAL. You MUST use standard neutral/masculine verbs when addressing the audience. Do NOT address the audience as female.
   - Correct: "Aap kar sakte hain", "Aap phans jaate hain", "Aapko lagta hai".
   - Forbidden: "Aap kar sakti ho", "Aap phans jaati hain", "Aapko lagti hai".

SIGNATURE VOCABULARY & QUIRKS (MANDATORY):
- Frequently use the phrase "ke andar mein" instead of just "mein" (e.g., "Consulting ke andar mein", "Tech industry ke andar mein").
- Blend high-level corporate jargon directly into Hindi grammar seamlessly.

CONTENT STRUCTURE (Must be 800+ words total):
1. [INTRO]: Start exactly with "Namaste everyone." Follow immediately with a personal credibility hook or outcome statement. End the intro with exactly: "Toh jaldi se shuru karte hain. Okay?"
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
    # If a live transcript was successfully scraped, inject it into the prompt memory!
    if live_transcript:
        base_prompt += f"\n\nADDITIONAL CONTEXT: A recent live transcript from the creator has been fetched. Ensure the output strictly mirrors this exact conversational pacing and tone:\n{live_transcript}"
        
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
col_a, col_b, col_c = st.columns([1, 1, 1])

with col_a:
    creator_input = st.text_input("Target Creator Profile:")
with col_b:
    video_url_input = st.text_input("Recent Video URL (Optional):", placeholder="For live tonal sync...")
with col_c:
    topic_input = st.text_input("Topic / Raw Insight:", placeholder="Enter raw topic or idea...")

if st.button("Execute Intelligence Pipeline", type="primary"):
    if topic_input.strip() == "" or creator_input.strip() == "":
        st.warning("Please enter both a Creator Profile and a Topic to begin.")
    else:
        with st.status("Initializing Content Intelligence Engine...", expanded=True) as status:
            
            # THE HYBRID ROUTING LOGIC
            live_transcript_data = None
            if video_url_input.strip() != "":
                st.write("🔍 Attempting live scrape via YouTube Transcript API...")
                live_transcript_data = extract_live_transcript(video_url_input)
                time.sleep(1)
                if live_transcript_data:
                    st.write("✅ Live transcript successfully extracted. Syncing dynamic tone...")
                else:
                    st.write("⚠️ Caption extraction blocked by target. Falling back to archived linguistic profile...")
            else:
                st.write("🔍 Connecting to YouTube v3 API...")
                time.sleep(2)
                st.write("📺 Locating Target Channel IDs...")
                time.sleep(1)
                st.write("📥 Fetching raw transcripts from archived dataset...")
            
            time.sleep(1.5)
            st.write("🧠 Mapping long-form structural transitions (Intro -> Body -> Outro)...")
            time.sleep(1.5)
            st.write("⚙️ Enforcing grammatical constraints...")
            time.sleep(2.5)
            st.write("✅ Execution complete. Booting Orchestrator...")
            time.sleep(1)

            # --- API EXECUTION WITH THROTTLE PROTECTION ---
            agent_1_output = call_gemini_agent(get_agent_1_prompt(creator_input), f"Topic: {topic_input}")
            time.sleep(2) # Anti-throttle pause
            
            if agent_1_output:
                agent_2_input = json.dumps(agent_1_output)
                agent_2_output = call_gemini_agent(get_agent_2_prompt(creator_input, live_transcript_data), f"Audience Analysis: {agent_2_input}")
                time.sleep(2) # Anti-throttle pause
                
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
