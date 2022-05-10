from json import loads
from time import sleep
from random import randint
from datetime import datetime

from mirai import Mirai

if __name__ == '__main__':
    with open('mirai/mirai.config.json', 'r', encoding='utf-8') as f:
        data = loads(f.read())
    client = Mirai(data['host'], data['auth_key'], data['qq'])
    client.auth(data['qq'])
    # client.send_group_message(data['2021计算机协会会员群'], 'ffjtql')

    last_message = ''
    repeated = False
    target_group = data['2021计算机协会会员群']
    total_ffjtql = 0

    # client.send_group_message(target_group, [{'type': 'Image', 'imageId': '{177BF6DE-2AA5-08BA-75F7-E31B5888CC3C}.png', 'url': 'http://gchat.qpic.cn/gchatpic_new/2056963663/1072992996-3115744559-177BF6DE2AA508BA75F7E31B5888CC3C/0?term=2', 'path': None, 'base64': None}])
    # exit()

    while True:
        messages = client.fetch_message()
        for message in messages:
            if message['type'] == 'GroupMessage':
                if message['sender']['group']['id'] == target_group:
                    print("parse msg: {}".format(message))
                    if message['messageChain'][1]['type'] == 'Plain':
                        if message['messageChain'][1]['text'] == 'ffjtql':
                            total_ffjtql += 1
                    if message['messageChain'][1:] == last_message:
                        if repeated == False:
                            try:
                                client.send_group_message(
                                    target_group, last_message)
                                if last_message[0]['type'] == 'Plain':
                                    if last_message[0]['text'] == 'ffjtql':
                                        total_ffjtql += 1
                            except RuntimeError as e:
                                print(e)
                            repeated = True
                    else:
                        repeated = False
                    last_message = message['messageChain'][1:]

        now = datetime.now()
        if now.hour == 21 and now.minute == 0 and now.second == 1: 
            client.send_group_message(
                target_group, '今日ffjtql次数:' + str(total_ffjtql))
            total_ffjtql = 0

        if randint(0, 3600 * 3) == 1:
            client.send_group_message(target_group, 'ffjtql')
            total_ffjtql += 1
            continue
        else:
            sleep(0.95)
