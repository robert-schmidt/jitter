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
		--icon assets/Jitter.icns \
		--exclude-module pynput \
		run.py
	@# Hide dock icon — app lives in menu bar only
	/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" dist/Jitter.app/Contents/Info.plist 2>/dev/null || \
	/usr/libexec/PlistBuddy -c "Set :LSUIElement true" dist/Jitter.app/Contents/Info.plist
	@echo "Dock icon hidden (LSUIElement=true)"
	@# Re-sign after plist modification (otherwise signature is invalid → "damaged" on other Macs)
	codesign --force --deep --sign - dist/Jitter.app
	@echo "Ad-hoc re-signed"

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
