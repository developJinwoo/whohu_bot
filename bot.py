from telegram.ext import filters, ConversationHandler, Updater, JobQueue
from telegram import ForceReply, Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from typing import Optional, Tuple
import telegram
import asyncio
from typing import Dict
import logging
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CallbackQueryHandler,
    PicklePersistence,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import os
import pickle
from collections import defaultdict
import random
from datetime import datetime, timedelta
import pytz

#from utils import *

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

LNAME               = "leaderboard.pickle"
POINT_NAME          = "point.pickle"
score_dict          = dict()
point_dict          = dict()

START_ROUTES, END_ROUTES, RPS_ROUTES, UPDOWN_ROUTES = range(4)
PLAY_RPS_GAME, PLAY_RPS_GAME_500, PLAY_RPS_GAME_1000, ROCK, PAPPER, SCISSOR, END_GAME = range(7)
MENU_CHU, LUCKY_DICE, LOAD_RPS, LOAD_UPDOWN, END, START_OVER = range(6)
UP, DOWN, SAME, PLAY_UD_GAME, PLAY_UD_GAME_1000, CALC_PRIZE = range(6)

def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])

def set_last_day():
    """ -------------------------------------------------------------------------------------------------------------
    Get the code of last day
    ------------------------------------------------------------------------------------------------------------- """
    global last_day
    l = []

    for d in score_dict.values():
        l += list( d.keys() )

    if l:
        last_day    = max( l )
    else:
        day_time = datetime.now()
        last_day = str(day_time).split(' ')[0]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("\U0001f37d\uFE0F 점메추", callback_data=str(MENU_CHU)),
            InlineKeyboardButton("\U0001f52e 오늘의 운세", callback_data=str(LUCKY_DICE)),
        ],
        [
            InlineKeyboardButton("\u270C\uFE0F \u270A \U0001f590\uFE0F 가위 바위 보!", callback_data=str(LOAD_RPS)),
            InlineKeyboardButton("\U0001f3b2 업 앤 다운", callback_data=str(LOAD_UPDOWN)),
        ],
        [
            InlineKeyboardButton("종료", callback_data=str(END)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("\U0001f916 후후봇입니다. 후..", reply_markup=reply_markup)
    return START_ROUTES

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "명령어 모음 \n /start  : 후후 봇 실행 \n /leaderboard  :  오늘의 한숨왕 \n /my_hu  : 나의 자산(후) 현황 \n" +
        "/hu_is_king  :  현재 자산(후) 랭킹 \n /lucky_hu  :  up&down 연승 랭킹 \n" +
        "'ㅊㅅ' or '출석'  : 출석체크 +1000후 \n 후.. 한번에 +100후"
    )
"""
--------------------------------------------------------------------------------------------------------------------------
업 & 다운 게임
--------------------------------------------------------------------------------------------------------------------------
"""
async def updown_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    query = update.callback_query
    await query.answer()

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

    if context.user_data["updown_game"] == 1:
        game_fee = context.user_data["game_fee"]
        game_prize = context.user_data["prize"] * 2
        context.user_data["prize"] = game_prize
    elif context.user_data["updown_game"] == 2:
        game_fee = context.user_data["game_fee"]
        game_prize = context.user_data["prize"]
    else:
        if query_data == '3':
            game_fee = 100
            game_prize = game_fee
        elif query_data == '4':
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
        reply_text += f"맞추면 {game_prize}후를 얻고 실패시 {game_fee}를 잃습니다. \n"
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
    
    data_trans: dict[str, str] = {'0': '업!',
                             '1': '다운!',
                             '2': '동률!'}
    
    user_choice = data_trans[query_data]
    user_emoji = choice_emoji(user_choice)
    new_bot_choice = random.randrange(1,7)
    if bot_dice == new_bot_choice and user_choice != '동률!':
        point_dict[user][last_day] -= game_fee
        point_dict[user]["total"] -= game_fee
        user_account = point_dict[user]["total"]
        del context.user_data["bot_dice"]
        del context.user_data["game_fee"]
        if context.user_data["updown_game"]:
            del context.user_data["prize"]

        reply_text = "주사위 눈금이 같습니다. 후.. \n"
        reply_text += f"이전 주사위 : \U0001f3b2 {bot_dice} : {new_bot_choice} \U0001f3b2 : 현재 주사위 \n"
        reply_text += f"{user}님의 선택은 {user_choice} \n"
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
        point_dict[user][last_day] -= game_fee
        point_dict[user]["total"] -= game_fee
        user_account = point_dict[user]["total"]
        del context.user_data["bot_dice"]
        del context.user_data["game_fee"]
        if context.user_data["updown_game"]:
            del context.user_data["prize"]

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
        point_dict[user][last_day] -= game_fee
        point_dict[user]["total"] -= game_fee
        user_account = point_dict[user]["total"]
        del context.user_data["bot_dice"]
        del context.user_data["game_fee"]
        if context.user_data["updown_game"]:
            del context.user_data["prize"]

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
    del context.user_data["bot_dice"]
    del context.user_data["game_fee"]
    game_prize = context.user_data["prize"]
    del context.user_data["prize"]
    del context.user_data["updown_game"]
    vic_in_a_row = context.user_data["victory"]
    del context.user_data["victory"]

    if point_dict[user]["victory"] < vic_in_a_row:
        point_dict[user]["victory"] = vic_in_a_row
        point_dict[user]["vic_prize"] = game_prize

    point_dict[user][last_day] += game_prize
    point_dict[user]["total"] += game_prize
    user_account = point_dict[user]["total"]
    
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
    ## save the dict
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )
    return START_ROUTES

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
            InlineKeyboardButton("500후", callback_data=str(PLAY_RPS_GAME_500)),
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
    if query_data == '0':
        game_fee = 100
    elif query_data == '1':
        game_fee = 500
    elif query_data == '2':
        game_fee = 1000

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
    
    data_trans: dict[str, str] = {'5': '가위',
                             '4': '보',
                             '3': '바위'}
    rules: dict[str, str] = {'바위': '가위',
                             '가위': '보',
                             '보': '바위'}
    
    user_choice = data_trans[query_data]
    bot_choice = get_bot_choice()
    user_emoji = get_emoji(user_choice)
    bot_emoji = get_emoji(bot_choice)

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
        point_dict[user][last_day] += game_fee
        point_dict[user]["total"] += game_fee
        user_account += game_fee
        reply_text = f"축하합니다. {user}님이 이겼습니다. 후!! \n"
        reply_text += f"후후 봇 : {bot_emoji} / {user_emoji} : {user}님 \n"
        reply_text += f"승리 상금 {win_prize}후를 적립해 드립니다.\n"
        reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
        with open( POINT_NAME, 'wb' ) as pf:
            pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )
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
        point_dict[user][last_day] -= game_fee 
        point_dict[user]["total"] -= game_fee
        user_account -= game_fee
        reply_text = "후.. 졌습니다. 후.. \n"
        reply_text += f"후후 봇 : {bot_emoji} / {user_emoji} : {user}님 \n"
        reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
        with open( POINT_NAME, 'wb' ) as pf:
            pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )
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

