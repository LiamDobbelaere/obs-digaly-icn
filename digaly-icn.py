import obspython as obs
from urllib import request, parse
import json

audio_sources = {}
apiurl = "https://icn.diga.link/api"
params = parse.urlencode({"apikey": "SorrySugarNotEnoughCash"})
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
    "Accept-Encoding": "none",
    "Accept-Language": "en-US,en;q=0.8",
    "Connection": "keep-alive",
}
last_data = None


def script_description():
    return "Adds Digaly's ICN support"


def script_delayed_load():
    obs.timer_remove(script_delayed_load)

    global audio_sources

    audio_sources = {}
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            if not obs.obs_source_active(source):
                continue
            flags = obs.obs_source_get_output_flags(source)
            if flags & obs.OBS_SOURCE_AUDIO:
                name = obs.obs_source_get_name(source)
                audio_sources[name] = obs.obs_source_get_volume(source)

        obs.source_list_release(sources)
    print(audio_sources)
    print("Communicating with ICN")
    print(apiurl + "/audiodevices?" + params)
    data = parse.urlencode(audio_sources).encode("utf-8")
    req = request.Request(
        apiurl + "/audiodevices?" + params, data=data, headers=headers
    )
    try:
        request.urlopen(req)
    except Exception as e:
        print("Error during http request")
        print(e)
        return

    obs.timer_remove(update_volume_levels)
    obs.timer_add(update_volume_levels, 3000)


def update_volume_levels():
    global last_data

    print("Incoming ICN data")
    req = request.Request(apiurl + "/audiodevices?" + params, headers=headers)
    data = None
    try:
        data = request.urlopen(req)
    except Exception as e:
        print("Error during http request")
        print(e)
        return

    if data.status == 200:
        try:
            contents = data.read()
            jsonp = json.loads(contents)
            print(jsonp)

            if last_data != contents:
                print("Applying new audio settings")
                sources = obs.obs_enum_sources()
                if sources is not None:
                    for source in sources:
                        if not obs.obs_source_active(source):
                            continue
                        flags = obs.obs_source_get_output_flags(source)
                        name = obs.obs_source_get_name(source)
                        if flags & obs.OBS_SOURCE_AUDIO and name in jsonp:
                            print("Adjusting volume for source:")
                            print(name)
                            obs.obs_source_set_volume(source, float(jsonp[name]))

                    obs.source_list_release(sources)
                last_data = contents

        except Exception as e:
            print("Error parsing JSON")
            print(e)
    else:
        print("Status code not 200")
        print(data.status)


def script_load(settings):
    obs.timer_remove(script_delayed_load)
    obs.timer_add(script_delayed_load, 3000)
