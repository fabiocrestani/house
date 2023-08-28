FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3002

CMD [ "uvicorn", "main:app" , "--reload", "--host", "0.0.0.0", "--port", "3002"]
