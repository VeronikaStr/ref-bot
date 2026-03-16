import random

rewards=[5,10,20,50,100,200,"jackpot"]

def spin():

    reward=random.choice(rewards)

    return reward
