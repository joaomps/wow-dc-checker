import random
import requests
import datetime
import schedule
import time
import json
from retrying import retry

get_accounts_url = 'https://expressjs-prisma-production.app/accounts'
disc_notifications = "https://discord.com/api/webhooks/123/1234"
accounts_ws = 'https://expressjs-prisma-production.app/accounts/'


@retry(stop_max_attempt_number=5, wait_fixed=3000)
def get_accounts():
    try:
        r = requests.get(get_accounts_url)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except requests.exceptions.Timeout:
        print("The request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
        return None


@retry(stop_max_attempt_number=5, wait_fixed=3000)
def handle_delete_account(account):
    payload = {'account': account}
    headers = {'content-type': 'application/json'}
    try:
        result = requests.delete(
            get_accounts_url, data=json.dumps(payload), headers=headers)
    except requests.exceptions.Timeout:
        print("The request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
        return None


@retry(stop_max_attempt_number=5, wait_fixed=3000)
def update_account_status(account):
    data = {
        "account": account,
        "break_time": 0,
        "status": "Offline"
    }

    headers = {"Content-Type": "application/json"}

    try:
        result = requests.post(accounts_ws, json=data, headers=headers)
    except requests.exceptions.Timeout:
        print("The request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
        return None


def send_discord_message(account):
    # send post to disc_notifications with the account
    data = {
        "content": "@here",
        "username": account,
        "embeds": [
            {
                "title": "Disconnected",
                "color": 14696255,
                "timestamp": str(datetime.datetime.utcnow()),
                "description": account + " was last seen a few minutes ago.",
            }
        ],
    }

    headers = {
        "Content-Type": "application/json"
    }

    result = requests.post(
        disc_notifications, json=data, headers=headers)

    if 200 <= result.status_code < 300:
        # delete account from ws
        handle_delete_account(account)
        update_account_status(account)
    else:
        print(
            f"Not sent with {result.status_code}, response:\n{result.json()}")


def handle_accounts():
    accounts = get_accounts()
    # get current date as string
    current_time = datetime.datetime.now()
    if accounts:
        for account in accounts:
            if account['status'] == 'Breaking':
                end_of_break_in_time = datetime.datetime.fromtimestamp(
                    account['break_time']) + datetime.timedelta(minutes=random.randint(3, 6))

                if current_time >= end_of_break_in_time:
                    send_discord_message(account['account'])
    else:
        print("No accounts found.")


schedule.every(2).minutes.do(handle_accounts)

while 1:
    n = schedule.idle_seconds()
    if n is None:
        # no more jobs
        break
    elif n > 0:
        # sleep exactly the right amount of time
        time.sleep(n)
    schedule.run_pending()
