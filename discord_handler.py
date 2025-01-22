import discord, bot_key, asyncio, sqlite3, sys, pytesseract, cv2, requests, openai, re, math
import numpy as np
from discord.ext import commands
from bot_key import key
from PIL import Image
from io import BytesIO
from ai_image_handling import *
from on_message_methods import *
from database_methods import *



# Create bot instance with a command prefix
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

global guild
global clean_channel


@bot.tree.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

# Event that runs when the bot is ready
@bot.event
async def on_ready():
    global guild, clean_channel
    # Sync commands with Discord API (needed for slash commands to work)
    await bot.tree.sync(guild=None)
    print(f'Logged in as {bot.user}')
    # Replace GUILD_NAME and CHANNEL_NAME with the actual names
    guild = discord.utils.get(bot.guilds, name="Lightner Gaming")  # Get the guild (server)
    if guild:
        channel = discord.utils.get(guild.text_channels, name="bot_send")  # Get the channel
        clean_channel = discord.utils.get(guild.text_channels, name="bot-test")
        if channel:
            return
        else:
            print("Channel not found!")
    else:
        print("Guild not found!")



# Slash command to add a card to the database
@bot.tree.command(name="manually_add_card", description="Manually add a card")
async def manually_add_card(interaction: discord.Interaction, 
                            name: str, 
                            card_type: str = None, 
                            rarity: str = None, 
                            mana_cost: str = None, 
                            power_and_toughness: str = None,
                            text: str = None, 
                            image_url: str = None):
    try:
        already_existing_card = find_card(interaction, name)
        if already_existing_card:
            await interaction.response.send_message(f"{name} is too much like {already_existing_card[0]['name']}.  Consider changing the name of your card.")
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in manually_add_card, {e, already_existing_card}"
        await interaction.response.send_message(error_message)

    try:
        add_card_logic(interaction=interaction, name=name, card_type=card_type, rarity=rarity, mana_cost=mana_cost, 
                                                                power_and_toughness=power_and_toughness, text=text, image_url=image_url)
        message, embed = search_card_logic(interaction, 'name', name)  # Directly call the search_card function
        if embed:
            await interaction.response.send_message(embed=embed)
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in manually_add_card, {e}"
        await interaction.response.send_message(error_message)

@bot.tree.command(name="add_card", description="Add a custom Magic card to the database using image recognition")
async def add_card(interaction: discord.Interaction, 
                   name: str, 
                   image_url: str):
    try:
        already_existing_card = find_card(interaction, 'name', name)
        if already_existing_card:
            await interaction.response.send_message(f"{name} is too much like {already_existing_card[0]['name']}.  Consider changing the name of your card.")
        add_card_logic(interaction=interaction, name=name, card_type=None, rarity=None, mana_cost=None, power_and_toughness=None, text=None, image_url=image_url)
        # Step 4: Search the card directly after adding it
        # Instead of invoking, directly call the search_card function
        message, embed, arg = search_card_logic(search_value=name, search_by='name')  # Directly call the search_card function
        if not embed:
            await interaction.response.send_message(message)
        else:
            await interaction.response.send_message(embed=embed)
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in add_card, {e}"
        await interaction.response.send_message(error_message)

@bot.tree.command(name="search_card", description="Search for Magic cards by any attribute")
async def search_card(
    interaction: discord.Interaction,
    search_value: str,
    search_by: str ='name'
):
    try:
        message, embed, arg = search_card_logic(search_by=search_by, search_value=search_value)
        if not embed:
            await interaction.response.send_message(message)
        else:
            await interaction.response.send_message(embed=embed)
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in search_card, {e}"
        await interaction.response.send_message(error_message)



# Slash command to list all cards in the database (useful for debugging)
@bot.tree.command(name="list_cards", description="List all Magic cards in the database")
async def list_cards(interaction: discord.Interaction):
    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, name FROM cards')
        cards = cursor.fetchall()
        conn.close()

        if cards:
            # Find the length of the longest card name
            max_name_length = max(len(card[1]) for card in cards)
            
            # Format the card names and ids into two columns, adjusting width based on the longest name
            card_names = "\n".join(f"{card[1]:<{max_name_length}}  id = {str(card[0])}" for card in cards)
            await interaction.response.send_message(f"Cards in database:\n{card_names}")
        else:
            await interaction.response.send_message("No cards found in the database.")
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in list_cards, {e}"
        await interaction.response.send_message(error_message)


