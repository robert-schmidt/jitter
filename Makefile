.PHONY: run build-mac build-win clean

run:
	python -m jitter.main

build-mac:
	pyinstaller \
		--name Jitter \
		--windowed \
		--osx-bundle-identifier com.jitter.app \
		--hidden-import pynput.keyboard._darwin \
		--hidden-import pynput.mouse._darwin \
		run.py

build-win:
	pyinstaller \
		--name Jitter \
		--onefile \
		--windowed \
		--hidden-import pynput.keyboard._win32 \
		--hidden-import pynput.mouse._win32 \
		run.py

clean:
	rm -rf build dist *.spec
