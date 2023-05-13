*** Settings ***
Library    BuiltIn
Library    OperatingSystem
Library    String
Library    RequestsLibrary
Library    Collections
Resource    ../../testing/resource/common.robot

Suite Setup    Setup Suite
Suite Teardown    Delete All Instances of l3vpn

*** Variables ***
${TEST_SUITE_BASE_PATH}    ${CURDIR}
@{SVC_INST_KEYS}    customer-name    service-id

*** Keywords ***
Setup Suite
	Setup NSO Session
	Delete All Instances of l3vpn

*** Test Cases ***
uc-01
    [Setup]    Setup Test for Use Case uc-01
    Test CREATE Dry-Run
    Test CREATE
    Test READ
    Test UPDATE Dry-Run
    Test UPDATE
    Test DELETE Dry-Run
    Test DELETE
