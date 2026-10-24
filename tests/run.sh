#!/bin/sh
# Executa toda a verificação local. Uso: sh tests/run.sh
set -e
cd "$(dirname "$0")/.."
python3 build.py --check
node --check lib.js && node --check app.js
node tests/lib.test.js
node tests/app.smoke.js
python3 -m unittest discover -s tests
