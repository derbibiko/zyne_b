#!/usr/bin/env bash

if [ -f "Zyne.py" ]; then
	rm -rf build
	rm -rf dist
	pyinstaller -F -w --clean ./scripts/Zyne_linux.spec
	rm -r build
else
	echo "start this script from the Zyne's root directory - ./scripts/builder_pyinstaller_linux.sh"
fi
