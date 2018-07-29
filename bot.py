#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import requests, time, os

TOKEN = 'YOUR_TOKEN'

updater = Updater(TOKEN)
dispatcher = updater.dispatcher


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hey there. Just send me a GIF and I'll upload it to "
                                                          "gfycat for you.")


def gfycat_that(bot, update):
    doc = update.message.document
    if doc.mime_type != 'video/mp4':
        return 
    
    chat_id = update.message.chat_id
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)

    directory = str(chat_id)
    path = os.path.join('.', directory, doc.file_id)
    if not os.path.isdir(directory):
        os.mkdir(directory)

    doc.get_file().download(custom_path=path)
    datakeys = {'title': update.message.text} if update.message.text else None
    r = requests.post('https://api.gfycat.com/v1/gfycats', data=datakeys)
    gfyname = r.json()['gfyname']

    requests.post('https://filedrop.gfycat.com', data={'key': gfyname}, files={'file': open(path, 'rb')})
    rson = requests.get('https://api.gfycat.com/v1/gfycats/fetch/status/' + gfyname).json()

    while rson['task'] == 'encoding':
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        time.sleep(5)
        rson = requests.get('https://api.gfycat.com/v1/gfycats/fetch/status/' + gfyname).json()
    if rson['task'] == 'complete':
        bot.send_message(chat_id=update.message.chat_id, text='https://gfycat.com/' + rson['gfyname'])

    os.remove(path)


start_handler = CommandHandler(str('start'), start)
gif_handler = MessageHandler(filters=Filters.document, callback=gfycat_that)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(gif_handler)
updater.start_polling()
updater.idle()
