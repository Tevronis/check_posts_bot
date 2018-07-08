# coding=utf-8
import json

import time
from collections import namedtuple
from datetime import datetime

from flask import Flask
from flask import request
from flask import jsonify

from threading import Thread
import requests

from flask_sslify import SSLify

# Security
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

# delete/set webhook:
# https://api.telegram.org/bot208996493:AAFjNkoaqm6nc04ozB1GJZvgJUIH9RWhVSI/deleteWebhook/
# https://api.telegram.org/bot208996493:AAFjNkoaqm6nc04ozB1GJZvgJUIH9RWhVSI/setWebhook?url=https://c0e6d40d.ngrok.io/

DELAY = 5
START_CHECK = False
WALL = '-54665275' #'-128033123'
SESSION_POSTS = []
my_thread = None
app = Flask(__name__)


sslify = SSLify(app)


class Worker(Thread):
    def __init__(self, chat_id):
        Thread.__init__(self)
        self.chat_id = chat_id
        r = requests.get('https://api.vk.com/method/wall.get',
                         params={'owner_id': WALL, 'count': 10, 'offset': 0, 'access_token': VK_TOKEN, 'v': '5.78'})

        global SESSION_POSTS
        SESSION_POSTS = [item for item in self.get_posts(r.json())]
        print('thread was started')

    def run(self):
        print('Worker.run()')
        while START_CHECK:
            time.sleep(DELAY)
            print('ya rabotayu')
            self.check_new_post(WALL)

    def get_posts(self, data):
        post = namedtuple('Post', ['owner', 'text', 'id', 'time'])
        result = []
        for item in data['response']['items']:
            result.append(post(owner=item['owner_id'], text=item['text'], id=item['id'], time=item['date']))

        return result

    def check_new_post(self, group_id):
        print('check_new_post {} '.format(group_id))
        r = requests.get('https://api.vk.com/method/wall.get',
                         params={'owner_id': group_id, 'count': 10, 'offset': 0, 'access_token': VK_TOKEN,
                                 'v': '5.78'})

        posts = self.get_posts(r.json())
        result = False
        global SESSION_POSTS
        for item in posts:
            if item not in SESSION_POSTS:
                result = True
                SESSION_POSTS.append(item)
                message = 'Время: {}, Текст: {}'.format(datetime.fromtimestamp(int(item.time)).strftime('%c'),
                                                        item.text)
                send_message(self.chat_id, text=message)
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
    global my_thread
    START_CHECK = True
    my_thread = Worker(chat_id)
    my_thread.start()
    print('start_check: {}'.format(chat_id))


def stop_check(chat_id, value):
    global START_CHECK
    START_CHECK = False
    print('stop_check: {}'.format(chat_id))


def help(chat_id, value):
    pass


def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def send_message(chat_id, text='test text'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text}
    #requests.post(url, json=answer)
    #print('LOG send_message: {} was send'.format(json.dumps(answer)))
    for proxy in PROXY_LIST:
        proxy_dict = {'http': 'https://{}/'.format(proxy), 'https': 'https://{}/'.format(proxy)}
        try:
            requests.post(url, json=answer, proxies=proxy_dict)
            print('LOG send_message: {} was send'.format(json.dumps(answer)))
            break
        except:
            print('Proxy {} not available, try next.'.format(proxy))
            continue


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        r = request.get_json()
        chat_id = r['message']['chat']['id']
        message = r['message']['text'].split()
        if message[0][1:] in COMMANDS.keys():
            COMMANDS[message[0][1:]](chat_id, message)
            send_message(chat_id, 'ок, принял')
        else:
            send_message(chat_id, 'Введите валидную команду или /help')
        # write_json(r)

        return jsonify(r)
    return '<h1>https://t.me/Michael_ardvyd</h1>'


COMMANDS = {'set_wall': set_wall, 'set_delay': set_delay, 'start_check': start_check, 'stop_check': stop_check,
            'help': help}

if __name__ == '__main__':
    app.run()

