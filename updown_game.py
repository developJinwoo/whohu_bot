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

LNAME = config.LNAME
POINT_NAME = config.POINT_NAME

UPDOWN_ROUTES = config.UPDOWN_ROUTES
START_ROUTES, END_ROUTES = config.START_ROUTES, config.END_ROUTES
LOAD_UPDOWN = config.LOAD_UPDOWN
UP, DOWN, SAME = config.UP, config.DOWN, config.SAME
PLAY_UD_GAME, PLAY_UD_GAME_1000, CALC_PRIZE = config.PLAY_UD_GAME, config.PLAY_UD_GAME_1000, config.CALC_PRIZE
END_GAME, END, START_OVER = config.END_GAME, config.END, config.START_OVER

"""
--------------------------------------------------------------------------------------------------------------------------
업 & 다운 게임
--------------------------------------------------------------------------------------------------------------------------
"""
async def updown_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    query = update.callback_query
    await query.answer()

    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )

    if not point_dict[user]["victory"]:
        point_dict[user]["victory"] = 0
    if not point_dict[user]["vic_prize"]:
        point_dict[user]["vic_prize"] = 0

    context.user_data["updown_game"] = defaultdict(int)
    keyboard = [
        [
            InlineKeyboardButton("100후", callback_data=str(PLAY_UD_GAME)),
            InlineKeyboardButton("1000후", callback_data=str(PLAY_UD_GAME_1000)),
        ],
        [
            InlineKeyboardButton("종료", callback_data=str(END_GAME)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = "\u2B06\uFE0F UP! & \u2B07\uFE0F DOWN! 게임입니다. \n"
    reply_text += "후후봇이 굴린 주사위보다 높을지 낮을지 맞추는 게임입니다. \n"
    reply_text += "맞추면 상금 2배 틀리면 베팅한돈을 잃습니다. \n"
    reply_text += f"{user}님 얼마를 걸고 게임하시겠습니까? \n"
    await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
    return UPDOWN_ROUTES

async def updown_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    query_data = update.callback_query.data
    # call_query = update.callback_query # Debug
    # await query.edit_message_text(text=f'{call_query}') # Debug
    user = update.effective_user.first_name
    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )

    if context.user_data["updown_game"] == 1:
        game_fee = context.user_data["game_fee"]
        game_prize = context.user_data["prize"] * 2
        context.user_data["prize"] = game_prize
    elif context.user_data["updown_game"] == 2:
        game_fee = context.user_data["game_fee"]
        game_prize = context.user_data["prize"]
    else:
        if query_data == '110':
            game_fee = 100
            game_prize = game_fee
        elif query_data == '111':
            game_fee = 1000
            game_prize = game_fee
        context.user_data["game_fee"] = game_fee
        context.user_data["prize"] = game_prize
        context.user_data["victory"] = 0
    
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
        if context.user_data["updown_game"]:
            bot_dice = context.user_data["bot_dice"]
        else:
            bot_dice = random.randrange(1,7)
            context.user_data["bot_dice"] = bot_dice
        reply_text = f"UP & DOWN 게임을 시작합니다. \n"
        reply_text += f"맞추면 {game_prize}후를 얻고 실패시 {game_fee}후를 잃습니다. \n"
        reply_text += f"후후봇 주사위 눈금은 \U0001f3b2 {bot_dice}입니다. \n "
        reply_text += "UP! or DOWN!"
        keyboard = [
            [
                InlineKeyboardButton("UP!", callback_data=str(UP)),
                InlineKeyboardButton("SAME!(x4)", callback_data=str(SAME)),
                InlineKeyboardButton("DOWN!", callback_data=str(DOWN)),
            ],
            [
                InlineKeyboardButton("종료", callback_data=str(END_GAME)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return UPDOWN_ROUTES
    
def choice_emoji(choice: str):
    if choice == "업!":
        return '\u2B06\uFE0F'
    elif choice == "다운!":
        return '\u2B07\uFE0F'
    elif choice == "동률!":
        return '\U0001f7f0'

async def get_UD_winner_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    업 & 다운 conv
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    query_data = update.callback_query.data
    query = update.callback_query
    await query.answer()
    bot_dice = context.user_data["bot_dice"]
    game_fee = context.user_data["game_fee"]
    game_prize = context.user_data["prize"]

    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )

    data_trans: dict[str, str] = {'101': '업!',
                             '102': '다운!',
                             '103': '동률!'}
    
    user_choice = data_trans[query_data]
    user_emoji = choice_emoji(user_choice)
    new_bot_choice = random.randrange(1,7)
    if bot_dice == new_bot_choice and user_choice != '동률!':
        point_dict[user][day] -= game_fee
        point_dict[user]["total"] -= game_fee
        user_account = point_dict[user]["total"]
        del context.user_data["bot_dice"]
        del context.user_data["game_fee"]
        if context.user_data["updown_game"]:
            del context.user_data["prize"]
        with open( POINT_NAME, 'wb' ) as pf:
            pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

        reply_text = "주사위 눈금이 같습니다. 후.. \n"
        reply_text += f"이전 주사위 : \U0001f3b2 {bot_dice} : {new_bot_choice} \U0001f3b2 : 현재 주사위 \n"
        reply_text += f"{user}님의 선택은 {user_emoji} {user_choice} \n"
        reply_text += "정답을 맞추지 못 하였습니다. \U0001f62d\U0001f62d \n"
        reply_text += f"{user}님의 현재 잔액은 {user_account}후 입니다."
        keyboard = [
            [
                InlineKeyboardButton("다시하기", callback_data=str(LOAD_UPDOWN)),
                InlineKeyboardButton("종료하기", callback_data=str(END)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return START_ROUTES
    elif bot_dice == new_bot_choice and user_choice == '동률!':
        game_prize *= 4
        reply_text = "주사위 눈금이 같습니다. 후.. \n"
        reply_text += f"이전 주사위 : \U0001f3b2 {bot_dice} : {new_bot_choice} \U0001f3b2 : 현재 주사위 \n"
        reply_text += f"{user}님의 선택은 {user_emoji} {user_choice} \n"
        reply_text += f"정답을 맞추셨습니다. 현재 상금 {game_prize}후\n"
        reply_text += "한 번 더 하시겠습니까? \n"

        context.user_data["prize"] = game_prize
        context.user_data["bot_dice"] = new_bot_choice
        context.user_data["updown_game"] = 2
        context.user_data["victory"] += 1
        
        keyboard = [
            [
                InlineKeyboardButton("한 번 더 베팅", callback_data=str(PLAY_UD_GAME)),
                InlineKeyboardButton("그만하기", callback_data=str(CALC_PRIZE)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return UPDOWN_ROUTES
    
    elif bot_dice < new_bot_choice and user_choice != '업!':
        point_dict[user][day] -= game_fee
        point_dict[user]["total"] -= game_fee
        user_account = point_dict[user]["total"]
        del context.user_data["bot_dice"]
        del context.user_data["game_fee"]
        if context.user_data["updown_game"]:
            del context.user_data["prize"]
        with open( POINT_NAME, 'wb' ) as pf:
            pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

        reply_text = "주사위가 굴려졌습니다. 후.. \n"
        reply_text += f"이전 주사위 : \U0001f3b2 {bot_dice}  :  {new_bot_choice} \U0001f3b2 \U0001f199 : 현재 주사위 \n"
        reply_text += f"{user}님의 선택은 {user_emoji} {user_choice} \n"
        reply_text += "정답을 맞추지 못 하였습니다. \U0001f62d\U0001f62d \n"
        reply_text += f"{user}님의 현재 잔액은 {user_account}후 입니다."
        keyboard = [
            [
                InlineKeyboardButton("다시하기", callback_data=str(LOAD_UPDOWN)),
                InlineKeyboardButton("종료하기", callback_data=str(END)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return START_ROUTES
    elif bot_dice < new_bot_choice and user_choice == '업!':
        reply_text = "주사위가 굴려졌습니다. 후.. \n"
        reply_text += f"이전 주사위 : \U0001f3b2 {bot_dice} : {new_bot_choice} \U0001f3b2 \U0001f199 : 현재 주사위 \n"
        reply_text += f"{user}님의 선택은 {user_emoji} {user_choice} \n"
        reply_text += f"정답을 맞추셨습니다. 현재 상금 {game_prize}후\n"
        reply_text += "한 번 더 하시겠습니까? \n"

        context.user_data["prize"] = game_prize
        context.user_data["bot_dice"] = new_bot_choice
        context.user_data["updown_game"] = 1
        context.user_data["victory"] += 1
        
        keyboard = [
            [
                InlineKeyboardButton("한 번 더 베팅", callback_data=str(PLAY_UD_GAME)),
                InlineKeyboardButton("그만하기", callback_data=str(CALC_PRIZE)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return UPDOWN_ROUTES
    
    elif bot_dice > new_bot_choice and user_choice == '다운!':
        reply_text = "주사위가 굴려졌습니다. 후.. \n"
        reply_text += f"이전 주사위 : \U0001f199 \U0001f3b2 {bot_dice} :  {new_bot_choice} \U0001f3b2 : 현재 주사위 \n"
        reply_text += f"{user}님의 선택은 {user_emoji} {user_choice} \n"
        reply_text += f"정답을 맞추셨습니다. 현재 상금 {game_prize}후\n"
        reply_text += "한번더 하시겠습니까? \n"
        
        context.user_data["prize"] = game_prize
        context.user_data["bot_dice"] = new_bot_choice
        context.user_data["updown_game"] = 1
        context.user_data["victory"] += 1

        keyboard = [
            [
                InlineKeyboardButton("한 번 더 베팅", callback_data=str(PLAY_UD_GAME)),
                InlineKeyboardButton("그만하기", callback_data=str(CALC_PRIZE)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return UPDOWN_ROUTES

    elif bot_dice > new_bot_choice and user_choice != '다운!':
        point_dict[user][day] -= game_fee
        point_dict[user]["total"] -= game_fee
        user_account = point_dict[user]["total"]
        del context.user_data["bot_dice"]
        del context.user_data["game_fee"]
        if context.user_data["updown_game"]:
            del context.user_data["prize"]
        with open( POINT_NAME, 'wb' ) as pf:
            pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

        reply_text = "주사위가 굴려졌습니다. 후.. \n"
        reply_text += f"이전 주사위 : \U0001f199 \U0001f3b2 {bot_dice}  : {new_bot_choice} \U0001f3b2 : 현재 주사위 \n"
        reply_text += f"{user}님의 선택은 {user_emoji} {user_choice} \n"
        reply_text += "정답을 맞추지 못 하였습니다. \U0001f62d\U0001f62d \n"
        reply_text += f"{user}님의 현재 잔액은 {user_account}후 입니다."
        keyboard = [
            [
                InlineKeyboardButton("다시하기", callback_data=str(LOAD_UPDOWN)),
                InlineKeyboardButton("종료하기", callback_data=str(END)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return START_ROUTES
    
async def calc_prize_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    query_data = update.callback_query.data
    query = update.callback_query
    await query.answer()
    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    
    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )

    del context.user_data["bot_dice"]
    del context.user_data["game_fee"]
    game_prize = context.user_data["prize"]
    del context.user_data["prize"]
    del context.user_data["updown_game"]
    vic_in_a_row = context.user_data["victory"]
    del context.user_data["victory"]

    if point_dict[user]["victory"] <= vic_in_a_row:
        point_dict[user]["victory"] = vic_in_a_row
        point_dict[user]["vic_prize"] = game_prize

    point_dict[user][day] += game_prize
    point_dict[user]["total"] += game_prize
    user_account = point_dict[user]["total"]
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

    reply_text = "축하합니다!!! \U0001f389\U0001f389\U0001f389 \n"
    reply_text += f"상금 {game_prize}후를 획득하셨습니다. \n"
    reply_text += f"{user}님은 현재 {user_account}후를 보유하고 있습니다. \n"
    keyboard = [
        [
            InlineKeyboardButton("다시하기", callback_data=str(LOAD_UPDOWN)),
            InlineKeyboardButton("종료하기", callback_data=str(END)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
    return START_ROUTES