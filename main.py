print("Hello world!")

from fastapi import FastAPI


def read_temperature():
    f = open("/sys/class/thermal/thermal_zone0/temp", "r")
    value = 0
    try:
        value = int(f.read())
        value = value / 1000
    except:
        pass
    return value


app = FastAPI()
read_temperature()

@app.get("/")
async def root():
    t = read_temperature()
    return {
        "temperature_cpu": t
    }