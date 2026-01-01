
import re
import urllib.parse
from base64 import standard_b64encode
from random import choice
from typing import Optional

import cloudscraper
import lk21
import requests
from bs4 import BeautifulSoup
import logging

LOGGER = logging.getLogger(__name__)

class DirectDownloadLinkException(Exception):
    pass

def direct_link_generator(text_url: str) -> Optional[str]:
    """ 
    Direct links generator 
    Ports logic from reference bot
    """
    if 'youtube.com' in text_url or 'youtu.be' in text_url:
        # We handle YouTube separately via yt-dlp
        return None
        
    try:
        if 'zippyshare.com' in text_url:
            return zippy_share(text_url)
        elif 'yadi.sk' in text_url:
            return yandex_disk(text_url)
        elif 'cloud.mail.ru' in text_url:
            return cm_ru(text_url)
        elif 'mediafire.com' in text_url:
            return mediafire(text_url)
        elif 'osdn.net' in text_url:
            return osdn(text_url)
        elif 'github.com' in text_url:
            return github(text_url)
        elif 'hxfile.co' in text_url:
            return hxfile(text_url)
        elif 'anonfiles.com' in text_url:
            return anonfiles(text_url)
        elif 'letsupload.io' in text_url:
            return letsupload(text_url)
        elif 'fembed.net' in text_url or 'fembed.com' in text_url or 'femax20.com' in text_url or 'fcdn.stream' in text_url or 'feurl.com' in text_url:
            return fembed(text_url)
        elif 'sbembed.com' in text_url or 'streamsb.net' in text_url or 'sbplay.org' in text_url:
            return sbembed(text_url)
        elif '1drv.ms' in text_url:
            return onedrive(text_url)
        elif 'pixeldrain.com' in text_url:
            return pixeldrain(text_url)
        elif 'antfiles.com' in text_url:
            return antfiles(text_url)
        elif 'streamtape.com' in text_url:
            return streamtape(text_url)
        elif '1fichier.com' in text_url:
            return fichier(text_url)
        elif 'solidfiles.com' in text_url:
            return solidfiles(text_url)
        else:
            return None # Not supported by custom logic, maybe try generic or yt-dlp
    except Exception as e:
        LOGGER.error(f"DDL Generation failed for {text_url}: {e}")
        return None


def zippy_share(url: str) -> str:
    # Note: Zippyshare is mostly dead but keeping legacy support just in case
    try:
        link = re.findall("https:/.(.*?).zippyshare", url)[0]
        response_content = (requests.get(url)).content
        bs_obj = BeautifulSoup(response_content, "lxml")
        js_script = bs_obj.find("div", {"class": "center", }).find_all("script")[1]
        js_content = re.findall(r'\.href.=."/(.*?)";', str(js_script))
        js_content = 'var x = "/' + js_content[0] + '"'
        # Simple eval without js2py if possible, or use simplified logic
        # For now, placeholder as Zippyshare is down
        return None
    except Exception:
        return None

def yandex_disk(url: str) -> str:
    try:
        text_url = re.findall(r'\bhttps?://.*yadi\.sk\S+', url)[0]
    except IndexError:
        return None
    api = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}'
    try:
        dl_url = requests.get(api.format(text_url)).json()['href']
        return dl_url
    except KeyError:
        return None

def cm_ru(url: str) -> str:
    # Requires external script usually, skipping for now unless critical
    return None

def mediafire(url: str) -> str:
    try:
        text_url = re.findall(r'\bhttps?://.*mediafire\.com\S+', url)[0]
    except IndexError:
        return None
    page = BeautifulSoup(requests.get(text_url).content, 'lxml')
    info = page.find('a', {'aria-label': 'Download file'})
    return info.get('href')

