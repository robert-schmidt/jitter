.PHONY: run build-mac build-win clean

run:
	python -m jitter.main

build-mac:
	@# Ensure cliclick is available
	@which cliclick >/dev/null 2>&1 || (echo "Installing cliclick..." && brew install cliclick)
	pyinstaller \
		--name Jitter \
		--windowed \
		--osx-bundle-identifier com.jitter.app \
		--exclude-module pynput \
		run.py

build-win:
	pyinstaller \
		--name Jitter \
		--onefile \
		--windowed \
		--hidden-import pynput.keyboard._win32 \
		--hidden-import pynput.mouse._win32 \
		--add-data "jitter/_settings_runner.py:jitter" \
		run.py

clean:
	rm -rf build dist *.spec
