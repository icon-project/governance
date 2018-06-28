#/bin/bash

tbears clear
tbears run governance --install params.json

python -m unittest test_governance.py
