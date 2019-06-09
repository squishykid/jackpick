import requests
from json.decoder import JSONDecodeError
import time
import lxml.html as lh
from datetime import datetime

BASE_URL = 'https://www.opal.com.au'

class Opal():

    def __init__(self, session=None):
        self.session = session
        print(session)
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

    def logout(self):
        url = BASE_URL + '/registered/logout'
        r = self.session.get(url)

    def cards(self, retry=True):
        if self.session is None:
            raise RuntimeError('need to login first')
        url = BASE_URL + '/registered/getJsonCardDetailsArray'
        params = {
            '_': int(time.time())
        }
        r = self.session.get(url, params=params)
        try:
            return r.json() # todo: add some validation
        except JSONDecodeError:
            if 'session expired' in r.text.lower() and retry == True:
                print('session expired, trying again')
                return self.cards(retry=False)
            print('decode error', r, r.text)
            raise
    
    def _transactions(self, page):
        def get_text(s):
            if s is None:
                return None
            return s.strip()

        def get_date(s):
            s = get_text(s)
            return datetime.strptime(s, '%a%d/%m/%Y%H:%M')

        def get_mode(x):
            try:
                return x[0].get('alt', None)#.values()
            except:
                return None

        doc = lh.fromstring(page)
        for x in doc.xpath('//tbody/tr'): # for each transaction
            jn = get_text(x[4].text)
            yield {
                'tx_id': int(get_text(x[0].text)),
                'date': get_date(x[1].text_content()),
                'mode': get_mode(x[2]),
                'details': get_text(x[3].text),
                'journey_number': jn if jn is None else int(jn),
                'fare_applied': get_text(x[5].text),
                'fare': get_text(x[6].text),
                'discount': get_text(x[7].text),
                'amount': get_text(x[8].text)
            }
    
    def trips(self, card, page=1, limit=-1):
        if self.session is None:
            raise RuntimeError('need to login first')

        url = BASE_URL + '/registered/opal-card-activities-list'
        params = {
            "AMonth": "-1",
            "AYear": "-1",
            "cardIndex": card,
            "pageIndex": page,
            '_': int(time.time())
        }
        r = self.session.get(url, params=params)

        for t in self._transactions(r.text):
            if t['tx_id'] <= limit:
                return
            yield t
        if 'title="Next page"' not in r.text:
            return
        yield from self.trips(card, page+1, limit)
