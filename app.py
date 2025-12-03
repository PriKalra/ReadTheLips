import streamlit as st
import os
import math
import tempfile
from openai import OpenAI
from moviepy.editor import VideoFileClip, AudioFileClip
import time

# --- Page Config & Styling ---
st.set_page_config(
    page_title="ReadTheLips AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Whisprflow-like aesthetics
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff3333;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.3);
    }
    .transcript-box {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 20px;
        font-family: 'Source Sans Pro', sans-serif;
    }
    .speaker-label {
        font-weight: bold;
        color: #ff4b4b;
        margin-bottom: 5px;
        display: block;
    }
    .timestamp {
        color: #808495;
        font-size: 0.8em;
        margin-left: 10px;
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    api_key_input = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API Key here.")
    
    # Try to get from environment if not input
    if not api_key_input:
        api_key_input = os.getenv("OPENAI_API_KEY")
        if api_key_input:
            st.success("✅ API Key loaded from environment")
        else:
            st.warning("⚠️ Please enter your API Key")
            
    st.markdown("---")
    st.subheader("Options")
    enable_diarization = st.checkbox("Identify Speakers (AI)", value=False, help="Uses GPT-4o to infer speaker labels. Slower but better formatted.")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Inspired by **Whisprflow**.\nBuilt with OpenAI Whisper & GPT-4o.")

# --- Helper Functions ---

def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def transcribe_chunk(client, file_path):
    """Transcribes a single audio file chunk."""
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="text"
        )
    return transcription

