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
	[ -d "tests/.venv" ] || python3 -m venv tests/.venv
	tests/.venv/bin/python -m pip install --upgrade pip > /dev/null
	tests/.venv/bin/pip install -r tests/requirements.txt > /dev/null
	tests/.venv/bin/pytest tests/ -v
	PYTEST_EXIT_CODE=$$?
	rm -rf tests/.venv
	exit $$PYTEST_EXIT_CODE

all: build-all
clean: clean-packages
test: test-packages
