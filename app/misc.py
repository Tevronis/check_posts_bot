import json
import time
from collections import namedtuple
from datetime import datetime

import requests

BOT_TOKEN = '208996493:AAFjNkoaqm6nc04ozB1GJZvgJUIH9RWhVSI'
URL = 'https://api.telegram.org/bot{}/'.format(BOT_TOKEN)
VK_TOKEN = '2e0516132e0516132e051613372e50dfbd22e052e0516137523b1196397d016cf92f539'
WHITE_USER_LIST = []
PROXY_LIST = ['149.3.91.202:3128', '190.153.139.121:62225', '183.88.52.208:8080', '125.24.4.114:8080', '47.88.5.58:808',
              '180.250.252.3:8080', '103.10.81.172:8080', '200.110.13.89:53281', '85.35.159.222:8080',
              '212.45.5.146:8080']
PROXY_SERVER = '149.3.91.202'
PROXY_PORT = '3128'
proxie = {'http': 'https://{}:{}/'.format(PROXY_SERVER, PROXY_PORT),
          'https': 'https://{}:{}/'.format(PROXY_SERVER, PROXY_PORT)}

DELAY = 20
START_CHECK = False
processed = []
WALL = '-54665275'  # '-128033123'
SESSION_POSTS = []
my_thread = None


def init():
    r = requests.get('https://api.vk.com/method/wall.get',
                     params={'owner_id': WALL, 'count': 10, 'offset': 0, 'access_token': VK_TOKEN, 'v': '5.78'})
    ru = get_updates()
    for item in ru['result']:
        update_id = item['update_id']
        processed.append(update_id)
    global SESSION_POSTS
    SESSION_POSTS = [item for item in get_posts(r.json())]
    print('init')


def worker():
    init()
    print('Worker.run()')
    i = 0
    chat_id = (yield)
    while True:
        time.sleep(DELAY)
        if i <= DELAY:
            chat_id = (yield)
        if START_CHECK:
            print('ya rabotayu')
            check_new_post(WALL, chat_id)
        i = (i + DELAY) % 180


def get_posts(data):
    post = namedtuple('Post', ['owner', 'text', 'id', 'time', 'signer_id'])
    result = []
    for item in data['response']['items']:
        text_to_send = ''
        signerid = ''
        if item['text']:
            text_to_send = item['text']
        if 'signer_id' in item:
            signerid = item['signer_id']
        result.append(post(owner=item['owner_id'], text=text_to_send, id=item['id'], time=item['date'], signer_id=signerid))

    return result


def check_new_post(group_id, chat_id):
    print('check_new_post {} '.format(group_id))
    r = requests.get('https://api.vk.com/method/wall.get',
                     params={'owner_id': group_id, 'count': 10, 'offset': 0, 'access_token': VK_TOKEN,
                             'v': '5.78'})

    posts = get_posts(r.json())
    result = False
    global SESSION_POSTS
    for item in posts:
        if item not in SESSION_POSTS:
            result = True
            SESSION_POSTS.append(item)
            key_w = ['спасибо', 'лучший', 'мощь', 'топ']
            bad = False
            if item.signer_id == '179694695': # del Boris
                bad = True
            for kw in key_w:
                if kw.lower() in str(item.text).lower(): bad = True
            if bad:
                return result
            template = 'Пост: https://vk.com/fuckbet?w=wall{}_{} \nВремя: {}, \nТекст: {}'
            message = template.format(item.owner, item.id, datetime.fromtimestamp(int(item.time)).strftime('%c'),
                                      item.text)
            send_message(chat_id, text=message)
    return result


def set_wall(chat_id, value):
    global WALL
    WALL = value[1]
    print('set_wall: {}'.format(value))


def set_delay(chat_id, value):
    global DELAY
    try:
        DELAY = int(value[1])
    except:
        pass
    print('set_delay: {}'.format(value))


def start_check(chat_id, value):
    global START_CHECK
    START_CHECK = True
    print('start_check: {}'.format(chat_id))


def stop_check(chat_id, value):
    global START_CHECK
    START_CHECK = False
    print('stop_check: {}'.format(chat_id))


def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def send_message(chat_id, text='test text'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text}
    # requests.post(url, json=answer)
    # print('LOG send_message: {} was send'.format(json.dumps(answer)))
    for proxy in PROXY_LIST:
        proxy_dict = {'http': 'https://{}/'.format(proxy), 'https': 'https://{}/'.format(proxy)}
        try:
            requests.post(url, json=answer, proxies=proxy_dict)
            print('LOG send_message: {} was send'.format(json.dumps(answer)))
            break
        except:
            print('Proxy {} not available, try next.'.format(proxy))
            continue


def get_updates():
    # r = requests.get(URL + 'getUpdates')
    # print('LOG get_updates')
    # return r.json()
    for proxy in PROXY_LIST:
        proxy_dict = {'http': 'https://{}/'.format(proxy), 'https': 'https://{}/'.format(proxy)}
        try:
            r = requests.get(URL + 'getUpdates', proxies=proxy_dict)
            print('LOG get_updates')
            # write_json(r.json())
            return r.json()
            break
        except:
            print('Proxy {} not available, try next.'.format(proxy))
            continue


COMMANDS = {'set_wall': set_wall, 'set_delay': set_delay, 'start_check': start_check, 'stop_check': stop_check}


def calculate(r):
    result = 0
    for item in r['result']:
        chat_id = item['message']['chat']['id']
        result = chat_id
        update_id = item['update_id']
        message = item['message']['text'].split()
        if update_id not in processed:
            processed.append(update_id)
            if message[0][1:] in COMMANDS.keys():
                COMMANDS[message[0][1:]](chat_id, message)
                send_message(chat_id, 'ок, принял')
            else:
                send_message(chat_id, 'Введите валидную команду')
    return result
