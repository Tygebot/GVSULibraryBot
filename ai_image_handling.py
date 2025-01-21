import openai
import requests
import numpy as np
import cv2
import io
from database_methods import *
from bot_key import trust

openai.api_key = trust

def get_chatgpt_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or the model of your choice
            messages=[
                {"role": "system", "content": "You are a living library from the world of Magic the Gathering.  You are wise and understanding. When given a Magic the Gathering card text, compare it to other cards in MTG history and make suggestions for edits. Say the names of cards that are similer and cite the specific text. Make your response short."},
                {"role": "user", "content": prompt},
            ]
        )
        
        return response.choices[0].message['content'].strip()
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in get_ai_response, {e}"
        return(error_message)


def advice_logic(card_name: str):
    try:
        arg, arg, card = search_card_logic(card_name)
        text = card['text']
        response = get_chatgpt_response(text)
        return response
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in get_ai_response, {e}"
        return(error_message)


def fetch_and_process_image(image_url):
    """
    Fetches and processes an image from a URL for use with a chat model.

    Args:
        image_url (str): URL of the image to fetch.

    Returns:
        BytesIO: Processed image as a byte stream.
    """
    try:
        # Fetch the image from the URL with redirection handling
        response = requests.get("https://cdn.discordapp.com/attachments/1281363070165319825/1313630132673712239/Link_Hero_of_Hyrule_3.jpg?ex=678cd125&is=678b7fa5&hm=e4c4316ab4009797e5197b8080c0e29f3701e8a9e4b2aa1e05a110c8ef4021c6&", allow_redirects=True)

        if response.status_code == 200:
            # Check content type to ensure it's an image
            content_type = response.headers.get('Content-Type')
            if not content_type or "image" not in content_type:
                raise ValueError(f"URL does not point to an image. Content-Type: {content_type}")

            # Convert response content into a NumPy array
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)

            # Decode the image into OpenCV format
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is not None:
                # Convert the OpenCV image to a byte stream in PNG format
                img_byte_array = io.BytesIO()
                _, buffer = cv2.imencode('.png', img)
                img_byte_array.write(buffer)
                img_byte_array.seek(0)
                return img_byte_array
            else:
                raise ValueError("Image could not be decoded.")
        else:
            raise ValueError(f"Failed to fetch image. Status code: {response.status_code}")

    except Exception as e:
        error_message = f"<@&1313626558304616572> error in fetch_and_process_image, {e}"
        return(error_message)


def chat_with_image(prompt, image_url):
    """
    Sends a text prompt and an image to the chat model.

    Args:
        prompt (str): Text prompt for the model.
        image_url (str): URL of the image to include in the chat.

    Returns:
        str: Model's response.
    """
    try:
        # Set your OpenAI API key
        openai.api_key = "your-api-key"

        # Fetch and process the image
        image_stream = fetch_and_process_image(image_url)

        # Call the chat model
        response = openai.ChatCompletion.create(
            model="gpt-4-vision",  # Use a model that supports multimodal input
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a living library from the world of Magic: The Gathering. "
                        "You analyze both text and images of cards and provide insights "
                        "based on card history and mechanics."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            files={
                "image": image_stream,  # Attach the image
            }
        )

        # Extract and return the model's reply
        return response['choices'][0]['message']['content']

    except Exception as e:
        error_message = f"<@&1313626558304616572> error in chat_with_image, {e}"
        return(error_message)

