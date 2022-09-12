#!/usr/bin/env bash

if [ -f "Zyne.py" ]; then
	rm -rf build
	rm -rf dist
	pyinstaller --clean ./scripts/Zyne_macos.spec
	rm -r build
	rm dist/Zyne_B
else
	echo "start this script from the Zyne_B's root directory - ./scripts/builder_pyinstaller_macos.sh"
fi
