#/bin/bash

tbears clear
tbears run governance

./issue_rpc.sh getScoreStatus2
./issue_rpc.sh getScoreStatus
#./issue_rpc.sh acceptScore
#./issue_rpc.sh getScoreStatus
