#!/bin/bash

EOA1='hx9000000000000000000000000000000000000001'
GOVERNANCE='cx5cdb9522e8e3a7a1ef829913c6cc1da2af9db17f'
TXHASH1='0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27'
SCORE_ADDR='cxb0776ee37f5b45bfaea8cff1d8232fbb6122ec32'
WRONG_SCORE_ADDR='cx9999999999999999999999999999999999999999'

if [[ -z $1 ]]; then
    echo "Usage: $0 <command>"
    exit 1
fi
action=$1

CURL_CMD='curl -H "Content-Type: application/json" -d '
SERVER_URL='http://localhost:9000/api/v3'

case "$action" in
  gettxres )
      PARAMS="{
          \"jsonrpc\": \"2.0\",
          \"method\": \"icx_getTransactionResult\",
          \"id\": 1234,
          \"params\": {
              \"txHash\": \"$2\"
          }
      }"
  ;;
  getapi )
      PARAMS="{
          \"jsonrpc\": \"2.0\",
          \"method\": \"icx_getScoreApi\",
          \"id\": 1234,
          \"params\": {
              \"address\": \"$2\"
          }
      }"
  ;;
  acceptScore )
      PARAMS="{
          \"jsonrpc\": \"2.0\",
          \"method\": \"icx_sendTransaction\",
          \"id\": 1234,
          \"params\": {
              \"from\": \"$EOA1\",
              \"to\": \"$GOVERNANCE\",
              \"timestamp\": \"0x1234567890\",
              \"dataType\": \"call\",
              \"data\": {
                  \"method\": \"acceptScore\",
                  \"params\": {
                      \"txHash\": \"$TXHASH1\"
                  }
              }
          }
      }"
  ;;
  getScoreStatus )
      PARAMS="{
          \"jsonrpc\": \"2.0\",
          \"method\": \"icx_call\",
          \"id\": 1234,
          \"params\": {
              \"from\": \"$EOA1\",
              \"to\": \"$GOVERNANCE\",
              \"timestamp\": \"0x1234567890\",
              \"dataType\": \"call\",
              \"data\": {
                  \"method\": \"getScoreStatus\",
                  \"params\": {
                      \"address\": \"$SCORE_ADDR\"
                  }
              }
          }
      }"
  ;;
  getScoreStatus2 )
      PARAMS="{
          \"jsonrpc\": \"2.0\",
          \"method\": \"icx_call\",
          \"id\": 1234,
          \"params\": {
              \"from\": \"$EOA1\",
              \"to\": \"$GOVERNANCE\",
              \"timestamp\": \"0x1234567890\",
              \"dataType\": \"call\",
              \"data\": {
                  \"method\": \"getScoreStatus\",
                  \"params\": {
                      \"address\": \"$WRONG_SCORE_ADDR\"
                  }
              }
          }
      }"
  ;;
  * )
    echo "Error: Invalid action... $action"
    echo "   Valid actions are [gettxres]."
    exit 1
  ;;
esac

echo "request = $PARAMS"
eval $CURL_CMD \'$PARAMS\' $SERVER_URL
echo
