from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import csv
import pickle
import os
import re
from math import floor
from pyvirtualdisplay import Display
from txt import send_sms
import sys
import datetime

# bet we are willing to place on favourite
BASEBET = 10

# class to store games
class Game():
	def __init__(self, p1, p1o, p2, p2o, bookie, time_until = False):
	
		# p1 and p2 should be alphabetic
		if (p1 > p2):
			self.p1 = p1
			self.p1o = p1o
			self.p2 = p2
			self.p2o = p2o
			self.time_until = time_until
		elif (p1 < p2):
			self.p1 = p2
			self.p1o = p2o
			self.p2 = p1
			self.p2o = p1o
			self.time_until = time_until
		
		self.bookie = bookie

class lay_game():
	def __init__(self, p1, p1o, p2, p2o, p1b, p2b, bookie):
			# p1 and p2 should be alphabetic
			if (p1 > p2):
				self.p1 = p1
				self.p1o = p1o
				self.p2 = p2
				self.p2o = p2o
				self.p1b = p1b
				self.p2b = p2b
			elif (p1 < p2):
				self.p1 = p2
				self.p1o = p2o
				self.p2 = p1
				self.p2o = p1o
				self.p2b = p1b
				self.p1b = p2b



# sportsbet
def SB(verbose = False):
	games = []
	driver = webdriver.Firefox()
	driver.get("http://www.sportsbet.com.au/betting/tennis?MegaNav")
	# each bet 'card' is in an accordion body
	matches = driver.find_elements_by_class_name("accordion-body")
	try:
		matches = driver.find_elements_by_xpath("//li")
	except:
		print "Error getting matches"
		driver.refresh()
	count = 0
	tot = len(matches)
	dec = 0
	# go through them, fetching odds
	if verbose:
		sys.stdout.write("[")
		
	days_ahead = 0	
	last_hour = 0
	new_day = False
	first = True
	for match in matches:

		if (float(count) / tot) > float(dec) / 10:
			if verbose:
				sys.stdout.write("=")
			sys.stdout.flush()
			dec += 0.5
		count += 1


		# get the score
		try:
		
			class_name = match.get_attribute("class")
			if class_name == "bettypes-header" and not first:
				days_ahead += 1
		
			prices = match.find_element_by_class_name("accordion-body")
			players = prices.find_element_by_class_name("market-buttons")
			playersInfo = players.find_elements_by_class_name("price-link")
			live = 0
			if playersInfo:
				p1 = str(playersInfo[0].find_element_by_class_name("team-name").text)
				p1o = float(playersInfo[0].find_element_by_class_name("odd-val").text)
				p2 = str(playersInfo[1].find_element_by_class_name("team-name").text)
				p2o = float(playersInfo[1].find_element_by_class_name("odd-val").text)

				# remove punctuation
				p1 = re.sub(r'[^\w\s]','',p1.split()[1])
				p2 = re.sub(r'[^\w\s]','',p2.split()[1])
			#	print p1
				
				game_info = match.find_element_by_class_name("market-name")
				start_time = game_info.find_element_by_class_name("start-time").text
				h = int(start_time.split(":")[0])
				m = int(start_time.split(":")[1])
				if first:
					first_h = h
					first_m = m
					first = False
					
				curr_time = datetime.datetime.now()
				
				ch = curr_time.hour
				ch += 10
				if (ch > 24):
					ch -= 24
				cm = curr_time.minute
				
				t = h + (days_ahead * 24) - ch
				
				#print p1, p2, t, h, m, ch
				
				games.append(Game(p1, p1o, p2, p2o, "Sportsbet", time_until=t))
				
		except:
			pass
	if verbose:
		print "]"
	driver.close()
	return games

# crownbet			
def CB():
	games = []
	driver = webdriver.Firefox()
	driver.get("https://crownbet.com.au/sports/tennis")
	time.sleep(3)
	
	ms = driver.find_element_by_id("sports-matches")
	matches = ms.find_elements_by_class_name("middle-section")

	tot = len(matches)
	count = 0
	dec = 0
	for match in matches:
		if (float(count) / tot) > float(dec) / 10:
			sys.stdout.write("=")
			sys.stdout.flush()
			dec += 0.5
		count += 1
		try:
			info = match.find_element_by_class_name("drop-down-content").find_element_by_class_name("sport-block")
			
			# first <tr> is header
			players = info.find_elements_by_css_selector("tr")[1:]
			
			
			p1data = players[0].find_elements_by_css_selector("td")
			p2data = players[1].find_elements_by_css_selector("td")

			
			p1pni = p1data[0]
			p1ppi = p1data[1]
			
			p2pni = p2data[0]
			p2ppi = p2data[1]			
			
			p1 = p1pni.find_element_by_css_selector("a").text
			p1o = float(p1ppi.find_element_by_css_selector("a").find_element_by_class_name("bet-amount").text)
			
			p2 = p2pni.find_element_by_css_selector("a").text
			p2o = float(p2ppi.find_element_by_css_selector("a").find_element_by_class_name("bet-amount").text)
			
			p1 = re.sub(r'[^\w\s]','',p1.split()[1])
			p2 = re.sub(r'[^\w\s]','',p2.split()[1])
			#print p1
			games.append(Game(p1, p1o, p2, p2o, "Crownbet"))
		except:
			#print "Error"
			continue
	print "]"
	driver.close()
	return games
	
