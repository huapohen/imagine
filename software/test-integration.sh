#!/bin/sh
# Fixed offline regression scope for board/LB1 integration. No model config or live-model tests.
set -eu
cd "$(dirname "$0")"
mkdir -p test-output
../firmware/test.sh
python3 -m lingban.serial_protocol --self-test
python3 - <<'PY'
import unittest
suite=unittest.TestSuite()
for pattern in ('test_core.py','test_http.py','test_protocols.py'):
    suite.addTests(unittest.defaultTestLoader.discover('tests',pattern=pattern))
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
PY
