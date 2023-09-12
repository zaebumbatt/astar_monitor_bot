import os

import requests
from celery.utils.log import get_task_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_task_logger(__name__)


SUBSCAN_API_KEY = os.getenv('SUBSCAN_API_KEY')
SUBSCAN_API_URL = 'https://astar.api.subscan.io/api/scan/'
SUBSCAN_API_V2_URL = 'https://astar.api.subscan.io/api/v2/scan/'


def make_request(resource: str, data: dict) -> [dict, None]:
    url = (
              SUBSCAN_API_V2_URL if resource != 'extrinsics' else SUBSCAN_API_URL
          ) + resource
    headers = {"x-api-key": SUBSCAN_API_KEY}
    response = requests.post(url, headers=headers, json=data)
    logger.info(f'make_request: {url} {response.status_code}')
    if response.status_code == 200:
        return response.json()
