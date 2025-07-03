#!/usr/bin/bash
DIRNAME=$(dirname $0)
NAMESPACE="test-equipment"
DEVICE="mid-itf/progattenuator/1"
TANGO_HOST=10.164.11.25:10000
cd $DIRNAME
../src/ska_tangoctl/tango_control/tangoctl.py -h


echo "_________________________________________"
echo "List classes"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -k"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -k

echo "_________________________________________"
echo "List device names as tree"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} --tree -q"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} --tree -q

echo "_________________________________________"
echo "List device names"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -dq"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -dq

echo "_________________________________________"
echo "List devices"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -lq"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -lq

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-attributes.json"
echo "List device attributes in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -ajq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -ajq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-commands.json"
echo "List device commands in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -cjq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -cjq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-properties.json"
echo "List device properties in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -pjq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -pjq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-properties.yaml"
echo "List device properties in YAML format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -pyq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -pyq -O ../${FILE_NAME}
yamllint ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}.json"
echo "List device attributes, commands and properties in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -acpjq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -acpjq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}.yaml"
echo "List device attributes, commands and properties in YAML format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -acpyq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -acpyq -O ../${FILE_NAME}
yamllint ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-status.json"
echo "List device attributes named 'status' to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A status -jq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A status -jq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="../${NAMESPACE}-buildState.json"
echo "List device attributes named 'buildState' in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A buildState -jq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A buildState -jq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="../${NAMESPACE}-buildState.yaml"
echo "List device attributes named 'buildState' in YAML format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A buildState -jq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A buildState -jq -O ../${FILE_NAME}
yamllint ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-buildState2.json"
echo "List device attributes named 'buildState' in short JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A buildState -jqs -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A buildState -jqs -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-buildState2.yaml"
echo "List device attributes named 'buildState' in short YAML format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A buildState -yqs -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -A buildState -yqs -O ../${FILE_NAME}
yamllint ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
echo "Ping device ${DEVICE}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -D ${DEVICE} --ping -q

echo "_________________________________________"
FILE_NAME=$(echo ${DEVICE} | tr "/" "-").json
echo "List attributes, commands and properties in JSON format for device ${DEVICE} to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -D ${DEVICE} -acpjq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -D ${DEVICE} -acpjq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME=$(echo ${DEVICE} | tr "/" "-").yaml
echo "List attributes, commands and properties in YAML format for device ${DEVICE} to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -D ${DEVICE} -acpyq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_control/tangoctl.py -H ${TANGO_HOST} -D ${DEVICE} -acpyq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

cd -
