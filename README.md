# Tennis-Arb
Automatic arbitrage system for Sportsbet

Credit to http://www.bespokebots.com/betfair-bots-APING.php for the Betfair API.

How it works:
  The bot scans betfair and sportsbet and compares the prices between the two markets. If sportsbet has overpriced a particular tennis 
  player, indicated by that player's back odds being higher than betfair's lay odds, the system places a bet.
  When sportsbet corrects the odds, the cash out value for the placed bet will have increased, and the bot will then cash out,
  securing a profit.

To use:
  Fill in your sportsbet username and password in SBBot.py. You will need to get SSL certifications (there is a tutorial
  on the betfair api page). Other requirements are selenium, and pyvirtualdisplay if you want the bot to run headless, for example on a
  cloud computer.
  
  Once requirements are met, run lay_back.py. The bot will run indefinitely.