def diarize_with_gpt4(client, transcript_text):
    """Uses GPT-4o to format the transcript with speaker labels."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional transcriber. Your task is to format the following raw transcript into a readable script. \n1. Identify different speakers (Speaker 1, Speaker 2, etc.) based on context, tone changes, and flow. \n2. Add paragraph breaks and the speaker stamps for readability. \n3. Do not summarize; keep the full content. \n4. If it's a monologue, label it as 'Speaker 1' and format it nicely."},
                {"role": "user", "content": transcript_text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Diarization error: {e}")
        return transcript_text

def process_and_transcribe(client, input_path, status_container):
    """
    Handles the logic of checking file size, extracting audio (if video),
    splitting into chunks (if needed), and transcribing.
    """
    temp_files_to_cleanup = []
    full_transcript = ""
    
    try:
        # 1. Identify if it's video or audio
        file_ext = os.path.splitext(input_path)[1].lower()
        audio_path = input_path

        # If video, extract audio first
        if file_ext in ['.mp4', '.mov', '.avi', '.mkv']:
            status_container.info("🎬 Extracting audio from video...")
            audio_path = input_path + ".mp3"
            
            # Use a custom logger or None to avoid the stdout error
            # We wrap in try/except to handle the specific moviepy error if it occurs
            try:
                video = VideoFileClip(input_path)
                video.audio.write_audiofile(audio_path, verbose=False, logger=None)
                video.close()
            except AttributeError:
                # Fallback for the 'NoneType' stdout error - sometimes logger=None causes it in certain envs
                # We try again with default logger but suppress output via other means if possible
                # Or just ignore if the file was actually created
                if not os.path.exists(audio_path):
                     # Try one more time with a simple print logger
                     video = VideoFileClip(input_path)
                     video.audio.write_audiofile(audio_path, verbose=False)
                     video.close()

            temp_files_to_cleanup.append(audio_path)

        # 2. Check file size and determine chunking strategy
        file_size_mb = get_file_size_mb(audio_path)
        OPENAI_LIMIT_MB = 25
        SAFETY_BUFFER_MB = 20

        if file_size_mb <= OPENAI_LIMIT_MB:
            status_container.info(f"⚡ File is small ({file_size_mb:.2f} MB). Transcribing directly...")
            full_transcript = transcribe_chunk(client, audio_path)
        else:
            status_container.info(f"📦 File is large ({file_size_mb:.2f} MB). Splitting into optimized chunks...")
            
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            
            chunk_duration = (SAFETY_BUFFER_MB / file_size_mb) * duration
            chunk_duration = max(10, math.floor(chunk_duration))
            
            num_chunks = math.ceil(duration / chunk_duration)
            
            progress_bar = status_container.progress(0)

            for i in range(num_chunks):
                start_time = i * chunk_duration
                end_time = min((i + 1) * chunk_duration, duration)
                
                chunk_filename = f"{audio_path}_part_{i}.mp3"
                temp_files_to_cleanup.append(chunk_filename)
                
                # Create chunk
                sub_clip = audio.subclip(start_time, end_time)
                sub_clip.write_audiofile(chunk_filename, verbose=False, logger=None)
                sub_clip.close()
                
                # Transcribe chunk
                # status_container.text(f"Transcribing chunk {i+1}/{num_chunks}...")
                chunk_text = transcribe_chunk(client, chunk_filename)
                full_transcript += chunk_text + " "
                
                # Update progress
                progress_bar.progress((i + 1) / num_chunks)
            
            audio.close()
            progress_bar.empty()

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None
    finally:
        # Cleanup temp files
        for f in temp_files_to_cleanup:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

    return full_transcript

# --- Main UI Logic ---

st.title("🎙️ ReadTheLips AI")
st.markdown("### Transform your audio & video into structured text.")

# Tabs for Upload vs Dictate
tab1, tab2 = st.tabs(["📁 Upload File", "🎤 Dictate"])

transcript_result = None

with tab1:
    uploaded_file = st.file_uploader("Drop your MP4, MP3, WAV file here", type=['mp3', 'mp4', 'wav', 'm4a', 'mov'])
    
    if uploaded_file and st.button("Transcribe File", key="btn_upload"):
        if not api_key_input:
            st.error("Please provide an API Key in the sidebar.")
        else:
            client = OpenAI(api_key=api_key_input)
            status_box = st.empty()
            
            with st.spinner("Processing your file..."):
                # Save to temp
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                raw_transcript = process_and_transcribe(client, tmp_file_path, status_box)
                
                # Ensure we close any potential file handles
                if 'video' in locals():
                    try:
                        video.close()
                    except:
                        pass
                
                # Robust file deletion
                if os.path.exists(tmp_file_path):
                    max_retries = 3
                    for i in range(max_retries):
                        try:
                            os.remove(tmp_file_path)
                            break
                        except PermissionError:
                            time.sleep(1.0)
                        except Exception as e:
                            print(f"Error deleting temp file: {e}")
                            break
                
                if raw_transcript:
                    if enable_diarization:
                        status_box.info("🤖 AI is identifying speakers and formatting...")
                        transcript_result = diarize_with_gpt4(client, raw_transcript)
                    else:
                        transcript_result = raw_transcript
                    
                    status_box.success("Done!")

with tab2:
    st.markdown("Record your voice directly.")
    audio_value = st.audio_input("Click to record")
    
    if audio_value and st.button("Transcribe Recording", key="btn_record"):
        if not api_key_input:
            st.error("Please provide an API Key in the sidebar.")
        else:
            client = OpenAI(api_key=api_key_input)
            status_box = st.empty()
            
            with st.spinner("Transcribing recording..."):
                # Save audio_value (BytesIO) to a temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_value.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Transcribe directly (recordings are usually small enough, but we use the safe function anyway)
                raw_transcript = process_and_transcribe(client, tmp_file_path, status_box)
                
                # Robust file deletion for dictation
                if os.path.exists(tmp_file_path):
                    max_retries = 3
                    for i in range(max_retries):
                        try:
                            os.remove(tmp_file_path)
                            break
                        except PermissionError:
                            time.sleep(1.0)
                        except Exception as e:
                            print(f"Error deleting temp file: {e}")
                            break
                    
                if raw_transcript:
                    if enable_diarization:
                        status_box.info("🤖 AI is identifying speakers and formatting...")
                        transcript_result = diarize_with_gpt4(client, raw_transcript)
                    else:
                        transcript_result = raw_transcript
                    status_box.success("Done!")

# --- Display Results ---
if transcript_result:
    st.markdown("---")
    st.subheader("📝 Transcript")
    
    # Display in a styled box
    st.markdown(f'<div class="transcript-box">{transcript_result.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    
    # Download options
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download as Text",
            data=transcript_result,
            file_name="transcript.txt",
            mime="text/plain"
        )
