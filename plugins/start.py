import os
import asyncio
import config
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, SECONDS
from helper_func import subscribed, decode, get_messages
from database.database import add_user, present_user, del_user, full_userbase

# Add time in seconds for waiting before deleting
SECONDS = int(os.getenv("SECONDS", "600"))

# Start command handler


@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # Add user to database if not present
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass

    text = message.text

    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            string = await decode(base64_string)
            argument = string.split("-")

            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                    ids = range(start, end + 1) if start <= end else []

                except Exception as e:
                    print(f"Error parsing argument: {e}")
                    return

            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]

                except Exception as e:
                    print(f"Error parsing argument: {e}")
                    return

            else:
                return

        except Exception as e:
            print(f"Error decoding argument: {e}")
            return

    else:
        # No command with arguments, handle the 'else' block
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "ᴀʙᴏᴜᴛ", callback_data="about"),
                    InlineKeyboardButton(
                        "ᴄʟᴏꜱᴇ", callback_data="close")
                ]
            ]
        )
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )
        return

    # Notify user that content is being prepared
    temp_msg = await message.reply("!! ᴄᴏɴᴛᴇɴᴛ ᴠᴇᴛᴛɪɴɢ !!")

    try:
        messages = await get_messages(client, ids)

    except Exception as e:
        print(f"Error fetching messages: {e}")
        await temp_msg.edit_text("ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ᴄᴏɴᴛᴇɴᴛ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")
        return

    if not messages:
        sent_msg = await message.reply_text("ɴɪɢɢᴀ ʏᴏᴜ ʟᴀᴛᴇ. ɢᴇᴛ ʏᴏᴜʀ ᴀss ɪɴ ʜᴇʀᴇ ɪɴ ᴛɪᴍᴇ")

        # Auto delete the message after 7 seconds
        await asyncio.sleep(7)
        try:
            await sent_msg.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")

        return

    # Delete the temporary message before sharing files
    await temp_msg.delete()

    sent_messages = []
    found_files = False

    for msg in messages:
        # Check if the message is empty (no document)
        if msg.document is None:
            # Skip empty files
            continue

        found_files = True

        # Generate caption based on configuration
        if bool(CUSTOM_CAPTION) and bool(msg.document):
            caption = CUSTOM_CAPTION.format(
                previouscaption="" if not msg.caption else msg.caption.html,
                filename=msg.document.file_name
            )
        else:
            caption = "" if not msg.caption else msg.caption.html

        # Determine reply markup based on configuration
        if DISABLE_CHANNEL_BUTTON:
            reply_markup = msg.reply_markup
        else:
            reply_markup = None

        try:
            # Copy message to user with specified settings
            copied_msg = await msg.copy(
                chat_id=message.from_user.id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                protect_content=PROTECT_CONTENT
            )
            sent_messages.append(copied_msg)

        except FloodWait as e:
            await asyncio.sleep(e.x)
            copied_msg = await msg.copy(
                chat_id=message.from_user.id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                protect_content=PROTECT_CONTENT
            )
            sent_messages.append(copied_msg)

        except:
            pass

    if found_files:
        # Notify the user about the deletion process and wait before deletion
        deletion_msg = await client.send_message(
            chat_id=message.from_user.id,
            text="<b><center>❗<u> Important </u> ❗</center></b>\n\nSorry Dude This File/Video Will Be Deleted in 10 min\n\n🍁So, Please Immediately Save This File In Your Saved Messages.🍂",
            parse_mode=ParseMode.HTML
        )

        await asyncio.sleep(SECONDS)

        # Delete each sent message and update the user
        for msg in sent_messages:
            try:
                await msg.delete()

            except Exception as e:
                print(f"Error deleting message: {e}")
                pass

        # Inform user about completion of deletion process
        await deletion_msg.edit_text("")

    else:
        # No files found, inform the user
        sent_msg = await message.reply_text("ɴɪɢɢᴀ ʏᴏᴜ ʟᴀᴛᴇ. ɢᴇᴛ ʏᴏᴜʀ ᴀss ɪɴ ʜᴇʀᴇ ɪɴ ᴛɪᴍᴇ")

        # Auto delete the message after 7 seconds
        await asyncio.sleep(7)
        try:
            await sent_msg.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")
    return


# =====================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message without any spaces.</code>"""

# =====================================================================================##


@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(text="⚡ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ⚡", url=client.invitelink),
            InlineKeyboardButton(text="⚡ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ⚡",
                                 url=client.invitelink2),
        ]
    ]

    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text='𝐓𝐫𝐲 𝐀𝐠𝐚𝐢𝐧',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
        disable_web_page_preview=True
    )

######## ---------------            USERS USING BOT COMMAND            ---------------########


@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")


