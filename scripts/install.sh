#!/bin/bash

./scripts/clean.sh

if [ -x "$(which python)" ]; then
    virtualenv --clear --no-site-packages -p python py2

    ./py2/bin/pip install coverage
    ./py2/bin/pip install zope.interface
    ./py2/bin/pip install zope.lifecycleevent
    ./py2/bin/pip install zope.component
    ./py2/bin/pip install zope.deprecation
    ./py2/bin/pip install https://github.com/conestack/odict/archive/master.zip
    ./py2/bin/pip install https://github.com/conestack/plumber/archive/master.zip
    ./py2/bin/pip install https://github.com/conestack/node/archive/master.zip
    ./py2/bin/pip install -e .
fi
if [ -x "$(which python3)" ]; then
    virtualenv --clear --no-site-packages -p python3 py3

    ./py3/bin/pip install coverage
    ./py3/bin/pip install zope.interface
    ./py3/bin/pip install zope.lifecycleevent
    ./py3/bin/pip install zope.component
    ./py3/bin/pip install zope.deprecation
    ./py3/bin/pip install https://github.com/conestack/odict/archive/master.zip
    ./py3/bin/pip install https://github.com/conestack/plumber/archive/master.zip
    ./py3/bin/pip install https://github.com/conestack/node/archive/master.zip
    ./py3/bin/pip install -e .
fi
