#!/usr/bin/bash
DIRNAME=$(dirname $0)
NAMESPACE="test-equipment"
DEVICE="mid-itf/progattenuator/1"
cd $DIRNAME
../src/ska_tangoctl/tango_kontrol/tangoktl.py -h
echo "_________________________________________"
echo "List contexts"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -xq"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -xq

echo "_________________________________________"
echo "List contexts in JSON format"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -xqj"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -xqj

echo "_________________________________________"
echo "List namespaces"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -nq"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -nq

echo "_________________________________________"
echo "List services"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -z"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -z

echo "_________________________________________"
echo "List pods"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -o"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -o

echo "_________________________________________"
echo "List classes"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -k"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -k

echo "_________________________________________"
echo "List device names as tree"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} --tree -q"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} --tree -q

echo "_________________________________________"
echo "List device names"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -dq"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -dq

echo "_________________________________________"
echo "List devices"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -lq"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -lq

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-attributes.json"
echo "List device attributes in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -ajq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -ajq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-commands.json"
echo "List device commands in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -cjq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -cjq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-properties.json"
echo "List device properties in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -pjq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -pjq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-properties.yaml"
echo "List device properties in YAML format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -pyq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -pyq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}.json"
echo "List device attributes, commands and properties in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -acpjq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -acpjq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}.yaml"
echo "List device attributes, commands and properties in YAML format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -acpyq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -acpyq -O ../${FILE_NAME}
yamllint ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-status.json"
echo "List device attributes named 'status' to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A status -jq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A status -jq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="../${NAMESPACE}-buildState.json"
echo "List device attributes named 'buildState' in JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="../${NAMESPACE}-buildState.yaml"
echo "List device attributes named 'buildState' in YAML format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jq -O ../${FILE_NAME}
yamllint ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-buildState2.json"
echo "List device attributes named 'buildState' in short JSON format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jqs -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -jqs -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME="${NAMESPACE}-buildState2.yaml"
echo "List device attributes named 'buildState' in short YAML format to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -yqs -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -A buildState -yqs -O ../${FILE_NAME}
yamllint ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
echo "Ping device ${DEVICE}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -D ${DEVICE} --ping -q

echo "_________________________________________"
FILE_NAME=$(echo ${DEVICE} | tr "/" "-").json
echo "List attributes, commands and properties in JSON format for device ${DEVICE} to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -D ${DEVICE} -acpjq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -D ${DEVICE} -acpjq -O ../${FILE_NAME}
jsonlint-php -q ../${FILE_NAME}
ls -lh ../${FILE_NAME}

echo "_________________________________________"
FILE_NAME=$(echo ${DEVICE} | tr "/" "-").yaml
echo "List attributes, commands and properties in YAML format for device ${DEVICE} to ${FILE_NAME}"
echo "$ ./src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -D ${DEVICE} -acpyq -O ${FILE_NAME}"
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -N ${NAMESPACE} -D ${DEVICE} -acpyq -O ../${FILE_NAME}
yamllint ../${FILE_NAME}
ls -lh ../${FILE_NAME}

cd -
