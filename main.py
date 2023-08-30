"""A simple app to report the CPU temperature of my raspberry pi"""
import argparse
import random
import uvicorn
from fastapi import FastAPI
from fastapi import Request
#from fastapi import WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

is_mock = False
templates = Jinja2Templates(directory="templates")
app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static",
)


def read_temperature():
    """Read CPU temperature"""

    # Mockup for testing without real HW
    global is_mock
    if is_mock:
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

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request})

@app.get("/info", response_class=HTMLResponse)
def info(request: Request):
    data = {"temperature_cpu": read_temperature()}
    return templates.TemplateResponse(
        "info.html",
        {"request": request, "data": data}
    )

def main():
    parser = argparse.ArgumentParser(
        prog="House", description="My house logger"
    )
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-m', '--mock', action='store_true')
    args = parser.parse_args()
    global is_mock
    is_mock = args.mock

    print(f"Using args: {args}")

    if args.debug:
        uvicorn.run(app, port=3002, host="0.0.0.0", log_level="debug")
    else:
        uvicorn.run(app, port=3002, host="0.0.0.0")


if __name__ == "__main__":
    main()
