# Taken from https://github.com/Saros72/IPTV-Web-Server/blob/main/providers/magio/login.py

import requests
import os
import json
import sys

# Constants
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
DEVICE_ID = "ab2731523db7"
DEVICE_NAME = "hruska"
DEVICE_TYPE = "OTT_IPAD"


def set_data(data):
    """Save data to a JSON file."""
    json_object = json.dumps(data, indent=4)
    with open(".magio_token.json", "w") as outfile:
        outfile.write(json_object)


def get_data():
    try:
        with open(".magio_token.json", "r") as openfile:
            data = json.load(openfile)
        accesstoken = data["accesstoken"]
        refreshtoken = data["refreshtoken"]
    except:
        accesstoken = ""
        refreshtoken = ""
    return accesstoken, refreshtoken


def login():
    """Log in to the service and return access and refresh tokens."""
    # Initial request parameters and headers
    params = {
        "dsid": DEVICE_ID,
        "deviceName": DEVICE_NAME,
        "deviceType": DEVICE_TYPE,
        "osVersion": "18.0",
        "appVersion": "4.0.18",
        "language": "SK",
    }
    headers = {
        "Origin": "https://www.magiogo.sk",
        "Pragma": "no-cache",
        "Referer": "https://www.magiogo.sk/",
        "User-Agent": USER_AGENT,
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    # Initial authentication request
    response = requests.post(
        "https://skgo.magio.tv/v2/auth/init", params=params, headers=headers
    ).json()
    access_token = response["token"]["accessToken"]

    # Login request parameters and headers
    login_params = {
        "loginOrNickname": os.environ["MAGIO_USERNAME"],
        "password": os.environ["MAGIO_PASSWORD"],
    }
    login_headers = {
        "authorization": "Bearer " + access_token,
        "Origin": "https://www.magiogo.sk",
        "Pragma": "no-cache",
        "Referer": "https://www.magiogo.sk/",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": USER_AGENT,
    }

    # Login request
    login_response = requests.post(
        "https://skgo.magio.tv/v2/auth/login", json=login_params, headers=login_headers
    ).json()

    if login_response["success"]:
        return login_response["token"]["accessToken"], login_response["token"][
            "refreshToken"
        ]
    else:
        print(login_response["errorMessage"])
        return "", ""


def register_device():
    """Register the device and save the tokens."""
    access_token, refresh_token = login()
    if not access_token:
        sys.exit(1)

    # Fetch channel ID
    params = {"list": "LIVE", "queryScope": "LIVE"}
    headers = {
        "authorization": "Bearer " + access_token,
        "Origin": "https://www.magiogo.sk",
        "Pragma": "no-cache",
        "Referer": "https://www.magiogo.sk/",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": USER_AGENT,
    }
    response = requests.get(
        "https://skgo.magio.tv/v2/television/channels", params=params, headers=headers
    ).json()
    channel_id = response["items"][0]["channel"]["channelId"]

    # Request stream URL
    stream_params = {
        "service": "LIVE",
        "name": DEVICE_NAME,
        "devtype": "OTT_IPAD",
        "id": channel_id,
        "prof": "p5",
        "ecid": "",
        "drm": "verimatrix",
    }
    stream_response = requests.get(
        "https://skgo.magio.tv/v2/television/stream-url",
        params=stream_params,
        headers=headers,
    ).json()

    if stream_response["success"]:
        access_token, refresh_token = login()
        set_data({"accesstoken": access_token, "refreshtoken": refresh_token})

        print("Login successful")
    else:
        print(
            stream_response["errorMessage"].replace(
                "exceeded-max-device-count", "Exceeded maximum device count"
            )
        )
