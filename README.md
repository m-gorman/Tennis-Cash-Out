# Tennis-Arb
Automatic arbitrage system for Sportsbet

Credit to http://www.bespokebots.com/betfair-bots-APING.php for the Betfair API.

How it works:
  The bot scans betfair and sportsbet and compares the prices between the two markets. If sportsbet has overpriced a particular tennis 
  player it places a bet on them.
  When sportsbet corrects the odds, the cash out value for the placed bet will have increased, and the bot will then cash out,
  securing a profit.

To use:
  Fill in your sportsbet username and password in sb_settings. You will need to get SSL certifications (there is a tutorial
  on the betfair api page).
  
  Once requirements are met, run lay_back.py
