import base64
import os
import zipfile
import requests
import streamlit as st
from PIL import Image
from io import BytesIO

#set favicon to logos/favicon_atelierbox.png
st.set_page_config(page_title="Image Processing and Resizing", layout="centered", page_icon="logos/favicon_atelierbox.png")

# Constants for API
API_URL = "https://image-api.photoroom.com/v2/edit"
API_KEY = st.secrets["api_key"] 
HEADERS = {
    "Accept": "image/png, application/json",
    "x-api-key": API_KEY,
}


# Path to your logo file
logo_path = "logos/logo_atelierbox.avif"  # Make sure this path is correct

# Function to encode image in base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Get base64 string of the logo
logo_base64 = get_base64_image(logo_path)

# Custom CSS 
st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: #fbf7f1;
    }}
    [data-testid="stForm"] {{
        background: #f0e0c9;
    }}
    .top-left-logo {{
        position: absolute;
        top: 10px;
        left: 10px;
        width: 300px;
    }}
    </style>
    <img src="data:image/png;base64,{logo_base64}" class="top-left-logo">
    """,
    unsafe_allow_html=True,
)



# Function to process images with PhotoRoom API
def process_image_with_photoroom(uploaded_file, api_params, output_format="jpeg"):
    # Ensure output format for the API request is one of the supported formats
    api_output_format = output_format if output_format in ["jpeg", "jpg", "png"] else "jpeg"
    api_params["export.format"] = api_output_format  # Set API format parameter

    # Send the request to the PhotoRoom API
    files = {
        "imageFile": uploaded_file.getvalue(),
    }
    response = requests.post(API_URL, headers=HEADERS, files=files, data=api_params)
    
    if response.status_code == 200:
        # Load the image from the response
        img = Image.open(BytesIO(response.content))

        # Convert the image to RGB if it's JPEG or JPG and has an alpha channel
        if img.mode == "RGBA" and api_output_format in ["jpeg", "jpg"]:
            img = img.convert("RGB")

        # Prepare output in the requested format (convert to webp if needed)
        img_byte_arr = BytesIO()
        quality = 85  # Start with a high quality for file size adjustments
        step = -5  # Decrease in quality steps
        while True:
            img_byte_arr.seek(0)

            # Save in the specified format with quality adjustments
            if output_format == "webp":
                img.save(img_byte_arr, format="WEBP", quality=quality)
            elif output_format in ["jpeg", "jpg"]:
                img.save(img_byte_arr, format="JPEG", quality=quality, optimize=True)
            else:
                img.save(img_byte_arr, format="PNG", optimize=True)

            file_size = img_byte_arr.tell() / 1024  # Size in KB
            if file_size <= 200 or quality <= 5:
                break
            quality += step
        
        return img_byte_arr.getvalue()
    else:
        st.error(f"Echec de traitement de {uploaded_file.name}: {response.status_code} - {response.text}")
        return None

# Function to resize images and adjust file size
from PIL import Image
from io import BytesIO

def resize_image(uploaded_file, target_width, target_height, output_format, padding_color=(255, 255, 255)):
    with Image.open(uploaded_file) as img:
        original_width, original_height = img.size
        ratio = min(target_width / original_width, target_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

        # Resize the image while preserving aspect ratio
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        # Always create an RGBA image with the desired background color and target dimensions
        final_img = Image.new("RGBA", (target_width, target_height), (*padding_color, 255))
        
        # Paste the resized image onto the new background with alpha mask (if any)
        final_img.paste(resized_img, ((target_width - new_width) // 2, (target_height - new_height) // 2), mask=resized_img if resized_img.mode == "RGBA" else None)

        # Convert to RGB if output is JPEG or any format that does not support alpha
        if output_format.lower() in ["jpeg", "jpg"]:
            final_img = final_img.convert("RGB")

        # Save with quality adjustments to fit within 70KB to 200KB range
        img_byte_arr = BytesIO()
        quality = 85  # Start with high quality
        step = -5  # Step to decrease quality if file size is too large
        while True:
            img_byte_arr = BytesIO()
            # Save the image with the current quality level
            if output_format.lower() == "webp":
                final_img.save(img_byte_arr, format="WEBP", quality=quality)
            elif output_format.lower() in ["jpeg", "jpg"]:
                final_img.save(img_byte_arr, format="JPEG", quality=quality, optimize=True)
            else:
                # For PNG, try reducing to 256 colors (PNG8)
                temp_img = final_img.convert("P", palette=Image.ADAPTIVE, colors=256)
                temp_img.save(img_byte_arr, format="PNG", optimize=True)

            # Use len() to get the actual file size with metadata
            file_size = len(img_byte_arr.getvalue()) / 1024  # Size in KB, including metadata
            print(f"File size with metadata: {file_size} KB at quality {quality}")


            if file_size <= 200 or quality <= 5:
                break
            quality += step
            
        return img_byte_arr.getvalue()




###### Streamlit Interface ######
st.markdown(" ")
st.markdown(" ")
st.markdown(" ")
st.markdown(" ")
st.markdown(" ")
st.title("Interface de transformation automatique d'images")

# Section 1: Image Processing with PhotoRoom API
st.header("• Traitement d'images")
st.markdown("Remplissez le formulaire pour traiter automatiquement les images téléversées. Vous pouvez spécifier la couleur de fond, le format de sortie et la taille de l'image. Une ombre douce sera automatiquement appliquée.")
uploaded_files = st.file_uploader("Glissez-déposez des images pour les traiter", accept_multiple_files=True, type=["png", "jpg", "jpeg", "webp"], key="process")

# API Parameters Form
with st.form(key="process_form"):
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    output_size = st.text_input("Taille de sortie (e.g., 1200x1500)", value="1200x1500")
    export_format = st.selectbox("Format de sortie", options=["jpeg", "png", "jpg", "webp"], index=0)
    background_color = st.color_picker("Couleur de fond (par défaut gris #efefef)", value="#EFEFEF")
    process_button = st.form_submit_button("Traiter les images")
    st.markdown('</div>', unsafe_allow_html=True)

if process_button:
    if uploaded_files:
        with st.spinner("Traitement des images..."):
            progress_bar = st.progress(0)
            output_zip = BytesIO()
            with zipfile.ZipFile(output_zip, "w") as zipf:
                for idx, uploaded_file in enumerate(uploaded_files):
                    api_params = {
                        "background.color": background_color.lstrip("#"),
                        "export.format": export_format,
                        "outputSize": output_size,
                        "padding": 0.1,
                        "shadow.mode": "ai.soft",
                    }
                    success = False
                    processed_image = process_image_with_photoroom(uploaded_file, api_params)
                    if processed_image:
                        success = True
                        filename_without_ext, _ = os.path.splitext(uploaded_file.name)
                        output_name = f"{filename_without_ext}_processed.{export_format}"
                        zipf.writestr(output_name, processed_image)
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
            
            output_zip.seek(0)
            if success:
                st.download_button("Télécharger les images traitées", output_zip, "processed_images.zip", "application/zip")
    else:
        st.warning("Veuillez téléverser des images à traiter.")

# Section 2: Image Resizing
st.header("• Redimensionnement d'images")
uploaded_resize_files = st.file_uploader("Glissez-déposez des images pour les redimensionner", accept_multiple_files=True, type=["png", "jpg", "jpeg", "webp"], key="resize")

# Resizing Parameters Form
with st.form(key="resize_form"):
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    resize_width = st.number_input("Largeur visée (optionnel)", min_value=1, step=1, value=1200)
    resize_height = st.number_input("Hauteur visée (optionnel)", min_value=1, step=1, value=1500)
    resize_format = st.selectbox("Format de sortie", options=["JPEG", "PNG", "WEBP"], index=0, key="resize_format")
    padding_color = st.color_picker("Couleur de remplissage des bords (par défaut gris #efefef)", value="#EFEFEF")
    resize_button = st.form_submit_button("Redimensionner les images")
    st.markdown('</div>', unsafe_allow_html=True)

if resize_button:
    if uploaded_resize_files:
        with st.spinner("Redimensionnement des images..."):
            progress_bar = st.progress(0)
            padding_color = tuple(int(padding_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
            output_zip = BytesIO()
            with zipfile.ZipFile(output_zip, "w") as zipf:
                for idx, uploaded_file in enumerate(uploaded_resize_files):
                    resized_image = resize_image(uploaded_file, resize_width, resize_height, resize_format, padding_color)
                    if resized_image:
                        filename_without_ext, _ = os.path.splitext(uploaded_file.name)
                        output_name = f"resized_{filename_without_ext}.{resize_format.lower()}"
                        zipf.writestr(output_name, resized_image)
                    
                    progress_bar.progress((idx + 1) / len(uploaded_resize_files))
            
            output_zip.seek(0)
            st.download_button("Télécharger les images redimensionnées", output_zip, "resized_images.zip", "application/zip")
    else:
        st.warning("Veuillez téléverser des images à redimensionner.")
