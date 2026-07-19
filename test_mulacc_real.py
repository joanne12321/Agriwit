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
def run_t(dic):
    def on_open(ws):
        ws.send(json.dumps({
            'common': {'app_id': os.getenv('XUNFEI_APP_ID')},
            'business': dic,
            'data': {'status': 0, 'format': 'audio/L16;rate=16000', 'encoding': 'raw', 'audio': base64.b64encode(b'\x00'*3200).decode()}
        }))
        time.sleep(0.1)
        ws.send(json.dumps({
            'data': {'status': 2, 'format': 'audio/L16;rate=16000', 'encoding': 'raw', 'audio': base64.b64encode(b'\x00'*3200).decode()}
        }))
    def on_message(ws, msg): 
        print(f'{dic} => {msg}')
        if "status" in msg or "code" in msg:
            ws.close()
            ws_done.set()
    def on_error(ws, err): 
        ws_done.set()

    ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error)
    threading.Thread(target=ws.run_forever).start(); ws_done.wait(4); ws_done.clear()

run_t({'domain': 'slm', 'language': 'zh_cn', 'accent': 'mulacc', 'dwa': 'wpgs'})
