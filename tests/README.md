# NSO Package Testing Framework
The testing framework is composed of two parts:

* Makefile integration
* CRUD Keywords in [Robot Framework](https://robotframework.org/)

## Makefile Integration
With Makefile integration, testing is initiated with ```make test``` - for test execution of all packages - or ```make test-<package>``` - for test execution of a single package.

The Makefile targets for testing perform a set of steps to create a Python3 virtual environment and install the Python packages required for testing (contained in [tests/test-reqs.txt](tests/test-reqs.txt)).

The ```robot``` utility is then called with a few standard options and a list of packages to be tested. Each service package can have one or more 'robot' files to define a unique testing process for that package. The robot utility will recursively search the specified service package directories for any ```*.robot``` files and execute any tests contained within. However, as noted in the upcoming sections, this README enforces a naming of ```create_and_delete.robot``` for ease of standardization.

## CRUD Keywords
Defined in [tests/library/utils.py](tests/library/utils.py) and [tests/resource/common.robot](tests/resource/common.robot), the keywords and utility functions define the processes to make RESTCONF API calls to NSO and compare the responses to the expected output.

The keywords also look for the following NSO server details in environment variables and use them to establish a session:

* NSO_URL=https://\<host>
* NSO_USERNAME=\<username>
* NSO_PASSWORD=\<password>

When referenced in a robot test, the keywords define and use variables that are only valid within the ```test``` scope. These variables are re-initialized at the beginning of each test based on the contents of the ```create.xml``` file. Some of the variables are available for use in rendering the templates for the expected responses from NSO.

***

## Adding tests to an NSO Service Package

In the respective service package directory, create a directory to contain the test cases. For example; within the ```l3vpn``` service package, create a ```tests``` directory as ```l3vpn/tests```

### Create a Robot file from the template

1. Copy the file ```tests/create_and_delete.robot.template``` and paste into the folder created above (i.e.; ```l3vpn/tests```) as ```create_and_delete.robot```

1. Update references to the package name. For example; again using the ```l3vpn``` service package as an example, under ```Suite Teardown``` you would change the statement to ```Delete All Instances of l3vpn Service```

1. Update ```@{SVC_INST_KEYS}``` to reference list keys in YANG for instantiating the particular service model (i.e.; customer-name, service-id, vpn-id)

1. Update ```${TEST_SUITE_BASE_PATH}``` if directory containing test cases is not 'tests'; relative to robot file, as per the folder created above (i.e.; ```l3vpn/tests```)

1. Create tests using the template for CRUD testing, adding a unique name for the test case to the ```[Setup]``` line. For example;
```
Test Port-based and Vlan-based UC-01
    [Setup]     Setup Test for Use Case uc-01
    Test CREATE Dry-Run
    Test CREATE
    Test READ
    Test UPDATE Dry-Run
    Test UPDATE
    Test DELETE Dry-Run
    Test DELETE
```

### Create a directory for each test case

For example; ```l3vpn/tests/uc-01```

**NOTE: We are matching the name of the test directory in question per the ```[Setup]``` template added in the ```create_and_delete.robot``` file. For example, if the folder we are creating is ```uc-01```, then the ```[Setup]     Setup Test for Use Case uc-01``` must be indicated as such in order for Robot to determine which folder to use for the test**

###  Create the following files within each test case directory:

* create.xml
* create_expected.xml
* update.xml
* update_expected.xml
* read_expected.xml
* delete_expected.xml
* README.md

### Generate the content of each file using the following steps:

* Step 1
  * Use the NSO CLI to create a new service instance; specifically, with the parameters/constraints intended for the service use case

  ```
  set services l3vpn Disneyland "L3VPN Test 01" 1 cir 123 mtu 2000 inet IPv4
  set services l3vpn Disneyland "L3VPN Test 01" 1 device xr-0 redistribution-protocol [ static connected ] interface TenGigabitEthernet-iosxr 2/0 port-mode true ipv4-local-prefix 10.10.10.1/29
  set services l3vpn Disneyland "L3VPN Test 01" 1 device xr-0 static ipv4-static-destination-prefix 172.16.1.0/24 ipv4-static-forwarding [ 10.10.10.2 10.10.10.3 ]
  set services l3vpn Disneyland "L3VPN Test 01" 1 device xr-1 redistribution-protocol [ static connected ] interface TenGigabitEthernet-iosxr 2/0 port-mode true ipv4-local-prefix 10.10.10.9/29
  set services l3vpn Disneyland "L3VPN Test 01" 1 device xr-1 static ipv4-static-destination-prefix 172.16.1.0/24 ipv4-static-forwarding [ 10.10.10.10 10.10.10.11 ]
  set services l3vpn Disneyland "L3VPN Test 01" 1 device xr-2 redistribution-protocol [ static connected ] interface GigabitEthernet-iosxr 2/0 port-mode true ipv4-local-prefix 10.10.10.17/29
  set services l3vpn Disneyland "L3VPN Test 01" 1 device xr-2 static ipv4-static-destination-prefix 172.16.1.0/24 ipv4-static-forwarding [ 10.10.10.18 10.10.10.19 ]
  ```

* Step 2
  * Use the NSO CLI to display the XML payload for the service configuration entered in Step 1
    * ```show | compare | display xml```
  * Copy the output into the ```create.xml``` file, omitting the ```<services>``` XML element

**NOTE: If you are _NOT_ using NSO CLI to derive the XML templates for the rest of the steps, you can revert the changes in NSO at this time with ```revert no-confirm```**


* Step 3
  * Execute a "dry-run" creation of the service instance, using either the NSO CLI or by performing an HTTP(s) POST via a method of your choice to the NSO RESTCONF API. This will render the expected dry-run output, in XML
    * Example Using CURL: ```curl -k -X POST -H "Content-Type: application/yang-data+xml" -H "Accept: application/yang-data+xml" -u <username>:<password> -d @create.xml "https://<host>/restconf/data/tailf-ncs:services?dry-run=xml" | xmllint --format -```
      * ```<username>:<password>``` is a username/password able to authenticate with NSO and authorized to perform CRUD operations on the service package
      * ```<host>``` is the NSO host targeted for the CRUD operations
      * Copy the output into the ```create_expected.xml``` file
    * Example using NSO CLI: ```commit dry-run outformat xml```
      * Copy **ONLY** the XML elements from this output to the ```create_expected.xml``` file in-between the ```<data></data>``` tags of the below snippet:
      ```xml
      <dry-run-result xmlns='http://tail-f.com/ns/rest/dry-run'>
        <result-xml>
          <local-node>
            <data>
            </data>
          </local-node>
        </result-xml>
      </dry-run-result>
      ```


* Step 4
  * Perform the same as in Step 3 **WITHOUT** the dry-run
  * Example Using CURL: ```curl -k -X POST -H "Content-Type: application/yang-data+xml" -H "Accept: application/yang-data+xml" -u <username>:<password> -d @create.xml "https://<host>/restconf/data/tailf-ncs:services"```
    * ```<username>:<password>``` is a username/password able to authenticate with NSO and authorized to perform CRUD operations on the service package
    * ```<host>``` is the NSO host targeted for the CRUD operations
    * This should return a HTTP status code ```201 created``` with a blank response body
  * Example using NSO CLI: ```commit```


* Step 5
  * Using either the NSO CLI or by performing an HTTP(s) GET via a method of your choice, we will be retrieving the service configuration payload from NSO. If using HTTP(s) GET, the URL should include the service package URI appended with the service instance keystring
  * Example Using CURL: ```curl -k -X GET -H "Accept: application/yang-data+xml" -u <username>:<password> "https://<host>/restconf/data/tailf-ncs:services/l3vpn:l3vpn=Disneyland,L3VPN%20Test%2001,1" | xmllint --format -```
    * ```<username>:<password>``` is a username/password able to authenticate with NSO and authorized to perform CRUD operations on the service package
    * ```<host>``` is the NSO host targeted for the CRUD operations
    * This should return an HTTP status code ```200 OK``` with the service instance and a list of modified devices in the response body
    * Copy the output into the ```read_expected.xml``` file
  * Example using NSO CLI: ```show configuration services l3vpn Disneyland L3VPN\ Test\ 01 1 | display xml```
    * Copy the output into the ```read_expected.xml``` file omitting the ```<services></services>``` and ```<config></config>``` XML tags


* Step 6
  * Copy the contents of the ```create.xml``` file and paste into the ```update.xml``` file
  * Make a few changes (except for the instance keys). Be sure to use the ```operation``` attribute as required to have NSO properly delete, merge, or replace the elements in the service instance depending on what updates you want to make. If using strictly NSO CLI, make the changes to the service instance within the NSO CLI.


* Step 7
  * Using either the NSO CLI or by performing an HTTP(s) PUT via a method of your choice, update the service instance. If using HTTP(s) PUT, the ```update.xml``` will be used as payload to the NSO service instance URI appended with ```?dry-run=xml``` to render the dry-run XML output
  * Example Using CURL: ```curl -k -X PUT -H "Content-Type: application/yang-data+xml" -H "Accept: application/yang-data+xml" -u <username>:<password> -d @update.xml "https://<host>/restconf/data/tailf-ncs:services/l3vpn:l3vpn=Disneyland,L3VPN%20Test%2001,1?dry-run=xml" | xmllint --format -```
    * ```<username>:<password>``` is a username/password able to authenticate with NSO and authorized to perform CRUD operations on the service package
    * ```<host>``` is the NSO host targeted for the CRUD operations
    * This should return a HTTP status code ```200 OK``` with the dry-run XML as the body of the response
    * Copy the output into the ```update_expected.xml``` file
  * Example using NSO CLI: ```commit dry-run outformat xml```
    * Copy **ONLY** the XML elements from this output to the ```update_expected.xml``` file in-between the ```<data></data>``` tags of the below snippet:
    ```xml
    <dry-run-result xmlns='http://tail-f.com/ns/rest/dry-run'>
      <result-xml>
        <local-node>
          <data>
          </data>
        </local-node>
      </result-xml>
    </dry-run-result>
    ```


* Step 8
  * Perform the same as in Step 7 **WITHOUT** the dry-run
  * Example Using CURL: ```curl -k -X PUT -H "Content-Type: application/yang-data+xml" -H "Accept: application/yang-data+xml" -u <username>:<password> -d @update.xml "https://<host>/restconf/data/tailf-ncs:services/l3vpn:l3vpn=Disneyland,L3VPN%20Test%2001,1"```
    * ```<username>:<password>``` is a username/password able to authenticate with NSO and authorized to perform CRUD operations on the service package
    * ```<host>``` is the NSO host targeted for the CRUD operations
    * This should return a HTTP status code ```201 created``` with a blank response body
  * Example using NSO CLI: ```commit```


* Step 9
  * Execute a "dry-run" deletion of the service instance, using either the NSO CLI or by performing an HTTP(s) DELETE via a method of your choice. This will render the expected dry-run output, in XML
  * Example Using CURL: ```curl -k -X DELETE -H "Accept: application/yang-data+xml" -u <username>:<password> "https://<host>/restconf/data/tailf-ncs:services/l3vpn:l3vpn=Disneyland,L3VPN%20Test%2001,1?dry-run=xml" | xmllint --format -```
    * This should return a HTTP status code ```204 No Content``` with the dry-run XML as the body of the response
    * Copy the output into the ```delete_expected.xml``` file.
  * Example using NSO CLI:
    * ```delete services l3vpn Disneyland L3VPN\ Test\ 01 1```
    * ```commit dry-run outformat xml```
    * Copy **ONLY** the XML elements from this output to the ```delete_expected.xml``` file in-between the ```<data></data>``` tags of the below snippet:
    ```xml
    <dry-run-result xmlns='http://tail-f.com/ns/rest/dry-run'>
      <result-xml>
        <local-node>
          <data>
          </data>
        </local-node>
      </result-xml>
    </dry-run-result>
    ```


* README.md
  * Add any relevant details about the test case.

***

## Testing

To initiate testing from the repository root, execute the following command in a Bash shell after replacing the placeholder text:

    NSO_URL=https://<host>/ NSO_USERNAME=<username> NSO_PASSWORD=<password>  make -C packages test

Or to run tests for a specific service package:

    NSO_URL=https://<host>/ NSO_USERNAME=<username> NSO_PASSWORD=<password> make test-l3vpn
