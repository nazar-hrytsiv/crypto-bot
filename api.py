import requests
import json

from logger import logger
from config import base_url

class API():
    
    def __init__(self, name, key):
        '''
        CoinMarketCap API (https://coinmarketcap.com/api/documentation/v1/)

        :param name - API's name
        :param key - API's key
        '''
        self.name = name
        self.key = key # api key
        self.headers = {
            'Accepts':'application/json',
            'X-CMC_PRO_API_KEY': self.key
        }


    def latest_listings(self, limit=100):
        '''
        API endpoint for latest listings ordered by MarketCap value in descended order

        :param limit - number of requested coins
        :return - list of coins in text format with HTML markup
        '''
        logger.info('limit: {}'.format(limit))
        try:
            url = base_url + '/v1/cryptocurrency/listings/latest'
            parameters = {
                'start':'1',
                'limit':limit,
                'convert':'USD',
            }
            response = requests.get(
                url=url, 
                params=parameters, 
                headers=self.headers
            )
            if response.status_code != 200:
                logger.error('API request failed; status_code: {}; reason: {}; text: {}'.format(response.status_code, response.reason, response.text))
                return {'status':0}
            else:
                data = json.loads(response.text)['data']
                text_coins = []
                for row in data:
                    text_coins.append('\n<code>{} - ${:.2f}</code>'.format(row['symbol'], row['quote']['USD']['price']))
                return {'status':1, 'coins':text_coins}
        except Exception as e:
            logger.exception(e)