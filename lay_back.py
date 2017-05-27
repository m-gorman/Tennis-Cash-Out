import os
import pickle
import settings
from logger import Logger
from time import time, sleep
from betfair.api_ng import API
from datetime import datetime, timedelta
import arb
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import csv
import pickle
import os
import re
from math import floor
from pyvirtualdisplay import Display
from txt import send_sms
import sys
from gubbins_ng import BetBot
from logger import Logger
from manager import USERNAME, PASSWORD, APP_KEY, AUS
from SBBot import SBBot
import random
#argecho.py
import sys

# maximum amount of bets allowed to be pending at one time
MAX_PENDING_BETS = 1
CURR_PENDING_BETS = 0

# minimum ration between betfair back price and sportsbet back price
MIN_RATIO = 1.05
# minimum number of hours until game starts for bet to be allowed
MIN_HOURS_UNTIL = 8
# minumum difference between betfair lay price and sportsbet back price
MIN_BL_DIFF = 0.02
# maximum player odds (cash out value often does not increase past initial stake for bets with high starting odds)
MAX_ODDS = 4





arbs = []
notified = []

display = Display(visible=0, size=(1600,900))

display.start()

last_cashout_time = time()
#sb_games = arb.SB(verbose = True)

print "BOT STARTED: Min ratio: %f Min hours until: %d Min back lay diff: %f Max back odds: %f" % (MIN_RATIO, MIN_HOURS_UNTIL, MIN_BL_DIFF, MAX_ODDS)

while 1:

	try:


		# attempt cashouts every 15-30 minutes
		# keep a bit of randomness so not too obvious
		
		time_since_last_cashout = time() - last_cashout_time
		if (time_since_last_cashout > random.randint(60 * 15, 60 * 30) and CURR_PENDING_BETS > 0):
			last_cashout_time = time()
			sb = SBBot()
			num_cashed_out = sb.cashout()
			sb.exit() 
			# subtract the number of cashed out bets from tally of pending bets
			CURR_PENDING_BETS -= num_cashed_out

		if (CURR_PENDING_BETS >= MAX_PENDING_BETS):
			sleep(3 * 60)
			continue
		


		now = datetime.now()
		h = now.hour
		h += 10
		if (h > 24):
			h -= 24
		print "========== " + ((str(h) + " : " + str(now.minute)) if showtime else "") + " ==============="
		print CURR_PENDING_BETS, MAX_PENDING_BETS
		# get betfair prices
		bot = BetBot()
		bf_games = bot.get_lay_prices(USERNAME, PASSWORD, APP_KEY, AUS)
		# get sportsbet prices
		sb_games = arb.SB()

		for back in sb_games:
			for lay in bf_games:
				try:
					if (back.p1 == lay.p1 and back.p2 == lay.p2):
						s = str(back.p1) 
						s += str(back.p2)
						if back.p1o > lay.p1o or back.p2o > lay.p2o or s in arbs:
							#if s not in arbs or True:
							print back.p1, back.p1o, lay.p1o, lay.p1b, back.bookie, back.time_until, back.p1o / lay.p1b
							print back.p2, back.p2o, lay.p2o, lay.p2b, back.bookie, back.time_until, back.p2o / lay.p2b
							print ">"
							arbs.append(s)
							message = False
							bet_placed = False
							if (back.p1o - lay.p1o >= MIN_BL_DIFF and back.p1o < MAX_ODDS and back.p1o / lay.p1b > MIN_RATIO and back.time_until >= MIN_HOURS_UNTIL and CURR_PENDING_BETS < MAX_PENDING_BETS):
								if s not in notified:
									print "Attempting to place bet"
									message = "Game: %s v %s. %s back odds: %f, lay odds: %f. back odds: %f, lay odds: %f.At %s" % (back.p1, back.p2, back.p1, back.p1o, lay.p1o, back.p2o, lay.p2o, back.bookie)
									sb = SBBot()
									bet_placed = sb.place_bet(back.p1, back.p1o, back.p2, back.p2o, back.p1)
							if (back.p2o - lay.p2o >= MIN_BL_DIFF and back.p2o < MAX_ODDS and back.p2o / lay.p2b > MIN_RATIO and back.time_until >= MIN_HOURS_UNTIL and CURR_PENDING_BETS < MAX_PENDING_BETS):
								if s not in notified:
									print "Attempting to place bet"
									message = "Game: %s v %s. %s back odds: %f, lay odds: %f. back odds: %f, lay odds: %f. At %s" % (back.p1, back.p2, back.p2, back.p2o, lay.p2o, back.p1o, lay.p1o, back.bookie)
									sb = SBBot()
									bet_placed = sb.place_bet(back.p1, back.p1o, back.p2, back.p2o, back.p2)
								
							notified.append(s)

							if bet_placed:
								CURR_PENDING_BETS += 1
				except:
					pass
	except:
		print "---Error---"