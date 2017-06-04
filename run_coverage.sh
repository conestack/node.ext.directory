#!/bin/sh
./$1/bin/coverage run -m node.ext.directory.tests
./$1/bin/coverage report
./$1/bin/coverage html
