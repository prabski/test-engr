import random
import time
import json
import streamlit as st
import sys
import tempfile
import argparse
import base64
import io
import os
from pathlib import Path
  

# quiz_app.py
# Prevent argparse in __main__ from failing when Streamlit injects extra args
if 'streamlit' in sys.modules:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    tmp.write(b'[]')
    tmp.flush()
    tmp.close()
    sys.argv = [sys.argv[0], '--questionFile', tmp.name]

st.set_page_config(page_title="Show Concepts")
st.title("Concepts App")

# Allow user to select image directory
st.subheader("Select Image Directory")
available_dirs = []
assets_path = Path("assets/images/concepts")

# Get all images from assets/images/concepts directory
def get_images_from_directory(imgdir):
    print(f"Looking for images in directory: {img_dir}")
    supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp')
    images = [str(f) for f in img_dir.iterdir() if f.suffix.lower() in supported_formats]
    return sorted(images)

if assets_path.exists():
    # Get all subdirectories under assets/images
    available_dirs = [str(d.relative_to(assets_path)) for d in assets_path.iterdir() if d.is_dir()]
    available_dirs.insert(0, ".")  # Add root directory as option

if available_dirs:
    selected_dir = st.selectbox(
        "Choose image folder:",
        options=available_dirs,
        format_func=lambda x: "Root (assets/images)" if x == "." else x
    )
    
    if selected_dir == ".":
        img_dir = assets_path
    else:
        img_dir = assets_path / selected_dir
        print(f" 1 Selected image directory: {img_dir} {selected_dir}")
    st.session_state.image_list = get_images_from_directory(img_dir)




# Initialize session state for image gallery
if "current_image_idx" not in st.session_state:
    st.session_state.current_image_idx = 0


# Display image gallery
if st.session_state.image_list:
    st.session_state.current_image_idx = st.session_state.get("current_image_idx", 0)
    st.subheader("Image Gallery")
    current_img = st.session_state.image_list[st.session_state.current_image_idx]
    
    st.image(current_img, caption=f"Image {st.session_state.current_image_idx + 1} of {len(st.session_state.image_list)}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Previous") and st.session_state.current_image_idx > 0:
            st.session_state.current_image_idx -= 1
            st.rerun()
    
    with col2:
        if st.button("➡️ Next") and st.session_state.current_image_idx < len(st.session_state.image_list) - 1:
            st.session_state.current_image_idx += 1
            st.rerun()
else:
    st.warning("No images found in assets/images directory")

st.divider()