# calculate how much to bet on a game
def calcBetAmt(game1, game2):
	max1 = max(game1.p1o, game2.p1o)
	
	max2 = max(game1.p2o, game2.p2o)
	
	minOdds = min(max1, max2)
	
	maxOdds = max(max1, max2)
	
	
	if minOdds == game1.p1o:
		favBet = game1.p1
		b1 = game1.bookie
	elif minOdds == game1.p2o:
		favBet = game1.p2
		b1 = game1.bookie
	elif minOdds == game2.p1o:
		favBet = game2.p1
		b1 = game2.bookie
	elif minOdds == game2.p2o:
		favBet = game2.p2
		b1 = game2.bookie
	favBetAmt = BASEBET
	
	if maxOdds == game1.p1o:
		outsiderBet = game1.p1
		b2 = game1.bookie
	elif maxOdds == game1.p2o:
		outsiderBet = game1.p2
		b2 = game1.bookie
	elif maxOdds == game2.p1o:
		outsiderBet = game2.p1
		b2 = game2.bookie
	elif maxOdds == game2.p2o:
		outsiderBet = game2.p2
		b2 = game2.bookie
	
	#outsiderBetAmt = BASEBET * (minOdds / maxOdds)
	gameStr = favBet + str(minOdds)

	if gameStr not in alerted:
		alerted.append(gameStr)
		outsiderBetAmt = BASEBET / (maxOdds - 1)
		print "+++++++++++++++++++++++++++++++++++++ARB OPPORTUNITY+++++++++++++++++++++++++++++++++++++++++"
		print "Game: %s vs %s, profit %f" % (game1.p1, game1.p2, minOdds ** -1 + maxOdds ** -1)
		print "%f on %s (%f) at %s" % (favBetAmt, favBet, minOdds, b1)
		print "%f on %s (%f) at %s" % (outsiderBetAmt, outsiderBet, maxOdds, b2)
		print BASEBET * minOdds - outsiderBetAmt - 10, BASEBET + outsiderBetAmt
		
		# favourite has overpriced odds
		if b1 == "Sportsbet":
			print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>CASH OUT OPPORTUNITY<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
			print "Game: %s vs %s, profit %f" % (game1.p1, game1.p2, minOdds ** -1 + maxOdds ** -1)
			print "%f on %s (%f) at %s" % (favBetAmt, favBet, minOdds, b1)
			print "%f on %s (%f) at %s" % (outsiderBetAmt, outsiderBet, maxOdds, b2)
			print BASEBET * minOdds - outsiderBetAmt - 10, BASEBET + outsiderBetAmt
			#send_sms("Cash out opp: " + favBet + ", odds are " + str(minOdds), "+61410067065") 
		# close outsider has overpriced odds
		elif b2 == "Sportsbet" and maxOdds < 2.9:
			print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>CASH OUT OPPORTUNITY<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
			print "Game: %s vs %s, profit %f" % (game1.p1, game1.p2, minOdds ** -1 + maxOdds ** -1)
			print "%f on %s (%f) at %s" % (favBetAmt, favBet, minOdds, b1)
			print "%f on %s (%f) at %s" % (outsiderBetAmt, outsiderBet, maxOdds, b2)
			print BASEBET * minOdds - outsiderBetAmt - 10, BASEBET + outsiderBetAmt 
			#send_sms("Cash out opp: " + outsiderBet + ", odds are " + str(maxOdds), "+61410067065") 
	
def findArb(oddCollections):
	games = []
	alreadyArbed = []
	for bookie in oddCollections:
		games += bookie
	for game1 in games:
		for game2 in games:
			try:
				prof = 1000
				max1 = max(game1.p1o, game2.p1o)
				max2 = max(game1.p2o, game2.p2o)
				skip = False
				for pair in alreadyArbed:
					if game1 in pair and game2 in pair:
						skip = True
				if skip:
					continue
				if (game1.p1 == game2.p1 and game1.p2 == game2.p2 and game1.bookie != game2.bookie):
					prof = max1**-1 + max2**-1
					if prof < 1:
						alreadyArbed.append([game1, game2])
						calcBetAmt(game1, game2)
			except:
				pass

				
