**IPTV Magiogo** is an IPTV service that provides a list of channels and EPG data directly from the [Magio Go](https://www.magiogo.sk/) website. \

### Requirements

[magiogo](https://magiogo.sk) \
[python3](https://www.python.org/) \
some IPTV player like [kodi](https://kodi.tv/)

### Installation

You can install and run the service using [docker compose](./docker-compose.yml). \
Don't forget to update environment variables!

However, if you want to run it outside docker, install packages from [requirements.txt](./requirements.txt) and run <kbd>[src/main.py](./src/main.py)</kbd> with the following environment variables:
`MAGIO_USERNAME, MAGIO_PASSWORD, HOST`

```bash
$ pip install -r requirements.txt
$ MAGIO_USERNAME=hello MAGIO_PASSWORD=asd HOST=localhost:4589 python src/main.py
```

### Routes

- `/` - list of channels (viewable in browser)
- `/service/playlist` - m3u playlist
- `/service/epg` - epg data (xmltv format)
