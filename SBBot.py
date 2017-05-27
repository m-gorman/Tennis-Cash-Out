from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import csv
import pickle
import sys
from pyvirtualdisplay import Display
import math
from sb_settings import USER, PWORD

# Bot for logged in sportsbet operations
class SBBot():
	def __init__(self):
	#	print self.user, self.password
		self.STAKE_SIZE = 240
	#	print "Init"
		driver = webdriver.Firefox()
		self.login(driver)
		self.get_balance()
		print "Balance: "
		print self.balance

	# restart current driver
	def refresh_login(self):
		self.driver.close()
		
		driver = webdriver.Firefox()

		self.login(driver)
		
	def get_balance(self):
		balance = float(self.driver.find_element_by_id("balance-value").text.replace("$", ""))
		self.balance = balance


	def login(self, driver):
		print "Logging in"
	#	print self.user
	#	print self.password
		driver.get("http://www.sportsbet.com.au/")
	#	print "At page"
		# Login ======================
		time.sleep(7)
		user = driver.find_element_by_id("fakeusername")
		user.click()
		time.sleep(3)
		user = driver.find_element_by_id("username")
		time.sleep(2)

		pword = driver.find_element_by_id("fakepassword")
		
		
		user.send_keys(USER)
		time.sleep(3)
		pword.send_keys(PASSWORD)
	#	print "Sent keys"
		pword = driver.find_element_by_id("password")
		time.sleep(1)
	#	print "Pressing enter"
		pword.send_keys(Keys.ENTER)
		time.sleep(5)
	#	print "Done"

		# ============================
		self.driver = driver

	# cashout bets if their value is greater than certain amount	
	def cashout(self):
		time.sleep(10)
		num_bets_cashed_out = 0

		driver = self.driver
		driver.get("http://www.sportsbet.com.au/")

		pendingBets = driver.find_element_by_id("pendingBets")
		pendingBets.click()
		time.sleep(5)

		driver.find_element_by_id("trans-head-opencloseall").click()

		time.sleep(5)
		bets = driver.find_elements_by_class_name("accordion-extra")
		print "Attempting cashout"
		for bet in bets:
			try:
				bet.find_element_by_class_name("btnRefresh").click()
				time.sleep(2)
				betID = bet.get_attribute("id")
				betID = betID.replace("accordion-extra-", "")
				cashoutValue = float(bet.find_element_by_class_name("btnRefresh").text.replace("$", ""))
				
				stake = bet.find_element_by_id("cashout-main-" + betID).find_element_by_css_selector("p").text
				stake = stake.replace("$", "")
				stake = float(stake)
				# cash out if we have made a profit
				print str(cashoutValue) + " versus original stake of " + str(stake)
				if cashoutValue > stake:
					cashoutBtn = bet.find_element_by_id("cashout-button-" + betID)
					cashoutBtn.click()
					time.sleep(2)
					confirmPanel = bet.find_element_by_id("cashout-confirm-" + betID)
					confirmBtn = confirmPanel.find_element_by_css_selector("a")
					confirmBtn.click()
					num_bets_cashed_out += 1
			except:
				pass

		return num_bets_cashed_out

	def exit(self):
		self.driver.close()

	# place a bet on the game with given players
	# will not place if the odds do not match
	# amount will be the balance floored to the nearest 5
	def place_bet(self, p1, p1o, p2, p2o, betOn):
	
		betAmt = math.floor(self.balance / 5) * 5
		
		#print "bet size will be" + str(betAmt)
		driver = self.driver
		#print "New fn"
		time.sleep(5)
		#print "Getting page"
		driver.get("http://www.sportsbet.com.au/betting/tennis?MegaNav")

		time.sleep(5)
		#print "Finding items"
		# each bet 'card' is in an accordion body
		matches = driver.find_elements_by_xpath("//li[contains(@id, 'match')]")

		bet_prepared = False	
		num = len(matches)
		count = 0
		# go through them, fetching odds
		for match in matches:
			# get the score
			#print str(count) + " / " + str(num)
			count += 1
			try:
				gameInfo = match.find_element_by_class_name("market-name")
				playersInfo = match.find_element_by_class_name("accordion-body").find_elements_by_class_name("price-link")
			 	if playersInfo:
					gp1 = str(playersInfo[0].find_element_by_class_name("team-name").text)
					gp1o = float(playersInfo[0].find_element_by_class_name("odd-val").text)
					gp2 = str(playersInfo[1].find_element_by_class_name("team-name").text)
					gp2o = float(playersInfo[1].find_element_by_class_name("odd-val").text)
					start_time = gameInfo.find_element_by_class_name("start-time").text
 					gp1 = gp1.split()[1]
 					gp2 = gp2.split()[1]
 					if (gp1 == p1 and gp2 == p2 and p1o == gp1o and p2o == gp2o):
 					 	playersInfo[int(gp2 == betOn)].click()
 					 	bet_prepared = True
 					 	break
 					elif (gp1 == p1 and gp2 == p2 and (p1o != gp1o or p2o != gp2o)):
 						print "Odds have changed"
 						break
 					elif (gp1 == p2 and gp2 == p1 and gp1o == p2o and gp2o == p1o):
 					 	playersInfo[int(gp2 == betOn)].click()
 					 	bet_prepared = True
 					 	break
 					elif (gp1 == p2 and gp2 == p1 and (gp1o != p2o or gp2o != p1o)):
 					 	print "Odds have changed"
 					 	break
			except:
				print "Error"

		if bet_prepared:
			#print "Prepped"
			time.sleep(1.5)
			input_amount = driver.find_element_by_css_selector("input#stake_sgl_0")
			input_amount.send_keys(str(betAmt))
			#print "Sent amount"
			time.sleep(1)
			driver.find_element_by_css_selector("a#bs-placebet").click()
			#print "Clicked place bet"
			time.sleep(30)
			driver.find_element_by_css_selector("a.bs-confirm-show.btn-y").click()
			print "***BET PLACED***"
		else:
			print "Couldn't find game"
		time.sleep(120)
		self.driver.close()

		if bet_prepared:
			return True
		else:
			return False



if __name__ == "__main__":
	args = sys.argv[1:]

	if len(args) < 6:
		print ("Usage: p1 p1o p2 p2o betOn amount (optional)username (optional)password")
		sys.exit()

	p1 = args[0]
	p1o = float(args[1])
	p2 = args[2]
	p2o = float(args[3])
	betOn = args[4]
	amount = float(args[5])
	
	try:
		username = args[6]
		pword = args[7]
	except:
		username = pword = None

	display = Display(visible=0, size=(1600,900))
	display.start()
	print username, pword
	if (username and pword):
		print "Using custom login"
		c = SBBot()
	else:
		print "Default login"
		c = SBBot()
	c.cashout()
	c.get_balance()
	print c.balance
	#c.place_bet(p1, p1o, p2, p2o, betOn)