*** Settings ***
Library    BuiltIn
Library    OperatingSystem
Library    String
Library    RequestsLibrary
Library    Collections
Library    ../library/utils.py

*** Variables ***
${NSO_URL}    %{NSO_URL}
@{NSO_AUTH}    %{NSO_USERNAME}    %{NSO_PASSWORD}

${NSO_BASE_PATH}    restconf/data/tailf-ncs:services/
&{HEADERS}    Accept=application/yang-data+xml    Content-Type=application/yang-data+xml

*** Keywords ***
Setup NSO Session
	Create Session    NSO    ${NSO_URL}    auth=@{NSO_AUTH}    verify=False    disable_warnings=True

Delete All Instances of ${PACKAGE}
	DELETE On Session    NSO    url=${NSO_BASE_PATH}?fields=${PACKAGE}:${PACKAGE}

Setup Test for Use Case ${USE_CASE}
	${CREATE_RENDERED}=    Render Template           ${TEST_SUITE_BASE_PATH}/${USE_CASE}/create.xml
	${CREATE_SVC_INST}=    Service Instance          ${CREATE_RENDERED}
	${CREATE_PAYLOAD}=     Encode String To Bytes    ${CREATE_RENDERED}    UTF-8
	${CREATE_EXPECTED}=    Render Template           ${TEST_SUITE_BASE_PATH}/${USE_CASE}/create_expected.xml      create=${CREATE_SVC_INST}
	${READ_EXPECTED}=      Render Template           ${TEST_SUITE_BASE_PATH}/${USE_CASE}/read_expected.xml      create=${CREATE_SVC_INST}
	${UPDATE_RENDERED}=    Render Template           ${TEST_SUITE_BASE_PATH}/${USE_CASE}/update.xml
	${UPDATE_SVC_INST}=    Service Instance          ${UPDATE_RENDERED}
	${UPDATE_PAYLOAD}=     Encode String To Bytes    ${UPDATE_RENDERED}    UTF-8
	${UPDATE_EXPECTED}=    Render Template           ${TEST_SUITE_BASE_PATH}/${USE_CASE}/update_expected.xml      create=${CREATE_SVC_INST}    update=${UPDATE_SVC_INST}
	${DELETE_EXPECTED}=    Render Template           ${TEST_SUITE_BASE_PATH}/${USE_CASE}/delete_expected.xml      create=${CREATE_SVC_INST}    update=${UPDATE_SVC_INST}
	${KEYSTRING}=          Service Instance Keystring     ${CREATE_SVC_INST}    ${SVC_INST_KEYS}

	Set Test Variable    ${CREATE_SVC_INST}
	Set Test Variable    ${CREATE_PAYLOAD}
	Set Test Variable    ${CREATE_EXPECTED}
	Set Test Variable    ${READ_EXPECTED}
	Set Test Variable    ${UPDATE_PAYLOAD}
	Set Test Variable    ${UPDATE_EXPECTED}
	Set Test Variable    ${DELETE_EXPECTED}
	Set Test Variable    ${KEYSTRING}
	Set Test Variable    ${USE_CASE}

Test CREATE Dry-Run
	Log    ${CREATE_PAYLOAD}
	${CRUD_TEST}=   Set Variable    Test CREATE Dry-Run
	${RESP}=    POST On Session    NSO    url=${NSO_BASE_PATH}?dry-run=xml   data=${CREATE_PAYLOAD}    headers=${HEADERS}
	Create File     ${OUTPUT DIR}/${CREATE_SVC_INST.package}/${USE_CASE}/create_received.xml    ${RESP.text}
	Should Be Equal As Integers    ${RESP.status_code}    201   ${RESP.text}
	Validate Response    ${RESP.text}    ${CREATE_EXPECTED}

Test CREATE
	${RESP}=    POST On Session    NSO    url=${NSO_BASE_PATH}   data=${CREATE_PAYLOAD}    headers=${HEADERS}
	Should Be Equal As Integers    ${RESP.status_code}    201   ${RESP.text}

Test READ
	${CRUD_TEST}=   Set Variable   Test READ
	${RESP}=    GET On Session    NSO    url=${NSO_BASE_PATH}${CREATE_SVC_INST.package}:${CREATE_SVC_INST.package}=${KEYSTRING}
	Create File     ${OUTPUT DIR}/${CREATE_SVC_INST.package}/${USE_CASE}/read_received.xml    ${RESP.text}
	Should Be Equal As Integers    ${RESP.status_code}    200   ${RESP.text}
	Validate Response    ${RESP.text}    ${READ_EXPECTED}

Test UPDATE Dry-Run
	Log    ${UPDATE_PAYLOAD}
	${CRUD_TEST}=   Set Variable   Test UPDATE Dry-Run
	${RESP}=    PATCH On Session    NSO   url=${NSO_BASE_PATH}${CREATE_SVC_INST.package}:${CREATE_SVC_INST.package}=${KEYSTRING}?dry-run=xml   data=${UPDATE_PAYLOAD}    headers=${HEADERS}
	Create File     ${OUTPUT DIR}/${CREATE_SVC_INST.package}/${USE_CASE}/update_received.xml    ${RESP.text}
	Should Be Equal As Integers    ${RESP.status_code}    200   ${RESP.text}
	Validate Response    ${RESP.text}    ${UPDATE_EXPECTED}

Test UPDATE
	${RESP}=    PATCH On Session    NSO   url=${NSO_BASE_PATH}${CREATE_SVC_INST.package}:${CREATE_SVC_INST.package}=${KEYSTRING}   data=${UPDATE_PAYLOAD}    headers=${HEADERS}
	Should Be Equal As Integers    ${RESP.status_code}    204   ${RESP.text}

Test DELETE Dry-Run
	${CRUD_TEST}=   Set Variable   Test DELETE Dry-Run
	${RESP}=    DELETE On Session    NSO    url=${NSO_BASE_PATH}${CREATE_SVC_INST.package}:${CREATE_SVC_INST.package}=${KEYSTRING}?dry-run=xml
	Create File     ${OUTPUT DIR}/${CREATE_SVC_INST.package}/${USE_CASE}/delete_received.xml    ${RESP.text}
	Should Be Equal As Integers    ${RESP.status_code}    200   ${RESP.text}
	Validate Response    ${RESP.text}    ${DELETE_EXPECTED}

Test DELETE
	${RESP}=    DELETE On Session    NSO    url=${NSO_BASE_PATH}${CREATE_SVC_INST.package}:${CREATE_SVC_INST.package}=${KEYSTRING}
	Should Be Equal As Integers    ${RESP.status_code}    204   ${RESP.text}
