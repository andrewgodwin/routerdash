import json
from django.shortcuts import render
from django.http import HttpResponse
from .calculations import get_speeds, get_devices


def json_response(data):
    return HttpResponse(json.dumps(data), content_type="application/json")


def human_speed(raw_speed):
    return "..." if raw_speed is None else "%.02f Mb/s" % (raw_speed / 125000.0)


def home(request):
    return render(request, "dashboard.html")


def ajax_speeds(request):
    rx, tx = get_speeds("eth0")
    rx_string = human_speed(rx)
    tx_string = human_speed(tx)
    return json_response([rx, tx, rx_string, tx_string])


def ajax_devices(request):
    devices = get_devices("br0")
    response = []
    for device in devices.values():
        if "rx_speed" in device:
            device["rx_speed_human"] = human_speed(device["rx_speed"])
        if "tx_speed" in device:
            device["tx_speed_human"] = human_speed(device["tx_speed"])
        response.append(device)
    return json_response(sorted(response, key=lambda x: x['name']))
