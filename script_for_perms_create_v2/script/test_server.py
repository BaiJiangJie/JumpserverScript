import requests
from httpsig.requests_auth import HTTPSignatureAuth

__all__ = [
    'test'
]


def test():
    key_id = 'b55d354a-3d9c-486b-a4d4-997a8e094f83'
    key_secret = '3f81551d-ece1-4cf2-99a7-24d09ca26e3e'

    headers = {
        'X-JMS-ORG': '',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Date': "Mon, 17 Feb 2014 06:11:05 GMT",
    }
    print('>> headers: {} >> auth >> {}'.format(headers, ''))

    signature_headers = ['(request-target)', 'accept', 'date', 'host']

    auth = HTTPSignatureAuth(
        key_id=key_id,
        secret=key_secret,
        headers=signature_headers
    )

    url = 'http://jumpserver-test.fit2cloud.com/api/health/'

    res = requests.get(url, headers=headers, auth=auth)

    print(res.status_code)

    print(res.content)

    if res.status_code == 200:
        print(res.json())
