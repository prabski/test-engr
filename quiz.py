import random
import time
import json
import streamlit as st
import sys
import tempfile
import argparse
import base64
import io
  

# quiz_app.py
# Prevent argparse in __main__ from failing when Streamlit injects extra args
if 'streamlit' in sys.modules:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    tmp.write(b'[]')
    tmp.flush()
    tmp.close()
    sys.argv = [sys.argv[0], '--questionFile', tmp.name]

st.set_page_config(page_title="Quiz App")
st.title("Quiz App")

uploaded_file = st.file_uploader("Upload questions JSON", type="json")
ask_count = st.sidebar.slider("Number of questions (0 = all)", 0, 10, 0)

# session state initialization
if 'questions' not in st.session_state:
    st.session_state.questions = None
    st.session_state.order = []
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.answered = False

# load uploaded file into session state
if uploaded_file is not None:
    if st.session_state.questions is None:
        data = json.load(uploaded_file)
        if not isinstance(data, list):
            st.error("JSON must be a list of question objects (each with 'question', 'options', 'answer').")
        else:
            st.session_state.questions = data
            total = len(data)
            n = total if ask_count == 0 else min(ask_count, total)
            # create a shuffled order only once per upload
            st.session_state.order = list(range(n))
            if not st.session_state.order or len(st.session_state.order) != n:
                st.session_state.order = random.sample(range(total), n)
                st.session_state.index = 0
                st.session_state.score = 0
                st.session_state.answered = False
# quiz UI

if st.session_state.questions:
    if st.session_state.index >= len(st.session_state.order):
        st.session_state.index = 0
    q_idx = st.session_state.order[st.session_state.index]
    q = st.session_state.questions[q_idx]
    st.markdown(f"### Question {st.session_state.index + 1} / {len(st.session_state.order)}")
    st.write(q.get("question", ""))
    options = q.get("options", [])
    selected = st.radio("Choose an option:", options, key=f"choice_{st.session_state.index}")
    
    print(f"Question data: {q}")
    # show image if present (supports several JSON key names and formats)
    caption = None
    img_field = None
    for k in ('image', 'image_url', 'img', 'image_data', 'image_base64', 'image_b64'):
        if k in q:
            img_field = q[k]
            break

    # handle dict-style image field like {"url": "...", "caption": "..."}
    if isinstance(img_field, dict):
        caption = img_field.get('caption')
        img_field = img_field.get('url') or img_field.get('data') or img_field.get('base64')

    if isinstance(img_field, str):
        if img_field.startswith('data:'):
            # data URL (data:image/png;base64,...)
            try:
                _, b64 = img_field.split(',', 1)
                img_bytes = base64.b64decode(b64)
                st.image(io.BytesIO(img_bytes), caption=caption, width=800, height=600)
            except Exception:
                st.warning("Unable to decode image data URL.")
        else:
            # URL or local path
            st.image(img_field, caption=caption)
    elif img_field is not None:
        # bytes or file-like object
        try:
            st.image(img_field, caption=caption)
        except Exception:
            st.warning("Unable to display image for this question.")

            # play sound/video if question has playsound field
    play = q.get("playsound") or q.get("play_sound")
    print(f"Playsound content: {play}")
    
    show_play_button = st.button("▶️ Play", key=f"play_{st.session_state.index}")
    if show_play_button and play:
        try:
            if isinstance(play, str):
                # data URL (base64) for audio
                if play.startswith("data:audio"):
                        _, b64 = play.split(",", 1)
                        audio_bytes = base64.b64decode(b64)
                        st.audio(io.BytesIO(audio_bytes))
                        # HTTP URL: prefer embedding YouTube via st.video, direct audio via st.audio
                elif play.startswith("http"):
                    if "youtube.com" in play or "youtu.be" in play:
                        st.video(play, start_time=0)
                        st.markdown('''
                        <script>
                        setTimeout(function() {
                            const video = document.querySelector('video');
                            if (video) {
                                video.volume = 0.2;
                            }
                        }, 1000);
                        </script>
                        ''', unsafe_allow_html=True)
                    elif any(play.lower().endswith(ext) for ext in (".mp3", ".wav", ".ogg", ".m4a")):
                        # Create HTML audio player with volume control
                        st.markdown(f'''
                        <audio controls>
                            <source src="{play}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                        <script>
                            document.querySelector('audio').volume = 0.2;
                        </script>
                        ''', unsafe_allow_html=True)
                    else:
                        st.video(play)
                else:
                    st.warning("Unsupported playsound string format.")
            elif isinstance(play, (bytes, bytearray)):
                # For bytes data, we need to create a data URL and use HTML audio
                b64_data = base64.b64encode(play).decode()
                st.markdown(f'''
                <audio controls>
                    <source src="data:audio/mpeg;base64,{b64_data}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <script>
                    document.querySelector('audio').volume = 0.2;
                </script>
                ''', unsafe_allow_html=True)
            else:
                st.warning("Unable to play provided playsound content.")
        except Exception as e:
            st.warning(f"Could not play sound/video: {e}")

    # Submit shown before answering; Next/Finish shown after answering
    if not st.session_state.answered:
        if st.button("Submit"):
            st.session_state.answered = True
            correct_idx = int(q.get("answer", 1)) - 1
            is_correct = (0 <= correct_idx < len(options) and options[correct_idx] == selected)
            if is_correct:
                st.success("Correct!")
                st.session_state.score += 1
            else:
                correct_text = options[correct_idx] if 0 <= correct_idx < len(options) else "N/A"
                st.error(f"Wrong. Correct answer: {correct_text}")
            print(f"User selected: {selected}, Correct answer: {correct_text if not is_correct else selected}")
            if st.session_state.index >= len(st.session_state.order) - 1:
                   # last question: show final score and restart option
                st.info(f"Quiz completed! Score: {st.session_state.score} / {len(st.session_state.order)}")
                st.balloons()
                if st.button("Restart"):
                    st.session_state.order = []
                    st.session_state.index = 0
                    st.session_state.score = 0
                    st.session_state.answered = False
            else:
                st.session_state.answered = False
                st.session_state.index += 1
                if st.button("Next"):
                    pass
                    
        
    
else:
    st.info("Upload a questions JSON to start the quiz.")
    st.session_state.answered = False

