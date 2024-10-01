from login import register_device
from magiogo import get_channels, get_stream, get_catchup

import os
from datetime import datetime

from bottle import route, redirect, response, request, template, run

catchup = ' catchup="append" catchup-source="?utc={utc}&utcend={utcend}",'

host, port = os.environ.get("HOST", "localhost:8888").split(":")
port = int(port)


@route("/service/playlist")
def magio_playlist():
    input_stream_ = ""
    ch = get_channels()
    t = ""
    for x, y in ch.items():
        t = (
            t
            + '#EXTINF:-1 provider="Magio GO" group-title="'
            + y["group"]
            + '" tvg-logo="'
            + y["logo"]
            + '"'
            + catchup
            + y["name"].replace(" HD", "")
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

print(f"Starting server on {host}:{port}")
run(host=host, port=port, reloader=False)
