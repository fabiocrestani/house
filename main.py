"""A simple app to report the CPU temperature of my raspberry pi"""
import argparse
import random
import uvicorn
import time
import threading
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import influxdb_client, os, time
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS



# Init FastAPI -------------------------------------------------------------------------
templates = Jinja2Templates(directory="templates")
app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static",
)

# FastAPI endpoints --------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request})

@app.get("/info", response_class=HTMLResponse)
def info(request: Request):
    return templates.TemplateResponse(
        "info.html", {
            "request": request,
            "data_buffer": Monitor.data_buffer
        }
    )

# Monitor class ------------------------------------------------------------------------
class Monitor:
    data_buffer = []
    running = True
    is_mock = False
    is_debug = False
    sleep_time_seconds = 1
    influxdb_token = ""
    influxdb_org = ""
    influxdb_bucket = ""
    influxdb_url = ""
    influxdb_write_api = None

    @staticmethod
    def init_influxdb():
        try:
            write_client = influxdb_client.InfluxDBClient(
                url=Monitor.influxdb_url,
                token=Monitor.influxdb_token,
                org=Monitor.influxdb_org,
                verify_ssl=False
            )

            Monitor.influxdb_write_api = write_client.write_api(
                write_options=SYNCHRONOUS)
        except Exception as e:
            print("Error seting up influxdb: " + str(e))

    @staticmethod
    def read_temperature():
        """Read CPU temperature"""

        # Mockup for testing without real HW
        if Monitor.is_mock:
            value = 33 + random.randint(0, 5) + (random.randint(0, 100) / 100) + 0.2
            return value
        
        file = open("/sys/class/thermal/thermal_zone0/temp", "r")
        value = 0
        try:
            value = int(file.read())
            value = value / 1000
        except Exception:
            pass
        return value

    @staticmethod
    def thread_get_data():
        while Monitor.running:
            now = datetime.now()
            dt_string = now.strftime("%d.%m.%Y %H:%M:%S")
            local_buffer = {
                "temperature_cpu": Monitor.read_temperature(),
                "timestamp": dt_string
            }
            if Monitor.is_debug:
                print(local_buffer)

            # Add data to influxdb
            point = (
                Point("house")
                .tag("location", "pi1")
                .field("temperature", Monitor.read_temperature())
            )
            try:
                Monitor.influxdb_write_api.write(
                    bucket=Monitor.influxdb_bucket,
                    org=Monitor.influxdb_org,
                    record=point
                )
            except Exception as e:
                print("Error adding data to influxdb: " + str(e))

            # Add data to local buffer (to be deleted)
            Monitor.data_buffer = Monitor.data_buffer[-200:]
            Monitor.data_buffer.append(local_buffer)
            time.sleep(Monitor.sleep_time_seconds)


def main():
    parser = argparse.ArgumentParser(
        prog="House", description="My house logger"
    )
    parser.add_argument('-m', '--mock', action='store_true')
    args = parser.parse_args()
    print(f"Initializing main() using: {args}")

    # Set monitor parameters
    Monitor.is_mock = args.mock
    Monitor.is_debug = os.environ.get("HOUSE_DEBUG", False)
    Monitor.sleep_time_seconds = os.environ.get("HOUSE_SLEEP_TIME_SECONDS", 1)
    Monitor.influxdb_token = os.environ.get("INFLUXDB_TOKEN")
    Monitor.influxdb_org = os.environ.get("INFLUXDB_USERNAME", "fabio")
    Monitor.influxdb_bucket = os.environ.get("INFLUXDB_BUCKET", "house")
    Monitor.influxdb_url = os.environ.get(
        "INFLUXDB_URL", "https://influxdb.raspberrypi.fabiocrestani.eu1.k8g8.com")
    Monitor.init_influxdb()

    # Monitor main thread
    x = threading.Thread(target=Monitor.thread_get_data, args=())
    x.start()

    # FastAPI main thread
    if Monitor.is_debug:
        uvicorn.run(app, port=3002, host="0.0.0.0", log_level="debug")
    else:
        uvicorn.run(app, port=3002, host="0.0.0.0")


if __name__ == "__main__":
    main()
