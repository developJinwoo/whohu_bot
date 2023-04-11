from telegram.ext import filters, ConversationHandler
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from typing import Optional, Tuple
import asyncio
from typing import Dict
import logging
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ChatMemberHandler,
    PicklePersistence,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import os
import pickle
from datetime import datetime
from collections import defaultdict
import random

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

LNAME               = "leaderboard.pickle"
POINT_NAME          = "point.pickle"
score_dict          = dict()
point_dict          = dict()

CHOOSING, RPS_GAME, USER_CHOICE = range(3)

reply_keyboard = [
    ["\U0001f37d\uFE0F 점메추", "\U0001f3b2 오늘의 운세"],
    ["\u270C\uFE0F \u270A \U0001f590\uFE0F 가위 바위 보!"],
    ["Done"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    user = update.effective_user.first_name

    await update.message.reply_text(f"{user} 오늘 하루도 고생해라! \U0001f607", reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

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
    """Send a message when the command /start is issued."""
    user = update.effective_user.first_name
    reply_text = "후.. ㅈ같네"
    await update.message.reply_html(
        reply_text, reply_markup=markup,
    )
    return CHOOSING

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "명령어 모음 \n /start  : 후후 봇 실행 \n /leaderboard  :  오늘의 한숨왕 \n /dice  :  오늘의 운세 \n /my_point  : 나의 자산(후) 현황 \n" +
        "/money_king  :  현재 자산(후) 랭킹 \n" +
        "'ㅊㅅ' or '출석'  : 출석체크 +1000후 \n 후.. 한번에 +100후"
    )
async def rock_papper_scissor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    reply_text = "가위 바위 보 게임입니다. \n"
    reply_text += f"{user}님 100후를 걸고 게임하시겠습니까? \n"
    reply_text += "(네/아니요)"
    await update.message.reply_text(reply_text)
    return RPS_GAME

def get_bot_choice() -> str:
    return random.choice(['가위', '바위', '보'])

def get_emoji(choice: str):
    if choice == "가위":
        return "\u270C\uFE0F"
    elif choice == "바위":
        return "\u270A"
    elif choice == "보":
        return "\U0001f590\uFE0F"

async def load_RPS_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    game_fee = 100
    if point_dict[user]["total"] < game_fee:
        await update.message.reply_text("후가 부족합니다. 후..", reply_markup=markup,)
    else:
        user_account = point_dict[user]["total"]
        user_account -= game_fee
        
        reply_text = f"게임비용으로 {game_fee}후를 차감하였습니다.\n"
        reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
        reply_text += "당신의 선택은? \n "
        reply_text += "(가위/바위/보)"
        await update.message.reply_text(reply_text)
        return USER_CHOICE
    
async def get_RPS_winner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    user_choice = update.message.text
    bot_choice = get_bot_choice()
    user_emoji = get_emoji(user_choice)
    bot_emoji = get_emoji(bot_choice)
    
    rules: dict[str, str] = {'바위': '가위',
                             '가위': '보',
                             '보': '바위'}
    
    game_fee = 100
    user_account = point_dict[user]["total"]
    if user_choice == "가위" or user_choice == "바위" or user_choice == "보":
        if user_choice == bot_choice:
            reply_text = "비겼습니다. 후.. \n"
            reply_text += f"후후 봇 : {bot_emoji} / {user_emoji} : {user}님 \n"
            reply_text += f"게임비용 {game_fee}후를 돌려드립니다.\n"
            reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
            with open( POINT_NAME, 'wb' ) as pf:
                pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )
            await update.message.reply_text(reply_text,reply_markup=markup,)
            return CHOOSING
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
            await update.message.reply_text(reply_text,reply_markup=markup,)
            return CHOOSING
        else:
            point_dict[user][last_day] -= game_fee 
            point_dict[user]["total"] -= game_fee
            user_account -= game_fee
            reply_text = "후.. 졌습니다. 후.. \n"
            reply_text += f"후후 봇 : {bot_emoji} / {user_emoji} : {user}님 \n"
            reply_text += f"남아있는 잔액은 {user_account}후 입니다. \n"
            with open( POINT_NAME, 'wb' ) as pf:
                pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )
            await update.message.reply_text(reply_text,reply_markup=markup,)
            return CHOOSING

    
async def dice_cmd_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    rand_num = random.randrange(0,6)
    if rand_num == 1:
        await update.message.reply_text(f'{user}님의 행운은 최악입니다.',reply_markup=markup,)
    elif rand_num == 2:
        await update.message.reply_text(f'{user}님의 행운은 좋지 않습니다.',reply_markup=markup,)
    elif rand_num == 3:
        await update.message.reply_text(f'{user}님의 행운은 보통입니다.',reply_markup=markup,)
    elif rand_num == 4:
        await update.message.reply_text(f'{user}님의 행운은 좋은편입니다.',reply_markup=markup,)
    elif rand_num == 5:
        await update.message.reply_text(f'{user}님의 행운은 아주 좋은편입니다.',reply_markup=markup,)
    elif rand_num == 6:
        await update.message.reply_text(f'{user}님의 행운은 최상입니다.',reply_markup=markup,)
    else:
        await update.message.reply_text(f'{user}님의 행운은 없습니다. \n 오늘 하루는 지옥입니다.',reply_markup=markup,)
    return CHOOSING

