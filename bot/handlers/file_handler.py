#!/usr/bin/env python3
"""File handler for receiving videos"""

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

from bot import bot, OWNER_ID, AUTHORIZED_USERS, DOWNLOAD_DIR, LOGGER, user_data
from bot.keyboards.menus import main_menu, close_button
from bot.ffmpeg.core import get_video_info, format_media_info
from bot.utils.helpers import is_video_file, get_readable_file_size
from bot.utils.progress import Progress


# Helper function to check authorization
def is_authorized(user_id: int) -> bool:
    if not AUTHORIZED_USERS:
        return True
    return user_id in AUTHORIZED_USERS or user_id == OWNER_ID


@bot.on_message(filters.private & (filters.video | filters.document))
async def handle_video(client: Client, message: Message):
    """Handle received video files and subtitles"""
    user = message.from_user
    
    if not is_authorized(user.id):
        await message.reply_text("❌ You are not authorized.")
        return
    
    # helper to check subtitle
    def is_subtitle_file(filename: str) -> bool:
        if not filename: return False
        return any(filename.lower().endswith(ext) for ext in ['.srt', '.ass', '.ssa', '.vtt', '.sub'])

    fname = message.document.file_name if message.document else (message.video.file_name if message.video else "")
    
    # Get current state
    waiting_for = user_data.get(user.id, {}).get('waiting_for')
    
    # 1. Check if waiting for Subtitles
    if waiting_for in ['subtitle', 'hardsub']:
        if message.document and is_subtitle_file(fname):
            user_data[user.id]['subtitle_message'] = message
            user_data[user.id]['subtitle_name'] = fname
            
            # Determine operation
            operation = 'add_subtitle' if waiting_for == 'subtitle' else 'hardsub'
            user_data[user.id]['waiting_for'] = None
            
            await message.reply_text(
                "✅ Subtitle file received!\n\n"
                "Processing will begin shortly...",
                quote=True
            )
            
            from bot.handlers.message_handler import MockQuery
            from bot.handlers.callbacks import process_video
            await process_video(client, MockQuery(message, user), operation, {})
            return
        else:
            await message.reply_text("❌ Please send a valid subtitle file (.srt, .ass, .ssa, .vtt).")
            return

    # 2. Check if waiting for Second Video (Vid+Vid)
    if waiting_for == 'second_video':
        # Check if it's a video
        is_video = False
        if message.video: is_video = True
        if message.document and is_video_file(fname): is_video = True
        
        if not is_video:
            await message.reply_text("❌ Please send a valid video file.")
            return

        user_data[user.id]['second_video_message'] = message
        user_data[user.id]['second_video_name'] = fname
        user_data[user.id]['waiting_for'] = None
        
        from bot.handlers.message_handler import MockQuery
        from bot.handlers.callbacks import process_video
        
        await message.reply_text("✅ Second video received! Merging...", quote=True)
        await process_video(client, MockQuery(message, user), 'merge_video', {})
        return

    # 3. Check if it's a new Video
    is_video = False
    if message.video: is_video = True
    if message.document and is_video_file(fname): is_video = True
    
    if is_video:
        file_name = fname or f"video_{message.video.file_unique_id}.mp4"
        file_size = message.document.file_size if message.document else message.video.file_size
        
        # Store file info for this user
        user_data[user.id] = {
            'message_id': message.id,
            'file_name': file_name,
            'file_size': file_size,
            'file_path': None,
            'operation': None,
            'settings': user_data.get(user.id, {}).get('settings', {}),
        }
        
        info_text = (
            f"<b>📁 File Received!</b>\n\n"
            f"<b>📄 Name:</b> <code>{file_name}</code>\n"
            f"<b>💾 Size:</b> {get_readable_file_size(file_size)}\n\n"
            f"<b>Select an operation from the menu below:</b>"
        )
        
        await message.reply_text(
            info_text,
            reply_markup=main_menu(user.id),
            quote=True
        )
        return

    # 4. Check if random Subtitle (not waiting)
    if message.document and is_subtitle_file(fname):
        await message.reply_text(
            "ℹ️ To add subtitles, please send a video first, then select <b>Vid+Sub</b> from the menu.",
            quote=True
        )
        return

    # 5. Unknown/Invalid
    await message.reply_text(
        "❌ Please send a video file.\n\n"
        "Supported formats: mp4, mkv, avi, mov, webm, flv, etc."
    )


