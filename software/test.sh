#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p test-output
../firmware/test.sh
python3 -m lingban.serial_protocol --self-test
python3 -m unittest discover -s tests -v
