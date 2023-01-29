import requests
import datetime
import schedule
import time
import json

get_accounts_url = 'https://expressjs-prisma-production-36b8.up.railway.app/accounts'
disc_notifications = "https://discord.com/api/webhooks/1068981486759460864/CmAriOIh4cPiZkWGWhBiEqKXiAaPLZfpDFAe7Ppx7eUHP_QU3szCM60UsGjhxoIp3FCf"


def get_accounts():
    r = requests.get(get_accounts_url)
    if r.status_code == 200:
        return r.json()
    else:
        return None

def handle_delete_account(account):
    payload = {'account':account}
    headers = {'content-type': 'application/json'}
    result = requests.delete(get_accounts_url, data=json.dumps(payload), headers=headers)

def send_discord_message(account, minutes_passed):
    # send post to disc_notifications with the account and minutes_passed
    data = {
        "content": "@here",
        "username": account,
        "embeds": [
            {
                "title": "Disconnected",
                "color": 14696255,
                "timestamp": str(datetime.datetime.utcnow()),
                "description": account + " was last seen " + str(minutes_passed) + " minutes ago",
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
    else:
        print(
            f"Not sent with {result.status_code}, response:\n{result.json()}")


def handle_accounts():
    accounts = get_accounts()
    # get current date as string
    current_time = datetime.datetime.now()
    if accounts:
        for account in accounts:
            # convert date from string to datetime object
            account_lastseen = datetime.datetime.strptime(
                account['lastseen'], '%Y-%m-%dT%H:%M:%S.%fZ')
            # check how many minutes have passed between current_time and account_lastseen
            minutes_passed = (
                current_time - account_lastseen).total_seconds() / 60
            if minutes_passed > 5:
                send_discord_message(account['account'], minutes_passed)
    else:
        print("No accounts found.")

schedule.every(1).minute.do(handle_accounts)

while True:
    schedule.run_pending()
    time.sleep(1)
