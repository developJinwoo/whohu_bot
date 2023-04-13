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

START_ROUTES, END_ROUTES, RPS_ROUTES = range(3)
PLAY_RPS_GAME, PLAY_RPS_GAME_500, PLAY_RPS_GAME_1000, ROCK, PAPPER, SCISSOR, END_GAME = range(7)
MENU_CHU, LUCKY_DICE, LOAD_RPS, END, START_OVER = range(5)

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
            InlineKeyboardButton("\U0001f3b2 오늘의 운세", callback_data=str(LUCKY_DICE)),
        ],
        [
            InlineKeyboardButton("\u270C\uFE0F \u270A \U0001f590\uFE0F 가위 바위 보!", callback_data=str(LOAD_RPS)),
            InlineKeyboardButton("종료", callback_data=str(END)),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("\U0001f916 후후봇입니다. 후..", reply_markup=reply_markup)
    return START_ROUTES

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "명령어 모음 \n /start  : 후후 봇 실행 \n /leaderboard  :  오늘의 한숨왕 \n /my_hu  : 나의 자산(후) 현황 \n" +
        "/hu_is_king  :  현재 자산(후) 랭킹 \n" +
        "'ㅊㅅ' or '출석'  : 출석체크 +1000후 \n 후.. 한번에 +100후"
    )

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
    query_data = update.callback_query.data
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
        text = f'{user}님의 행운은 \U0001f631 최악입니다.'
    elif rand_num == 2:
        text = f'{user}님의 행운은 \U0001f610 보통입니다.'
    elif rand_num == 3:
        text = f'{user}님의 행운은 \U0001f340 최상입니다.'
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
            END_ROUTES: [
                CallbackQueryHandler(start, pattern="^" + str(START_OVER) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ]
        },
        fallbacks=[CommandHandler("end", end)],
    )
    application.add_handler(conv_handler22)

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", show_leads))
    application.add_handler(CommandHandler("hu_is_king", show_money_leads))
    application.add_handler(CommandHandler("my_hu", my_point_cmd))

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.Regex(r'(a?후)'), get_hu))
    application.add_handler(MessageHandler(filters.Regex(r'ㅊㅅ'), chul_seok))
    application.add_handler(MessageHandler(filters.Regex(r'출석'), chul_seok))
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

