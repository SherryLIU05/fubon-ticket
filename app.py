import os
import re
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# LINE TOKEN
# =========================

LINE_TOKEN = "你的LINE_NOTIFY_TOKEN"

# =========================
# 富邦售票頁
# =========================

URL = (
    "https://guardians.fami.life/"
    "UTK0204_?PERFORMANCE_ID=P19MQCN0&PRODUCT_ID=P15UU08Q"
)

CHECK_INTERVAL = 5

BLOCK_KEYWORDS = [
    "輪椅",
    "wheelchair"
]

last_state = set()

# =========================
# Session + Retry
# =========================

session = requests.Session()

retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("https://", adapter)
session.mount("http://", adapter)

# =========================


def notify(msg):

    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}"
    }

    data = {
        "message": msg
    }

    try:

        requests.post(
            "https://notify-api.line.me/api/notify",
            headers=headers,
            data=data,
            timeout=10
        )

    except Exception as e:

        print("LINE ERROR:", e)


def fetch_html():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64)"
        ),
        "Connection": "close",
        "Cache-Control": "no-cache"
    }

    r = session.get(
        URL,
        headers=headers,
        timeout=20
    )

    print("status =", r.status_code)

    return r.text


def parse_ticket(html):

    soup = BeautifulSoup(html, "html.parser")

    areas = soup.find_all("area")

    found = []

    for area in areas:

        title = area.get("title", "")

        if not title:
            continue

        try:
            title = title.encode("latin1").decode("utf-8")
        except:
            pass

        # 排除輪椅席
        blocked = False

        for b in BLOCK_KEYWORDS:

            if b in title:
                blocked = True
                break

        if blocked:
            continue

        # 找剩餘票數
        match = re.search(r"尚餘：(\d+)", title)

        if not match:
            continue

        remain = int(match.group(1))

        if remain > 0:

            area_match = re.search(r"票區:(.*?)\s", title)

            area_name = (
                area_match.group(1)
                if area_match
                else "未知區域"
            )

            found.append({
                "area": area_name,
                "remain": remain
            })

    return found


def main():

    global last_state

    print("watcher started")

    while True:

        try:

            html = fetch_html()

            available = parse_ticket(html)

            current_state = set()

            for item in available:
                current_state.add(item["area"])

            new_areas = current_state - last_state

            if new_areas:

                lines = []

                for item in available:

                    if item["area"] in new_areas:

                        lines.append(
                            f'{item["area"]} 剩 {item["remain"]} 張'
                        )

                msg = (
                    "⚾ 富邦 vs 中信 有票釋出！\n\n"
                    + "\n".join(lines)
                )

                notify(msg)

                print("NOTIFIED")

            last_state = current_state

            print("checked")

        except Exception as e:

            print("ERROR:", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
