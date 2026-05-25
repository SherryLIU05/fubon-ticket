import requests
from bs4 import BeautifulSoup
import time

URL = "https://guardians.fami.life/PerformanceListControl?PRODUCT_ID=P15UU08Q"

CHECK_INTERVAL = 3

last_state = {}

def check_ticket():
    global last_state

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(URL, headers=headers, timeout=10)

    soup = BeautifulSoup(r.text, "html.parser")

    areas = soup.find_all("area")

    found = []

    current_state = {}

    for area in areas:
        title = area.get("title", "")

        if "輪椅" in title:
            continue

        remain = 0

        if "尚餘：" in title:
            try:
                remain = int(title.split("尚餘：")[1])
            except:
                pass

        current_state[title] = remain

        old = last_state.get(title, 0)

        if remain > 0 and old == 0:
            found.append(title)

    if found:
        print("🎟️ 有票釋出！")

        for f in found:
            print(f)

    else:
        print("checked")

    last_state = current_state


while True:
    try:
        check_ticket()
    except Exception as e:
        print("ERROR:", e)

    time.sleep(CHECK_INTERVAL)
