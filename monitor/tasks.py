import json
import os
import time

import requests
from celery import shared_task
from celery.utils.log import get_task_logger

from core.subscan import make_request
from core.telegram_bot import (create_extrinsic_message,
                               create_new_dapp_message,
                               create_ton_transfer_message,
                               create_transfer_message, send_message)
from core.tonapi import make_tonapi_request
from monitor.models import Account, Dapp, TONAccount, TONTransfer, Transfer

logger = get_task_logger(__name__)


ASTAR_CHAT_ID = os.getenv('TELEGRAM_ASTAR_CHAT_ID')
TON_CHAT_ID = os.getenv('TELEGRAM_TON_CHAT_ID')
ASTAR_TRANSFER_LOWER_LIMIT = int(os.getenv('ASTAR_TRANSFER_LOWER_LIMIT', 1000000))
TON_TRANSFER_LOWER_LIMIT = int(os.getenv('TON_TRANSFER_LOWER_LIMIT', 10000))


@shared_task
def get_latest_transfers() -> None:
    data = {'row': 100, 'page': 0}
    response = make_request('transfers', data)
    if not response:
        logger.info('make_request has failed')
        return

    for transfer in reversed(response['data']['transfers']):
        amount = float(transfer.get('amount', 0))
        usd_amount = float(transfer.get('usd_amount', 0))
        asset_symbol = transfer.get('asset_symbol', '')

        if (
            not transfer.get('success')
            or float(amount) < ASTAR_TRANSFER_LOWER_LIMIT
        ):
            continue

        from_account, _ = Account.objects.get_or_create(
            address=transfer.get('from'),
            defaults={
                'display': transfer.get(
                    'from_account_display', {}
                ).get('display', ''),
            }
        )
        to_account, _ = Account.objects.get_or_create(
            address=transfer.get('to'),
            defaults={
                'display': transfer.get(
                    'to_address_display', {}
                ).get('display', ''),
            }
        )
        _, created = Transfer.objects.get_or_create(
            extrinsic_index=transfer.get('extrinsic_index'),
            defaults={
                'from_account': from_account,
                'to_account': to_account,
                'asset_symbol': asset_symbol,
                'module': transfer.get('module', ''),
                'amount': amount,
                'usd_amount': usd_amount,
            },
        )

        if created:
            send_message(
                ASTAR_CHAT_ID,
                create_transfer_message(
                    from_account,
                    to_account,
                    amount,
                    usd_amount,
                    asset_symbol,
                )
            )


@shared_task
def get_latest_dapp_staking() -> None:
    data = {
        'row': 100,
        'page': 0,
        'module': 'dappsstaking'
    }
    response = make_request('extrinsics', data)
    if not response:
        logger.info('get_latest_dapp_staking has failed')
        return

    for transaction in reversed(response['data']['extrinsics']):
        call_module_function = transaction.get('call_module_function')
        extrinsic_index = transaction.get('extrinsic_index')
        params = transaction.get('params')

        if (
            not transaction.get('success')
            or not call_module_function
            or not params
            or call_module_function not in (
                'bond_and_stake',
                'unbond_and_unstake',
            )
        ):
            continue

        params = json.loads(params)

        account_address = None
        amount = 0
        asset_symbol = 'ASTR'
        dapp_address = None
        for param in params:
            if param.get('type_name') == 'SmartContract':
                value = param.get('value')
                if value:
                    dapp_address = value.get('Evm')

            if param.get('type_name') == 'Balance':
                amount = int(param.get('value', 0)) / 10 ** 18

                if float(amount) >= ASTAR_TRANSFER_LOWER_LIMIT:
                    account_address = transaction.get('account_id')

        if account_address and dapp_address:
            account, _ = Account.objects.get_or_create(
                address=account_address
            )
            _, created = Transfer.objects.get_or_create(
                extrinsic_index=extrinsic_index,
                defaults={
                    'from_account': account,
                    'to_account': account,
                    'asset_symbol': asset_symbol,
                    'module': call_module_function,
                    'amount': amount,
                },
            )

            dapp_account, _ = Account.objects.get_or_create(
                address=dapp_address
            )
            dapp = Dapp.objects.filter(account=dapp_account).first()

            if created:
                send_message(
                    ASTAR_CHAT_ID,
                    create_extrinsic_message(
                        account,
                        dapp,
                        call_module_function,
                        amount,
                        asset_symbol,
                    )
                )


