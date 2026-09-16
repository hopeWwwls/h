"""
آپلود فایل به uploadkon.ir — آپلودر پشتیبان برای زمانی که imgurl.ir در دسترس نباشد.
"""

import json
import os
import re
import time
import logging
import requests

logger = logging.getLogger(__name__)

UPLOAD_URL = "https://uploadkon.ir/"
FIELD_NAME = "file"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android 16; Mobile; rv:153.0) Gecko/153.0 Firefox/153.0",
    "Accept": "*/*",
    "Accept-Language": "en-US",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://uploadkon.ir",
    "Referer": "https://uploadkon.ir/",
}

_LINK_RE = re.compile(r'id="image1"[^>]*>(https://uploadkon\.ir/uploads/[^<]+)<')
_FALLBACK_LINK_RE = re.compile(r'https://uploadkon\.ir/uploads/(?!thumbs/)([^"\\<\s]+)')


def _upload_once(file_path: str) -> str:
    file_name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        files = {FIELD_NAME: (file_name, f)}
        data = {"submitr": "1", "ajax": "1"}
        resp = requests.post(
            UPLOAD_URL,
            headers=HEADERS,
            files=files,
            data=data,
            timeout=120,
        )
    resp.raise_for_status()
    raw_text = resp.text

    message_content = raw_text
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list) and parsed:
            message_content = parsed[0].get("message_content") or parsed[0].get("i") or raw_text
    except (ValueError, TypeError, AttributeError, IndexError):
        pass

    match = _LINK_RE.search(message_content) or _FALLBACK_LINK_RE.search(message_content)
    if not match:
        raise RuntimeError(f"لینک پیدا نشد. پاسخ:\n{raw_text[:800]}")
    return match.group(0) if match.re is _LINK_RE else f"https://uploadkon.ir/uploads/{match.group(1)}"


def upload_file(file_path: str, max_attempts: int = 3) -> str:
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            url = _upload_once(file_path)
            logger.info("uploadkon upload ok (attempt %d): %s", attempt, url)
            return url
        except Exception as e:
            last_err = e
            logger.warning("uploadkon upload attempt %d/%d failed: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(3 * attempt)
    raise last_err


def extract_variable(cdn_url: str) -> str:
    filename = cdn_url.split("/")[-1]
    return os.path.splitext(filename)[0]
