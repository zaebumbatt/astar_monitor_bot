import os

import requests
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

TON_API_KEY = os.getenv('TON_API_KEY')
TON_API_URL = 'https://tonapi.io/v2/'


def make_tonapi_request(resource: str) -> [dict, None]:
    url = TON_API_URL + resource
    headers = {'Authorization': f'Bearer {TON_API_KEY}'}
    response = requests.get(url, headers=headers)
    logger.info(f'make_tonapi_request: {url} {response.status_code}')
    if response.status_code == 200:
        return response.json()
