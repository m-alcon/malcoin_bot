# bot.py
import requests
import os
import random
import re
import datetime
import json
from flask import Flask, request # Add your telegram token as environment variable
# from apscheduler.schedulers.background import BackgroundScheduler

def read_file(path):
    with open(path, 'r') as f:
        return list(f.readlines())

COINBASE_URL='https://api.pro.coinbase.com/'
BOT_URL = f'https://api.telegram.org/bot{os.environ["BOT_KEY"]}/'
URLS = {
    'message':      BOT_URL + 'sendMessage',
    'animation':    BOT_URL + 'sendAnimation',
    'dice':    BOT_URL + 'sendDice',
    'poll':         BOT_URL + 'sendPoll',
    'stop_poll':    BOT_URL + 'stopPoll',
    # 'resources':    'https://raw.githubusercontent.com/miquelalcon/gl-telegram-bot/master/resources/',
    'product':     COINBASE_URL + 'products/%s/stats'
}

HELP = "/help\n    Show this message\n/decide\n    Decide for you\n/product CRYPTO-COIN\n    Shows the value of CRYPTO in COIN"

app = Flask(__name__)
# scheduler = BackgroundScheduler()

commands = {
    'help': [[
        r'^\/help\s*\n*$',
        r'^\/help\@malcoin_bot\s*\n*$',
        ], []
    ],
    'decide': [[
        r'^\/decide\s*\n*$',
        r'^\/decide\@malcoin_bot\s*\n*$',
        ], []
    ],
    'product': [[
        r'^\/product\s+(?P<product>[\w\-]+)\s*\n*$',
        r'^\/product\@malcoin_bot\s+(?P<product>[\w\-]+)\s*\n*$',
        ], ['product']
    ],
}
for k in commands.keys():
    commands[k][0] = [re.compile(x) for x in commands[k][0]]

def is_command(message):
    if 'entities' in message:
        for entity in message['entities']:
            if entity['type'] == 'bot_command':
                return True
    return False

def get_command(message):
    for k, v in commands.items():
        for c in v[0]:
            result = c.search(message['text'])
            if result:
                if v[1]:
                    return [k, result.groups(v[1])]
                return [k]
    return []

# @scheduler.scheduled_job('cron', id='test', day_of_week='mon-fri', hour=11, minute=45)
# def test():
#     msg = 'message'
#     send_message(chat_id, msg)


def send_message(chat_id, text, parse_mode='', reply_id=''):
    response_msg = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_id:
        response_msg['reply_to_message_id'] = reply_id
    if parse_mode:
        response_msg['parse_mode'] = parse_mode
    requests.post(URLS['message'], json=response_msg)

def send_animation(chat_id, animation, reply_id=''):
    response_msg = {
        "chat_id": chat_id,
        "animation": animation,
    }
    if reply_id:
        response_msg['reply_to_message_id'] = reply_id
    requests.post(URLS['animation'], json=response_msg)

def send_dice(chat_id, reply_id=''):
    response_msg = {
        "chat_id": chat_id,
    }
    if reply_id:
        response_msg['reply_to_message_id'] = reply_id
    requests.post(URLS['dice'], json=response_msg)

def get_product_last(coin): #TODO: check possible coin
    content = json.loads(requests.get(URLS['product']%coin).content)
    if 'last' in content:
        return content['last']
    else:
        return ''

@app.route('/', methods=['POST'])
def main():
    data = request.json

    # Normal messages
    if 'message' in data and 'text' in data['message']:
        message = data['message']
        chat_id = message['chat']['id']
        message_txt = message['text'].lower()
        message_usr = ''
        if 'from' in message and 'username' in message['from']:
            message_usr = message['from']['username']
        
        if is_command(message):
            command = get_command(message)
            if command and command[0] == 'help':
                send_message(chat_id, HELP)
            if command and command[0] == 'decide':
                text = "Invest if %s"%random.choice(['odd','even'])
                send_message(chat_id, text)
                send_dice(chat_id)
            elif command and command[0] == 'product':
                coin = command[1][0]
                value = get_product_last(coin)
                coins = coin.split('-')
                if value:
                    send_message(chat_id, 'The value of %s in %s is %s'%(coins[0], coins[1], value))
                else:
                    send_message(chat_id, 'Product %s was not found.'%coin)
            else:
                send_message(chat_id, 'Wrong command. See /help for detailed information.')

    return ''

def create_app():
    #scheduler.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    create_app()
