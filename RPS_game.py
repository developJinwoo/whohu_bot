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

import config
from utils import pickler, unpickler

LNAME = config.LNAME
POINT_NAME = config.POINT_NAME

START_ROUTES, END_ROUTES = config.START_ROUTES, config.END_ROUTES
END_GAME, END, START_OVER = config.END_GAME, config.END, config.START_OVER
PLAY_RPS_GAME, PLAY_RPS_GAME_500, PLAY_RPS_GAME_1000 = config.PLAY_RPS_GAME, config.PLAY_RPS_GAME_500, config.PLAY_RPS_GAME_1000
ROCK, PAPPER, SCISSOR = config.ROCK, config.PAPPER, config.SCISSOR
RPS_ROUTES = config.RPS_ROUTES
LOAD_RPS = config.LOAD_RPS

"""
--------------------------------------------------------------------------------------------------------------------------
가위바위보 게임
--------------------------------------------------------------------------------------------------------------------------
"""
async def rock_papper_scissor_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("100후", callback_data=str(PLAY_RPS_GAME)),
            InlineKeyboardButton("5000후", callback_data=str(PLAY_RPS_GAME_500)),
            InlineKeyboardButton("1000후", callback_data=str(PLAY_RPS_GAME_1000)),
        ],
        [
            InlineKeyboardButton("종료", callback_data=str(END_GAME)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = "가위 바위 보 게임입니다. \n"
    reply_text += f"{user}님 얼마를 걸고 게임하시겠습니까? \n"
    await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
    return RPS_ROUTES

async def rock_papper_scissor_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    query_data = update.callback_query.data
    # call_query = update.callback_query # Debug
    # await query.edit_message_text(text=f'{call_query}') # Debug
    user = update.effective_user.first_name
    if query_data == '240':
        game_fee = 100
    elif query_data == '241':
        game_fee = 5000
    elif query_data == '242':
        game_fee = 1000

    point_dict = await unpickler(POINT_NAME)
    context.user_data["game_fee"] = game_fee
    if point_dict[user]["total"] < game_fee:
        keyboard = [
            [
                InlineKeyboardButton("처음으로", callback_data=str(START_OVER)),
                InlineKeyboardButton("종료하기", callback_data=str(END)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="후가 부족합니다. 후..", reply_markup=reply_markup)
        return END_ROUTES
    else:
        user_account = point_dict[user]["total"]
        user_account -= game_fee
        reply_text = f"게임비용으로 {game_fee}후를 차감하였습니다.\n"
        reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
        reply_text += "당신의 선택은? \n "
        reply_text += "(가위/바위/보)"
        keyboard = [
            [
                InlineKeyboardButton("\u270C\uFE0F", callback_data=str(SCISSOR)),
                InlineKeyboardButton("\u270A", callback_data=str(ROCK)),
                InlineKeyboardButton("\U0001f590\uFE0F", callback_data=str(PAPPER)),
            ],
            [
                InlineKeyboardButton("종료", callback_data=str(END_GAME)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return RPS_ROUTES
    
async def get_RPS_winner_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    가위바위보 conv
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    query_data = update.callback_query.data
    query = update.callback_query
    await query.answer()
    # call_query = update.callback_query
    # await query.edit_message_text(text=f'{call_query}') # Debug
    day_time = datetime.now()
    day = str(day_time).split(' ')[0]

    data_trans: dict[str, str] = {'203': '가위',
                             '202': '보',
                             '201': '바위'}
    rules: dict[str, str] = {'바위': '가위',
                             '가위': '보',
                             '보': '바위'}
    
    user_choice = data_trans[query_data]
    bot_choice = get_bot_choice()
    user_emoji = get_emoji(user_choice)
    bot_emoji = get_emoji(bot_choice)

    point_dict = await unpickler(POINT_NAME)

    game_fee = context.user_data["game_fee"]
    del context.user_data["game_fee"]
    user_account = point_dict[user]["total"]
    if user_choice == bot_choice:
        reply_text = "비겼습니다. 후.. \n"
        reply_text += f"후후 봇 : {bot_emoji} / {user_emoji} : {user}님 \n"
        reply_text += f"게임비용 {game_fee}후를 돌려드립니다.\n"
        reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
        keyboard = [
            [
                InlineKeyboardButton("다시하기", callback_data=str(LOAD_RPS)),
                InlineKeyboardButton("종료하기", callback_data=str(END)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return START_ROUTES
    
    elif rules[user_choice] == bot_choice:
        win_prize = game_fee*2
        point_dict[user][day] += game_fee
        point_dict[user]["total"] += game_fee
        user_account += game_fee

        await pickler(POINT_NAME, point_dict)
        reply_text = f"축하합니다. {user}님이 이겼습니다. 후!! \n"
        reply_text += f"후후 봇 : {bot_emoji} / {user_emoji} : {user}님 \n"
        reply_text += f"승리 상금 {win_prize}후를 적립해 드립니다.\n"
        reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
        keyboard = [
            [
                InlineKeyboardButton("다시하기", callback_data=str(LOAD_RPS)),
                InlineKeyboardButton("종료하기", callback_data=str(END)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return START_ROUTES
    else:
        point_dict[user][day] -= game_fee 
        point_dict[user]["total"] -= game_fee
        user_account -= game_fee
        
        await pickler(POINT_NAME, point_dict)
        reply_text = "후.. 졌습니다. 후.. \n"
        reply_text += f"후후 봇 : {bot_emoji} / {user_emoji} : {user}님 \n"
        reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
        keyboard = [
            [
                InlineKeyboardButton("다시하기", callback_data=str(LOAD_RPS)),
                InlineKeyboardButton("종료하기", callback_data=str(END)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return START_ROUTES


def get_bot_choice() -> str:
    return random.choice(['가위', '바위', '보'])

def get_emoji(choice: str):
    if choice == "가위":
        return "\u270C\uFE0F"
    elif choice == "바위":
        return "\u270A"
    elif choice == "보":
        return "\U0001f590\uFE0F"