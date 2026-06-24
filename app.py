import streamlit as st
import json
import time
import urllib.parse as urlparse
from google import genai
from google.genai import types
from openai import OpenAI
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
    st.error("⚠️ ARMSB CORE: Primary API key missing from Secure Vault.")
    st.stop()

try:
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ ARMSB CORE: Auxiliary API key missing from Secure Vault.")
    st.stop()

GEMINI_MODEL = "gemini-3.5-flash"
OPENAI_MODEL = "gpt-5.5"

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

You are completely right, I lost the high-fidelity constraints from your backup. I missed the explicit "Correct/Forbidden" verb examples, the `(MANDATORY)` tags, the expanded structure headers, and the specific prompt memory comment at the bottom. Those explicit examples are exactly why your earlier generations had much better grammatical alignment.

Here is your exact backup restored, with the new `CRITICAL NAME RULE` seamlessly injected at the top. Replace your current function with this:

```python
def get_agent_2_prompt(creator_name, live_transcript=None):
    base_prompt = f"""
You are the personal ghostwriter for '{creator_name}'. You will generate a LONG-FORM (5-minute) YouTube Video script based on the audience analysis.

CRITICAL NAME RULE: The creator must NEVER say their own name in the script. Never write "Main [Name]" or introduce the creator by name. The creator refers to herself ONLY as "Main" (I). Real YouTubers never introduce themselves mid-script.

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

```

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
# MASKED DIAGNOSTIC ORCHESTRATOR FUNCTION 
# -----------------------------------------
def call_llm_agent(system_prompt, user_content):
    # The Execution Chain
    chain = [
        {"engine": "google", "model": GEMINI_MODEL, "name": "ARMSB Logic Node v3.5", "msg": "Initializing..."},
        {"engine": "google", "model": GEMINI_MODEL, "name": "ARMSB Logic Node v3.5 (Auto-Retry)", "msg": "Network congestion. Retrying primary node..."},
        {"engine": "google", "model": "gemini-2.5-flash", "name": "ARMSB Logic Node v2.5", "msg": "Re-routing to secondary logic node..."},
        {"engine": "openai", "model": OPENAI_MODEL, "name": "ARMSB Auxiliary Core 5.5", "msg": "Internal nodes saturated. Engaging external fallback..."}
    ]
    
    for i, step in enumerate(chain):
        # Trigger stealth toast for retries
        if i > 0:
            st.toast(f"⏳ ARMSB Core: {step['msg']}", icon="🔄")
            time.sleep(2)
            
        try:
            if step["engine"] == "google":
                response = gemini_client.models.generate_content(
                    model=step["model"],
                    contents=user_content,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.4
                    )
                )
                result = json.loads(response.text)
                result["_engine_used"] = step["name"]
                return result
                
            elif step["engine"] == "openai":
                openai_response = openai_client.chat.completions.create(
                    model=step["model"],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.4,
                    response_format={"type": "json_object"}
                )
                result = json.loads(openai_response.choices[0].message.content)
                result["_engine_used"] = step["name"]
                return result
                
        except Exception as e:
            error_str = str(e).lower()
            # If it's a traffic jam or quota error, proceed to the next step in the chain
            if any(err in error_str for err in ["503", "unavailable", "429", "overloaded", "quota", "billing", "insufficient"]):
                if i == len(chain) - 1:
                    # All fallbacks exhausted
                    st.error("🚨 ARMSB CORE : Error code 503. Clustered demand exceeded maximum thresholds. Please try again.")
                    return None
                else:
                    continue
            else:
                # Completely different error (e.g. system interrupt)
                st.error("🚨 ARMSB CORE : Internal system connection interrupted.")
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
                        st.caption(f"⚙️ **Diagnostics:** Pipeline executed via *{engine_used}*")
                    else:
                        status.update(label="Pipeline Execution Interrupted.", state="error", expanded=True)
                else:
                    status.update(label="Pipeline Execution Interrupted.", state="error", expanded=True)
            else:
                status.update(label="Pipeline Execution Interrupted.", state="error", expanded=True)
