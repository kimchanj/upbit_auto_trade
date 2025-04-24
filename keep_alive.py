# keep_alive.py
from flask import Flask
from threading import Thread
import requests
import time
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def self_ping(url, interval=10):
    """10초마다 자신의 URL을 호출해서 슬립 방지."""
    while True:
        try:
            requests.get(url, timeout=5)
        except:
            pass
        time.sleep(interval)

def keep_alive():
    # 1) 웹서버 스레드
    Thread(target=run_web, daemon=True).start()
    # 2) 자가 ping 스레드
    url = os.getenv("REPLIT_URL") or "<YOUR_REPLIT_URL>"
    Thread(target=self_ping, args=(url,), daemon=True).start()
