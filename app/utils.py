import collections
from datetime import datetime
import json
import time

import requests

BOT_TOKEN = '208996493:AAFjNkoaqm6nc04ozB1GJZvgJUIH9RWhVSI'
URL = 'https://api.telegram.org/bot{}/'.format(BOT_TOKEN)
VK_TOKEN = '2e0516132e0516132e051613372e50dfbd22e052e0516137523b1196397d016cf92f539'
WHITE_USER_LIST = []
PROXIES_MOD = False
PROXIES_LIST = ['149.3.91.202:3128', '190.153.139.121:62225', '183.88.52.208:8080', '125.24.4.114:8080',
                '47.88.5.58:808',
                '180.250.252.3:8080', '103.10.81.172:8080', '200.110.13.89:53281', '85.35.159.222:8080',
                '212.45.5.146:8080']
DELAY = 20
START_CHECK = False
processed = []
SESSION_POSTS = []

users = collections.defaultdict(set)
groups = ['-54665275']


# '1': ['123', '456']

class Vkpost:
    filter_words = ['спасибо', 'лучший', 'мощь', 'топ']

    def __init__(self, reply):
        self.owner = reply['owner_id']
        self.text = reply['text'] if 'text' in reply else ''
        self.post_id = reply['id']
        self.time = reply['date']
        self.author_id = reply['signer_id'] if 'signer_id' in reply else ''

    def present(self):
        template = 'Пост: https://vk.com/fuckbet?w=wall{}_{} \nВремя: {}, \nТекст: {}'
        return template.format(self.owner, self.post_id, datetime.fromtimestamp(int(self.time)).strftime('%c'),
                               self.text)

    def validation(self):
        if self.author_id == '179694695':
            return False
        for fw in Vkpost.filter_words:
            if fw.lower() in str(self.text).lower():
                return False
        return True


def get_posts(group):
    r = requests.get('https://api.vk.com/method/wall.get',
                     params={'owner_id': group, 'count': 5, 'offset': 0, 'access_token': VK_TOKEN,
                             'v': '5.78'})
    data = r.json()
    result = []
    for post in data['response']['items']:
        result.append(Vkpost(post))
    return result


def send_message(chat_id, post):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': post}
    if not PROXIES_MOD:
        requests.post(url, json=answer)
    else:
        for proxy in PROXIES_LIST:
            proxy_dict = {'http': 'https://{}/'.format(proxy), 'https': 'https://{}/'.format(proxy)}
            try:
                requests.post(url, json=answer, proxies=proxy_dict)
                break
            except:
                print('Proxy {} not available, try next.'.format(proxy))
    print('LOG send_message: {} was send to {}'.format(post, chat_id))


def get_updates():
    r = None
    if not PROXIES_MOD:
        r = requests.get(URL + 'getUpdates')
    else:
        for proxy in PROXIES_LIST:
            proxy_dict = {'http': 'https://{}/'.format(proxy), 'https': 'https://{}/'.format(proxy)}
            try:
                r = requests.get(URL + 'getUpdates', proxies=proxy_dict)
                break
            except:
                print('Proxy {} not available, try next.'.format(proxy))
    print('LOG get_updates')
    return r.json()


def check_new_post():
    global SESSION_POSTS
    posts = {}  # 'group_id': [Vkpost]
    for group in groups:
        if group not in posts:
            posts[group] = []
        posts[group].extend(get_posts(group))

    used_posts = []
    for chat_id in users.keys():
        for group in users[chat_id]:
            for post in posts[group]:
                if post.post_id in SESSION_POSTS:
                    continue
                used_posts.append(post.post_id)
                if post.validation():
                    send_message(chat_id, post.present())
    for item in set(used_posts):
        SESSION_POSTS.append(item)


def calculate(r):
    global START_CHECK
    global WALL
    global DELAY
    for item in r['result']:
        chat_id = item['message']['chat']['id']
        users[chat_id].add('-54665275')  # user_id: [groups]

        tg_post_id = item['update_id']
        message = item['message']['text'].split()

        if tg_post_id not in processed:
            processed.append(tg_post_id)
            cmd = message[0][1:]
            if cmd == 'set_wall':
                WALL = message[1]
                print('set_wall: {}'.format(message))
            elif cmd == 'set_delay':
                DELAY = int(message[1]) if len(message) > 1 and message[1].isdigit() else 20
                print('set_delay: {}'.format(DELAY))
            elif cmd == 'start_check':
                START_CHECK = True
                print('start_check: {}'.format(chat_id))
            elif cmd == 'stop_check':
                START_CHECK = False
                print('stop_check: {}'.format(chat_id))
            else:
                send_message(chat_id, 'Введите валидную команду')
            send_message(chat_id, 'ок, принял')


def init():
    global SESSION_POSTS
    for group in groups:
        tg_req = get_updates()
        for item in tg_req['result']:
            processed.append(item['update_id'])
        SESSION_POSTS = [item.post_id for item in get_posts(group)]
        print('init')


def worker():
    init()
    print('Worker.run()')
    i = 0
    while True:
        time.sleep(DELAY)
        if i <= DELAY:
            flag = (yield)
        if START_CHECK:
            print('ya rabotayu')
            check_new_post()
        i = (i + DELAY) % 180
