#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build
c++ -std=c++11 -Wall -Wextra -Werror -Iinclude test/protocol_test.cpp -o build/protocol_test
./build/protocol_test
./build/protocol_test --golden ../docs/software/serial-golden-vectors.tsv
c++ -std=c++11 -Wall -Wextra -Werror -Iinclude test/controller_test.cpp -o build/controller_test
./build/controller_test
