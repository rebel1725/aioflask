#!/bin/python3
from datetime import datetime, timezone
from flask import Flask, render_template, request
from math import ceil
import json
import re
import tomllib

app = Flask(__name__)

HEX_COLOUR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


with open("config.toml", "rb") as config_file:
    config = tomllib.load(config_file)


def colour0to255(x):
    return max(0, ceil(256 * x) - 1)


def colourstring(r, g, b):
    return "#" + hex(0x1000000 + r * 0x10000 + g * 0x100 + b)[3:]


def generate_colour(vr, sr):
    BR = 1 if sr < 0.5 else 2 * (1 - sr)
    BG = 2 * sr if sr < 0.5 else 1
    R = 0.5 + (BR - 0.5) * vr
    G = 0.5 + (BG - 0.5) * vr
    B = 0.5 - 0.5 * vr
    r = colour0to255(R)
    g = colour0to255(G)
    b = colour0to255(B)
    return colourstring(r, g, b)


def generate_bar(title, count, values, basetime):
    now = datetime.now(timezone.utc)
    minute = int((now - basetime).total_seconds() // 60)
    timerange = list(range(minute - count, minute))
    colours_base = [0] * count * 100
    totalvalid = 0
    totalsuccess = 0
    for j1, i1 in enumerate(timerange):
        if str(i1) in values.keys():
            totalvalid += 1
            totalsuccess += values[str(i1)]
            for i2 in range(100):
                colours_base[j1 * 100 + i2] = values[str(i1)] + 1
    brow = {"title": title, "value": f"{totalsuccess}/{totalvalid}", "colours": []}
    for i1 in range(100):
        valid = 0
        success = 0
        for i2 in range(count):
            if colours_base[i1 * count + i2] > 0:
                valid += 1
                success += colours_base[i1 * count + i2] - 1
        brow["colours"].append(generate_colour(valid / count, (success / valid) if valid != 0 else 0))
    return brow


@app.route("/")
def index():
    bar_rows = []
    count = int(request.args['count']) if 'count' in request.args else 1440
    for i1 in config:
        logfile = config[i1]["logfile"]
        with open(logfile, "rb") as f:
            values = json.loads(f.read())
        title = config[i1]["display"]
        basetime = datetime.fromisoformat(config[i1]["basetime"])
        bar_rows.append(generate_bar(title, count, values, basetime))
    return render_template("index.html", bar_rows=bar_rows, count=count)


if __name__ == "__main__":
    app.run(debug=True)
