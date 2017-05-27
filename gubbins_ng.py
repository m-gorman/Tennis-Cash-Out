__version__ = 0.01

import os
import pickle
import settings
from logger import Logger
from time import time, sleep
from betfair.api_ng import API
from datetime import datetime, timedelta
from arb import lay_game
import sys

class BetBot(object):
    """betfair laying bot - lays the field using settings.py parameters"""
    def __init__(self):
        self.username = '' # set by run() function at startup
        self.logger = None # set by run() function at startup
        self.api = None # set by run() function at startup
        self.abs_path = os.path.abspath(os.path.dirname(__file__))
        self.ignores_path = '%s/ignores.pkl' % self.abs_path
        self.ignores = self.unpickle_data(self.ignores_path, []) # list of market ids
        self.betcount_path = '%s/betcount.pkl' % self.abs_path
        self.betcount = self.unpickle_data(self.betcount_path, {}) # keys = hours, vals = market ids
        self.throttle = {
            'next': time(), # time we can send next request. auto-updated in do_throttle()
            'wait': 1.0, # time in seconds between requests
            'keep_alive': time(), # auto-updated in keep_alive()
            'update_closed': time() # auto-updated in update_ignores()
        }
        self.session = False

    def pickle_data(self, filepath = '', data = None):
        """pickle object to file"""
        f = open(filepath, 'wb')
        pickle.dump(data, f)
        f.close()

    def unpickle_data(self, filepath = '', default_object = None):
        """unpickle file to object. returns object"""
        if os.path.exists(filepath):
            f = open(filepath, 'rb')
            data = pickle.load(f)
            f.close()
            return data
        return default_object # return default object (empty)

    def update_ignores(self, market_id = ''):
        """update ignores list"""
        if market_id:
            # add market to ignores dict
            if market_id not in self.ignores:
                self.ignores.append(market_id)
                self.pickle_data(self.ignores_path, self.ignores)
        else:
            # check for closed markets (once every 2 hours)
            count = len(self.ignores)
            now = time()
            if count > 0 and now > self.throttle['update_closed']:
                secs = 2 * 60 * 60 # 2 hours
                self.throttle['update_closed'] = now + secs
                msg = 'CHECKING %s MARKETS FOR CLOSED STATUS...' % count
                self.logger.xprint(msg)
                for i in range(0, count, 5):
                    market_ids = self.ignores[i:i+5] # list of upto 5 market ids
                    self.do_throttle()
                    books = self.get_market_books(market_ids)
                    for book in books:
                        if book['status'] == 'CLOSED':
                            # remove from ignores
                            self.ignores.remove(book['marketId'])
                            self.pickle_data(self.ignores_path, self.ignores)

    def update_betcount(self, betcount = 0):
        """update bet count to avoid exceeding 1000 bets per hour"""
        hour = datetime.utcnow().hour
        if hour not in self.betcount:
            # new hour
            self.betcount[hour] = [betcount]
            # remove 'old' keys
            for key in self.betcount:
                if key != hour: self.betcount.pop(key)
        else:
            # current hour
            self.betcount[hour].append(betcount)
        # pickle
        self.pickle_data(self.betcount_path, self.betcount)

    def get_betcount(self):
        """returns bet count for current hour as integer"""
        betcount = 0
        hour = datetime.utcnow().hour
        if hour in self.betcount:
            betcount = sum(self.betcount[hour])
        return betcount

    def do_throttle(self):
        """return when it's safe to continue"""
        now = time()
        if now < self.throttle['next']:
            wait = self.throttle['next'] - now
            sleep(wait)
        self.throttle['next'] = time() + self.throttle['wait']
        return

    def do_login(self, username = '', password = ''):
        """login to betfair & set session status"""
        self.session = False
        resp = self.api.login(username, password)
        if resp == 'SUCCESS':
            self.session = True
        else:
            self.session = False # failed login
            msg = 'api.login() resp = %s' % resp
            raise Exception(msg)

    def keep_alive(self):
        """refresh login session. sessions expire after 20 mins.
        NOTE: betfair throttle = 1 req every 7 mins
        """
        now = time()
        if now > self.throttle['keep_alive']:
            # refresh
            self.session = False
            resp = self.api.keep_alive()
            if resp == 'SUCCESS':
                self.throttle['keep_alive'] = now + (15 * 60) # add 15 mins
                self.session = True
            else:
                self.session = False
                msg = 'api.keep_alive() resp = %s' % resp
                raise Exception(msg)

    def get_markets(self, market_ids = None):
        """returns a list of markets
        @market_ids: type = list. list of market ids to get info for.
        HINT: market ids can be filtered from menu paths
        """
        if market_ids:
            params = {
                'filter': {
                    'marketTypeCodes': settings.market_types,
                    'marketBettingTypes': ['MATCH_ODDS'],
                    'turnInPlayEnabled': True, # will go in-play
                    'inPlayOnly': False, # market NOT currently in-play
                    'marketIds': market_ids
                },
                'maxResults': 100 # maximum allowed by betfair
            }
            # send the request
            markets = self.api.get_markets(params)
            if type(markets) is list:
                return markets
            else:
                msg = 'api.get_markets() resp = %s' % markets
                raise Exception(msg)

    def create_bets(self, markets = None, market_paths = None):
        """returns a dict of bets. keys = market ids, vals = list of bets"""
        market_bets = {}
        # loop through markets
        for market in markets:
            # get bet settings for this market
            market_id = market['marketId']
            if market_id in market_paths:
                bets_index = market_paths[market_id]['bets_index']
                bets = settings.market_bets[bets_index]
                # create bets for this market
                market_path = market_paths[market_id]['market_path']
                market_bets[market_id] = {'bets': [], 'market_path': market_path}
                for runner in market['runners']:
                    for bet in bets:
                        new_bet = {}
                        new_bet['selectionId'] = runner['selectionId']
                        new_bet['side'] = bet['side']
                        new_bet['orderType'] = 'LIMIT'
                        new_bet['limitOrder'] = {
                            'size': bet['stake'],
                            'price': bet['price'],
                            'persistenceType': 'PERSIST' # KEEP at in-play. Set as 'LAPSE' to cancel.
                        }
                        market_bets[market_id]['bets'].append(new_bet)
        return market_bets # max bet count = 1000

    def place_bets(self, market_bets = None):
        """loop through markets and place bets
        @market_bets: type = dict returned from create_bets()
        NOTE: market_bets will contain up to 1000 bets!
        """
        for market_id in market_bets:
            bets = market_bets[market_id]['bets']
            if bets:
                # update & check bet count
                new_betcount = len(bets)
                self.update_betcount(new_betcount)
                betcount = self.get_betcount() # total bets placed in current hour
                if betcount >= settings.max_transactions: return
                # place bets...
                market_path = market_bets[market_id]['market_path']
                msg = 'MARKET PATH: %s\n' % market_path
                msg += 'PLACING %s BETS...\n' % len(bets)
                for i, bet in enumerate(bets):
                    msg += '%s: %s\n' % (i, bet)
                self.logger.xprint(msg)
                self.do_throttle()
                resp = self.api.place_bets(market_id, bets)
                if (type(resp) is dict
                    and 'status' in resp
                    ):
                    if resp['status'] == 'SUCCESS':
                        # add to ignores
                        self.update_ignores(market_id)
                        msg = 'PLACE BETS: SUCCESS'
                        self.logger.xprint(msg)
                    else:
                        if resp['errorCode'] == 'INSUFFICIENT_FUNDS':
                            msg = 'PLACE BETS: FAIL (%s)' % resp['errorCode']
                            self.logger.xprint(msg)
                            sleep(180) # wait 3 minutes
                        else:
                            msg = 'PLACE BETS: FAIL (%s)' % resp['errorCode']
                            self.logger.xprint(msg, True) # do not raise error - allow bot to continue
                            # add to ignores
                            self.update_ignores(market_id)
                else:
                    msg = 'PLACE BETS: FAIL\n%s' % resp
                    raise Exception(msg)


    def filter_tennis_paths(self, menu_paths = None):
        """ returns market ids of tennis game markets """
        keepers = {}
        # loop through all menu paths
        for market_id in menu_paths:
			try:
				market_path = menu_paths[market_id]
				path_texts = market_path.split('/')
				sport = path_texts[2]
			   # market_type = path_texts[7]
				if sport == "Tennis" and u"Match Odds" in path_texts:
					players = None
					for i in path_texts:
						if u" v " in i:
							players = i
					players = players.split(" v ")
					p1 =  players[0].split()[1] if len(players[0].split()) > 1 else players[0] 
					p2 =  players[1].split()[1] if len(players[1].split()) > 1 else players[1] 
					try:
						p1 = str(p1)
						p2 = str(p2)
					except:
						pass
				# check filters
					# keep this market?
					keepers[market_id] = {
						'p1' : p1,
						'p2' : p2
					}
			except:
				pass
        return keepers


    def filter_menu_path(self, menu_paths = None):
        """returns list of paths matching filters specified in settings.py
        @menu_paths: dict of menu paths. keys = market ids, vals = menu paths
        """
        keepers = {}
        # loop through all menu paths
        for market_id in menu_paths:
            market_path = menu_paths[market_id]
            path_texts = market_path.split('/')
            # check filters
            for filter_index, filter in enumerate(settings.menu_filters):
                # check if ALL search text matches this market
                matched_all = False
                for text in filter:
                    if text in path_texts:
                        matched_all = True
                    else:
                        matched_all = False
                        break
                # keep this market?
                if matched_all:
                    keepers[market_id] = {
                        'bets_index': filter_index,
                        'market_path': market_path,
                        'path_text' : path_texts
                    }
        return keepers

    def get_lay_prices(self, username = '', password = '', app_key = '', aus = False, verbose=False):
        # create the API object
        self.username = username
        self.api = API(aus, ssl_prefix = username)
        self.api.app_key = app_key
        self.logger = Logger(aus)
        self.logger.bot_version = __version__
        # login to betfair api-ng
        self.do_login(username, password)
        pd = ['SP_AVAILABLE', 'SP_TRADED', 'EX_BEST_OFFERS', 'EX_ALL_OFFERS', 'EX_TRADED']

        all_menu_paths = self.api.get_menu_paths(self.ignores)

        market_paths = self.filter_tennis_paths(all_menu_paths)

        games = []

        count = 0
        dec = 0
        tot = len(market_paths)
        if verbose:
            sys.stdout.write("[")
        for key in market_paths.keys():
            if verbose:
                print "%d / %d" % (count, tot)
            #if (float(count) / tot) > float(dec) / 10:
            #    sys.stdout.write("=")
           #     sys.stdout.flush()
           #     dec += 0.5
            count += 1
            try:
                r = self.api.get_market_books(market_ids=[key], price_data = pd)
                market_paths[key]["p1_lay"] = r[0][u"runners"][0][u'ex'][u'availableToLay'][0][u'price']
                market_paths[key]["p2_lay"] = r[0][u"runners"][1][u'ex'][u'availableToLay'][0][u'price']
                market_paths[key]["p1_back"] = r[0][u"runners"][0][u'ex'][u'availableToBack'][0][u'price']
                market_paths[key]["p2_back"] = r[0][u"runners"][1][u'ex'][u'availableToBack'][0][u'price']

                m = market_paths[key]

                p1 = m["p1"]
                p2 = m["p2"]
                p1o = m["p1_lay"]
                p2o = m["p2_lay"]
                p1b = m["p1_back"]
                p2b = m["p2_back"]


                games.append(lay_game(p1, p1o, p2, p2o, p1b, p2b, "Betfair"))
            except:
                pass

        return games

    def run(self, username = '', password = '', app_key = '', aus = False):
        # create the API object
        self.username = username
        self.api = API(aus, ssl_prefix = username)
        self.api.app_key = app_key
        self.logger = Logger(aus)
        self.logger.bot_version = __version__
        # login to betfair api-ng
        self.do_login(username, password)
        while self.session:
            self.do_throttle()
            self.keep_alive() # refresh login session (every 15 mins)
            # check bet count
            betcount = self.get_betcount()

            pd = ['SP_AVAILABLE', 'SP_TRADED', 'EX_BEST_OFFERS', 'EX_ALL_OFFERS', 'EX_TRADED']

            all_menu_paths = self.api.get_menu_paths(self.ignores)

            market_paths = self.filter_tennis_paths(all_menu_paths)

            for key in market_paths.keys():
                r = self.api.get_market_books(market_ids=[key], price_data = pd)
                market_paths[key]["p1_lay"] = r[0][u"runners"][0][u'ex'][u'availableToLay'][0]
                market_paths[key]["p2_lay"] = r[0][u"runners"][1][u'ex'][u'availableToLay'][0]
                


            if True:
                1
            else:
                # bet count limit reached for this hour
                utcnow = datetime.utcnow()
                nextdate = utcnow + timedelta(hours = 1)
                nextdate = datetime(nextdate.year, nextdate.month, nextdate.day, nextdate.hour)
                wait = (nextdate - utcnow).total_seconds()
                if wait > 0:
                    mins, secs = divmod(wait, 60)
                    msg = 'WARNING: TRANSACTION LIMIT REACHED FOR CURRENT HOUR\n'
                    msg += 'Sleeping for %dm %ds' % (mins, secs)
                    self.logger.xprint(msg)
                    # wait until next hour, keeping session alive
                    time_target = time() + wait
                    while time() < time_target:
                        self.keep_alive() # refresh login session (runs every 15 mins)
                        sleep(0.5) # CPU saver!
        if not self.session:
            msg = 'SESSION TIMEOUT'
            raise Exception(msg)
