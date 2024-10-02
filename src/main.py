from login import register_device
from magiogo import get_channels, get_stream, get_catchup, get_epg
from common import parse_season_number

import os
import xmltv
from datetime import datetime, timedelta

from bottle import route, redirect, response, request, template, run

catchup = ' catchup="append" catchup-source="?utc={utc}&utcend={utcend}",'

host, port = os.environ.get("HOST", "0.0.0.0:4589").split(":")
port = int(port)


@route("/service/playlist")
def magio_playlist():
    input_stream_ = "#KODIPROP:inputstream=inputstream.ffmpegdirect\n#KODIPROP:mimetype=application/x-mpegURL\n#KODIPROP:inputstream.ffmpegdirect.stream_mode=timeshift\n#KODIPROP:inputstream.ffmpegdirect.is_realtime_stream=true\n"
    ch = get_channels()
    t = ""
    for x, y in ch.items():
        t = (
            t
            + '#EXTINF:-1 provider="Magio GO" group-title="'
            + y["group"]
            + '" tvg-id="'
            + str(x)
            + '" tvg-logo="'
            + y["logo"]
            + '"'
            + catchup
            + y["name"]
            + "\n"
            + input_stream_
            + "http://"
            + str(host)
            + ":"
            + str(port)
            + "/service/"
            + str(x)
            + ".m3u8\n"
        )
    if t != "":
        t = "#EXTM3U\n" + t
    response.content_type = "text/plain; charset=UTF-8"
    return t


@route("/service/epg")
def magio_epg():
    if os.path.exists(".epg.xmltv") and os.path.getsize(".epg.xmltv") > 0:
        if (
            datetime.now() - datetime.fromtimestamp(os.path.getmtime(".epg.xmltv"))
        ).days < 7:
            response.content_type = "application/octet-stream"
            response.headers["Content-Disposition"] = "inline; filename=epg.xmltv"
            return open(".epg.xmltv", "r").read()

    date_from = datetime.now() - timedelta(days=0)
    date_to = datetime.now() + timedelta(days=7)

    channels = get_channels()
    channel_ids = list(channels.keys())
    epg = get_epg(channel_ids, date_from, date_to)

    writer = xmltv.Writer(
        date=datetime.now().strftime("%Y%m%d%H%M%S"),
        generator_info_name="MagioGoIPTVServer",
        generator_info_url="",
        source_info_name="Magio GO Guide",
        source_info_url="https://skgo.magio.tv/v2/television/epg",
    )

    for id, channel in channels.items():
        channel_dict = {
            "display-name": [(channel["name"], "sk")],
            "icon": [{"src": channel["logo"]}],
            "id": id,
        }
        writer.addChannel(channel_dict)

    for channel_id, programmes in epg.items():
        for programme in programmes:
            programme_dict = {
                "category": [(genre, "en") for genre in programme.genres],
                "channel": channel_id,
                "credits": {
                    "producer": [producer for producer in programme.producers],
                    "actor": [actor for actor in programme.actors],
                    "writer": [writer for writer in programme.writers],
                    "director": [director for director in programme.directors],
                },
                "date": str(programme.year),
                "desc": [(programme.description, "")],
                "icon": [{"src": programme.poster}, {"src": programme.thumbnail}],
                "length": {"units": "seconds", "length": str(programme.duration)},
                "start": programme.start_time.strftime("%Y%m%d%H%M%S"),
                "stop": programme.end_time.strftime("%Y%m%d%H%M%S"),
                "title": [(programme.title, "")],
            }

            # Define episode info only if provided
            if programme.episodeNo is not None:
                # Since seasonNo seems to be always null, try parsing the season from the title (e.g. Kosti X. = 10)
                if programme.seasonNo is None:
                    (show_title_sans_season, programme.seasonNo) = parse_season_number(
                        programme.title
                    )
                    programme_dict["title"] = [(show_title_sans_season, "")]

                programme_dict["episode-num"] = [
                    (
                        f"{(programme.seasonNo or 1) - 1} . {(programme.episodeNo or 1) - 1} . 0",
                        "xmltv_ns",
                    )
                ]

            writer.addProgramme(programme_dict)

    writer.write(".epg.xmltv", True)

    response.content_type = "application/octet-stream"
    response.headers["Content-Disposition"] = "inline; filename=epg.xmltv"
    return open(".epg.xmltv", "r").read()


@route("/")
def magio_list():
    names = []
    info: dict = {"title": "Magio GO"}
    ch = get_channels()
    for x, y in ch.items():
        names.append(("/service/" + str(x) + ".m3u8", y["name"].replace(" HD", "")))
    info["names"] = names
    return template("./templates/links.tpl", info)


@route("/service/<id>")
def magio_play(id):
    print(f"Playing {id}")
    if "utc" in request.query_string:
        if "utcend" in request.query_string:
            end = request.query["utcend"]
        else:
            now = int(datetime.now().timestamp())
            end = int(request.query["utc"]) + 10800
            if end > now:
                end = now - 60
        try:
            stream = get_catchup(id, request.query["utc"], str(end))
        except:
            stream = get_stream(id)
    else:
        stream = get_stream(id)
    response.content_type = "application/dash+xml"
    return redirect(stream)


print("Registering device")
register_device()

print("Starting server on 0.0.0.0:4589")
run(host="0.0.0.0", port=4589, reloader=False)