######## ---------------            BROADCAST COMMAND(with BUTTONS)            ---------------########
@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        # Retrieve user base to broadcast messages to
        query = await full_userbase()

        # Get the message to be broadcasted
        broadcast_msg = message.reply_to_message

        # Initialize counters for statistics
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        # Ask for buttons (optional)
        try:
            buttons_message = await client.ask(
                text="Please send the button text and URL in this format: \nButtonText1:URL1 \nButtonText2:URL2\n\nOr type 'skip' to skip adding buttons.",
                chat_id=message.from_user.id,
                timeout=600
            )
        except asyncio.TimeoutError:
            await message.reply("⏳ Time ran out. Proceeding without adding buttons.")
            buttons_message = None

        buttons = []
        if buttons_message and buttons_message.text.strip().lower() != 'skip':
            # Parse button text and URLs
            button_pairs = buttons_message.text.split(',')
            for pair in button_pairs:
                # Split once to handle cases where URLs contain ':'
                parts = pair.split(':', 1)
                if len(parts) == 2:
                    text, url = parts
                    buttons.append(
                        [InlineKeyboardButton(text.strip(), url=url.strip())])

        # Prepare reply markup with buttons
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

        # Notify users about the broadcasting process
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>", reply_markup=reply_markup)

        # Iterate over each user and attempt to send the broadcast message
        for chat_id in query:
            try:
                # Send message with buttons
                await broadcast_msg.copy(chat_id, reply_markup=reply_markup)
                successful += 1
            except FloodWait as e:
                # Handle FloodWait exceptions by waiting and retrying
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id, reply_markup=reply_markup)
                successful += 1
            except UserIsBlocked:
                # Handle blocked users by removing them from the user base
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                # Handle deactivated accounts by removing them from the user base
                await del_user(chat_id)
                deleted += 1
            except Exception as ex:
                # Handle other exceptions (unsuccessful attempts)
                unsuccessful += 1
                print(f"Failed to broadcast to {chat_id}: {ex}")

            # Increment total users counter
            total += 1

        # Format and edit the initial "Please wait" message to show broadcast statistics
        status = f"""<b><u>Broadcast Completed</u></b>

<b>Total Users:</b> <code>{total}</code>
<b>Successful:</b> <code>{successful}</code>
<b>Blocked Users:</b> <code>{blocked}</code>
<b>Deleted Accounts:</b> <code>{deleted}</code>
<b>Unsuccessful:</b> <code>{unsuccessful}</code>"""

        await pls_wait.edit(status)

    else:
        # If not used as a reply, reply with an error message after a delay
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

######################----------------------New---------------------------#################################


settings = {
    "custom_caption": {
        "enabled": False,
        "caption": getattr(config, "CUSTOM_CAPTION", None)
    },
    "auto_delete": False,
    "protected_content": getattr(config, "PROTECT_CONTENT", False)
}

def update_config():
    with open("config.py", "w") as f:
        f.write(f"SECONDS = {config.SECONDS}\n")
        f.write(f"PROTECT_CONTENT = {settings['protected_content']}\n")
        caption = 'None' if settings["custom_caption"]["caption"] is None else f"'{settings['custom_caption']['caption']}'"
        f.write(f"CUSTOM_CAPTION = {caption}\n")

# Settings commands
@app.on_message(filters.command("settings") & filters.user(ADMINS))
def settings_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("CUSTOM CAPTION", callback_data='custom_caption')],
        [InlineKeyboardButton("CUSTOM BUTTON", callback_data='custom_button')],
        [InlineKeyboardButton("AUTO DELETE", callback_data='auto_delete')],
        [InlineKeyboardButton("PROTECT CONTENT", callback_data='protected_content')],
        [InlineKeyboardButton("BACK", callback_data='back')],
    ])
    message.reply_text('Here is the settings menu. Customize your settings as per your need:', reply_markup=keyboard)

# Custom caption commands
@app.on_message(filters.command("add_caption") & filters.user(ADMINS))
def add_caption(client, message):
    try:
        caption = message.text.split(maxsplit=1)[1]
        settings["custom_caption"]["caption"] = caption
        update_config()
        message.reply_text(f"Custom caption set to: {caption}")
    except IndexError:
        message.reply_text("Usage: /add_caption <your caption>")

@app.on_message(filters.command("remove_caption") & filters.user(ADMINS))
def remove_caption(client, message):
    settings["custom_caption"]["caption"] = None
    update_config()
    message.reply_text("Custom caption removed.")

@app.on_message(filters.command("caption_on") & filters.user(ADMINS))
def caption_on(client, message):
    settings["custom_caption"]["enabled"] = True
    message.reply_text("Custom caption is now ON.")

@app.on_message(filters.command("caption_off") & filters.user(ADMINS))
def caption_off(client, message):
    settings["custom_caption"]["enabled"] = False
    message.reply_text("Custom caption is now OFF.")

# Auto delete commands
@app.on_message(filters.command("auto_delete_on") & filters.user(ADMINS))
def auto_delete_on(client, message):
    settings["auto_delete"] = True
    message.reply_text("Auto delete is now ON.")

@app.on_message(filters.command("auto_delete_off") & filters.user(ADMINS))
def auto_delete_off(client, message):
    settings["auto_delete"] = False
    message.reply_text("Auto delete is now OFF.")

# Protected content commands
@app.on_message(filters.command("protect_content_on") & filters.user(ADMINS))
def protect_content_on(client, message):
    settings["protected_content"] = True
    update_config()
    message.reply_text("Protected content is now ON.")

@app.on_message(filters.command("protect_content_off") & filters.user(ADMINS))
def protect_content_off(client, message):
    settings["protected_content"] = False
    update_config()
    message.reply_text("Protected content is now OFF.")

# Callback query handler
@app.on_callback_query()
def handle_callback_query(client, callback_query):
    data = callback_query.data
    if data == 'custom_caption':
        callback_query.message.edit_text(
            "Use /add_caption <your caption> to set a custom caption, /remove_caption to remove it, "
            "/caption_on to enable it, and /caption_off to disable it."
        )
    elif data == 'custom_button':
        callback_query.message.edit_text("This is useless.")
    elif data == 'auto_delete':
        callback_query.message.edit_text(
            "Use /auto_delete_on to enable auto delete and /auto_delete_off to disable it."
        )
    elif data == 'protected_content':
        callback_query.message.edit_text(
            "Use /protect_content_on to enable protected content and /protect_content_off to disable it."
        )
    elif data == 'back':
        callback_query.message.edit_text("Back to main menu.")
