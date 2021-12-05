# The order of packages is significant as there are dependencies between
# the packages. Typically generated namespaces are used by other packages.
PACKAGES = \
	utils \
	inventory \
	l3vpn

ALL_PACKAGES=$(PACKAGES)

.ONESHELL:

.SILENT:

all: build-all

build-all:
	@for i in $(ALL_PACKAGES); do \
        echo '------- COMPILING PACKAGE: '$${i}; \
        $(MAKE) -s -C $${i}/src all || exit 1; \
    done

MKDIR_P = mkdir -p

clean-packages:
	@for i in $(PACKAGES); do \
    echo '------- CLEAN PACKAGE: '$${i}; \
    $(MAKE) -s -C $${i}/src clean || exit 1; \
    done

clean: clean-packages

normalize-test-xml:
	[ -d "test_venv" ] || python3 -m venv test_venv
	test_venv/bin/pip install -r tests/test-reqs.txt > /dev/null
	test_venv/bin/pip freeze | grep -v -f tests/test-reqs.txt - | xargs test_venv/bin/pip uninstall -y
	test_venv/bin/python3 tests/library/utils.py normalize_tests

test-packages:
	[ -d "test_venv" ] || python3 -m venv test_venv
	test_venv/bin/pip install -r tests/test-reqs.txt > /dev/null
	test_venv/bin/pip freeze | grep -v -f tests/test-reqs.txt - | xargs test_venv/bin/pip uninstall -y
	test_venv/bin/robot -d tests/logs/ -N "Service Packages" --suitestatlevel 2 $(PACKAGES)
	ROBOT_EXIT_CODE=$$?
	#rm -rf test_venv
	exit $$ROBOT_EXIT_CODE

test: test-packages

package-targets = $(addprefix test-, $(PACKAGES))

$(package-targets):	test-%: %
	[ -d "test_venv" ] || python3 -m venv test_venv
	test_venv/bin/pip install -r tests/test-reqs.txt > /dev/null
	test_venv/bin/pip freeze | grep -v -f tests/test-reqs.txt - | xargs test_venv/bin/pip uninstall -y
	test_venv/bin/robot -d tests/logs/$</ $<
	ROBOT_EXIT_CODE=$$?
	#rm -rf test_venv
	exit $$ROBOT_EXIT_CODE