def osdn(url: str) -> str:
    osdn_link = 'https://osdn.net'
    try:
        text_url = re.findall(r'\bhttps?://.*osdn\.net\S+', url)[0]
    except IndexError:
        return None
    page = BeautifulSoup(requests.get(text_url, allow_redirects=True).content, 'lxml')
    info = page.find('a', {'class': 'mirror_link'})
    text_url = urllib.parse.unquote(osdn_link + info['href'])
    mirrors = page.find('form', {'id': 'mirror-select-form'}).findAll('tr')
    urls = []
    for data in mirrors[1:]:
        mirror = data.find('input')['value']
        urls.append(re.sub(r'm=(.*)&f', f'm={mirror}&f', text_url))
    return urls[0]

def github(url: str) -> str:
    try:
        text_url = re.findall(r'\bhttps?://.*github\.com.*releases\S+', url)[0]
    except IndexError:
        return None
    download = requests.get(text_url, stream=True, allow_redirects=False)
    try:
        return download.headers["location"]
    except KeyError:
        return None

def onedrive(link: str) -> str:
    link_without_query = urllib.parse.urlparse(link)._replace(query=None).geturl()
    direct_link_encoded = str(standard_b64encode(bytes(link_without_query, "utf-8")), "utf-8")
    direct_link1 = f"https://api.onedrive.com/v1.0/shares/u!{direct_link_encoded}/root/content"
    resp = requests.head(direct_link1)
    if resp.status_code != 302:
        return None
    return resp.next.url

def hxfile(url: str) -> str:
    try:
        bypasser = lk21.Bypass()
        return bypasser.bypass_filesIm(url)
    except: return None

def anonfiles(url: str) -> str:
    try:
        bypasser = lk21.Bypass()
        return bypasser.bypass_anonfiles(url)
    except: return None

def letsupload(url: str) -> str:
    try:
        link = re.findall(r'\bhttps?://.*letsupload\.io\S+', url)[0]
        bypasser = lk21.Bypass()
        return bypasser.bypass_url(link)
    except: return None

def fembed(link: str) -> str:
    try:
        bypasser = lk21.Bypass()
        dl_url = bypasser.bypass_fembed(link)
        # Return highest quality
        if isinstance(dl_url, dict):
            # Sort keys implies quality?
            return dl_url[max(dl_url.keys())] # Assuming keys are resolution or similar
        return dl_url
    except: return None

def sbembed(link: str) -> str:
    try:
        bypasser = lk21.Bypass()
        dl_url = bypasser.bypass_sbembed(link)
        if isinstance(dl_url, dict):
             return dl_url[max(dl_url.keys())]
        return dl_url
    except: return None

def pixeldrain(url: str) -> str:
    url = url.strip("/ ")
    file_id = url.split("/")[-1]
    info_link = f"https://pixeldrain.com/api/file/{file_id}/info"
    dl_link = f"https://pixeldrain.com/api/file/{file_id}"
    resp = requests.get(info_link).json()
    if resp.get("success"):
        return dl_link
    return None

def antfiles(url: str) -> str:
    try:
        bypasser = lk21.Bypass()
        return bypasser.bypass_antfiles(url)
    except: return None

def streamtape(url: str) -> str:
    try:
        bypasser = lk21.Bypass()
        return bypasser.bypass_streamtape(url)
    except: return None

def fichier(link: str) -> str:
    # 1Fichier requires more complex handling, simplified check
    regex = r"^([http:\/\/|https:\/\/]+)?.*1fichier\.com\/\?.+"
    if not re.match(regex, link):
        return None
    # Very basic scraping attempt
    try:
        req = requests.post(link)
        soup = BeautifulSoup(req.content, 'lxml')
        if soup.find("a", {"class": "ok btn-general btn-orange"}) is not None:
             return soup.find("a", {"class": "ok btn-general btn-orange"})["href"]
    except: pass
    return None

def solidfiles(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        pageSource = requests.get(url, headers=headers).text
        mainOptions = str(re.search(r'viewerOptions\'\,\ (.*?)\)\;', pageSource).group(1))
        import json
        dl_url = json.loads(mainOptions)["downloadUrl"]
        return dl_url
    except: return None
