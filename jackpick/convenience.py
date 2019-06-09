"""Convenience functions"""
import re
import datetime


RE_DOLLARS = re.compile(r'^-?\$\d+.\d{2}$')
RE_STRIP = re.compile(r'[^\d-]')


def parse_dollars_amount(amount_str):
    if not RE_DOLLARS.match(amount_str):
        raise ValueError(f'unable to parse dollars amount {amount_str}.')
    return float(RE_STRIP.sub('', amount_str)) / 100


def end_of_weekly_travel_reward():
    n = datetime.datetime.now()
    monday = (n + datetime.timedelta(-n.weekday())).date()
    return datetime.datetime.combine(monday, datetime.datetime.min.time())


def card_status(o, card_idx, card):
    balance = parse_dollars_amount(card['cardBalanceInDollars'])
    journey_number = None
    wt_end = end_of_weekly_travel_reward()
    last_topup = None
    for t in o.trips(card=card_idx):
        if last_topup is None:
            topup_amount = t['amount']
            topup_date = t['date']
            amount_c = parse_dollars_amount(topup_amount)
            if amount_c > 0:
                last_topup = (amount_c, topup_date)

        if journey_number is None and wt_end is not None:
            j_date = t['date']
            if j_date >= wt_end:
                jn = t['journey_number']
                if jn is not None:
                    journey_number = jn
            else:
                wt_end = None
                journey_number = 0

        if last_topup is not None and (journey_number is not None or wt_end is None):
            break
    return {
        'cardNumber': card['cardNumber'],
        'balance': balance,
        'weekly_travel_journeys': journey_number,
        'last_topup': last_topup
    }


def current_status(o, card_numbers=None):
    for i, card in enumerate(o.cards()):
        card_number = card['cardNumber']
        if card_numbers and card_number not in card_numbers:
            continue
        yield card_status(o, i, card)
