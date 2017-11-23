NAME=tendrl-monitoring-integration
VERSION := $(shell PYTHONPATH=. python -c \
             'import version; print version.__version__' \
             | sed 's/\.dev[0-9]*//')
RELEASE=5
COMMIT := $(shell git rev-parse HEAD)
SHORTCOMMIT := $(shell echo $(COMMIT) | cut -c1-7)

all: srpm

clean:
	rm -rf dist/
	rm -rf $(NAME)-$(VERSION).tar.gz
	rm -rf $(NAME)-$(VERSION)-$(RELEASE).el7.src.rpm

dist:
	wget https://grafana.com/api/plugins/vonage-status-panel/versions/1.0.5/download \
	  --output-document=vonage-status-panel-1.0.5-0-g4ecb061.zip
	python setup.py sdist \
	  && mv dist/$(NAME)-$(VERSION).tar.gz .

srpm: dist
	fedpkg --dist epel7 srpm

rpm: dist
	mock -r epel-7-x86_64 rebuild $(NAME)-$(VERSION)-$(RELEASE).el7.src.rpm --resultdir=. --define "dist .el7"

gitversion:
	# Set version and release to the latest values from Git
	sed -i $(NAME).spec \
	  -e "/^Release:/cRelease: $(shell date +"%Y%m%dT%H%M%S").$(SHORTCOMMIT)"

snapshot: gitversion srpm


.PHONY: dist rpm srpm gitversion snapshot
