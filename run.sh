#/bin/bash

tbears stop
tbears clear
tbears start
tbears deploy governance -c deploy.json

python -m unittest -v test_governance.py
