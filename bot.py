from telegram.ext import filters, ConversationHandler, Updater, JobQueue
from telegram import ForceReply, Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from typing import Optional, Tuple
import telegram
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
    CallbackContext,
    MessageHandler,
    filters,
)
import os
import pickle
from collections import defaultdict
import random
from datetime import datetime, timedelta
import pytz
import requests
import schedule
from apscheduler.schedulers.blocking import BlockingScheduler
import asyncio
import aiofiles

import config
from slot_machine import slot_conv, slot_play, slot_info, slot_open, get_slot_prize
from updown_game import updown_conv, updown_play, get_UD_winner_conv, calc_prize_conv
from RPS_game import rock_papper_scissor_conv, rock_papper_scissor_play, get_RPS_winner_conv

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

LNAME = config.LNAME
POINT_NAME = config.POINT_NAME
score_dict          = dict()
point_dict          = dict()

START_ROUTES, END_ROUTES = config.START_ROUTES, config.END_ROUTES
RPS_ROUTES, UPDOWN_ROUTES, SLOT_ROUTES = config.RPS_ROUTES, config.UPDOWN_ROUTES, config.SLOT_ROUTES
PLAY_RPS_GAME, PLAY_RPS_GAME_500, PLAY_RPS_GAME_1000 = config.PLAY_RPS_GAME, config.PLAY_RPS_GAME_500, config.PLAY_RPS_GAME_1000
ROCK, PAPPER, SCISSOR = config.ROCK, config.PAPPER, config.SCISSOR
MENU_CHU, LUCKY_DICE = config.MENU_CHU, config.LUCKY_DICE
LOAD_RPS, LOAD_UPDOWN, LOAD_SLOT = config.LOAD_RPS, config.LOAD_UPDOWN, config.LOAD_SLOT
UP, DOWN, SAME = config.UP, config.DOWN, config.SAME
PLAY_UD_GAME, PLAY_UD_GAME_1000, CALC_PRIZE = config.PLAY_UD_GAME, config.PLAY_UD_GAME_1000, config.CALC_PRIZE
END_GAME, END, START_OVER = config.END_GAME, config.END, config.START_OVER
PLAY_SLOT, SLOT_INFO, SLOT_OPEN, GET_SLOT_PRIZE = config.PLAY_SLOT, config.SLOT_INFO, config.SLOT_OPEN, config.GET_SLOT_PRIZE

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
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
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
            InlineKeyboardButton("\U0001f3b0 슬롯머신", callback_data=str(LOAD_SLOT)),
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
        "/donation  :  1000후 기부 \n end or /end  :  후후 봇 종료 \n" +
        "'ㅊㅅ' or '출석'  : 출석체크 +1000후 \n 후.. 한번에 +100후"
    )

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
    Show the hu is king
    ------------------------------------------------------------------------------------------------------------- """
    txt         = f"\U0001F4C5 LEADERBOARD OF DAY { last_day }\n\n"
    money_lead_dict   = dict()
    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )
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

async def donation_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    포인트 기부
    ------------------------------------------------------------------------------------------------------------- """
    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    user = update.effective_user.first_name

    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )

    point_dict[user][day] -= 1000
    point_dict[user]["total"] -= 1000
    
    whohu_bot = "whohu_bot"
    if whohu_bot not in point_dict:
        point_dict[whohu_bot] = defaultdict(int)
        point_dict[whohu_bot]["donation"] = 0
        point_dict[whohu_bot]["total"] = 0
    point_dict[whohu_bot]["donation"] += 1000
    point_dict[whohu_bot]["total"] += 1000
    donation = point_dict[whohu_bot]["donation"]

    ## save the dict
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )
    await update.message.reply_text(f"1000후 기부하셨습니다. \n 현재 기부 잔액 {donation}후")

async def get_donation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    포인트 구걸
    ------------------------------------------------------------------------------------------------------------- """
    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    user = update.effective_user.first_name
    
    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )
    whohu_bot = "whohu_bot"
    donation = point_dict[whohu_bot]["donation"]
    if donation > 0:
        point_dict[user][day] += donation
        point_dict[user]["total"] += donation
        point_dict[whohu_bot]["donation"] = 0
        point_dict[whohu_bot]["total"] = 0
        ## save the dict
        with open( POINT_NAME, 'wb' ) as pf:
            pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )
        await update.message.reply_text(f"구걸에 성공하여 {donation}후 획득하셨습니다!!")
    else:
        await update.message.reply_text("현재 기부된 후가 없습니다. \n 당신의 안쓰러운 처지를 어필해 보세요.")

async def my_point_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    현재 내 후 포인트 현황
    ------------------------------------------------------------------------------------------------------------- """
    day_time = datetime.now()
    day = str(day_time).split(' ')[0]
    user = update.effective_user.first_name
    
    with open( POINT_NAME, "rb" ) as f:
        point_dict = pickle.load( f )
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
    chat_id = update.effective_chat.id
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    scheduled_time = datetime(now.year, now.month, now.day, 15, 20, 0, tzinfo=pytz.timezone('Asia/Seoul'))  # 매일 오후 5시
    #chat_id = update.effective_chat.id
    chat_id = -838335379
    text = "후.. 후이팅!!"
    text2 = "후.. 후이팅!!22222"
    await context.bot.send_message(chat_id=chat_id, text=text)
    if now.hour >= 9: #and now.minute == 20:
        await context.bot.send_message(chat_id=chat_id, text=text2)

async def bot_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=f'chat id : {chat_id}')

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
                CallbackQueryHandler(slot_conv, pattern="^" + str(LOAD_SLOT) + "$"),
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
            ],
            SLOT_ROUTES: [
                CallbackQueryHandler(slot_open, pattern="^" + str(SLOT_OPEN) + "$"),
                CallbackQueryHandler(slot_info, pattern="^" + str(SLOT_INFO) + "$"),
                CallbackQueryHandler(slot_play, pattern="^" + str(PLAY_SLOT) + "$"),
                CallbackQueryHandler(get_slot_prize, pattern="^" + str(GET_SLOT_PRIZE) + "$"),
  
                CallbackQueryHandler(end, pattern="^" + str(END_GAME) + "$"),
            ],


        },
        fallbacks=[CommandHandler("end", end)],
    )
    application.add_handler(conv_handler22)

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", show_leads))
    application.add_handler(CommandHandler("hu_is_king", show_money_leads))
    application.add_handler(CommandHandler("lucky_hu", show_victory_leads))
    application.add_handler(CommandHandler("my_hu", my_point_cmd))
    application.add_handler(CommandHandler("donation", donation_cmd))
    

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.Regex(r'(a?후)'), get_hu))
    application.add_handler(MessageHandler(filters.Regex(r'ㅊㅅ'), chul_seok))
    application.add_handler(MessageHandler(filters.Regex(r'출석'), chul_seok))
    application.add_handler(MessageHandler(filters.Regex(r'ㅌㄱ'), go_home))
    application.add_handler(MessageHandler(filters.Regex(r'end'), end))
    application.add_handler(MessageHandler(filters.Regex(r'구걸'), get_donation))
    application.add_handler(MessageHandler(filters.Regex(r'test'), bot_test))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()

