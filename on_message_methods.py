import discord, bot_key, asyncio, sqlite3, sys, pytesseract, cv2, requests, openai, re, traceback
import numpy as np
from discord.ext import commands
from bot_key import key
from PIL import Image
from io import BytesIO
from database_methods import *

def vote(message: discord.Message):
    try:
    #VOTING LOGIC       
        if message.channel.name in ['bot-test', 'custom-commander-submissions']:   
            # Check if the message contains an HTTPS link
               # Check if the message contains an HTTPS link or an image attachment
            has_link = re.search(r'https?://[^\s]+', message.content) is not None
            has_image = any(
                attachment.content_type and attachment.content_type.startswith("image/")
                for attachment in message.attachments
                )
            if has_image or has_link:    
                name = get_card_name_from_image(message.content)
                already_existing_card = find_card('arg', 'name', name)
                if already_existing_card:
                    return (f"{name} is too much like {already_existing_card[0]['name']}.  Consider changing the name of your card.")
                return (f"Start")
            else:
                return None
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in vote, {e}"
        return(error_message)

def count_vote(message: discord.Message):
    try:
        # Count green and red squares
        green_square_count = 0
        red_square_count = 0
        success = False
        for reaction in message.reactions:
            if reaction.emoji == "🟩":  # Green square emoji
                green_square_count = reaction.count - 1  # Subtract 1 for the bot's own reaction, if any
            elif reaction.emoji == "🟥":  # Red square emoji
                red_square_count = reaction.count - 1
        
        reaction_summary = (f"🟩 Green squares: {green_square_count}. \n🟥 Red sqaures: {red_square_count}.\n")
        
        total_votes = green_square_count + red_square_count
        if total_votes < 5: #TODO change values to desired
            reaction_summary += "Card must have at least 5 votes, please try again.\n"
        elif total_votes > 0 and (green_square_count / total_votes) < .60:
            reaction_summary += "Greens must make up 60% of the vote. Vote Failed. \n"
        else:
            reaction_summary += "Success!!! Card will be added to the database."
            success = True
        # Notify the reactions
        if reaction_summary:
            if success == True:
                success = False 
                #THIS ADDS CARD TO DATABASE
                #try:
                name_of_card, arg = add_card_logic('arg', image_url=message.content)
                #except Exception as e:
                #    await message.channel.send(e)
                return name_of_card, True, reaction_summary
            return arg, False, reaction_summary

        else:
            return None
    
    except Exception as e:
        return(f"<@&1313626558304616572> error in count_vote, {e}")

    
def scryfall_search(message: str):
    try:
        # Regex pattern to find content inside ["..."], but not inside double brackets [["..."]], and excluding quotes
        pattern = r'(?<!\[)\[([^\[\]]+)\](?!\])'
        matches = re.findall(pattern, message)
        return matches
    except Exception as e:
        return(f"<@&1313626558304616572> error in scryfall_search, {e}")