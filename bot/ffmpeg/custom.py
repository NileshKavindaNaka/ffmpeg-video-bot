#!/usr/bin/env python3
"""Custom FFmpeg command execution"""

import shlex
from typing import Tuple
from bot.ffmpeg.core import FFmpeg

async def execute_custom_command(input_file: str, args: str, output_file: str) -> Tuple[bool, str]:
    """Execute custom FFmpeg arguments"""
    ffmpeg = FFmpeg(input_file, output_file)
    
    # Split arguments
    try:
        cmd_args = shlex.split(args)
    except Exception as e:
        return False, f"Invalid arguments: {e}"
    
    return await ffmpeg.run_ffmpeg(cmd_args)
