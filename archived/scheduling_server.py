import supabase_controller as db
import telegram_controller as tg
import schedule
import time
import indicator_evaluator as ie

def fetch_alerts():
    alerts = db.fetch_alerts()
    # only select those with alert has alert_enabled = True
    alerts = [alert for alert in alerts if alert.get('alert_enabled')]
    return alerts
# fetch all alerts from db

def job():
    alerts = fetch_alerts()
    for alert in alerts:
        ticker = alert['ticker']
        settings = alert['settings']
        result = ie.analyze_stock(ticker, settings )
        print(result)
        tg.send_message(chat_id=27392018, message=str(result))
    # print(alerts)
    # tg.send_message(chat_id=27392018, message=str(alerts))
    
schedule.every(10).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
# alerts = db.fetch_alerts()
# print(alerts)


    