#!/usr/bin/bash
DIRNAME=$(dirname $0)
cd $DIRNAME
../src/ska_tangoctl/tango_kontrol/tangoktl.py -h
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -k
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -K test-equipment -bq
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -K test-equipment -dq
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -K test-equipment -zq
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -K test-equipment -z
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -K test-equipment -acpj
echo "_________________________________________"
../src/ska_tangoctl/tango_kontrol/tangoktl.py -K test-equipment -A status
cd -
