# Taken from https://github.com/Saros72/IPTV-Web-Server/blob/main/providers/magio/magio.py

from datetime import datetime, timedelta
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


def get_epg(channels, from_date, to_date):
    from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
    to_date = to_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    now = datetime.utcnow()

    days = int((to_date - from_date).days)

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

    headers["authorization"] = "Bearer " + accesstoken

    result = {}

    for n in range(days):
        current_day = from_date + timedelta(n)

        filter = "startTime=ge=%sT00:00:00.000Z;startTime=le=%sT00:59:59.999Z" % (
            current_day.strftime("%Y-%m-%d"),
            (current_day + timedelta(days=1)).strftime("%Y-%m-%d"),
        )

        fetch_more = True
        offset = 0
        while fetch_more:
            params = {
                "name": DEVICE_NAME,
                "devtype": DEVICE_TYPE,
                "id": id,
                "prof": "p5",
                "ecid": "",
                "drm": "verimatrix",
                "lang": "SK",
                "offset": offset * 20,
                "list": "LIVE",
                "filter": filter,
            }

            # Request EPG
            req = requests.get(
                "https://skgo.magio.tv/v2/television/epg",
                params=params,
                headers=headers,
            ).json()

            fetch_more = len(req["items"]) == 20
            offset = offset + 1

            for i in req["items"]:
                for p in i["programs"]:
                    channel = str(p["channel"]["id"])

                    if channel not in channels:
                        continue

                    if channel not in result:
                        result[channel] = []

                    programme = _programme_data(p["program"])
                    programme.start_time = datetime.utcfromtimestamp(
                        p["startTimeUTC"] / 1000
                    )
                    programme.end_time = datetime.utcfromtimestamp(
                        p["endTimeUTC"] / 1000
                    )
                    programme.duration = p["duration"]
                    programme.is_replyable = (
                        programme.start_time > (now - timedelta(days=7))
                    ) and (programme.end_time < now)

                    result[channel].append(programme)

    return result


class Base:
    def __repr__(self):
        return str(self.__dict__)


class Programme(Base):
    def __init__(self):
        self.id = ""  # type: str
        # Programme Start Time in UTC
        self.start_time = None  # type: datetime or None
        # Programme End Time in UTC
        self.end_time = None  # type: datetime or None
        self.title = ""
        self.description = ""
        self.thumbnail = ""
        self.poster = ""
        self.duration = 0
        self.genres = []  # type: List[str]
        self.actors = []  # type: List[str]
        self.directors = []  # type: List[str]
        self.writers = []  # type: List[str]
        self.producers = []  # type: List[str]
        self.seasonNo = None
        self.episodeNo = None
        self.year = None  # type: int or None
        self.is_replyable = False
        # programme metadata
        self.metadata = {}  # type: Dict[str, int]


def _programme_data(pi):
    def safe_int(value, default=None):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    programme = Programme()
    programme.id = pi["programId"]
    programme.title = pi["title"]
    programme.description = "%s\n%s" % (
        pi["episodeTitle"] or "",
        pi["description"] or "",
    )

    pv = pi["programValue"]
    if pv["episodeId"] is not None:
        programme.episodeNo = safe_int(pv["episodeId"])
    if pv["seasonNumber"] is not None:
        programme.seasonNo = safe_int(pv["seasonNumber"])
    if pv["creationYear"] is not None:
        programme.year = safe_int(pv["creationYear"])
    for i in pi["images"]:
        programme.thumbnail = i
        break
    for i in pi["images"]:
        if "_VERT" in i:
            programme.poster = i
            break
    for d in pi["programRole"]["directors"]:
        programme.directors.append(d["fullName"])
    for a in pi["programRole"]["actors"]:
        programme.actors.append(a["fullName"])
    if pi["programCategory"] is not None:
        for c in pi["programCategory"]["subCategories"]:
            programme.genres.append(c["desc"])

    return programme
