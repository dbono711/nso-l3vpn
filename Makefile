.ONESHELL:

.SILENT:

build-all:
	@for i in l3vpn; do \
        echo '------- COMPILING PACKAGE: '$${i}; \
        $(MAKE) -s -C $${i}/src all || exit 1; \
    done

clean-packages:
	@for i in l3vpn; do \
    echo '------- CLEAN PACKAGE: '$${i}; \
    $(MAKE) -s -C $${i}/src clean || exit 1; \
    done

test-packages:
	[ -d "testing/.venv" ] || python3 -m venv testing/.venv
	testing/.venv/bin/python -m pip install --upgrade pip
	testing/.venv/bin/pip install -r testing/test-requirements.txt > /dev/null
	testing/.venv/bin/pip freeze | grep -v -f testing/test-requirements.txt - | xargs testing/.venv/bin/pip uninstall -y
	testing/.venv/bin/robot -d testing/logs/ -N "NSO L3VPN" --suitestatlevel 2 l3vpn/tests/crud_testing.robot
	ROBOT_EXIT_CODE=$$?
	rm -rf testing/.venv
	exit $$ROBOT_EXIT_CODE

all: build-all
clean: clean-packages
test: test-packages