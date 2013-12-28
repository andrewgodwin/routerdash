import json
from django.shortcuts import render
from django.http import HttpResponse
from .calculations import get_speeds, get_devices


def json_response(data):
    return HttpResponse(json.dumps(data), content_type="application/json")


def home(request):
    return render(request, "dashboard.html")


def ajax_speeds(request):
    rx, tx = get_speeds("eth0")
    rx_string = "..." if rx is None else "%.02f Mb/s" % (rx / 125000.0)
    tx_string = "..." if tx is None else "%.02f Mb/s" % (tx / 125000.0)
    return json_response([rx, tx, rx_string, tx_string])


def ajax_devices(request):
    devices = get_devices("br0")
    devices = {"x": {"mac": "00:00:5e:00:01:8f", "name": "pikachu"}}
    return json_response(sorted(devices.values(), key=lambda x:x['mac']))
