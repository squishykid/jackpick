import requests
from json.decoder import JSONDecodeError
import time
import lxml.html as lh
from datetime import datetime
import voluptuous as vol

BASE_URL = 'https://www.opal.com.au'

MATCH_DOLLARS = vol.validators.Match(r'^-?\$\d+.\d{2}$')

CARD_SCHEMA = vol.Schema({
    vol.Required('cardNumber'): vol.All(str, vol.Length(min=16, max=16)),
    vol.Required('cardNickName'): str,
    vol.Required('cardState'): str,
    vol.Required('cardBalance'): int,
    vol.Required('active'): bool,
    vol.Required('svPending'): int,
    vol.Required('toBeActivated'): bool,
    vol.Required('displayName'): str,
    vol.Required('cardBalanceInDollars'): MATCH_DOLLARS,
    vol.Required('currentCardBalanceInDollars'): MATCH_DOLLARS,
    vol.Required('svPendingInDollars'): vol.Any(None, MATCH_DOLLARS) 
}, extra=vol.REMOVE_EXTRA)

CARDS_SCHEMA = vol.Schema([CARD_SCHEMA])

class Opal():
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None

    def __enter__(self):
        assert self.session is None, 'must logout first'
        session = requests.Session()
        url = BASE_URL + '/login/registeredUserUsernameAndPasswordLogin'
        params = {
            'h_username': self.email,
            'h_password': self.password,
            'submit': 'Log in'
        }
        r = session.post(url, params=params)
        try:
            val = r.json()
        except JSONDecodeError:
            raise ValueError('unable to log in')
        if val['errorMessage'] is not None:
            raise ValueError(val['errorMessage'])
        self.session = session
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        url = BASE_URL + '/registered/logout'
        r = self.session.get(url)
        self.session = None
        return False

    def cards(self):
        if self.session is None:
            raise RuntimeError('need to login first')
        url = BASE_URL + '/registered/getJsonCardDetailsArray'
        params = {
            '_': int(time.time())
        }
        r = self.session.get(url, params=params)
        return CARDS_SCHEMA(r.json())

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
