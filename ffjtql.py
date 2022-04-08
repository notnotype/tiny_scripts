from json import loads
from time import sleep

from mirai import Mirai

if __name__ == '__main__':
    while True:
        with open('mirai/mirai.config.json', 'r', encoding='utf-8') as f:
            data = loads(f.read())
        client = Mirai(data['host'], data['auth_key'], data['qq'])
        client.auth(data['qq'])
        client.send_group_message(data['2021计算机协会会员群'], 'ffjtql')

        sleep(60*60*4)