@bot.on_message(filters.private & filters.audio)
async def handle_audio(client: Client, message: Message):
    """Handle audio files (for Vid+Aud operation)"""
    user = message.from_user
    
    if not is_authorized(user.id):
        return
    
    # Check if user has a pending video operation
    if user.id in user_data and user_data[user.id].get('waiting_for') == 'audio':
        user_data[user.id]['audio_message'] = message
        user_data[user.id]['audio_name'] = message.audio.file_name if message.audio else "audio.mp3"
        user_data[user.id]['waiting_for'] = None
        
        await message.reply_text(
            "✅ Audio file received!\n\n"
            "Processing will begin shortly...",
            quote=True
        )
        
        from bot.handlers.message_handler import MockQuery
        from bot.handlers.callbacks import process_video
        await process_video(client, MockQuery(message, user), 'add_audio', {})
        
    else:
        await message.reply_text(
            "ℹ️ Send a video first, then select <b>Vid+Aud</b> to add this audio.",
            quote=True
        )





@bot.on_message(filters.private & filters.photo)
async def handle_photo(client: Client, message: Message):
    """Handle photos (for watermark or thumbnail)"""
    user = message.from_user
    
    if not is_authorized(user.id):
        return
    
    waiting_for = user_data.get(user.id, {}).get('waiting_for')
    
    # 1. Set Thumbnail
    if waiting_for == 'set_thumbnail':
        from bot.utils.db_handler import get_db
        db = get_db()
        
        # Save highest quality file_id
        file_id = message.photo.file_id
        await db.set_thumbnail(user.id, file_id)
        
        user_data[user.id]['waiting_for'] = None
        
        await message.reply_text(
            "✅ <b>Custom thumbnail saved!</b>\n"
            "It will be used for all future video uploads.",
            quote=True
        )
        return

    # 2. Watermark Image
    if waiting_for == 'watermark_image':
        user_data[user.id]['watermark_message'] = message
        user_data[user.id]['waiting_for'] = None
        
        await message.reply_text(
            "✅ Watermark image received!\n\n"
            "Now configure position, opacity, etc.",
            quote=True
        )
        
        if 'watermark_settings' not in user_data[user.id]:
            user_data[user.id]['watermark_settings'] = {}
        
        from bot.keyboards.menus import watermark_menu
        await message.reply_text(
            "Image saved. Configure settings:",
            reply_markup=watermark_menu(user.id)
        )
        return


@bot.on_message(filters.private & filters.text & ~filters.command(["start", "help", "settings", "vset", "cancel", "stats", "log", "broadcast", "zip", "unzip", "thumb"]))
async def handle_text_input(client: Client, message: Message):
    # ... (rest of handle_text_input is unchanged, but we needed to modify handle_photo first)
    # Actually, I am replacing the file content from handle_photo onwards, so I need to include handle_text_input if I am replacing a chunk that covers both.
    # But I can just target handle_photo block if I am careful.
    # Let's just implement handle_photo correctly.
    pass 
    # I will rely on the fact that I am replacing handle_photo and can leave handle_text_input alone if I target correctly.
    # But wait, looking at the previous file view, handle_photo ends around line 199.
    # I'll just replace the handle_photo function.

