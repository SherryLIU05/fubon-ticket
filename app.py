import re
import time
import requests

from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =====================================
# 富邦售票頁
# =====================================

URL = (
    "https://guardians.fami.life/"
    "UTK0204_?PERFORMANCE_ID=P19MQCN0&PRODUCT_ID=P15UU08Q"
)

# 幾秒檢查一次
CHECK_INTERVAL = 5

# 排除關鍵字
BLOCK_KEYWORDS = [
    "輪椅",
    "wheelchair"
]

# 上一次已通知區域
last_state = set()

# =====================================
# Session Retry
# =====================================

session = requests.Session()

retry = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("https://", adapter)
session.mount("http://", adapter)

# =====================================


def fetch_html():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "close"
    }

    response = session.get(
        URL,
        headers=headers,
        timeout=20
    )

    print("status =", response.status_code)

    return response.text


def parse_ticket(html):

    soup = BeautifulSoup(html, "html.parser")

    areas = soup.find_all("area")

    found = []

    for area in areas:

        title = area.get("title", "")

        if not title:
            continue

        # 修正中文亂碼
        try:
            title = title.encode("latin1").decode("utf-8")
        except:
            pass

        # 排除輪椅席
        blocked = False

        for keyword in BLOCK_KEYWORDS:

            if keyword.lower() in title.lower():
                blocked = True
                break

        if blocked:
            continue

        # 找剩餘票數
        remain_match = re.search(r"尚餘：(\d+)", title)

        if not remain_match:
            continue

        remain = int(remain_match.group(1))

        # 有票
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

    print("================================")
    print("⚾ 富邦悍將搶票監控啟動")
    print("================================")

    while True:

        try:

            html = fetch_html()

            available = parse_ticket(html)

            current_state = set()

            for item in available:
                current_state.add(item["area"])

            # 新釋出票區
            new_areas = current_state - last_state

            # 有新票
            if new_areas:

                print("\n")
                print("================================")
                print("🚨🚨🚨 有票釋出啦！！！ 🚨🚨🚨")
                print("================================")

                for item in available:

                    if item["area"] in new_areas:

                        print(
                            f'🎫 {item["area"]} '
                            f'剩 {item["remain"]} 張'
                        )

                print("\n搶票網址：")
                print(URL)

                print("================================")
                print("\n")

            else:

                print("checked - 無票")

            last_state = current_state

        except Exception as e:

            print("ERROR:", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