async def dice_cmd_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    오늘의 운세 conv
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    rand_num = random.randrange(1,4)
    keyboard = [
        [
            InlineKeyboardButton("다시하기", callback_data=str(LUCKY_DICE)),
            InlineKeyboardButton("종료하기", callback_data=str(END)),
        ],
        [
            InlineKeyboardButton("-= 개발중 =-", callback_data=str(END)),
        ]
    ]
    
    if rand_num == 1:
        text = f'{user}님의 행운은 \U0001f631 최악입니다. -1000후'
        point_dict[user][last_day] -= 1000
        point_dict[user]["total"] -= 1000
    elif rand_num == 2:
        text = f'{user}님의 행운은 \U0001f610 보통입니다.'
    elif rand_num == 3:
        text = f'{user}님의 행운은 \U0001f340 최상입니다. +1000후'
        point_dict[user][last_day] += 1000
        point_dict[user]["total"] += 1000
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f'오늘의 운세 \n {text}', reply_markup=reply_markup)
    
    return START_ROUTES

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

async def show_money_leads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    Show the hu money leaderboard 
    ------------------------------------------------------------------------------------------------------------- """
    txt         = f"\U0001F4C5 LEADERBOARD OF DAY { last_day }\n\n"
    money_lead_dict   = dict()

    for user in point_dict:
        if "total" in point_dict[user]:
            money_lead_dict[user] = point_dict[user]["total"]

    sorting     = lambda x: ( x[ 1 ], x[ 0 ] )
    money_lead_list   = [ ( k, v ) for k, v in sorted( money_lead_dict.items(), key=sorting, reverse=True) ]
    for r, ( u, s ) in enumerate( money_lead_list, 1 ):
        if r == 1:
            medal   = "\U0001F947"
        elif r == 2:
            medal   = "\U0001F948"
        elif r == 3:
            medal   = "\U0001F949"
        else:
            medal   = ''
        txt     += f"{ r }. { medal } @{ u } ( { s }후 )\n"
    await update.message.reply_text((f"{txt}"))

async def show_victory_leads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    Show the victory of up & down in a row leaderboard 
    ------------------------------------------------------------------------------------------------------------- """
    txt         = f"\U0001F4C5 LEADERBOARD OF DAY { last_day }\n\n"
    vic_lead_dict   = dict()
    vic_prize_lead_dict   = dict()

    for user in point_dict:
        if "victory" in point_dict[user]:
            vic_lead_dict[user] = point_dict[user]["victory"]
            vic_prize_lead_dict[user] = point_dict[user]["vic_prize"]

    sorting     = lambda x: ( x[ 1 ], x[ 0 ] )
    vic_lead_list   = [ ( k, v ) for k, v in sorted( vic_lead_dict.items(), key=sorting, reverse=True) ]
    for r, ( u, s ) in enumerate( vic_lead_list, 1 ):
        if r == 1:
            medal   = "\U0001F947"
        elif r == 2:
            medal   = "\U0001F948"
        elif r == 3:
            medal   = "\U0001F949"
        else:
            medal   = ''
        vic_prize = vic_prize_lead_dict[u]
        txt     += f"{ r }. { medal } @{ u } ( { s }연승! {vic_prize}후 획득! )\n"
    await update.message.reply_text((f"{txt}"))

