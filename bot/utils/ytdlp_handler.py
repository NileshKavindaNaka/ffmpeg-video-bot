#!/usr/bin/env python3
"""YT-DLP Handler with cookie support and better error handling"""

import os
import asyncio
import tempfile
import logging
from typing import Optional, Tuple

LOGGER = logging.getLogger(__name__)


async def get_cookies_path(user_id: int = None) -> Optional[str]:
    """
    Get cookies file path. Writes cookies from MongoDB to temp file if available.
    Returns None if no cookies are stored.
    """
    from bot.utils.db_handler import get_db
    db = get_db()
    if not db:
        return None
    
    try:
        # Try user-specific cookies first, then global
        cookies_data = await db.get_cookies(user_id) if user_id else None
        if not cookies_data:
            cookies_data = await db.get_cookies(0)  # Global cookies (user_id=0)
        
        if not cookies_data:
            return None
        
        # Write to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(cookies_data)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        LOGGER.error(f"Error getting cookies: {e}")
        return None


async def download_with_ytdlp(
    url: str,
    output_dir: str,
    user_id: int = None,
    status_msg=None,
    format_id: str = None
) -> Tuple[bool, str]:
    """
    Download video using yt-dlp with proper error handling and cookie support.
    
    Returns:
        Tuple[bool, str]: (success, file_path or error_message)
    """
    import glob
    
    # Prepare output template
    out_tpl = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    # Build command with simpler, more compatible options
    cmd = ["yt-dlp", "-o", out_tpl]
    
    # Add format selection - use simpler "best" for better compatibility
    if format_id:
        cmd.extend(["-f", format_id])
    else:
        # Simpler format selection that works better with age-restricted/geo-blocked
        cmd.extend(["-f", "best"])
    
    # Add cookies if available
    cookies_path = await get_cookies_path(user_id)
    if cookies_path:
        cmd.extend(["--cookies", cookies_path])
        LOGGER.info(f"Using cookies file for yt-dlp")
    
    # Add other useful options
    cmd.extend([
        "--no-playlist",      # Download single video
        "--no-warnings",
        "--no-check-certificates",  # Bypass SSL issues
        "--extractor-retries", "3",  # Retry failed extractions
        "--retries", "3",     # Retry failed downloads
        "--fragment-retries", "3",
        url
    ])
    
    try:
        if status_msg:
            cookie_status = "🍪" if cookies_path else "⚠️ No cookies"
            await status_msg.edit_text(
                f"🎬 <b>Downloading with yt-dlp...</b>\n"
                f"<code>{url[:50]}...</code>\n\n"
                f"{cookie_status}"
            )
        
        # Run yt-dlp
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        
        # Cleanup cookies temp file
        if cookies_path and os.path.exists(cookies_path):
            try:
                os.remove(cookies_path)
            except:
                pass
        
        # Get combined output for error checking
        output_text = stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')
        
        if proc.returncode == 0:
            # Find the downloaded file (newest file in output_dir)
            candidates = glob.glob(os.path.join(output_dir, "*"))
            if candidates:
                file_path = max(candidates, key=os.path.getmtime)
                # Check if file is not empty
                if os.path.getsize(file_path) > 0:
                    return True, file_path
                else:
                    os.remove(file_path)
                    return False, "⚠️ Downloaded file is empty. YouTube may require cookies.\n\nUse /cookies set to upload your cookies.txt file."
            else:
                return False, "Download completed but file not found"
        else:
            # Parse error message
            error_msg = output_text.strip()
            
            # Extract meaningful error
            if "Sign in to confirm your age" in error_msg:
                return False, "⚠️ Age-restricted video. Please provide cookies from a logged-in account using /cookies command."
            elif "Private video" in error_msg:
                return False, "⚠️ This is a private video."
            elif "Video unavailable" in error_msg:
                return False, "⚠️ Video is unavailable in your region or has been removed."
            elif "confirm you're not a bot" in error_msg or "Sign in" in error_msg:
                return False, "⚠️ YouTube requires authentication. Please upload cookies using /cookies command."
            elif "HTTP Error 429" in error_msg:
                return False, "⚠️ Too many requests. Please try again later."
            elif "Unsupported URL" in error_msg:
                return False, "⚠️ This URL is not supported by yt-dlp."
            elif "downloaded file is empty" in error_msg.lower() or "file is empty" in error_msg.lower():
                return False, "⚠️ YouTube blocked the download. Please upload cookies using /cookies command.\n\n<b>How to get cookies:</b>\n1. Install 'Get cookies.txt' extension in Chrome\n2. Go to YouTube and login\n3. Export cookies and upload with /cookies set"
            elif "no video formats" in error_msg.lower():
                return False, "⚠️ No downloadable formats found. The video may be protected or region-locked."
            else:
                # Return last few lines of error
                error_lines = error_msg.split('\n')
                # Filter out empty lines
                error_lines = [l for l in error_lines if l.strip()]
                short_error = '\n'.join(error_lines[-3:]) if len(error_lines) > 3 else error_msg
                return False, f"❌ yt-dlp error:\n<code>{short_error[:500]}</code>"
                
    except Exception as e:
        LOGGER.error(f"yt-dlp exception: {e}")
        return False, f"❌ Error running yt-dlp: {str(e)}"


async def get_video_info(url: str, user_id: int = None) -> Optional[dict]:
    """Get video info without downloading"""
    cmd = ["yt-dlp", "--dump-json", "--no-download", "--no-warnings", url]
    
    cookies_path = await get_cookies_path(user_id)
    if cookies_path:
        cmd.insert(1, "--cookies")
        cmd.insert(2, cookies_path)
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        
        if cookies_path and os.path.exists(cookies_path):
            try:
                os.remove(cookies_path)
            except:
                pass
        
        if proc.returncode == 0:
            import json
            return json.loads(stdout.decode('utf-8'))
    except Exception as e:
        LOGGER.error(f"Error getting video info: {e}")
    
    return None