@bot.tree.command(name="remove_card", description="Remove a card from the database")
async def remove_card(
    interaction: discord.Interaction,
    card_name: str = None,  
    card_id: int = None
):
    try:
        remove_card_output = remove_card_logic(interaction=interaction, card_name=card_name, card_id=card_id)
        if remove_card_output:
            await interaction.response.send_message(remove_card_output)
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in remove_card, {e, remove_card_output}"
        await interaction.response.send_message(error_message)




@bot.tree.command(name="edit_card", description="Edit a card's content")
async def edit_card(interaction: discord.Interaction, card_name: str):
    try:
    
        # Defer the response to keep the interaction alive
        await interaction.response.defer()

        # Search for the card first
        cards = find_card(interaction, 'name', card_name)
        
        if not cards:
            await interaction.followup.send(f"No card found with name '{card_name}'.")
            return
        
        if len(cards) > 1:
            await interaction.followup.send(f"Multiple cards found with name '{card_name}', please be more specific.")
            return
        
        # We have found the card, let's interactively ask for which field to edit
        found_card = cards[0]
        
        # Prompt user to select which field to edit
        await interaction.followup.send(f"Which attribute of '{found_card['name']}' would you like to edit?\n"
                                        "Choose one of the following:\n"
                                        "1. Name\n"
                                        "2. Type\n"
                                        "3. Rarity\n"
                                        "4. Mana Cost\n"
                                        "5. Power/Toughness\n"
                                        "6. Text\n"
                                        "7. Image_url")
        
        # Wait for the user's response
        def check_channel(message):
            return message.author == interaction.user and message.content.strip().lower() in ['1', '2', '3', '4', '5', '6', 'name', "type", 
                                                                                                'rarity', 'mana cost', 'power', 'toughness', 
                                                                                                'image', 'url', 'power/toughness', 'power and toughness', 'text'] and \
                message.channel.id == interaction.channel.id
        
        def check_if_string(message):
            return message.author == interaction.user and isinstance(message.content.strip(), str) and message.channel.id == interaction.channel.id
        
        def check_if_rarity(message):
            return message.author == interaction.user and message.content.strip().lower() in ['common', 'uncommon', 'rare', 'mythic'] and message.channel.id == interaction.channel.id
        
        def check_if_mana_cost(message):
            if message.author == interaction.user and message.channel.id == interaction.channel.id:
                message = message.content.strip().lower()
                valid__mana_letters = ['w', 'u', 'b', 'r', 'g'] #or int 
                for letter in message:
                    if letter not in valid__mana_letters: 
                        if letter.isalpha() and not letter.isdigit:
                            return False
                return True
        
        def check_if_power_or_toughness(message):
            return message.author == interaction.user and message.content.isdigit() and message.channel.id == interaction.channel.id
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in edit_card, {e}"
        await interaction.response.send_message(error_message)

    
    try:
        # Await user's response to choose the field
        choice_message = await bot.wait_for('message', check=check_channel, timeout=60)  # Increased timeout to 60 seconds
        choice = choice_message.content

        # Ask the user for the new content based on the chosen attribute
        if choice == '1' or choice == 'name':
            await interaction.followup.send(f"Enter the new name for '{found_card['name']}':")
            new_name_message = await bot.wait_for('message', check=check_if_string, timeout=60)
            new_name = new_name_message.content
            update_column = 'name'
            new_value = new_name
        elif choice == '2' or choice == 'type':
            await interaction.followup.send(f"Enter the new type for '{found_card['name']}':")
            new_type_message = await bot.wait_for('message', check=check_if_string, timeout=60)
            new_type = new_type_message.content
            update_column = 'type'
            new_value = new_type
        elif choice == '3' or choice == 'rarity':
            await interaction.followup.send(f"Enter the new rarity for '{found_card['name']}':")
            new_rarity_message = await bot.wait_for('message', check=check_if_rarity, timeout=60)
            new_rarity = new_rarity_message.content
            update_column = 'rarity'
            new_value = new_rarity
        elif choice == '4' or choice == 'mana cost':
            await interaction.followup.send(f"Enter the new mana cost for '{found_card['name']}':")
            new_mana_cost_message = await bot.wait_for('message', check=check_if_mana_cost, timeout=60)
            new_mana_cost = new_mana_cost_message.content
            update_column = 'mana_cost'
            new_value = new_mana_cost
        elif choice == '5' or choice == 'power' or choice == 'toughness' or choice == 'power/toughness' or choice == 'power and toughness':
            await interaction.followup.send(f"Enter the new power/toughness for '{found_card['name']}':")
            new_power_and_toughness_message = await bot.wait_for('message', check=check_if_power_or_toughness, timeout=60)
            new_power_and_toughness = new_power_and_toughness_message.content
            update_column = 'power_and_toughness'
            try:
                new_value = int(new_power_and_toughness)
            except ValueError:
                await interaction.followup.send("Invalid")
                return
        elif choice == '6' or choice == 'text':
            await interaction.followup.send(f"Enter the new text for '{found_card['name']}':")
            new_text_message = await bot.wait_for('message', check=check_if_string, timeout=60)
            new_text = new_text_message.content
            update_column = 'text'
            new_value = new_text
        elif choice == '7' or choice == 'url' or choice == 'image':
            await interaction.followup.send(f"Enter new url for {found_card['image_url']}")
            new_url_message = await bot.wait_for('message', check=check_if_string, timeout=60)
            new_url = new_url_message.content
            update_column = 'image_url'
            new_value = new_url
            

        # Update the database with the new value
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update the card in the database
        cursor.execute(f"UPDATE cards SET {update_column} = ? WHERE id = ?", (new_value, found_card['id']))
        conn.commit()
        conn.close()

        await interaction.followup.send(f"The {update_column} of '{found_card['name']}' has been updated to '{new_value}'.")
    
    except asyncio.TimeoutError:
        # Handle the timeout case
        await interaction.followup.send("You took too long to respond. Please try again.")
    except discord.errors.InteractionResponded:
        # If interaction is already responded to, you can't send further responses
        print("Interaction already responded.")

