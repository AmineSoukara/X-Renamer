import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

import os
import time
import asyncio
import pyrogram
import random

if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

from script import script

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

from plugins.helpers import progress_for_pyrogram

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from plugins.helpNekmo import take_screen_shot

from PIL import Image
from database.database import *


async def force_name(bot, message):

    await bot.send_message(
        message.reply_to_message.from_user.id,
        "Enter New Name For Movie\n\n⚠️ Note : Extension Not required, Y3ni Bla Mtdir Dak .mp4 ola .mkv",
        reply_to_message_id=message.reply_to_message.message_id,
        reply_markup=ForceReply(True)
    )


@Client.on_message(filters.private & filters.reply & filters.text)
async def cus_name(bot, message):
    
    if (message.reply_to_message.reply_markup) and isinstance(message.reply_to_message.reply_markup, ForceReply):
        asyncio.create_task(rename_doc(bot, message))     
    else:
        print('No media present')

    
async def rename_doc(bot, message):
    
    mssg = await bot.get_messages(
        message.chat.id,
        message.reply_to_message.message_id
    )    
    
    media = mssg.reply_to_message

    
    if media.empty:
        await message.reply_text('Alach Ms7tiiih 😕', True)
        return
        
    filetype = media.document or media.video or media.audio or media.voice or media.video_note
    try:
        actualname = filetype.file_name
        splitit = actualname.split(".")
        extension = (splitit[-1])
    except:
        extension = "mp4"

    await bot.delete_messages(
        chat_id=message.chat.id,
        message_ids=message.reply_to_message.message_id,
        revoke=True
    )
    
    if message.from_user.id in Config.AUTH_USERS:
        file_name = message.text
        description = script.CUSTOM_CAPTION_UL_FILE.format(newname=file_name)
        download_location = Config.DOWNLOAD_LOCATION + "/"
        thumb_image_path = download_location + str(message.from_user.id) + ".jpg"
        if not os.path.exists(thumb_image_path):
            mes = await thumb(message.from_user.id)
            if mes != None:
                m = await bot.get_messages(message.chat.id, mes.msg_id)
                await m.download(file_name=thumb_image_path)
                thumb_image_path = thumb_image_path

        a = await bot.send_message(
            chat_id=message.chat.id,
            text=script.DOWNLOAD_START,
            reply_to_message_id=message.message_id
        )
        
        c_time = time.time()
        the_real_download_location = await bot.download_media(
            message=media,
            file_name=download_location,
            progress=progress_for_pyrogram,
            progress_args=(
                script.DOWNLOAD_START,
                a,
                c_time
            )
        )
        if the_real_download_location is not None:
            await bot.edit_message_text(
                text=script.SAVED_RECVD_DOC_FILE,
                chat_id=message.chat.id,
                message_id=a.message_id
            )

            new_file_name = download_location + file_name + "." + extension
            mcaption = file_name + " " + " @MoviesBdarija"
            mov = "./pic/mov.jpg"
            os.rename(the_real_download_location, new_file_name)
            await bot.edit_message_text(
                text=script.UPLOAD_START,
                chat_id=message.chat.id,
                message_id=a.message_id
                )
            # logger.info(the_real_download_location)

            if os.path.exists(thumb_image_path):
                width = 0
            height = 0
            duration = 0
            metadata = extractMetadata(createParser(new_file_name))
            try:
             if metadata.has("duration"):
                duration = metadata.get('duration').seconds
            except:
              pass
            thumb_image_path = Config.DOWNLOAD_LOCATION + "/" + str(message.from_user.id) + ".jpg"
            if not os.path.exists(thumb_image_path):
               try:
                    thumb_image_path = await take_screen_shot(new_file_name, os.path.dirname(new_file_name), random.randint(0, duration - 1))
               except:
                    thumb_image_path = None
            else:
                width = 0
                height = 0
                metadata = extractMetadata(createParser(thumb_image_path))
                if metadata.has("width"):
                    width = metadata.get("width")
                if metadata.has("height"):
                    height = metadata.get("height")
                # resize image
                # ref: https://t.me/PyrogramChat/44663
                # https://stackoverflow.com/a/21669827/4723940
                Image.open(thumb_image_path).convert("RGB").save(thumb_image_path)
                img = Image.open(thumb_image_path)
                # https://stackoverflow.com/a/37631799/4723940
                # img.thumbnail((90, 90))
                img.resize((320, height))
                img.save(thumb_image_path, "JPEG")
                # https://pillow.readthedocs.io/en/3.1.x/reference/Image.html#create-thumbnails
            c_time = time.time()
            await bot.send_video(
                chat_id=message.chat.id,
                video=new_file_name,
                duration=duration,
                thumb=thumb_image_path,
                caption=mcaption,
                # reply_markup=reply_markup,
                reply_to_message_id=message.reply_to_message.message_id,
                progress=progress_for_pyrogram,
                progress_args=(
                    script.UPLOAD_START,
                    a, 
                    c_time
                )
            )

            try:
                os.remove(new_file_name)
            except:
                pass                 
            try:
                os.remove(thumb_image_path)
            except:
                pass  

            await bot.edit_message_text(
                text=script.AFTER_SUCCESSFUL_UPLOAD_MSG,
                chat_id=message.chat.id,
                message_id=a.message_id,
                disable_web_page_preview=True
            )
            
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text="😄 Rah Golna Lik Ghi Admins Likykhdmo Bhad Bot",
            reply_to_message_id=message.message_id
        )
