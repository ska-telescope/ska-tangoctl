#!/usr/bin/bash

run_test()
{
	sleep 2
	LOGF="../log/check_tangoktl.$(date +%Y%m%dT%H%M%S).log"
	echo "${TCMD} >${LOGF} 2>&1" >> ${TEST_LOGF}
	.${TCMD} >${LOGF} 2>&1
	if [ $? -eq 0 ]
	then
		echo "[  OK  ] ${TNAME}"
	else
		echo "[FAILED] ${TNAME}"
		if [ ! -z "${VERBOSE}" ]
		then
			echo "$ ${TCMD}"
			cat ${LOGF}
		fi
	fi
}

lint_json()
{
	sleep 2
	LOGF="check_tangoktl.$(date +%Y%m%dT%H%M%S).log"
	TNAME="Lint JSON file ${FILE_NAME}"
	jsonlint-php -q ../log/${FILE_NAME} >${LOGF} 2>&1
	if [ $? -eq 0 ]
	then
		echo "[  OK  ] ${TNAME}"
	else
		echo "[FAILED] ${TNAME}"
		if [ ! -z "${VERBOSE}" ]
		then
			echo "$ ${TCMD}"
			cat ${LOGF}
		fi
	fi
}

lint_yaml()
{
	sleep 2
	LOGF="check_tangoktl.$(date +%Y%m%dT%H%M%S).log"
	TNAME="Lint YAML file ${FILE_NAME}"
	yamllint ../log/${FILE_NAME} >${LOGF} 2>&1
	if [ $? -eq 0 ]
	then
		echo "[  OK  ] ${TNAME}"
	else
		echo "[FAILED] ${TNAME}"
		if [ ! -z "${VERBOSE}" ]
		then
			echo "$ ${TCMD}"
			cat ${LOGF}
		fi
	fi
}

mkdir -p log
rm -f log/check_tangoktl.log
rm -f log/check_tangoktl.*.log
rm -f log/check_tangoktl.*.yaml
rm -f log/check_tangoktl.*.json

DIRNAME=$(dirname $0)
NAMESPACE="test-equipment"
DEVICE="mid-itf/progattenuator/1"
TEST_LOGF="../log/check_tangoktl.log"
cd $DIRNAME

TNAME="List contexts"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -xq"
run_test

TNAME="List contexts in JSON format"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -xqj"
run_test

TNAME="List namespaces"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -nq"
run_test


TNAME="List services"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -z"
run_test

TNAME="List pods"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -b"
run_test


TNAME="List classes"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -k"
run_test


TNAME="List device names as tree"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} --tree -q"
run_test


TNAME="List device names"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -dq"
run_test


TNAME="List devices"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -lq"
run_test

FILE_NAME="check_tangoktl.${NAMESPACE}-attributes.json"
TNAME="List device attributes in JSON format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -ajq -O ../log/${FILE_NAME}"
run_test
lint_json

FILE_NAME="check_tangoktl.${NAMESPACE}-commands.json"
TNAME="List device commands in JSON format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -cjq -O ../log/${FILE_NAME}"
run_test
lint_json

FILE_NAME="check_tangoktl.${NAMESPACE}-properties.json"
TNAME="List device properties in JSON format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -pjq -O ../log/${FILE_NAME}"
run_test
lint_json

FILE_NAME="check_tangoktl.${NAMESPACE}-properties.yaml"
TNAME="List device properties in YAML format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -pyq -O ../log/${FILE_NAME}"
run_test
lint_yaml

FILE_NAME="check_tangoktl.${NAMESPACE}.json"
TNAME="List device attributes, commands and properties in JSON format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -acpjq -O ../log/${FILE_NAME}"
run_test
lint_json

FILE_NAME="check_tangoktl.${NAMESPACE}.yaml"
TNAME="List device attributes, commands and properties in YAML format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -acpyq -O ../log/${FILE_NAME}"
run_test
lint_yaml

FILE_NAME="check_tangoktl.${NAMESPACE}-status.json"
TNAME="List device attributes named 'status' to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A status -jq -O ../log/${FILE_NAME}"
run_test
lint_json

FILE_NAME="check_tangoktl.${NAMESPACE}-buildState.json"
TNAME="List device attributes named 'buildState' in JSON format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jq -O ../log/${FILE_NAME}"
run_test
lint_json

FILE_NAME="check_tangoktl.${NAMESPACE}-buildState.yaml"
TNAME="List device attributes named 'buildState' in YAML format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jq -O ../log/${FILE_NAME}"
run_test
lint_yaml

FILE_NAME="check_tangoktl.${NAMESPACE}-buildState2.json"
TNAME="List device attributes named 'buildState' in short JSON format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jqs -O ../log/${FILE_NAME}"
run_test
lint_json

FILE_NAME="check_tangoktl.${NAMESPACE}-buildState2.yaml"
TNAME="List device attributes named 'buildState' in short YAML format to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -yqs -O ../log/${FILE_NAME}"
run_test
lint_yaml

TNAME="Ping device ${DEVICE}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -D ${DEVICE} --ping -q"
run_test

FILE_NAME=check_tangoktl.$(echo ${DEVICE} | tr "/" "-").json
TNAME="List attributes, commands and properties in JSON format for device ${DEVICE} to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -D ${DEVICE} -acpjq -O ../log/${FILE_NAME}"
run_test
lint_json

FILE_NAME=check_tangoktl.$(echo ${DEVICE} | tr "/" "-").yaml
TNAME="List attributes, commands and properties in YAML format for device ${DEVICE} to ${FILE_NAME}"
TCMD="./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -D ${DEVICE} -acpyq -O ../log/${FILE_NAME}"
run_test
lint_yaml

cd - >/dev/null
