import requests
import calendar
import time
from hashlib import sha256
from urllib.parse import urlparse

class SetRepClient:
    def __init__(self, base_url: str, user_key: str, user_token: str, app_code: str):
        try:
            chk_url = urlparse(base_url)
            if not all([chk_url.scheme, chk_url.netloc]):
                raise Exception("Wrong URL")
        except ValueError:
            raise Exception("Wrong URL")
        self.base_url: str = base_url
        self.user_key: str = user_key
        self.user_token: str = user_token
        self.app_code: str = app_code
        self.headers = {
            'Content-Type': 'application/json'
        }
        
    def get_sections(self)->list: 
        payload = {
            'token': self._get_token(),
            'app': self.app_code
        }
        response = self._send_request(payload)
        return response.get('data', [])
    
    def get_section_keys_values(self, section_code: str)->list:
        payload = {
            'token': self._get_token(),
            'app': self.app_code,
            'sectcode': section_code
        }
        response = self._send_request(payload)
        return response.get('data', [])
    
    def get_key_value(self, section_code: str, key_code: str)->str:
        payload = {
            'token': self._get_token(),
            'app': self.app_code,
            'sectcode': section_code,
            'keycode': key_code
        }
        response = self._send_request(payload)
        return response.get('data')
    
    def set_key_value(self, section_code: str, key_code: str, value: str)->bool:
        payload = {
            'token': self._get_token(),
            'app': self.app_code,
            'sectcode': section_code,
            'keycode': key_code,
            'value': value
        }
        response = self._send_request(payload)
        return response.get('succeeded', False)
    
    def _send_request(self, payload):
        response = requests.post(self.base_url, json=payload, headers=self.headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('succeeded', False):
                return result
            else:
                if result.get('err', False):
                    raise Exception(result.get('err'))
                else:
                    raise Exception("Unknown error")
        else:
            raise Exception(f"Server responded with status code: {response.status_code}")
        
    def _get_token(self)->str:
        key: str = self.user_key
        token: str = self.user_token
        current_GMT = time.gmtime()
        time_stamp = calendar.timegm(current_GMT)
        if (time_stamp % 2) == 0:
            token = token + str(time_stamp) + token
        else:
            token = str(time_stamp) + token
        token = sha256(token.encode('utf-8')).hexdigest()
        return str(time_stamp) + '_' + key + '_' + token
