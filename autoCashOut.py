from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import csv
import pickle
from sb_settings import USER, PWORD
# Bot for logged in sportsbet operations
class SBBot():
	def __init__(self):
		self.STAKE_SIZE = 200

		driver = webdriver.Firefox()
		self.login(driver)

	# restart current driver
	def refresh_login(self):
		self.driver.close()
		
		driver = webdriver.Firefox()

		self.login(driver)


	def login(self, driver):
		driver.get("http://www.sportsbet.com.au/")

		# Login ======================
		time.sleep(7)
		user = driver.find_element_by_id("fakeusername")
		pword = driver.find_element_by_id("fakepassword")

		user.send_keys(USER)
		pword.send_keys(PWORD)
		pword = driver.find_element_by_id("password")
		time.sleep(1)
		pword.send_keys(Keys.ENTER)
		time.sleep(5)

		# ============================
		self.driver = driver

	# cashout bets if their value is greater than certain amount	
	def cashout(self):
		driver = self.driver
		driver.get("http://www.sportsbet.com.au/")

		pendingBets = driver.find_element_by_id("pendingBets")
		pendingBets.click()
		time.sleep(5)

		driver.find_element_by_id("trans-head-opencloseall").click()

		time.sleep(5)
		bets = driver.find_elements_by_class_name("accordion-extra")
		for bet in bets:
			try:
				bet.find_element_by_class_name("btnRefresh").click()
				time.sleep(2)
				betID = bet.get_attribute("id")
				betID = betID.replace("accordion-extra-", "")
				cashoutValue = float(bet.find_element_by_class_name("btnRefresh").text.replace("$", ""))
				# cash out if we have made a profit
				print str(cashoutValue) + " versus original stake of " + str(self.STAKE_SIZE)
				if cashoutValue > self.STAKE_SIZE:
					cashoutBtn = bet.find_element_by_id("cashout-button-" + betID)
					cashoutBtn.click()
					time.sleep(2)
					confirmPanel = bet.find_element_by_id("cashout-confirm-" + betID)
					confirmBtn = confirmPanel.find_element_by_css_selector("a")
					confirmBtn.click()
			except:
				pass

	# place a bet on the game with given players
	# will not place if the odds do not match
	def place_bet(self, p1, p1o, p2, p2o, betOn):
		driver = self.driver

		time.sleep(5)

		driver.get("http://www.sportsbet.com.au/betting/tennis?MegaNav")

		time.sleep(5)

		# each bet 'card' is in an accordion body
		matches = driver.find_elements_by_xpath("//li[contains(@id, 'match')]")

			
			
		# go through them, fetching odds
		for match in matches:
			print len(matches)
			# get the score
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
 					print type(p1o), type(gp1o)
 					print p1, gp1, p2, gp2
 					if (gp1 == p1 and gp2 == p2 and p1o == gp1o and p2o == gp2o) or (gp1 == p2 and gp2 == p1 and gp1o == p2o and gp2o == p1o):
 					 	playersInfo[0].click()
 					 	break
			except:
				print "FUCK"

		#driver.refresh()



			# each bet 'card' is in an accordion body

				
			#driver.close()
if __name__ == "__main__":
	c = SBBot()
	c.place_bet(0,0,0,0,0)