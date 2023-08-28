"""A simple app to report the CPU temperature of my raspberry pi"""
from fastapi import FastAPI


def read_temperature():
    """Read CPU temperature"""
    file = open("/sys/class/thermal/thermal_zone0/temp", "r")
    value = 0
    try:
        value = int(file.read())
        value = value / 1000
    except Exception:
        pass
    return value


app = FastAPI()
read_temperature()

@app.get("/")
async def root():
    temperature_cpu = read_temperature()
    return {
        "temperature_cpu": temperature_cpu
    }
