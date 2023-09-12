import os

import telegram
from celery.utils.log import get_task_logger
from dotenv import load_dotenv

from monitor.models import Account, Dapp

load_dotenv()
logger = get_task_logger(__name__)

CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BOT = telegram.Bot(token=os.getenv('TELEGRAM_TOKEN'))


def create_transfer_message(
        from_account: Account,
        to_account: Account,
        amount: float,
        usd_amount: float,
        asset_symbol: str,
) -> str:
    sender_rank = from_account.rank
    sender_link = from_account.subscan_link
    sender = (
        f'Sender(Top {sender_rank}): {sender_link}'
        if sender_rank < 100 else f'Sender: {sender_link}'
    )

    receiver_rank = to_account.rank
    receiver_link = to_account.subscan_link
    receiver = (
        f'Receiver(Top {receiver_rank}): {receiver_link}'
        if receiver_rank < 100 else f'Receiver: {receiver_link}'
    )

    return (
        f'{sender}\n'
        f'{receiver}\n'
        f'Amount: {amount:,.2f} {asset_symbol}({usd_amount:,.2f} USD)\n'
    )


def create_extrinsic_message(
        account: Account,
        dapp: Dapp,
        action: str,
        amount: float,
        asset_symbol: str,
) -> str:
    account_rank = account.rank
    account_link = account.subscan_link
    dapp_link = dapp.portal_link

    acc = (
        f'Account(Top {account_rank}): {account_link}'
        if account_rank < 100 else f'Account: {account_link}'
    )

    return (
        f'{acc}\n'
        f'Action: {action}\n'
        f'Dapp: {dapp_link}\n'
        f'Amount: {amount:,.2f} {asset_symbol}\n')


def create_new_dapp_message(dapp: Dapp) -> str:
    return f'New dapp has been added: {dapp.portal_link}\n'


def send_message(message: str) -> BOT:
    logger.info(f'send_message: {message}')
    # return BOT.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
