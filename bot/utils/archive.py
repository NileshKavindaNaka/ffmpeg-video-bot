
import os
import shutil
import asyncio
import logging
import time

LOGGER = logging.getLogger(__name__)

async def extract_archive(file_path: str, output_dir: str, password: str = None) -> bool:
    """
    Extract archive to output_dir
    Supports zip, tar, and others via shutil or external tools if available
    """
    try:
        # Check if 7z is available (preferred for everything including rar)
        has_7z = shutil.which('7z')
        
        if has_7z:
            cmd = ['7z', 'x', f'-o{output_dir}', file_path, '-y']
            if password:
                cmd.append(f'-p{password}')
                
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True
            else:
                LOGGER.error(f"7z extraction failed: {stderr.decode()}")
                # Fallback to shutil if 7z failed (maybe it's not a 7z supported format? unlikely)
                
        # Fallback to shutil for standard formats (zip, tar)
        # shutil doesn't support password
        if password:
             LOGGER.error("Password provided but 7z not available/failed. Shutil cannot handle passwords.")
             return False
             
        shutil.unpack_archive(file_path, output_dir)
        return True
        
    except Exception as e:
        LOGGER.error(f"Extraction failed: {e}")
        return False

async def create_archive(input_path: str, output_path: str, type: str = "zip", password: str = None) -> str:
    """
    Create archive from input_path
    type: zip, tar, 7z
    """
    try:
        # Check if 7z available
        has_7z = shutil.which('7z')
        
        if has_7z and (password or type == '7z'):
            # Use 7z
            if not output_path.endswith(f".{type}"):
                 output_path += f".{type}"
            
            cmd = ['7z', 'a', text_type_map(type), output_path, input_path]
            if password:
                cmd.append(f'-p{password}')
                cmd.append('-mhe=on') # Encrypt headers too
                
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode == 0:
                return output_path
                
        # Shutil fallback
        base_name = os.path.splitext(output_path)[0]
        # shutil types: zip, tar, gztar, bztar, xztar
        if type == '7z': type = 'zip' # Fallback
        
        created_path = shutil.make_archive(base_name, type, input_path)
        return created_path
        
    except Exception as e:
        LOGGER.error(f"Archiving failed: {e}")
        return None

def text_type_map(t):
    if t == '7z': return '-t7z'
    if t == 'zip': return '-tzip'
    if t == 'tar': return '-ttar'
    return '-tzip'
