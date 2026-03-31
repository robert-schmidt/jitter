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
		--hidden-import pynput.keyboard._darwin \
		--hidden-import pynput.mouse._darwin \
		run.py
	@# Copy cliclick alongside the .app (not inside — avoids signature issues)
	cp "$$(which cliclick)" dist/cliclick
	@echo "cliclick copied to dist/cliclick (bundled alongside Jitter.app)"

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