def WH():
	gameList = []
	driver = webdriver.Firefox()
	driver.get("https://www.williamhill.com.au/tennis#offcanvas")
	
	tournies = driver.find_element_by_css_selector("div.block-inner").find_element_by_css_selector("ul").find_elements_by_css_selector("li")
	
	# first need to make sure all are showing
	for tournie in tournies[1:]:
		tournie.click()
	time.sleep(5)
	games = driver.find_elements_by_css_selector("div.row")

	count = 0
	tot = len(games)
	dec = 0
	sys.stdout.write("[")
	for game in games:

		if (float(count) / tot) > float(dec) / 10:
			sys.stdout.write("=")
			sys.stdout.flush()
			dec += 0.5
		count += 1
		try:

			info = game.find_elements_by_class_name("large-12")[1]
			
			players = info.find_elements_by_class_name("row")
			p1 = players[0].find_elements_by_css_selector("li")[0].text
			p1o = float(players[0].find_elements_by_css_selector("li")[1].find_element_by_css_selector("a").text)
			
			p2 = players[1].find_elements_by_css_selector("li")[0].text
			p2o = float(players[1].find_elements_by_css_selector("li")[1].find_element_by_css_selector("a").text)
			
			p1 = re.sub(r'[^\w\s]','',p1.split()[1])
			p2 = re.sub(r'[^\w\s]','',p2.split()[1])
			#print p1
			gameList.append(Game(p1, p1o, p2, p2o, "William Hill"))
		except:
			pass
	print "]"
	driver.close()

	return gameList

# fractional to decimal odds
def ftod(o):
	o = o.split("/")
	n = float(o[0])
	d = float(o[1])
	
	return (n/d) + 1

def marathon():
	games = []
	driver = webdriver.Firefox()
	driver.get("https://www.marathonbet.com/en/betting/2398?periodGroupAllEvents=0")
	matches = driver.find_elements_by_xpath("//tbody[contains(@id, 'event_')]")
	
	tot = len(matches)
	count = 0
	dec = 0
	sys.stdout.write("[")
	for match in matches:
		if (float(count) / tot) > float(dec) / 10:
			sys.stdout.write("=")
			sys.stdout.flush()
			dec += 0.5
		count += 1

		info = match.find_elements_by_css_selector("td")
		names = info[0].find_element_by_css_selector("table").find_elements_by_css_selector("div")
		p1 = names[0].text
		p2 = names[1].text
		
		
		prices = match.find_elements_by_class_name("price")
		p1o = float(prices[0].find_element_by_css_selector("span").get_attribute("data-selection-price"))
		p2o = float(prices[1].find_element_by_css_selector("span").get_attribute("data-selection-price"))
		
		p1 = re.sub(r'[^\w\s]','',p1.split()[0])
		p2 = re.sub(r'[^\w\s]','',p2.split()[0])
		#print p1
		games.append(Game(p1, p1o, p2, p2o, "MarathonBet"))
	print "]"
	driver.close()
	return games
	
def pinnacle():
	games = []
	driver = webdriver.Firefox()
	driver.get("https://www.pinnaclesports.com/en/odds/today/tennis")
	matches = driver.find_elements_by_css_selector("tbody.ng-scope")
	tot = len(matches)
	count = 0
	dec = 0
	sys.stdout.write("[")
	for match in matches:
		if (float(count) / tot) > float(dec) / 10:
			sys.stdout.write("=")
			sys.stdout.flush()
			dec += 0.5
		count += 1
		try:
			pinfo = match.find_elements_by_css_selector("tr.ng-scope")
			
			p1 = pinfo[0].find_element_by_class_name("name").text
			p2 = pinfo[1].find_element_by_class_name("name").text
			
			if ("(" or "Game") in (p1 or p2):
				continue
			
			p1 = re.sub(r'[^\w\s]','',p1.split()[1])
			p2 = re.sub(r'[^\w\s]','',p2.split()[1])
			
			#print p1
			#print p1, p2
			try:
				p1o = pinfo[0].find_elements_by_css_selector("td")[4].find_element_by_css_selector("span").text
				p2o = pinfo[1].find_elements_by_css_selector("td")[4].find_element_by_css_selector("span").text
			except:
				p1o = pinfo[0].find_elements_by_css_selector("td")[3].find_element_by_css_selector("span").text
				p2o = pinfo[1].find_elements_by_css_selector("td")[3].find_element_by_css_selector("span").text
				
			try:
				p1o = float(p1o)
				p2o = float(p2o)
			except:
				continue

			
			games.append(Game(p1, p1o, p2, p2o, "Pinnacle"))
		except:
			pass
	print "]"
	driver.close()
	return games

#display = Display(visible = 0, size=(1600, 900))
#display.start()

alerted = []
if __name__ == "__main__":
	while 1:
		print "Pinnacle"
		#pGames = pinnacle()
		print "Marathon Bet"	
		mrGames = marathon()
		print "William Hill"	
		whGames = WH()
		print "Crownbet"
		cbGames = CB()
		print "Sportsbet"
		sbGames = SB()

		findArb([cbGames, sbGames, whGames, mrGames])

	#time.sleep(10 * 60)