def show_day_lead( update, context ):
    """ -------------------------------------------------------------------------------------------------------------
    Show the leaderboard of the day
    ------------------------------------------------------------------------------------------------------------- """
    if len( score_dict ) == 0:
        txt     = "No users have played yet."
        return

    txt         = f"\U0001F4C5 LEADERBOARD OF DAY { last_day }\n\n"
    lead_dict   = dict()

    # get users scores
    for user in score_dict:
        if last_day in score_dict[ user ]:
            lead_dict[ user ]   = score_dict[ user ][ last_day ]

    # sort the leaderboard
    sorting     = lambda x: ( x[ 1 ], x[ 0 ].lower() )
    lead_list   = [ ( k, v ) for k, v in sorted( lead_dict.items(), key=sorting, reverse=True) ]

    # print the leaderboard
    for r, ( u, s ) in enumerate( lead_list, 1 ):
        if r == 1:
            medal   = "\U0001F947"
        elif r == 2:
            medal   = "\U0001F948"
        elif r == 3:
            medal   = "\U0001F949"
        else:
            medal   = ''
        txt     += f"{ r }. { medal } @{ u } ( { s } )\n"
    return txt

async def show_leads( update, context ):
    """ -------------------------------------------------------------------------------------------------------------
    Show the leaderboards
    ------------------------------------------------------------------------------------------------------------- """
    set_last_day()
    txt = show_day_lead( update, context )
    await update.message.reply_text(f"{txt}")

