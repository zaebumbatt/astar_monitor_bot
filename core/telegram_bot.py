import os

import requests
from celery.utils.log import get_task_logger

from monitor.models import Account, Dapp

logger = get_task_logger(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')


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


def create_ton_transfer_message(
        source_address: str,
        source_name: str,
        destination_address: str,
        destination_name: str,
        amount: str,
    ) -> str:

    def tonviewer_link(address, name) -> str:
        url = 'https://tonviewer.com/'
        return f"<a href='{url}{address}'>{name}</a>"

    sender = tonviewer_link(source_address, source_name or source_address)
    receiver = tonviewer_link(destination_address, destination_name or destination_address)
    asset_symbol = 'TON'
    return (
        f'Sender: {sender}\n'
        f'Receiver: {receiver}\n'
        f'Amount: {amount:,.2f} {asset_symbol}\n'
    )


def send_message(chat_id: str, message: str) -> None:
    logger.info(f'send_message: {message}')
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
    }

    response = requests.post(url, json=data)
    logger.info(f'send_message: {response.status_code}')
    if response.status_code != 200:
        logger.info(f'send_message: {response.text}')