async def dice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.first_name
    rand_num = random.randrange(0,6)
    if rand_num == 1:
        await update.message.reply_text(f'{user}님의 행운은 최악입니다.')
    elif rand_num == 2:
        await update.message.reply_text(f'{user}님의 행운은 좋지 않습니다.')
    elif rand_num == 3:
        await update.message.reply_text(f'{user}님의 행운은 보통입니다.')
    elif rand_num == 4:
        await update.message.reply_text(f'{user}님의 행운은 좋은편입니다.')
    elif rand_num == 5:
        await update.message.reply_text(f'{user}님의 행운은 아주 좋은편입니다.')
    elif rand_num == 6:
        await update.message.reply_text(f'{user}님의 행운은 최상입니다.')
    else:
        await update.message.reply_text(f'{user}님의 행운은 없습니다. \n 오늘 하루는 지옥입니다.')

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
    user = update.effective_user.first_name
    total = point_dict[user]["total"]

    await update.message.reply_text(f"{user}님의 자산현황 \n 오늘 {point_dict[user][last_day]}후 획득! \n 총 자산 {total}후")

async def jum_me_chu_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    점심 메뉴 추천
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    await update.message.reply_text(f"{user}! 너의 점심은 킹까스다!!",reply_markup=markup,)
    return CHOOSING
async def jum_me_chu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    점심 메뉴 추천
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    await update.message.reply_text(f"{user}! 너의 점심은 킹까스다!!")

async def chul_seok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ -------------------------------------------------------------------------------------------------------------
    출석 체크
    ------------------------------------------------------------------------------------------------------------- """
    user = update.effective_user.first_name
    check = "출석"
    if user not in point_dict:
        point_dict[user] = defaultdict(int)
    
    if point_dict[user][check] == last_day:
        await update.message.reply_text(f"{user}님은 이미 출석하셨습니다.")
    else:
        point_dict[user][check] = last_day
        point_dict[user][last_day] += 1000
        point_dict[user]["total"] += 1000
        await update.message.reply_text(f"{user}님 {last_day} 출석!! \n 출석 보상 +1000후 ")
    ## save the dict
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

async def get_hu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #u_id = user.id
    user = update.effective_user.first_name
    if user not in score_dict:
        score_dict[ user ] = defaultdict(int)
    if user not in point_dict:
        point_dict[user] = defaultdict(int)

    score = 1
    # add day and score to the dict
    score_dict[ user ][ last_day ] += score
    point_dict[user][last_day] += 100
    point_dict[user]["total"] += 100

    ## save the dict
    with open( LNAME, 'wb' ) as f:
        pickle.dump( score_dict, f, protocol=pickle.HIGHEST_PROTOCOL )
    with open( POINT_NAME, 'wb' ) as pf:
        pickle.dump( point_dict, pf, protocol=pickle.HIGHEST_PROTOCOL )

    #await update.message.reply_text(f"{user}\n {score_dict[user][day]} \n {day}")

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
    # on different commands - answer in Telegram
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex(r"점메추"), jum_me_chu_conv
                ),
                MessageHandler(
                    filters.Regex(r"오늘의 운세"), dice_cmd_conv
                ),
                MessageHandler(
                    filters.Regex(r"가위 바위 보"), rock_papper_scissor
                ),
            ],
            RPS_GAME: [
                MessageHandler(
                    filters.Regex(r"네"), load_RPS_game
                ),
                MessageHandler(
                    filters.Regex(r"(a?아니)"), done
                ),
            ],
            USER_CHOICE: [
                MessageHandler(
                    filters.Regex(r"가위"), get_RPS_winner
                ),
                MessageHandler(
                    filters.Regex(r"바위"), get_RPS_winner
                ),
                MessageHandler(
                    filters.Regex(r"보"), get_RPS_winner
                ),
            ]
        
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
        name="후후 봇",
        persistent=True,
    )
    application.add_handler(conv_handler)

    #application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", show_leads))
    application.add_handler(CommandHandler("money_king", show_money_leads))
    application.add_handler(CommandHandler("dice", dice_cmd))
    application.add_handler(CommandHandler("my_point", my_point_cmd))

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.Regex(r'(a?후)'), get_hu))
    application.add_handler(MessageHandler(filters.Regex(r'ㅊㅅ'), chul_seok))
    application.add_handler(MessageHandler(filters.Regex(r'출석'), chul_seok))
    application.add_handler(MessageHandler(filters.Regex(r'ㅈㅁㅊ'), jum_me_chu))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()