async def upload_file(client: Client, chat_id: int, file_path: str | list, status_msg: Message, caption: str = None, user_id: int = None):
    """Upload file with progress"""
    
    # Handle list of files (Media Group)
    if isinstance(file_path, list):
        from pyrogram.types import InputMediaPhoto
        media = []
        for f in file_path:
            # Assume photos for now (screenshots)
            media.append(InputMediaPhoto(f))
        
        await status_msg.edit_text("📤 Uploading album...")
        try:
            await client.send_media_group(chat_id, media)
        except Exception as e:
            await status_msg.edit_text(f"❌ Upload failed: {e}")
            raise e
        return

    # Single File
    file_name = os.path.basename(file_path) if isinstance(file_path, str) else "Album"
    progress = Progress(status_msg, "📤 Uploading", user_id=user_id, filename=file_name)
    
    # Store progress for cancellation
    if user_id and user_id in user_data:
        user_data[user_id]['progress'] = progress
    
    # Prepare Thumbnail
    thumb_path = None
    if user_id:
        from bot.utils.db_handler import get_db
        db = get_db()
        thumb_id = await db.get_thumbnail(user_id)
        
        if thumb_id:
            try:
                # Download thumb to temp
                import time
                temp_thumb = os.path.join(DOWNLOAD_DIR, f"thumb_{user_id}_{int(time.time())}.jpg")
                await client.download_media(thumb_id, file_name=temp_thumb)
                if os.path.exists(temp_thumb):
                    thumb_path = temp_thumb
            except Exception as e:
                LOGGER.error(f"Failed to download custom thumbnail: {e}")

    # Start Upload
    try:
        video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
        ext = os.path.splitext(file_name)[1].lower()
        
        sent_msg = None

        if ext in video_exts:
            sent_msg = await client.send_video(
                chat_id,
                file_path,
                caption=caption or f"✅ <code>{file_name}</code>",
                progress=progress.progress_callback,
                thumb=thumb_path
            )
        else:
            sent_msg = await client.send_document(
                chat_id,
                file_path,
                caption=caption or f"✅ <code>{file_name}</code>",
                progress=progress.progress_callback,
                thumb=thumb_path
            )
            
        # Log Channel Forwarding
        from bot import LOG_CHANNEL
        if sent_msg and LOG_CHANNEL:
            try:
                await sent_msg.copy(LOG_CHANNEL, caption=f"Processing Request from {user_id}\n\n" + (sent_msg.caption or ""))
            except Exception as e:
                LOGGER.error(f"Failed to forward to log channel: {e}")
                
    except Exception as e:
        if progress.cancelled:
            raise asyncio.CancelledError("Cancelled by user")
        raise e
    finally:
        # Cleanup thumb
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except:
                pass

@bot.on_message(filters.private & filters.text & ~filters.command(["start", "help", "settings", "vset", "cancel", "stats", "log", "broadcast", "zip", "unzip"]))
async def handle_text_input(client: Client, message: Message):
    """Handle text inputs (Rename, URL, etc.)"""
    user = message.from_user
    if not is_authorized(user.id):
        return

    text = message.text.strip()
    waiting_for = user_data.get(user.id, {}).get('waiting_for')

    # 1. Handle Rename Input
    if waiting_for == 'new_filename':
        old_path = user_data[user.id].get('processing_file') or user_data[user.id].get('file_path')
        if not old_path or not os.path.exists(old_path):
             await message.reply_text("❌ Original file lost. Please upload again.")
             return
             
        new_name = sanitize_filename(text)
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        try:
            os.rename(old_path, new_path)
            # Update data
            user_data[user.id]['file_path'] = new_path
            user_data[user.id]['processing_file'] = new_path
            user_data[user.id]['file_name'] = new_name
            user_data[user.id]['waiting_for'] = None
            
            await message.reply_text(
                f"✅ Renamed to: <code>{new_name}</code>",
                reply_markup=main_menu(user.id),
                quote=True
            )
        except Exception as e:
            await message.reply_text(f"❌ Rename failed: {e}")
        return

    # 2. Handle Final Rename Input
    if waiting_for == 'final_rename_input':
        old_path = user_data[user.id].get('output_path')
        if not old_path or not os.path.exists(old_path):
             await message.reply_text("❌ Processed file lost.")
             return
             
        new_name = sanitize_filename(text)
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        try:
            os.rename(old_path, new_path)
            # Update data
            user_data[user.id]['output_path'] = new_path
            user_data[user.id]['waiting_for'] = None
            
            status_msg = await message.reply_text(f"✅ Renamed to: <code>{new_name}</code>\nUploading...")
            
            # Proceed to upload
            from bot.handlers.callbacks import upload_processed_file
            await upload_processed_file(client, user.id, status_msg, "telegram")
            
        except Exception as e:
            await message.reply_text(f"❌ Rename failed: {e}")
        return

    # 3. Handle Other Inputs (e.g., FFMPEG CMD, Sub Intro) - to be implemented if needed
    
    # 4. Fallback: Handle URL
    if text.startswith("http://") or text.startswith("https://"):
        await handle_url_logic(client, message, text)
    else:
        # Just chat?
        pass


from bot.utils.helpers import sanitize_filename

