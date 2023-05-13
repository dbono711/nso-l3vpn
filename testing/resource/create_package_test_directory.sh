if [ "$1" == "" ] || [ $# -gt 1 ]; then echo "Please provide a single parameter for directory name...Done"; exit 1; fi

if [ -d "l3vpn/tests/$1" ];
then
    echo "Directory '$1' already exists...Skipping";
else
    cat << EOF >> "l3vpn/tests/crud_testing.robot"

$1
    [Setup]    Setup Test for Use Case $1
    Test CREATE Dry-Run
    Test CREATE
    Test READ
    Test UPDATE Dry-Run
    Test UPDATE
    Test DELETE Dry-Run
    Test DELETE
EOF
    mkdir "l3vpn/tests/$1";
    touch "l3vpn/tests/$1/create.xml";
    touch "l3vpn/tests/$1/create_expected.xml";
    touch "l3vpn/tests/$1/update.xml";
    touch "l3vpn/tests/$1/update_expected.xml";
    touch "l3vpn/tests/$1/read_expected.xml";
    touch "l3vpn/tests/$1/delete_expected.xml";
    touch "l3vpn/tests/$1/README.md";
fi

