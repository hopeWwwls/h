"""
ارسال پیامک از sms.ir — با ۳ بار تلاش مجدد
"""

import os
import time
import logging
import requests

logger = logging.getLogger(__name__)


def send_sms(text: str, max_attempts: int = 3) -> tuple:
    api_key     = os.environ["SMS_API_KEY"]
    line_number = os.environ["SMS_LINE_NUMBER"]
    target      = os.environ["TARGET_PHONE"]

    url = "https://api.sms.ir/v1/send/bulk"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": api_key,
    }
    payload = {
        "lineNumber": line_number,
        "messageText": text,
        "mobiles": [target],
        "sendDateTime": None,
    }

    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            try:
                data = r.json()
            except Exception:
                data = {"raw": r.text}
            logger.info("SMS attempt %d: %s %s", attempt, r.status_code, data)
            if r.status_code == 200:
                return r.status_code, data
            last_err = Exception(f"HTTP {r.status_code}: {data}")
        except Exception as e:
            last_err = e
            logger.warning("SMS attempt %d/%d failed: %s", attempt, max_attempts, e)
        if attempt < max_attempts:
            time.sleep(2 * attempt)

    logger.error("SMS failed after %d attempts: %s", max_attempts, last_err)
    return None, {"error": str(last_err)}
