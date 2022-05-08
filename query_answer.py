from io import BytesIO
import pytesseract
import keyboard

from configparser import ConfigParser
from PIL import ImageGrab, Image
from datetime import datetime
from icecream import ic
from time import sleep
from lxml.etree import HTML
from requests import session
from urllib.parse import quote, urljoin


RETRY = 6

client = session()
def get(url):
    resp = client.get(url, headers = {
    'Cookie' :f'Hm_lvt_b656d8b02edc9a9cf671edf4ceeddbc3=1651115525; __gads=ID=a7e9fcca5d24a93f-22b561d16fd20047:T=1651115623:RT=1651115623:S=ALNI_Mb49A5R_GGbBOBrQVkDIVPK37A49g; __gpi=UID=0000050fed2b2f68:T=1651115838:RT=1651115838:S=ALNI_MbHBFn_jjmTiJ0QKFPuHUBOHj5DWg; JSESSIONID=24CFFE36CCA2545912D53280A3A841C7; Hm_lpvt_b656d8b02edc9a9cf671edf4ceeddbc3={int(datetime.now().timestamp())}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'Referer': 'https://www.wkda.cn/ask/mpmpxaemyamxo.html'
})
    return resp

def query_question(question, retry=0):
    url = f'https://www.wkda.cn/ask?problem={quote(question)}'
    print(url)
    resp = get(url)
    if not resp.ok:
        if retry < RETRY:
            return query_question(question, retry+1)
        else:
            raise RuntimeError("max retry reached")
    html = HTML(resp.text)
    questions = html.xpath('//div[@class="lbox-ask"]/div/li/a/h2/text()')
    urls = html.xpath('//div[@class="lbox-ask"]/div/li/a/@href')
    urls = ['https://www.wkda.cn' + each for each in urls]
    return questions, urls

def get_answer(url, retry=0):
    print(url)
    resp = get(url)    
    if not resp.ok:
        if retry < RETRY:
            return get_answer(url, retry+1)
        else:
            raise RuntimeError("max retry reached")
    html = HTML(resp.text)
    div = html.xpath('//div[@class="lbox-ask"]/div[2]/div')[0]
    if div.get('news') is not None:
        print("please login")
        exit()
    else:
        answer = div.text
    return answer



config = ConfigParser()
config.read('./config/config.ini')

app_id = config.get('BaiduORC', 'AppID')
api_key = config.get('BaiduORC', 'APIKey')
secret_key = config.get('BaiduORC', 'SecretKey')

class BaiduORC:
    def __init__(self, app_id, api_key, secret_key):
        from aip import AipOcr
        self.orc = AipOcr(app_id, api_key, secret_key)

    def recognize(self, image) -> str:
        if isinstance(image, str):
            with open(image, 'rb') as f:
                image = f.read()
        elif isinstance(image, Image.Image):
            ba = BytesIO()
            image.save(ba, format='JPEG')
            image = ba.getvalue()
        result = self.orc.basicAccurate(image)
        # ic(result)
        result = '\n'.join([k['words'] for k in result['words_result']])
        return result


ocr = BaiduORC(app_id, api_key, secret_key)

while True:
    keyboard.wait(hotkey="ctrl+f1")
    keyboard.wait(hotkey="ctrl+c")
    sleep(.2)

    img = None
    while img is None:
        try:
            img = ImageGrab.grabclipboard()  
        except OSError:
            pass
        sleep(.1)

    text = ocr.recognize(img)
    print(f'querying question {text}')

    _question, _url = query_question(text)
    ic(_question)
    _ = get_answer(_url[0])
    print(_)