async def my_point_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    현재 내 후 포인트 현황
    ------------------------------------------------------------------------------------------------------------- """
    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    user = update.effective_user.first_name
    total = point_dict[user]["total"]

    await update.message.reply_text(f"{user}님의 자산현황 \n 오늘 {point_dict[user][day]}후 획득! \n 총 자산 {total}후")

async def jum_me_chu_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    점심 메뉴 추천 conv
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("한식", callback_data=str(END)),
            InlineKeyboardButton("중식", callback_data=str(END)),
            InlineKeyboardButton("일식", callback_data=str(END)),
            InlineKeyboardButton("랜덤", callback_data=str(END)),
        ],
        [
            InlineKeyboardButton("-= 개발중 =-", callback_data=str(START_OVER)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"먹지마!!", reply_markup=reply_markup)
    
    return END_ROUTES

async def chul_seok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    출석 체크
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    #day ="2023-04-12"
    check = "출석"
    if user not in point_dict:
        point_dict[user] = defaultdict(int)
    
    if point_dict[user][check] == day:
        await update.message.reply_text(f"{user}님은 이미 출석하셨습니다.")
    else:
        point_dict[user][check] = day
        point_dict[user][day] += 1000
        point_dict[user]["total"] += 1000
        await update.message.reply_text(f"{user}님 {day} 출석!! \n 출석 보상 +1000후 ")
    ## save the dict
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

async def go_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    퇴근 체크
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    if user not in point_dict:
        point_dict[user] = defaultdict(int)

    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    _time = str(day_time).split(' ')[1]
    _time = _time.split('.')[0]

    now = datetime.now(pytz.timezone('Asia/Seoul'))
    scheduled_time_5 = datetime(now.year, now.month, now.day, 17, 0, 0, tzinfo=pytz.timezone('Asia/Seoul'))
    scheduled_time_6 = datetime(now.year, now.month, now.day, 18, 0, 0, tzinfo=pytz.timezone('Asia/Seoul'))
    sch_time_5 = str(scheduled_time_5).split(' ')[1]
    sch_time_5 = sch_time_5.split('+')[0]
    sch_time_6 = str(scheduled_time_6).split(' ')[1]
    sch_time_6 = sch_time_6.split('+')[0]

    time_1 = datetime.strptime(_time,"%H:%M:%S")
    time_2 = datetime.strptime(sch_time_5,"%H:%M:%S")
    time_3 = datetime.strptime(sch_time_6,"%H:%M:%S")
    time_interval_5 = time_2 - time_1
    time_interval_6 = time_3 - time_1
    
    check = "퇴근"
    if point_dict[user][check] == day:
        await update.message.reply_text(f"{user}님은 이미 퇴근하셨습니다.")
    else:
        if time_interval_5.days >= 0:
            hms_5 = str(timedelta(seconds=time_interval_5.seconds))
            h5,m5,s5 = hms_5.split(':')
            hms_6 = str(timedelta(seconds=time_interval_6.seconds))
            h6,m6,s6 = hms_6.split(':')
            reply_text = f"퇴근 까지 {h5}시간 {m5}분 {s5}초 남았습니다. - 17시 퇴근 \n"
            reply_text += f"퇴근 까지 {h6}시간 {m6}분 {s6}초 남았습니다. - 18시 퇴근 \n"
            await update.message.reply_text(text=reply_text)
        else:
            point_dict[user][check] = day
            point_dict[user][day] += 1000
            point_dict[user]["total"] += 1000
            await update.message.reply_text(f"{user}님 {day} 퇴근!! \n 오늘 하루 고생하셨습니다. +1000후 ")
    ## save the dict
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

async def get_hu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #u_id = user.id
    user = update.effective_user.first_name
    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    if user not in score_dict:
        score_dict[ user ] = defaultdict(int)
    if user not in point_dict:
        point_dict[user] = defaultdict(int)

    score = 1
    # add day and score to the dict
    score_dict[ user ][ day ] += score
    point_dict[user][day] += 100
    point_dict[user]["total"] += 100

    ## save the dict
    with open( LNAME, 'wb' ) as f:
        pickle.dump( score_dict, f, protocol=pickle.HIGHEST_PROTOCOL )
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="힘들때 다시 찾아와줘 후..")
    return ConversationHandler.END

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = -838335379
    context.bot.send_message(chat_id=chat_id, text='퇴근하자~')

async def daily_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = -838335379
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    scheduled_time = datetime(now.year, now.month, now.day, 15, 20, 0, tzinfo=pytz.timezone('Asia/Seoul'))  # 매일 오후 5시
    if scheduled_time < now:
        scheduled_time += timedelta(days=1)  # 이미 지난 시간이면 다음날로 예약
    JobQueue.run_daily(send_message, scheduled_time, days=(0, 1, 2, 3, 4), context=chat_id)

async def bot_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    TOKEN = "5796035729:AAEiMHlyofIjoFyct-QEsDKtOh032bmvMvM"
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text='Hello World')

    await update.message.reply_text(chat_id)

def main() -> None:
    """Start the bot."""
    global score_dict
    global point_dict
    # Create the Application and pass it your bot's token.
    with open( "TOKEN.txt", 'r' ) as f:
        TOKEN = f.read()
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(TOKEN).persistence(persistence).build()

    # if exists, load the last pickled dict of leaderboard
    if os.path.isfile( LNAME ):
        with open( LNAME, "rb" ) as f:
            score_dict = pickle.load( f )

    if os.path.isfile( POINT_NAME ):
        with open( POINT_NAME, "rb" ) as f:
            point_dict = pickle.load( f )

    set_last_day()

    conv_handler22 = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(jum_me_chu_conv, pattern="^" + str(MENU_CHU) + "$"),
                CallbackQueryHandler(dice_cmd_conv, pattern="^" + str(LUCKY_DICE) + "$"),
                CallbackQueryHandler(rock_papper_scissor_conv, pattern="^" + str(LOAD_RPS) + "$"),
                CallbackQueryHandler(updown_conv, pattern="^" + str(LOAD_UPDOWN) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            END_ROUTES: [
                CallbackQueryHandler(start, pattern="^" + str(START_OVER) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            RPS_ROUTES: [
                CallbackQueryHandler(rock_papper_scissor_play, pattern="^" + str(PLAY_RPS_GAME) + "$"),
                CallbackQueryHandler(rock_papper_scissor_play, pattern="^" + str(PLAY_RPS_GAME_500) + "$"),
                CallbackQueryHandler(rock_papper_scissor_play, pattern="^" + str(PLAY_RPS_GAME_1000) + "$"),
                CallbackQueryHandler(get_RPS_winner_conv, pattern="^" + str(ROCK) + "$"),
                CallbackQueryHandler(get_RPS_winner_conv, pattern="^" + str(PAPPER) + "$"),
                CallbackQueryHandler(get_RPS_winner_conv, pattern="^" + str(SCISSOR) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END_GAME) + "$"),
            ],
            UPDOWN_ROUTES: [
                CallbackQueryHandler(updown_play, pattern="^" + str(PLAY_UD_GAME) + "$"),
                CallbackQueryHandler(updown_play, pattern="^" + str(PLAY_UD_GAME_1000) + "$"),
                CallbackQueryHandler(get_UD_winner_conv, pattern="^" + str(UP) + "$"),
                CallbackQueryHandler(get_UD_winner_conv, pattern="^" + str(DOWN) + "$"),
                CallbackQueryHandler(get_UD_winner_conv, pattern="^" + str(SAME) + "$"),
                CallbackQueryHandler(calc_prize_conv, pattern="^" + str(CALC_PRIZE) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END_GAME) + "$"),
            ]

        },
        fallbacks=[CommandHandler("end", end)],
    )
    application.add_handler(conv_handler22)

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", show_leads))
    application.add_handler(CommandHandler("hu_is_king", show_money_leads))
    application.add_handler(CommandHandler("lucky_hu", show_victory_leads))
    application.add_handler(CommandHandler("my_hu", my_point_cmd))
    

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.Regex(r'(a?후)'), get_hu))
    application.add_handler(MessageHandler(filters.Regex(r'ㅊㅅ'), chul_seok))
    application.add_handler(MessageHandler(filters.Regex(r'출석'), chul_seok))
    application.add_handler(MessageHandler(filters.Regex(r'ㅌㄱ'), go_home))
    #application.add_handler(MessageHandler(filters.Regex(r'test'), bot_test))
    
    #updater = Updater(TOKEN)
    #updater.update_queue(daily_job)
    #JobQueue.run_repeating(daily_job, interval=60, first=0)
    #JobQueue.start(daily_job)
    #updater.start_polling()

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()

