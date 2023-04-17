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

import config

LNAME = config.LNAME
POINT_NAME = config.POINT_NAME

END_ROUTES = config.END_ROUTES
END_GAME, END, START_OVER = config.END_GAME, config.END, config.START_OVER
SLOT_ROUTES, PLAY_SLOT, SLOT_INFO, SLOT_OPEN, GET_SLOT_PRIZE =config.SLOT_ROUTES, config.PLAY_SLOT, config.SLOT_INFO, config.SLOT_OPEN, config.GET_SLOT_PRIZE

global day
day_time = datetime.now()
day = str(day_time).split(' ')[0]

if os.path.isfile( LNAME ):
    with open( LNAME, "rb" ) as f:
        score_dict = pickle.load( f )

if os.path.isfile( POINT_NAME ):
    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )


async def slot_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    query = update.callback_query
    await query.answer()

    context.user_data["slot_game"] = defaultdict(int)
    context.user_data["slot_game_cnt"] = defaultdict(int)
    context.user_data["slot_game"] = 0
    context.user_data["slot_game_cnt"] = 0
    keyboard = [
        [
            InlineKeyboardButton("게임 하기", callback_data=str(SLOT_OPEN)),
            InlineKeyboardButton("후후 슬롯 안내", callback_data=str(SLOT_INFO)),
        ],
        [
            InlineKeyboardButton("종료", callback_data=str(END_GAME)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = "\U0001f3b0 후후 슬롯머신에 온것을 환영합니다. \n"
    reply_text += "같은 그림 3개를 맞추면 되는 간단한 게임입니다. \n"
    reply_text += "\U0001f48e,\U0001f48e,\U0001f48e 보석 3개를 맞춰 500만후의 주인공이 되세요! \n"
    reply_text += f"{user}님 후후 슬롯머신 게임을 하시겠습니까? \n"
    await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
    return SLOT_ROUTES

def roll_slot():
    casino_list = ["\U0001f48e", "\U0001f514", "\U0001f4b0", "\U0001f4a3", "\u2764\uFE0F","\U0001f340","\U0001f378", "\U0001f4b5",
                "\U0001f4b0",
                "\U0001f4b5","\U0001f4b5",
                "\U0001f340","\U0001f340","\U0001f340",
                "\u2764\uFE0F","\u2764\uFE0F","\u2764\uFE0F","\u2764\uFE0F",
                "\U0001f378", "\U0001f378", "\U0001f378", "\U0001f378", "\U0001f378", 
                "\U0001f514","\U0001f514","\U0001f514","\U0001f514","\U0001f514","\U0001f514",
                ]
    
    result_list = []
    sub_list_1 = []
    sub_list_2 = []
    for _ in range(3):
        sub_list_1.append(random.choice(casino_list))
        result_list.append(random.choice(casino_list))
        sub_list_2.append(random.choice(casino_list))
    return sub_list_1, result_list, sub_list_2

async def slot_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    query_data = update.callback_query.data

    game_fee = 500
    context.user_data["game_fee"] = game_fee
    user = update.effective_user.first_name
    
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
        if context.user_data["slot_game"]:
            point_dict[user][day] -= game_fee
            point_dict[user]["total"] -= game_fee
            user_account = point_dict[user]["total"]

            context.user_data["slot_game_cnt"] += 1
            slot_cnt = context.user_data["slot_game_cnt"]
            sub_1, result, sub_2 = roll_slot()
            with open( POINT_NAME, 'wb' ) as pf:
                pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )
            if result[0] == result[1] and result[0] == result[2]:
                prize = slot_money(result[0])
                keyboard = [
                    [
                        InlineKeyboardButton("상금 수령하기", callback_data=str(GET_SLOT_PRIZE)),
                        InlineKeyboardButton("상금 포기", callback_data=str(END_GAME)),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                reply_text = f"후후 슬롯 {slot_cnt}회차째 당첨!! \U0001f389 \U0001f389 \U0001f389 \n"
                reply_text += "--------------------------------------------------------------- \n"
                reply_text += f"        [{sub_1[0]}],[{sub_1[1]}],[{sub_1[2]}]    \n"
                reply_text += f">>> [{result[0]}],[{result[1]}],[{result[2]}] <<< \n"
                reply_text += f"        [{sub_2[0]}],[{sub_2[1]}],[{sub_2[2]}]    \n"
                reply_text += "--------------------------------------------------------------- \n"
                reply_text += f"{user}님 획득 당첨후 : {prize}후 \n"
                await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
                return SLOT_ROUTES
            else:

                keyboard = [
                    [
                        InlineKeyboardButton("Roll(-500후)", callback_data=str(PLAY_SLOT)),
                        InlineKeyboardButton("게임 종료", callback_data=str(END_GAME)),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                reply_text = f"후후 슬롯 {slot_cnt}회차 진행중... \n"
                reply_text += "--------------------------------------------------------------- \n"
                reply_text += f"        [{sub_1[0]}],[{sub_1[1]}],[{sub_1[2]}]    \n"
                reply_text += f">>> [{result[0]}],[{result[1]}],[{result[2]}] <<< \n"
                reply_text += f"        [{sub_2[0]}],[{sub_2[1]}],[{sub_2[2]}]    \n"
                reply_text += "--------------------------------------------------------------- \n"
                reply_text += "실패 \U0001f62d\U0001f62d\U0001f62d \n"
                reply_text += f"{user}님 현재 잔액 : {user_account} \n"
                await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
                return SLOT_ROUTES

            
        else:
            context.user_data["slot_game"] = 1
            sub_1, result, sub_2 = roll_slot()
            
            keyboard = [
                [
                    InlineKeyboardButton("Roll(-500후)", callback_data=str(PLAY_SLOT)),
                    InlineKeyboardButton("게임 종료", callback_data=str(END_GAME)),
                ],

            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            reply_text = "한방을 노린다. 후.. \n"
            reply_text += "--------------------------------------------------------------- \n"
            reply_text += f"        [{sub_1[0]}],[{sub_1[1]}],[{sub_1[2]}]    \n"
            reply_text += f">>> [{result[0]}],[{result[1]}],[{result[2]}] <<< \n"
            reply_text += f"        [{sub_2[0]}],[{sub_2[1]}],[{sub_2[2]}]    \n"
            reply_text += "--------------------------------------------------------------- \n"
            await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
            return SLOT_ROUTES
    
async def slot_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    query_data = update.callback_query.data

    game_fee = context.user_data["game_fee"]
    user = update.effective_user.first_name
    point_dict[user][day] -= game_fee
    point_dict[user]["total"] -= game_fee
    user_account = point_dict[user]["total"]

    context.user_data["slot_game_cnt"] += 1
    slot_cnt = context.user_data["slot_game_cnt"]

    sub_1, result, sub_2 = roll_slot()
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

    if result[0] == result[1] and result[0] == result[2]:
        prize = slot_money(result[0])
        context.user_data["slot_prize"] = prize
        keyboard = [
            [
                InlineKeyboardButton("상금 수령하기", callback_data=str(GET_SLOT_PRIZE)),
                InlineKeyboardButton("상금 포기", callback_data=str(END_GAME)),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_text = f"후후 슬롯 {slot_cnt}회차째 당첨!! \U0001f389 \U0001f389 \U0001f389 \n"
        reply_text += "--------------------------------------------------------------- \n"
        reply_text += f"        [{sub_1[0]}],[{sub_1[1]}],[{sub_1[2]}]    \n"
        reply_text += f">>> [{result[0]}],[{result[1]}],[{result[2]}] <<< \n"
        reply_text += f"        [{sub_2[0]}],[{sub_2[1]}],[{sub_2[2]}]    \n"
        reply_text += "--------------------------------------------------------------- \n"
        reply_text += f"{user}님 획득 당첨후 : {prize}후 \n"
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return SLOT_ROUTES
    else:

        keyboard = [
            [
                InlineKeyboardButton("Roll(-500후)", callback_data=str(SLOT_OPEN)),
                InlineKeyboardButton("게임 종료", callback_data=str(END_GAME)),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_text = f"후후 슬롯 {slot_cnt}회차 진행중... \n"
        reply_text += "--------------------------------------------------------------- \n"
        reply_text += f"        [{sub_1[0]}],[{sub_1[1]}],[{sub_1[2]}]    \n"
        reply_text += f">>> [{result[0]}],[{result[1]}],[{result[2]}] <<< \n"
        reply_text += f"        [{sub_2[0]}],[{sub_2[1]}],[{sub_2[2]}]    \n"
        reply_text += "--------------------------------------------------------------- \n"
        reply_text += "실패 \U0001f62d\U0001f62d\U0001f62d \n"
        reply_text += f"{user}님 현재 잔액 : {user_account} \n"
        await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
        return SLOT_ROUTES

async def get_slot_prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user.first_name

    prize = context.user_data["slot_prize"]
    point_dict[user][day] += prize
    point_dict[user]["total"] += prize
    user_account = point_dict[user]["total"]

    #del context.user_data["slot_prize"]
    del context.user_data["slot_game_cnt"]
    #del context.user_data["slot_game"]
    del context.user_data["game_fee"]
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

    keyboard = [
        [
            InlineKeyboardButton("게임하기", callback_data=str(SLOT_OPEN)),
            InlineKeyboardButton("종료", callback_data=str(END_GAME)),
        ],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = f"당첨을 축하드립니다!! \U0001f389 \U0001f389 \U0001f389 \n"
    reply_text += f"{user}님 현재 잔액 : {user_account} \n"
    await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
    return SLOT_ROUTES

def slot_money(emoji):
    if emoji == "\U0001f48e":
        # 보석
        return 5000000
    elif emoji == "\U0001f4b0":
        # 돈주머니
        return 1000000
    elif emoji == "\U0001f4b5":
        # 달러
        return 500000
    elif emoji == "\U0001f340":
        # 네잎크로바
        return 200000
    elif emoji == "\u2764\uFE0F":
        # 하트
        return 100000
    elif emoji == "\U0001f378":
        # 칵테일
        return 50000
    elif emoji == "\U0001f514":
        # 종
        return 10000
    
async def slot_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    query_data = update.callback_query.data
    # call_query = update.callback_query # Debug
    # await query.edit_message_text(text=f'{call_query}') # Debug
    user = update.effective_user.first_name

    keyboard = [
        [
            InlineKeyboardButton("게임하기", callback_data=str(SLOT_OPEN)),
            InlineKeyboardButton("종료", callback_data=str(END_GAME)),
        ],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    """
    보석 : 5,000,000
    돈주머니 : 1,000,000
    달러 : 500,000
    네잎 : 200,000
    하트 : 100,000
    칵테일 : 50,000
    종 : 10,000
    """
    reply_text = "\U0001f3b0 후후 슬롯머신 안내입니다. \n"
    reply_text += "슬롯머신 가운데 줄에 같은 그림 3개가 위치하면 상금을 얻습니다. 후.. \n"
    reply_text += "-------------------------------------------------------------------------------------------- \n"
    reply_text += "\U0001f48e,\U0001f48e,\U0001f48e 보석               : 5,000,000후 \n"
    reply_text += "\U0001f4b0,\U0001f4b0,\U0001f4b0 돈 주머니     : 1,000,000후 \n" 
    reply_text += "\U0001f4b5,\U0001f4b5,\U0001f4b5 달러               :    500,000후 \n"
    reply_text += "\U0001f340,\U0001f340,\U0001f340 네잎 크로버 :    200,000후 \n"
    reply_text += "\u2764\uFE0F,\u2764\uFE0F,\u2764\uFE0F 하트               :    100,000후 \n"
    reply_text += "\U0001f378,\U0001f378,\U0001f378 칵테일           :      50,000후 \n"
    reply_text += "\U0001f514,\U0001f514,\U0001f514 종                    :      10,000후 \n"
    reply_text += "\U0001f4a3,\U0001f4a3,\U0001f4a3 폭탄                :        꽝 \n"
    reply_text += "-------------------------------------------------------------------------------------------- \n"
    await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
    return SLOT_ROUTES