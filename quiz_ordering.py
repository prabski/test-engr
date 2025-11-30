import random
import time
import json
import streamlit as st
import sys
import tempfile
import argparse
import base64
import io
from streamlit_sortables import sort_items
  

# quiz_app.py
# Prevent argparse in __main__ from failing when Streamlit injects extra args
if 'streamlit' in sys.modules:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    tmp.write(b'[]')
    tmp.flush()
    tmp.close()
    sys.argv = [sys.argv[0], '--questionFile', tmp.name]

st.set_page_config(page_title="Quiz Ordering App")
st.title("Quiz App")
st.markdown("<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload JSON", type="json")
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
    st.markdown(f"<h4>Question {st.session_state.index + 1} / {len(st.session_state.order)}</h4>", unsafe_allow_html=True)
    print(f"Question data: {q}")
    st.write(q.get("question", ""))
    correct_order = [str(i) for i in q.get("correct_order", [])]
    images = {str(i+1): item["image"] for i, item in enumerate(q.get("items", []))}

    ordered_keys = sort_items(list(images.keys()), direction="horizontal")
    print("ordered keys:", ordered_keys)
    # Show reordered images
    for key in ordered_keys:
        st.image(images[key], caption=key, width=250)

    # Submit shown before answering; Next/Finish shown after answering
    if not st.session_state.answered:
        if st.button("Submit"):
            if ordered_keys == correct_order:
                st.success("✅ Correct! Well done.")
                st.session_state.score += 1
            else:
                st.error("❌ Incorrect. Try again!")
            st.session_state.answered = True
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

