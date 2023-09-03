call .venv\Scripts\activate.bat

set INFLUXDB_TOKEN=
set HOUSE_DEBUG=True

python .\main.py --mock
pause
