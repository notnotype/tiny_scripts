from json import loads
from time import sleep
from random import randint
from datetime import datetime
from fastapi import FastAPI
import fastapi
from uvicorn import run
import uvicorn

from mirai import Mirai


with open('mirai/mirai.config.json', 'r', encoding='utf-8') as f:
    data = loads(f.read())
client = Mirai(data['host'], data['auth_key'], data['qq'])
client.auth(data['qq'])
target_group = data['2021计算机协会会员群']

token = "whyffjisgod"

app = FastAPI()

@app.get('/send_group_message')
@app.post('/send_group_message')
async def _(msg: str, auth_key: str):
    sleep(0.50)
    msg.replace('jjj', 'ffj')
    msg.replace('JJJ', 'ffj')
    if auth_key != token:
        raise fastapi.HTTPException(401)
    print("send msg [{}] to [{}]".format(msg, target_group))
    try:
        client.send_group_message(target_group, msg)
    except Exception as e:
        print("error: {}", str(e))
        return str(e)
    return msg

uvicorn.run(app, port=3000, host="0.0.0.0")
