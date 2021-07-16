import schedule
import time
from helper_functions import update_api_idealista

# schedule an update once a month:
schedule.every(28).days.do(update_api_idealista)
#schedule.every(2).minutes.do(update_api_idealista)

while True:
    schedule.run_pending()
    time.sleep(1)