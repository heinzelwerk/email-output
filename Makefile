PYTHON := python3

APPLICATION_NAME := $(shell $(PYTHON) setup.py --name)
APPLICATION_VERSION := $(shell $(PYTHON) setup.py --version)

RPM_RELEASE := 1

.PHONY:	default help test srpm clean distclean

default:	help

help:
	@echo "There is no help."

test:
	tox

srpm:	build/rpm/SPECS/$(APPLICATION_NAME).spec build/rpm/SOURCES/$(APPLICATION_NAME)-$(APPLICATION_VERSION).tar.gz
	rpmbuild --define "_topdir $(PWD)/build/rpm" -bs $<
	cp "$(PWD)/build/rpm/SRPMS/$(APPLICATION_NAME)-$(APPLICATION_VERSION)-$(RPM_RELEASE).src.rpm" dist

build/rpm/SPECS/%.spec:
	mkdir -p build/rpm/SPECS
	echo "Name: $(APPLICATION_NAME)" > $@
	echo "Version: $(APPLICATION_VERSION)" >> $@
	echo "Release: $(RPM_RELEASE)" >> $@
	cat rpm/$*.spec.in >> $@
	LC_TIME=en_US.utf8 git log --format=format:"* %ad %an <%ae>%n- %s" --date=format:"%a %b %d %Y" >> $@

build/rpm/SOURCES/$(APPLICATION_NAME)-$(APPLICATION_VERSION).tar.gz:	dist/$(APPLICATION_NAME)-$(APPLICATION_VERSION).tar.gz
	mkdir -p build/rpm/SOURCES
	cp $< $@

dist/$(APPLICATION_NAME)-$(APPLICATION_VERSION).tar.gz:
	$(PYTHON) setup.py sdist --formats=gztar

clean:
	rm -rf build
	rm -rf $(subst -,_,$(APPLICATION_NAME)).egg-info

distclean:	clean
	rm -rf dist
