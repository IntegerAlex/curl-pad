# Simple build/install helpers for curlpad

.PHONY: build install clean release

build:
	./scripts/build_curlpad.sh

install:
	./scripts/install_curlpad.sh

release:
	./scripts/release.sh

clean:
	rm -rf build dist __pycache__

