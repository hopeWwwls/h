"""
آپلود فایل به imgurl.ir — با ۳ بار تلاش مجدد
"""

import os
import re
import time
import logging
import requests

logger = logging.getLogger(__name__)

UPLOAD_URL = "https://imgurl.ir/upload.php"
FIELD_NAME = "userfile[]"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android 16; Mobile; rv:153.0) Gecko/153.0 Firefox/153.0",
    "Accept": "*/*",
    "Accept-Language": "en-US",
    "Origin": "https://imgurl.ir",
    "Referer": "https://imgurl.ir/",
}


def _get_cookies() -> dict:
    session_val = os.environ.get("IMGURL_SESSION", "")
    if session_val:
        return {"mmh_user_session": session_val}
    return {}


def _upload_once(file_path: str) -> str:
    cookies = _get_cookies()
    file_name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        files = {FIELD_NAME: (file_name, f)}
        data = {"private_upload": "0"}
        resp = requests.post(
            UPLOAD_URL,
            headers=HEADERS,
            cookies=cookies,
            files=files,
            data=data,
            timeout=120,
        )
    resp.raise_for_status()
    html_text = resp.text
    match = re.search(r'https://cdn\.imgurl\.ir/uploads/([^"\s]+)', html_text)
    if not match:
        raise RuntimeError(f"لینک پیدا نشد. پاسخ:\n{html_text[:800]}")
    return match.group(0)


def upload_file(file_path: str, max_attempts: int = 3) -> str:
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            url = _upload_once(file_path)
            logger.info("upload ok (attempt %d): %s", attempt, url)
            return url
        except Exception as e:
            last_err = e
            logger.warning("upload attempt %d/%d failed: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(3 * attempt)
    raise last_err


def extract_variable(cdn_url: str) -> str:
    filename = cdn_url.split("/")[-1]
    return os.path.splitext(filename)[0]
