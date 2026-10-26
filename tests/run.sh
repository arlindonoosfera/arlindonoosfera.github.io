#!/bin/sh
# Executa toda a verificação local. Uso: sh tests/run.sh
set -e
cd "$(dirname "$0")/.."
python3 build.py --check
node --check site.js
node tests/site.test.js
python3 -m unittest discover -s tests