async def handle_url_logic(client, message, text):
    """Refactored URL handling logic"""
    user = message.from_user
    status_msg = await message.reply_text("🔎 Processing URL...", quote=True)
    
    # 1. Try Direct Link Generator
    from bot.utils.direct_links import direct_link_generator
    direct_link = direct_link_generator(text)
    
    if direct_link:
        download_url = direct_link
        await status_msg.edit_text(f"✅ Direct Link Detected!\n`{download_url}`\n\nStarting download...")
    else:
        # Fallback to authentic URL (maybe direct or yt-dlp supported)
        download_url = text
        await status_msg.edit_text("ℹ️ Standard URL detected. Attempting to download...")

    # Download Logic
    try:
        user_dir = os.path.join(DOWNLOAD_DIR, str(user.id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Use generic downloader that supports progress
        from bot.utils.helpers import download_http_file
        
        file_path = await download_http_file(download_url, user_dir, status_msg, user_id=user.id)
        
        if not file_path:
             await status_msg.edit_text("❌ Failed to download file from URL.")
             return
        
        # Prepare for processing
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        user_data[user.id] = {
            'message_id': message.id,
            'file_name': file_name,
            'file_size': file_size,
            'file_path': file_path, # Local path now
            'processing_file': file_path, # Set this too
            'operation': None,
            # Init settings if not present
            'settings': user_data.get(user.id, {}).get('settings', {}),
        }

        info_text = (
            f"<b>📁 File Downloaded!</b>\n\n"
            f"<b>📄 Name:</b> <code>{file_name}</code>\n"
            f"<b>💾 Size:</b> {get_readable_file_size(file_size)}\n\n"
            f"<b>Select an operation from the menu below:</b>"
        )
        
        await status_msg.edit_text(
            info_text,
            reply_markup=main_menu(user.id)
        )

    except Exception as e:
        LOGGER.error(f"URL Download failed: {e}")
        await status_msg.edit_text(f"❌ Error downloading URL: {str(e)}")


async def download_file(message: Message, status_msg: Message, user_id: int = None) -> str:
    """Download file from message with progress"""
    user = message.from_user
    uid = user_id or user.id
    
    # Create user directory
    user_dir = os.path.join(DOWNLOAD_DIR, str(uid))
    os.makedirs(user_dir, exist_ok=True)
    
    # Get file name
    if message.video:
        file_name = message.video.file_name or f"video_{message.video.file_unique_id}.mp4"
    elif message.document:
        file_name = message.document.file_name
    elif message.audio:
        file_name = message.audio.file_name or f"audio_{message.audio.file_unique_id}.mp3"
    else:
        file_name = "unknown_file"
    
    file_path = os.path.join(user_dir, file_name)
    
    # Create progress with cancel button
    progress = Progress(status_msg, "📥 Downloading", user_id=uid, filename=file_name)
    
    # Store progress instance for cancellation
    if uid in user_data:
        user_data[uid]['progress'] = progress
    
    try:
        await message.download(
            file_name=file_path,
            progress=progress.progress_callback
        )
    except Exception as e:
        if progress.cancelled:
            raise asyncio.CancelledError("Cancelled by user")
        raise e
    
    return file_path


async def upload_file(client: Client, chat_id: int, file_path: str | list, status_msg: Message, caption: str = None, user_id: int = None):
    """Upload file with progress"""
    
    # Handle list of files (Media Group)
    if isinstance(file_path, list):
        from pyrogram.types import InputMediaPhoto
        media = []
        for f in file_path:
            # Assume photos for now (screenshots)
            media.append(InputMediaPhoto(f))
        
        await status_msg.edit_text("📤 Uploading album...")
        try:
            await client.send_media_group(chat_id, media)
        except Exception as e:
            await status_msg.edit_text(f"❌ Upload failed: {e}")
            raise e
        return

        return
    
    file_name = os.path.basename(file_path) if isinstance(file_path, str) else "Album"
    progress = Progress(status_msg, "📤 Uploading", user_id=user_id, filename=file_name)
    
    # Store progress for cancellation
    if user_id and user_id in user_data:
        user_data[user_id]['progress'] = progress
    
    file_size = 0  # Will be set below or calculated
    if isinstance(file_path, str):
         file_size = os.path.getsize(file_path)
         # file_name already set
    
    # Decide upload method based on file type
    video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
    ext = os.path.splitext(file_name)[1].lower()
    
    try:
        if ext in video_exts:
            await client.send_video(
                chat_id,
                file_path,
                caption=caption or f"✅ <code>{file_name}</code>",
                progress=progress.progress_callback
            )
        else:
            await client.send_document(
                chat_id,
                file_path,
                caption=caption or f"✅ <code>{file_name}</code>",
                progress=progress.progress_callback
            )
    except Exception as e:
        if progress.cancelled:
            raise asyncio.CancelledError("Cancelled by user")
        raise e
