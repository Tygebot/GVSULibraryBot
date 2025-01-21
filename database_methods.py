import discord, bot_key, asyncio, sqlite3, sys, pytesseract, cv2, requests, openai, re
import numpy as np
from discord.ext import commands
from bot_key import key
from PIL import Image
from io import BytesIO
from image_reading import *

#NOTE: The edit_card function is too interactive with discord and all logic is in enforcer.py

"""
The folowing block is used to create the table, I left it here to show how I did it
"""
# # Create or connect to the SQLite database
# conn = sqlite3.connect('custom_magic_cards.db')
# cursor = conn.cursor()

# # Modify the table to include an image_url column
# cursor.execute('''
#     CREATE TABLE IF NOT EXISTS cards (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,  
#         name TEXT NOT NULL,
#         type TEXT,
#         rarity TEXT,
#         mana_cost TEXT,
#         power_and_toughness TEXT, 
#         text TEXT,
#         image_url TEXT
#     )
# ''')



# # Commit the changes and close the connection
# conn.commit()
# conn.close()

# Function to connect to the database
def get_db_connection():
    try:
        conn = sqlite3.connect('custom_magic_cards.db')
        conn.row_factory = sqlite3.Row  # To fetch rows as dictionaries
        return conn
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in get_db_connection, {e}"
        return(error_message)

def find_card(
    interaction: discord.Interaction,
    search_by: str,
    search_value: str): 
    try:
        # Allowed attributes to search by
        valid_attributes = ['name', 'type', 'rarity', 'mana_cost', 'power', 'toughness', 'text']
        
        # Check if the user input for 'search_by' is valid
        if search_by not in valid_attributes:
            return(f"Invalid search attribute. Please choose from {', '.join(valid_attributes)}.")

        # Build SQL query to search
        conn = get_db_connection()
        cursor = conn.cursor()

        # If the attribute is an integer type (power, toughness), treat search_value as an integer
        if search_by in ['power', 'toughness']:
            try:
                search_value = int(search_value)  # Convert to integer
                cursor.execute(f"SELECT * FROM cards WHERE {search_by} = ?", (search_value,))
            except ValueError:
                conn.close()
                return(f"Please provide a valid integer for {search_by}.")
        else:  # For string fields, use LIKE for partial matching
            cursor.execute(f"SELECT * FROM cards WHERE {search_by} LIKE ?", ('%' + search_value + '%',))

        cards = cursor.fetchall()
        conn.close()

        if cards:
            # Prepare a list of card names with their information
            return cards
        else:
            return None
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in find_card, {e}"
        return(error_message)
    
