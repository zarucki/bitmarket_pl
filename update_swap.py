#!/usr/bin/python
import requests
import hmac
import hashlib
import time
import json
import traceback
import logging
from pprint import pprint

logger = logging.getLogger('swap_update')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('swap_update.log')
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

configFile = open('config.json', 'r')
config = json.load(configFile)
configFile.close()

sleepTimeBetweenChecks = int(config['sleep_between_checks_in_seconds'])
publicKey = str(config['public_api_key'])
secretKey = str(config['secret_api_key'])

logger.info('SleepTime: ' + str(sleepTimeBetweenChecks) + ' PublicKey: ' + publicKey + ' SecretKey: ' + secretKey)

def mergeTwoDicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def getCurrentCutOff():
	swapStateJson = requests.get('https://www.bitmarket.pl/json/swapBTC/swap.json').json()
	cutoff = swapStateJson['cutoff']
	#demand = swapStateJson['demand']
	return cutoff

def bitMarketPlApiCall(method, params = {}):
	postDataAsDict = mergeTwoDicts(params, {
		'method': method,
		'tonce': int(time.time())
	})
	postParamsAsString = "&".join([param + '=' + str(postDataAsDict[param]) for param in postDataAsDict])

	postHeaders = {
		'API-Key': publicKey,
		'API-Hash': hmac.new(secretKey, postParamsAsString, hashlib.sha512).hexdigest()
	}

	request_response = requests.post('https://www.bitmarket.pl/api2/', data = postParamsAsString, headers = postHeaders)
	logger.debug(request_response)
	if request_response.status_code == 200:
		asJson = request_response.json()
		#print 'success', asJson['limit'], '; serverTime =', asJson['time']
	else:
		logger.info(request_response)
		logger.info(request_response.text)

	return request_response

def closeSwapPosition(id):
	logger.info('closing swap position: ' + str(id))
	logger.debug(bitMarketPlApiCall('swapClose', { 'id': id, 'currency': 'BTC' }).text)

def openSwapPosition(amount, rate):
	logger.info('Opening new swap position. Amount: ' + str(amount) + ' BTC, Rate: ' + str(rate) + ' %')
	logger.debug(bitMarketPlApiCall('swapOpen', { 'amount': amount, 'rate': rate, 'currency': 'BTC' }))

def checkIfShouldUpdateSwapRate():
	totalEarnings = 0
	while True:
		try:
			currentCutOff = getCurrentCutOff()
			currentSwapPositions = bitMarketPlApiCall('swapList', { 'currency': 'BTC' }).json()['data']
			if len(currentSwapPositions) == 0:
				logger.warn('No swap position to maximize, create a position.')
				time.sleep(sleepTimeBetweenChecks)
				continue

			currentSwapPosition = currentSwapPositions[0]

			maxProfitableRate = currentCutOff - 0.01

			currentRate = currentSwapPosition['rate']
			earnings = currentSwapPosition['earnings']
			earningsAsString = '{0:f}'.format(earnings)
			currentAmount = currentSwapPosition['amount']
			if currentRate != maxProfitableRate:
				logger.info('current rate: ' + str(currentRate) + ' not optimal. Changeing to: ' + str(maxProfitableRate))
				closeSwapPosition(currentSwapPosition['id'])
				logger.info('swap position ' + str(currentSwapPosition['id']) + ' earned: ' + earningsAsString + ' with amount: ' + str(currentAmount))
				openSwapPosition(currentAmount + earnings, maxProfitableRate)
				totalEarnings = totalEarnings + earnings
			else:
				logger.info('current rate: ' + str(currentRate) + ' is optimal. Earnings: ' + earningsAsString + ' BTC + Total earnings: ' + '{0:f}'.format(totalEarnings + earnings))

		except Exception as ex:
			logger.error(ex)
			traceback.print_exc()

		time.sleep(sleepTimeBetweenChecks)

def main():
	checkIfShouldUpdateSwapRate()

if __name__ == '__main__':
	main()
