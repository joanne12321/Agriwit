import sys, os, time, json, base64, hmac, hashlib, threading
from datetime import datetime, timezone; import urllib.parse; import websocket
from dotenv import load_dotenv

load_dotenv('d:/桌面/云稼集Agriwit/后端/.env')
host = 'iat.cn-huabei-1.xf-yun.com'
date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
secret = os.getenv('XUNFEI_API_SECRET')
path = '/v1'
sign_str = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
sign = base64.b64encode(hmac.new(secret.encode(), sign_str.encode(), hashlib.sha256).digest()).decode()
auth_str = f'api_key="{os.getenv("XUNFEI_API_KEY")}", algorithm="hmac-sha256", headers="host date request-line", signature="{sign}"'
auth = base64.b64encode(auth_str.encode()).decode()

url = f'wss://{host}{path}?' + urllib.parse.urlencode({'host': host, 'date': date, 'authorization': auth})

ws_done = threading.Event()
def run_t():
    def on_open(ws):
        print("Connected.")
        req = {
            "header": { "app_id": os.getenv("XUNFEI_APP_ID"), "status": 0 },
            "parameter": {
                "iat": {
                    "language": "zh_cn",
                    "accent": "mulacc",
                    "domain": "slm",
                    "result": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "json"
                    }
                }
            },
            "payload": {
                "audio": {
                    "encoding": "raw",
                    "sample_rate": 16000,
                    "channels": 1,
                    "bit_depth": 16,
                    "status": 0,
                    "seq": 0,
                    "audio": base64.b64encode(b'\x00'*3200).decode()
                }
            }
        }
        ws.send(json.dumps(req))
        
        time.sleep(0.1)
        req2 = {
            "header": { "app_id": os.getenv("XUNFEI_APP_ID"), "status": 2 },
            "payload": {
                "audio": {
                    "encoding": "raw",
                    "sample_rate": 16000,
                    "channels": 1,
                    "bit_depth": 16,
                    "status": 2,
                    "seq": 1,
                    "audio": base64.b64encode(b'\x00'*3200).decode()
                }
            }
        }
        ws.send(json.dumps(req2))

    def on_message(ws, msg): 
        print(f'Message => {msg}')
        m = json.loads(msg)
        if m.get('header', {}).get('status') == 2 or m.get('header', {}).get('code') != 0:
            ws.close()
            ws_done.set()
    def on_error(ws, err): 
        ws_done.set()

    ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error)
    threading.Thread(target=ws.run_forever).start(); ws_done.wait(4); ws_done.clear()

run_t()
