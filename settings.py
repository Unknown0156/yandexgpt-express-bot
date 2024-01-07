import os, logging
import configparser

try:
    express_bot_id = os.environ['EXPRESS_BOT_ID']
    express_bot_key = os.environ['EXPRESS_BOT_KEY']
    yandex_url  = os.environ['YANDEX_URL']
    yandex_api_key = os.environ['YANDEX_API_KEY']
except KeyError as e:
    logging.error(f"Environment variable error: {e}")

try:
    config = configparser.ConfigParser()
    config.read('config.ini')
    express_url = config.get('Express', 'express_url')
    redis_dsn = config.get('Bot', 'redis_dsn')
    max_context_size = int(config.get('Bot', 'max_context_size'))
    apm = config.get('APM', 'apm')
    apm_server = config.get('APM', 'apm_server')
    apm_name = config.get('APM', 'apm_name')
except Exception as e:
    logging.error(f"ConfigParser error: {e}")