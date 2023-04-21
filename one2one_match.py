from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from collections import defaultdict

from telegram.ext import (
    Application,
    ChatMemberHandler,
    CallbackQueryHandler,
    PicklePersistence,
    CommandHandler,
    ContextTypes,
    CallbackContext,
    MessageHandler,
    filters,
)

import pickle
import os
import random
from datetime import datetime, timedelta
import asyncio
import aiofiles

from utils import pickler, unpickler
import config

LNAME = config.LNAME
POINT_NAME = config.POINT_NAME
MATCH_NAME = config.MATCH_NAME
ROOMS_NAME = config.ROOMS_NAME

point_dict          = dict()
match_game_dict     = dict()
game_rooms_dict     = dict()

room_num = "0"

async def regi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    chat_id = update.message.chat_id
    if user not in match_game_dict:
        match_game_dict[user] = defaultdict(int)
        match_game_dict[user]["resi"] = 1

    if match_game_dict[user]["resi"] == 1:
        await update.message.reply_text( text= f'{user}님은 이미 등록하셨습니다.')
    else:
        match_game_dict[user]["id"] = chat_id
        room_num = "0"
        if room_num not in game_rooms_dict:
            game_rooms_dict[room_num] = {
                'room_num':{"0" : " ", "1" : " "},
                'random_num':{"0" : " ", "1" : " "},
                'bet': " "
                }
        await update.message.reply_text( text= f'{user}님 등록 완료! \n /join 으로 게임에 참여해 보세요')

    await pickler(ROOMS_NAME, game_rooms_dict)
    await pickler(MATCH_NAME, match_game_dict)

async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    match_game_dict = await unpickler(MATCH_NAME)
    game_rooms_dict = await unpickler(ROOMS_NAME)
    chat_id = match_game_dict[user]["id"]
    
    room_num = "0"
    if game_rooms_dict[room_num]["room_num"]["0"] == " ":
        game_rooms_dict[room_num]["room_num"]["0"] = user
        match_game_dict[user]["room"] = room_num
        await update.message.reply_text( text= f'{user}님 {room_num}번방(0)에 입장하셨습니다. \n /play 게임 시작')
    elif game_rooms_dict[room_num]["room_num"]["0"] != " " and game_rooms_dict[room_num]["room_num"]["1"] == " ":
        if game_rooms_dict[room_num]["room_num"]["0"] == user:
            await update.message.reply_text( text= f'{user}님께선 이미 {room_num}번방(0)에 입장하신 상태입니다. \n /play 게임 시작')
        else:
            game_rooms_dict[room_num]["room_num"]["1"] = user
            match_game_dict[user]["room"] = room_num
            await update.message.reply_text( text= f'{user}님 {room_num}번방(1)에 입장하셨습니다. \n /play 게임 시작')
    elif game_rooms_dict[room_num]["room_num"]["0"] != " " and game_rooms_dict[room_num]["room_num"]["1"] != " ":
        if game_rooms_dict[room_num]["room_num"]["1"] == user:
            await update.message.reply_text( text= f'{user}님께선 이미 {room_num}번방(1)에 입장하신 상태입니다. \n /play 게임 시작')
        else:
            await update.message.reply_text( text= f'모든 자리가 가득 찼습니다. 조금만 기다려주세요.')

    await pickler(MATCH_NAME, match_game_dict)
    await pickler(ROOMS_NAME, game_rooms_dict)

async def leave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    match_game_dict = await unpickler(MATCH_NAME)
    game_rooms_dict = await unpickler(ROOMS_NAME)
    chat_id = match_game_dict[user]["id"]
    room_num = "0"

    if game_rooms_dict[room_num]["room_num"]["0"] == user:
        game_rooms_dict[room_num]["room_num"]["0"] = " "
        game_rooms_dict[room_num]["random_num"]["0"] = " "
        match_game_dict[user]["room"] = " "
        await update.message.reply_text( text= f'{user}님 {room_num}번방(0)에서 퇴장하셨습니다.')
    elif game_rooms_dict[room_num]["room_num"]["1"] == user:
        game_rooms_dict[room_num]["room_num"]["1"] = " "
        game_rooms_dict[room_num]["random_num"]["1"] = " "
        match_game_dict[user]["room"] = " "
        await update.message.reply_text( text= f'{user}님 {room_num}번방(1)에서 퇴장하셨습니다.')
    elif game_rooms_dict[room_num]["room_num"]["0"] != user and game_rooms_dict[room_num]["room_num"]["1"] != user:
        await update.message.reply_text( text= f'방에 입장 상태가 아닙니다 /join 으로 입장하세요.')

    await pickler(MATCH_NAME, match_game_dict)
    await pickler(ROOMS_NAME, game_rooms_dict)
    #await update.message.reply_text( text= f'{user}님의 id는 {chat_id}입니다.')

