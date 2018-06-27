import unittest
import requests


class JsonRpcHelper:
    BASE_URL = 'http://localhost:9000/api/v3'

    MASTER_ADDR = 'hxaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    def __init__(self,
                 to,
                 url=BASE_URL,
                 from_=MASTER_ADDR,
                 method='icx_sendTransaction',
                 last_idx=1000):
        self.url = url
        self.from_ = from_
        self.to = to
        self.method = method
        self.last_idx = last_idx

    def __getattr__(self, name):
        self.last_idx += 1

        def func(*args, **kwargs):
            response = requests.post(self.url, json={
                "jsonrpc": "2.0",
                "method": self.method,
                "id": self.last_idx,
                "params": {
                    "version": "0x3",
                    "from": self.from_,
                    "to": self.to,
                    "stepLimit": "0x12345",
                    "timestamp": "0x563a6cf330136",
                    "dataType": "call",
                    "data": {
                        "method": name,
                        "params": kwargs,
                    }
                }
            })
            response_data = response.json()
            try:
                tx_hash = response_data['result']
                if self.method == 'icx_sendTransaction':
                    response = requests.post(self.url, json={
                        "jsonrpc": "2.0",
                        "method": "icx_getTransactionResult",
                        "id": self.last_idx,
                        "params": {
                            "txHash": tx_hash
                        }
                    })
                    response_data = response.json()
                return response_data['result']
            except KeyError:
                return response_data['error']

        return func


GOVERNANCE = 'cx5cdb9522e8e3a7a1ef829913c6cc1da2af9db17f'
SCORE_VALID_ADDR = 'cxb0776ee37f5b45bfaea8cff1d8232fbb6122ec32'
SCORE_INVALID_ADDR = 'cx1234567890123456789012345678901234567890'
VALID_TXHASH='0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27'
INVALID_TXHASH='0x0000000000000000000000000000000000000000000000000000000123456789'


class TestGovernance(unittest.TestCase):
    score_call = JsonRpcHelper(to=GOVERNANCE, method='icx_call')
    score_sendTx = JsonRpcHelper(to=GOVERNANCE)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_0_getScoreStatus(self):
        # initial status - pending
        result = self.score_call.getScoreStatus(address=SCORE_VALID_ADDR)
        self.assertEqual(result['next']['status'], 'pending')
        self.assertIsNotNone(result['next']['deployTxHash'])
        # error expected
        error = self.score_call.getScoreStatus(address=SCORE_INVALID_ADDR)
        self.assertEqual(error['code'], -32000)

    def test_1_acceptScore(self):
        result = self.score_sendTx.acceptScore(txHash=INVALID_TXHASH)
        self.assertEqual(result['status'], hex(0))
        self.assertEqual(result['failure']['message'], 'Invalid txHash')
        result = self.score_sendTx.acceptScore(txHash=VALID_TXHASH)
        self.assertEqual(result['status'], hex(1))
        # verify the written status
        result = self.score_call.getScoreStatus(address=SCORE_VALID_ADDR)
        self.assertEqual(result['current']['status'], 'active')
        self.assertIsNotNone(result['current']['deployTxHash'])
        self.assertIsNotNone(result['current']['auditTxHash'])
        # self.assertRaises(KeyError, result['next'])
