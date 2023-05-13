# NSO Package Testing Framework
The testing framework is composed of two parts:

* Makefile integration
* CRUD Keywords in [Robot Framework](https://robotframework.org/)

## Makefile Integration
Per the Makefile, testing is initiated with ```make test```

The Makefile targets for testing perform a set of steps to create a Python3 virtual environment and install the Python packages required for testing (contained in [testing/test-requirements.txt](testing/test-requirements.txt)).

The ```robot``` application is then called with a few standard options and a list of packages to be tested where it will use the ```crud_testing.robot``` file to execute any tests contained within.

## CRUD Keywords
Defined in [testing/library/utils.py](testing/library/utils.py) and [testing/resource/common.robot](testing/resource/common.robot), the keywords and utility functions define the processes to make RESTCONF API calls to NSO and compare the responses to the expected output.

The keywords also look for the following NSO server details in environment variables and use them to establish a session:

* NSO_URL=https://\<host>
* NSO_USERNAME=\<username>
* NSO_PASSWORD=\<password>

The keywords define and use variables that are only valid within the current testing scope. These variables are re-initialized at the beginning of each test based on the contents of the ```create.xml``` file. Some of the variables are available for use in rendering the templates for the expected responses from NSO.

***

## Included test cases
The following test cases have been included in the package

* uc-01:
  * Three devices, IPv4/IPv6, Static/BGP CE-Routing

## Adding a test case
From the root of this repository, execute the following to scaffold a new test case under the ```l3vpn/tests``` directory:

```bash testing/resources/create_package_test_directory.sh <test-case-name>```

The script performs the following:

* Checks to see if the <test-case-name> folder already exists and creates it if it doesn't
* Creates the XML files that will be populated in the section below
* Adds the test case to the ```l3vpn/tests/crud_testing.robot``` file

## Generating test case content
* Step 1
  * Use the NSO CLI to create a new service instance with the parameters intended for the service use case

* Step 2
  * Use the NSO CLI to display the XML payload for the service configuration entered in Step 1
    * ```show | compare | display xml```
  * Copy the output into the ```create.xml``` file, omitting the ```<services>``` XML element

* Step 3
  * Use the NSO CLI to execute a "dry-run" creation of the service instance
    * ```commit dry-run outformat xml```
      * Copy the output into the ```create_expected.xml``` file

* Step 4
  * Execute the same command as in Step 3 **WITHOUT** the ```dry-run outformat xml```
    * ```commit```

* Step 5
  * Use the NSO CLI to retrieve the service configuration payload from NSO.
    * For example; ```show configuration services l3vpn Disneyland service01 | display xml```
      * Copy the output into the ```read_expected.xml``` file omitting the ```<services></services>``` and ```<config></config>``` XML tags

* Step 6
  * Copy the contents of the ```create.xml``` file and paste into the ```update.xml``` file
  * Make a few changes (except for the instance keys). Be sure to use the ```operation``` attribute as required to have NSO properly delete, merge, or replace the elements in the service instance depending on what updates you want to make. If using strictly NSO CLI, make the changes to the service instance within the NSO CLI.

* Step 7
  * Use the NSO CLI to update the service instance.
    * ```commit dry-run outformat xml```
      * Copy the output into the ```update_expected.xml``` file

* Step 8
  * Perform the same as in Step 7 **WITHOUT** the dry-run
    * ```commit```

* Step 9
  * Use the NSO CLI to execute a "dry-run" deletion of the service instance
    * ```delete services l3vpn Disneyland service01```
    * ```commit dry-run outformat xml```
      * Copy the output into the ```delete_expected.xml``` file

* README.md
  * Add any relevant details about the test case.

***

## Testing
To initiate testing of all use cases, execute the following after replacing the placeholder (```< >```) text:

    NSO_URL=https://<host>/ NSO_USERNAME=<username> NSO_PASSWORD=<password>  make test