async def play_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    match_game_dict = await unpickler(MATCH_NAME)
    game_rooms_dict = await unpickler(ROOMS_NAME)
    user_0 = game_rooms_dict[room_num]["room_num"]["0"]
    user_1 = game_rooms_dict[room_num]["room_num"]["1"]

    if user == user_0 :
        if game_rooms_dict[room_num]["random_num"]["0"] == " ":
            user_0_num = random.randint(1,1000)
            game_rooms_dict[room_num]["random_num"]["0"] = user_0_num
            await update.message.reply_text( text= f'{user_0}님 랜덤 번호 선택 완료! \n /match 로 상대와 겨뤄보세요!')
        else:
            await update.message.reply_text( text= f'이미 선택하셨습니다. \n /match 로 상대와 겨뤄보세요!')
    
    elif user == user_1:
        if game_rooms_dict[room_num]["random_num"]["1"] == " ":
            user_1_num = random.randint(1,1000)
            game_rooms_dict[room_num]["random_num"]["1"] = user_1_num
            await update.message.reply_text( text= f'{user_1}님 랜덤 번호 선택 완료! \n /match 로 상대와 겨뤄보세요!')
        else:
            await update.message.reply_text( text= f'이미 선택하셨습니다. \n /match 로 상대와 겨뤄보세요!')
    else:
        await update.message.reply_text( text= f'{user}님은 방에 입장 상태가 아닙니다 /join 으로 입장하세요.')

    await pickler(MATCH_NAME, match_game_dict)
    await pickler(ROOMS_NAME, game_rooms_dict)

async def match_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    match_game_dict = await unpickler(MATCH_NAME)
    game_rooms_dict = await unpickler(ROOMS_NAME)
    user_0 = game_rooms_dict[room_num]["room_num"]["0"]
    user_1 = game_rooms_dict[room_num]["room_num"]["1"]
    user_0_num = game_rooms_dict[room_num]["random_num"]["0"]
    user_1_num = game_rooms_dict[room_num]["random_num"]["1"]

    if user_0 == " " or user_1 == " ":
        reply_text = '대결은 두사람 모두 방에 입장 후 가능합니다. \n'
        reply_text += '/join 으로 방에 입장해주세요.'
        await update.message.reply_text( text=reply_text)
    else:
        if user_0_num == " " or user_1_num == " ":
            reply_text = '대결할 준비가 되지 않았습니다. \n'
            reply_text += '두분 모두 /play 해주셔야 대결 할 수 있습니다. '
            await update.message.reply_text( text=reply_text)
        else:
            if user_0_num > user_1_num:
                game_rooms_dict[room_num]["random_num"]["0"] = " "
                game_rooms_dict[room_num]["random_num"]["1"] = " "
                reply_text = f'축하합니다!! {user_0}님께서 승리하셨습니다. \n'
                reply_text += f'{user_0} 님 : \U0001f199 {user_0_num} vs {user_1_num} : {user_1} \n'
                reply_text += '/leave : 방 나가기, /play : 다시 게임하기'
                await update.message.reply_text( text= reply_text)
            elif user_0_num < user_1_num:
                game_rooms_dict[room_num]["random_num"]["0"] = " "
                game_rooms_dict[room_num]["random_num"]["1"] = " "
                reply_text = f'축하합니다!! {user_1}님께서 승리하셨습니다. \n'
                reply_text += f'{user_0} 님 : {user_0_num} vs {user_1_num} \U0001f199 : {user_1} \n'
                reply_text += '/leave : 방 나가기, /play : 다시 게임하기'
                await update.message.reply_text( text= reply_text)
            else:
                game_rooms_dict[room_num]["random_num"]["0"] = " "
                game_rooms_dict[room_num]["random_num"]["1"] = " "
                reply_text = '대결은 무승부.. 후.. \n'
                reply_text += '/leave : 방 나가기, /play : 다시 게임하기'
                await update.message.reply_text( text=reply_text)

    await pickler(MATCH_NAME, match_game_dict)
    await pickler(ROOMS_NAME, game_rooms_dict)

async def match_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    match_game_dict = await unpickler(MATCH_NAME)
    game_rooms_dict = await unpickler(ROOMS_NAME)
    user_0 = game_rooms_dict[room_num]["room_num"]["0"]
    user_1 = game_rooms_dict[room_num]["room_num"]["1"]
    user_0_num = game_rooms_dict[room_num]["random_num"]["0"]
    user_1_num = game_rooms_dict[room_num]["random_num"]["1"]

    reply_text = f'현재 개설된 대결 방 : {room_num}번방 \n'
    reply_text += f'참여자 {room_num}-0번 : {user_0}님, {room_num}-1번 : {user_1}님 \n'
    reply_text += '/registration : 유저 등록(필) /join : 방 입장 /leave : 방 나가기, /play : 게임하기, /match : 대결하기'
    await update.message.reply_text( text=reply_text)





