import discord, bot_key, asyncio, sqlite3, sys, pytesseract, cv2, requests, openai, re
import numpy as np
from discord.ext import commands
from bot_key import key
from PIL import Image
from io import BytesIO


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def get_scaled_bounding_box(original_width, original_height, new_width, new_height, x, y, w, h):
    try:
        # Scale the bounding box according to the new resolution
        x_new = int((x / original_width) * new_width)
        y_new = int((y / original_height) * new_height)
        w_new = int((w / original_width) * new_width)
        h_new = int((h / original_height) * new_height)

        return x_new, y_new, w_new, h_new
    
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in get_scaled_bounding_box, {e}"
        return(error_message)

def crop_image_get_text(img, original_width_1, original_height_1, x_1, y_1, w_1, h_1):
    try:
        new_width, new_height, channels = img.shape 
        scaled_x, scaled_y, scaled_w, scaled_h = get_scaled_bounding_box(original_width_1, original_height_1, new_width, new_height, x_1, y_1, w_1, h_1)
        cropped_img = img[scaled_y:scaled_y + scaled_h, scaled_x:scaled_x + scaled_w]
        pil_image = Image.fromarray(cropped_img)
        text = pytesseract.image_to_string(pil_image) 
        return text.strip()    #FINAL TEXT GIVEN TO DATABASE 
    
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in crop_image_get_text, {e}"
        return(error_message)

def get_card_name_from_image(image_url):
    try:
        image = requests.get(image_url)
        original_width_1 = 1407 #example for scale
        original_height_1 = 1005 #example for scale
        if image.status_code == 200:
            # Convert the image into a NumPy array
            img_array = np.asarray(bytearray(image.content), dtype=np.uint8)
            # Decode the image into an OpenCV format
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            image_exists = True
        else:
            image_exists = False

        #Auto Name
        if image_exists:
            name = crop_image_get_text(img, original_width_1, original_height_1, 70, 70, 700, 70)
            
        return name

    except Exception as e:
        error_message = f"<@&1313626558304616572> error in get_card_name_from_image, {e}"
        return(error_message)