import requests
from json.decoder import JSONDecodeError
import time

BASE_URL = 'https://www.opal.com.au'

class Opal():

    def __init__(self, session=None):
        self.session = session
        if self.session is None:
            self.session = requests.Session()
    
    def session(self):
        return self.session

    def login(self, email, password):
        url = BASE_URL + '/login/registeredUserUsernameAndPasswordLogin'
        params = {
            'h_username': email,
            'h_password': password,
            'submit': 'Log in'
        }
        r = self.session.post(url, params=params)
        try:
            val = r.json()
        except JSONDecodeError:
            raise ValueError('invalid login')
        if val['errorMessage'] is not None:
            raise ValueError(val['errorMessage'])
        return val

    def cards(self):
        if self.session is None:
            raise RuntimeError('need to login first')
        url = BASE_URL + '/registered/getJsonCardDetailsArray'
        params = {
            '_': int(time.time())
        }
        r = self.session.get(url, params=params)
        return r.json() # todo: add some validation
    
    def _next_page(page):
        return 2 # next page number or None
    
    def _transactions(page):
        # tx_number, date, mode, details, journey number, fare applied, fare, discount, amount
        yield (1) 
    
    def trips(self, card=0, up_to_tx=None, page=1, limit=None):
        if self.session is None:
            raise RuntimeError('need to login first')
        # get the data

        # parse the stuff -> (next_page?, transaction numbers)
        # if found the transaction number
        r = 'do the request'
        for t in self._transactions(r.text):
            if t[0] <= limit:
                return
            yield t
        next_page = self._next_page(r.text)
        if next_page is None:
            return
        self.trips(card, up_to_tx, page+1, limit)


o = Opal()
print(o.login('email@here.com', 'passw0rd'))
print(o.cards())
