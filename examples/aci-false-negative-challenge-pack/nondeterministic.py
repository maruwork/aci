# CI-25 fixture: nondeterministic calls
import datetime
import random


def get_timestamp():
    return datetime.now()


def pick_winner(candidates):
    return random.choice(candidates)
