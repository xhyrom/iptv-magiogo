# Taken from https://github.com/Saros72/IPTV-Web-Server/blob/main/providers/magio/magio.py

from datetime import datetime
import requests
import json
from urllib.parse import urlparse

from login import get_data, set_data

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
DEVICE_NAME = "hruska"
DEVICE_TYPE = "OTT_IPAD"


# Function to get the stream URL for a given channel ID
def get_stream(id):
    accesstoken, refreshtoken = get_data()
    params = {"refreshToken": refreshtoken}
    headers = {
        "Origin": "https://www.magiogo.sk",
        "Pragma": "no-cache",
        "Referer": "https://www.magiogo.sk/",
        "User-Agent": USER_AGENT,
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    # Request new tokens
    req = requests.post(
        "https://skgo.magio.tv/v2/auth/tokens", json=params, headers=headers
    ).json()
    if req["success"]:
        accesstoken = req["token"]["accessToken"]
        refreshtoken = req["token"]["refreshToken"]
        set_data({"accesstoken": accesstoken, "refreshtoken": refreshtoken})

        # Request stream URL
        params = {
            "service": "LIVE",
            "name": DEVICE_NAME,
            "devtype": DEVICE_TYPE,
            "id": int(id.split(".")[0]),
            "prof": "p5",
            "ecid": "",
            "drm": "verimatrix",
        }
        headers["authorization"] = "Bearer " + accesstoken
        req = requests.get(
            "https://skgo.magio.tv/v2/television/stream-url",
            params=params,
            headers=headers,
        ).json()

        if req["success"]:
            url = req["url"]
            headers = {
                "Host": urlparse(url).netloc,
                "User-Agent": "ReactNativeVideo/3.13.2 (Linux;Android 10) ExoPlayerLib/2.10.3",
                "Connection": "Keep-Alive",
            }
            req = requests.get(url, headers=headers, allow_redirects=False)
            return req.headers["location"]
        else:
            return "http://sledovanietv.sk/download/noAccess-sk.m3u8"
    else:
        return "http://sledovanietv.sk/download/noAccess-sk.m3u8"


# Function to get the list of channels
def get_channels():
    accesstoken, refreshtoken = get_data()
    params = {"refreshToken": refreshtoken}
    headers = {
        "Origin": "https://www.magiogo.sk",
        "Pragma": "no-cache",
        "Referer": "https://www.magiogo.sk/",
        "User-Agent": USER_AGENT,
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    # Request new tokens
    req = requests.post(
        "https://skgo.magio.tv/v2/auth/tokens", json=params, headers=headers
    ).json()
    if req["success"]:
        accesstoken = req["token"]["accessToken"]
        refreshtoken = req["token"]["refreshToken"]
        set_data({"accesstoken": accesstoken, "refreshtoken": refreshtoken})

    params = {"list": "LIVE", "queryScope": "LIVE"}
    headers["authorization"] = "Bearer " + accesstoken
    ch = {}

    try:
        # Get categories and channels
        req = requests.get(
            "https://skgo.magio.tv/home/categories?language=sk", headers=headers
        ).json()["categories"]
        categories = {c["channelId"]: cc["name"] for cc in req for c in cc["channels"]}

        req = requests.get(
            "https://skgo.magio.tv/v2/television/channels",
            params=params,
            headers=headers,
        ).json()["items"]
        for c in req:
            group = categories[c["channel"]["channelId"]]
            ch[str(c["channel"]["channelId"])] = {
                "name": c["channel"]["name"],
                "logo": c["channel"]["logoUrl"],
                "group": group,
            }
    except:
        pass

    return ch


def get_catchup(id, utc, utcend):
    # Extract the integer part of the ID
    id = int(id.split(".")[0])

    # Retrieve access and refresh tokens
    accesstoken, refreshtoken = get_data()
    params = {"refreshToken": refreshtoken}
    headers = {
        "Origin": "https://www.magiogo.sk",
        "Pragma": "no-cache",
        "Referer": "https://www.magiogo.sk/",
        "User-Agent": USER_AGENT,
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    # Request new tokens
    req = requests.post(
        "https://skgo.magio.tv/v2/auth/tokens", json=params, headers=headers
    ).json()

    if req["success"]:
        accesstoken = req["token"]["accessToken"]
        refreshtoken = req["token"]["refreshToken"]
        set_data({"accesstoken": accesstoken, "refreshtoken": refreshtoken})

        params = {
            "service": "ARCHIVE",
            "name": DEVICE_NAME,
            "devtype": DEVICE_TYPE,
            "id": id,
            "prof": "p5",
            "ecid": "",
            "drm": "verimatrix",
        }
        headers["authorization"] = "Bearer " + accesstoken

        # Format start and end times
        date_time_start = datetime.fromtimestamp(int(utc))
        d_start = date_time_start.strftime("%Y-%m-%dT%H:%M:%S")
        date_time_end = datetime.fromtimestamp(int(utcend) + 15)
        d_end = date_time_end.strftime("%Y-%m-%dT%H:%M:%S")

        # Request EPG data
        epg_url = (
            f"https://skgo.magio.tv/v2/television/epg?filter=channel.id=={id}"
            f"%20and%20startTime=ge={d_start}.000Z%20and%20endTime=le={d_end}.000Z&limit=10&offset=0&lang=SK"
        )
        req = requests.get(epg_url, params=params, headers=headers).json()

        if req["success"]:
            scheduleId = str(req["items"][0]["programs"][0]["scheduleId"])
            params["id"] = int(scheduleId)

            # Request stream URL
            stream_url = "https://skgo.magio.tv/v2/television/stream-url"
            req = requests.get(stream_url, params=params, headers=headers).json()

            if req["success"]:
                return req["url"]

    # Return fallback URL if any request fails
    return "http://sledovanietv.sk/download/noAccess-sk.m3u8"
