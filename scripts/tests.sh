#!/bin/sh
if [ -x "$(which python)" ]; then
    ./py2/bin/python -m unittest node.ext.directory.tests
fi
if [ -x "$(which python3)" ]; then
    ./py3/bin/python -m unittest node.ext.directory.tests
fi