@bot.tree.command(name="advice", description="Bot will return adive on custom card")
async def advice(interaction: discord.Interaction, card_name: str):
    await interaction.response.defer()
    response = advice_logic(card_name)
    await interaction.followup.send(response)

# Event listener for new messages
@bot.event
async def on_message(message):
    try:
        global guild
        # Don't let the bot respond to its own messages
        if message.author == bot.user:
            return
        # Check if the message was sent in a guild (server)
        if isinstance(message.author, discord.Member):     
            #VOTING LOGIC       
            
            try_vote = vote(message)
            if try_vote:
                if try_vote != 'Start':
                    await message.channel.send(try_vote)
                else:
                    await message.add_reaction('🟩')
                    await message.add_reaction('🟥')
                    time = 60*60 #TODO, change to desired time
                    await message.channel.send(f"Timer started for the card posted by {message.author.mention}. React to the card within {math.floor(time/60/60)} hour(s)!")
                    # Wait for the timer to complete
                    await asyncio.sleep(time)

                    # Fetch the message again to get updated reactions
                    updated_message = await message.channel.fetch_message(message.id)
                                # Count green and red squares
                    name_of_card, check_success, vote_outcome = count_vote(updated_message)    
                    
                        # Notify the reactions
                    if vote_outcome:
                        await message.channel.send(f"Results to the card posted by {message.author.mention} are:\n{vote_outcome}")
                    else:
                        await message.channel.send(f"No reactions were added to the link posted by {message.author.mention}.")
                    if check_success:
                        content, embed, arg = search_card_logic(search_value=name_of_card)
                    if not embed:
                        await message.channel.send(content)
                    else:
                        await message.channel.send(embed=embed)
                    await bot.process_commands(message)
            
            #Scryfall Search Logic:
            matches = scryfall_search(message.content)
            if matches:
                for match in matches: 
                    content, embed, arg = search_card_logic(search_value=match)
                    if not embed:
                        await message.channel.send(content)
                    else:
                        await message.channel.send(embed=embed)
    except Exception as e:
        error_message = f"<@&1313626558304616572> error in on message, {e}"
        await message.channel.send(error_message)

@bot.tree.command(name="help", description="List all available commands with descriptions")
async def help_command(interaction: discord.Interaction):
    # Initialize an empty string for the help message
    help_message = "**List of available commands:**\n\n"
    
    # Iterate through each command and build the help message
    for command in bot.tree.get_commands():
        help_message += f"**/{command.name}**: {command.description}\n"
    
    # Send the message to the user
    await interaction.response.send_message(help_message)


# Run the bot with the token
bot.run(key)
