import time

cooldowns={}

def check(user):

    now=time.time()

    if user in cooldowns:

        if now-cooldowns[user] < 3:
            return False

    cooldowns[user]=now

    return True