def add_card_logic(interaction: discord.Interaction, 
                            name: str = None,
                            card_type: str = None, 
                            rarity: str = None, 
                            mana_cost: str = None, 
                            power_and_toughness: str = None,
                            text: str = None, 
                            image_url: str = None):
    
    

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
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
        if not name and image_exists:
            name = crop_image_get_text(img, original_width_1, original_height_1, 70, 70, 700, 70)

        already_existing_card = find_card(interaction, 'name', name)
        if already_existing_card:
            print('here')
            return (f"{name} is too much like {already_existing_card[0]['name']}.  Consider changing the name of your card.")
        
        #Auto Type
        if not card_type and image_exists:
            card_type = crop_image_get_text(img, original_width_1, original_height_1, 70, 800, 790, 70)    #FINAL CARD TYPE GIVEN TO DATABASE 

        #Auto Power and Toughness
        if not power_and_toughness and image_exists:
            power_and_toughness = crop_image_get_text(img, original_width_1, original_height_1, 800, 1260, 120, 60)
            
        #Auto Text 
        if not text and image_exists:
            text = crop_image_get_text(img, original_width_1, original_height_1, 65, 870, 870, 425)    #FINAL TEXT GIVEN TO DATABASE                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          

        #Default rarity
        if not rarity:
            rarity = None

        if not mana_cost:
            mana_cost = None

        cursor.execute('''
            INSERT INTO cards (name, type, rarity, mana_cost, power_and_toughness, text, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, card_type, rarity, mana_cost, power_and_toughness, text, image_url))
        
        conn.commit()
        conn.close()
        return(name, f"Card '{name}' has been added to the database.")
    except Exception as e:
        return(f"<@&1313626558304616572> error in add_card_logic, {e}")

def remove_card_logic(interaction:discord.Interaction, card_name:str=None, card_id:int=None):
    try:
        # Validate inputs
        if not card_name and not card_id:
            return ("You must provide either a card ID or card name.")


        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            if card_id:
                cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
                card = cursor.fetchone()

                if card:
                    # Delete the card with the matching id
                    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
                    conn.commit()
                    return (f"Card with id '{card_id}' has been removed.")
                else:
                    return (f"No cards found with id '{card_id}'.")

            # If card_name is provided, delete by name (or partial match)
            elif card_name:
                cursor.execute("SELECT * FROM cards WHERE name LIKE ?", ('%' + card_name + '%',))
                cards = cursor.fetchall()
                if cards:
                    if len(cards) == 1:
                        # Delete all cards with a matching name (partial matches)
                        cursor.executemany("DELETE FROM cards WHERE id = ?", [(card['id'],) for card in cards])
                        conn.commit()
                        return (f"{len(cards)} card(s) with name '{card_name}' have been removed.")
                    elif len(cards) > 1:
                        card_list = ""
                        for card in cards:
                            card_list += f"**{card['name']}** - {card['type']} - {card['rarity']}\n"
                            card_list += f"Mana Cost: {card['mana_cost']} | Power and Toughness: {card['power_and_toughness'] if card['power_and_toughness'] else 'N/A'}\n"
                            card_list += f"Text: {card['text'] or 'No text available'}\n\n"
                        return (f"Multple cards found, could you be more specific? \n\n {card_list}")

                else:
                    return (f"No cards found with name '{card_name}'.")
        except Exception as e:
            return(f"An error occurred: {str(e)}")

        finally:
            conn.close()
    except Exception as e:
        return(f"<@&1313626558304616572> error in count_vote, {e}")


def search_card_logic(
    search_value: str,
    search_by: str ='name'):
    try:

        # Allowed attributes to search by
        valid_attributes = ['name', 'type', 'rarity', 'mana_cost', 'power', 'toughness', 'text']
        
        # Check if the user input for 'search_by' is valid
        if search_by not in valid_attributes:
            return(f"Invalid search attribute. Please choose from {', '.join(valid_attributes)}."), False

        # Build SQL query to search
        conn = get_db_connection()
        cursor = conn.cursor()

        # If the attribute is an integer type (power, toughness), treat search_value as an integer
        if search_by in ['power', 'toughness']:
            try:
                cursor.execute(f"SELECT * FROM cards WHERE {search_by} = ?", (search_value,))
            except ValueError:        
                conn.close()
                return (f"Please provide a valid integer for {search_by}."), False
        else:  # For string fields, use LIKE for partial matching
            cursor.execute(f"SELECT * FROM cards WHERE {search_by} LIKE ?", ('%' + search_value + '%',))

        cards = cursor.fetchall()
        conn.close()

        if cards:
            # Prepare a list of card names with their information
            card_list = ""
            if len(cards) == 1:
                found_card = cards[0]
                # If the card exists, create and send the embed
                if found_card:
                    embed = discord.Embed(
                        title=found_card['name'],
                        description=f"**Type**: {found_card['type']}\n"
                                    f"**Rarity**: {found_card['rarity']}\n"
                                    f"**Mana Cost**: {found_card['mana_cost']}\n"
                                    f"**Power/Toughness**: {found_card['power_and_toughness'] if found_card['power_and_toughness'] else 'N/A'}\n"
                                    f"**Text**:\n {found_card['text'] or 'No text available'}",
                        color=discord.Color.blue()
                    )
                    
                    # If there is an image URL, add it to the embed
                    if found_card['image_url']:
                        embed.set_image(url=found_card['image_url'])  # Set the image for the card
                        #print(chat_with_image('Describe this card', found_card['image_url'])) #TODO, remove when done
                    else:
                        embed.set_footer(text="No image available.")

                    return False, embed, found_card
            
            else:
                for card in cards:
                    card_list += f"**{card['name']}** - {card['type']} - {card['rarity']}\n"
                    card_list += f"Mana Cost: {card['mana_cost']} | Power/Toughness: {card['power_and_toughness'] if card['power_and_toughness'] else 'N/A'}\n"
                    card_list += f"Text:\n {card['text'] or 'No text available'}\n\n"

                return (f"Found {len(cards)} cards:\n{card_list}"), False
        else:
            return(f"No cards found with {search_by} matching '{search_value}'."), False
    
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in vote, {e}"
        return(error_message)