@shared_task
def check_new_dapps() -> None:
    url = 'https://api.astar.network/api/v1/astar/dapps-staking/dapps'
    response = requests.get(url)
    logger.info(f'check_dapps: {url} {response.status_code}')
    if response.status_code != 200:
        return

    dapp_addresses = set(
        Dapp.objects.values_list('account__address', flat=True)
    )
    for row in response.json():
        address = row.get('address', '').lower()
        if address not in dapp_addresses:
            account, _ = Account.objects.get_or_create(address=address)
            dapp = Dapp.objects.create(
                name=row.get('name'),
                account=account,
            )
            send_message(ASTAR_CHAT_ID, create_new_dapp_message(dapp))


@shared_task
def get_account_balances() -> None:
    known_addresses = (Account.objects.exclude(name='')
                       .values_list('address', flat=True))
    max_addresses_per_request = 100
    for i in range(0, len(known_addresses), max_addresses_per_request):
        data = {'address': known_addresses[i:i + max_addresses_per_request]}
        response = make_request('accounts', data)
        if not response:
            logger.info('get_account_balances has failed')
            continue

        for row in response['data']['list']:
            address = row.get('address')
            substrate_account = row.get('substrate_account')
            if substrate_account:
                address = substrate_account.get('address')
            Account.objects.filter(address=address).update(
                balance=float(row['balance']),
                balance_lock=float(row['balance_lock']),
            )


@shared_task
def get_top_holders() -> None:
    data = {
        'row': 100,
        'page': 0,
        'order_field': 'balance',
        'order': 'desc'
    }
    response = make_request('accounts', data)
    if not response:
        logger.info('get_top_holders has failed')
        return
    for row in response['data']['list']:
        address = row.get('address')
        substrate_account = row.get('substrate_account')
        if substrate_account:
            address = substrate_account.get('address')
        Account.objects.update_or_create(
            address=address,
            defaults={
                'display': row.get('account_display', {}).get('display', ''),
                'balance': float(row['balance']),
                'balance_lock': float(row['balance_lock']),
            }
        )


@shared_task
def get_latest_ton_transfers() -> None:
    accounts = TONAccount.objects.all().values_list('name', 'address_raw')
    for name, address in accounts:
        if not address:
            continue
        time.sleep(1)  # rps limit
        response = make_tonapi_request(f'blockchain/accounts/{address}/transactions')
        if not response:
            logger.info('make_tonapi_request has failed')
            return
        transactions = response.get('transactions')
        if transactions is None:
            logger.info('no transactions in response')
            return
        for transaction in transactions:
            in_msg = transaction.get('in_msg')
            if in_msg is None:
                continue
            value = in_msg.get('value')
            source = in_msg.get('source')
            destination = in_msg.get('destination')
            if value is None or source is None or destination is None:
                continue

            amount = value / 10 ** 9
            if float(amount) < TON_TRANSFER_LOWER_LIMIT:
                continue

            source_address = source.get('address')
            source_name = name if source_address == address else source.get('name')
            destination_address = destination.get('address')
            destination_name = name if destination_address == address else destination.get('name')
            _, created = TONTransfer.objects.get_or_create(
                hash=transaction.get('hash'),
                defaults={
                    'source_address': source.get('address'),
                    'destination_address': destination.get('address'),
                    'amount': amount,
                },
            )
            if created:
                send_message(
                    TON_CHAT_ID,
                    create_ton_transfer_message(
                        source_address,
                        source_name,
                        destination_address,
                        destination_name,
                        amount,
                    )
                )
