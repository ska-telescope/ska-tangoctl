NAME

tangoctl - read and display information about Tango devices
tangoktl - read and display information about Tango devices running in Kubernetes

SYNOPSIS

    tangoktl.py --version
    tangoktl.py --help
    tangoktl.py -h
    tangoktl.py --show-ns
    tangoktl.py -k
    tangoktl.py -t -K NAMESPACE
    tangoktl.py -d|--class -K NAMESPACE
    tangoktl.py -d|--class -H HOST
    tangoktl.py -l -K NAMESPACE
    tangoktl.py -l -H HOST
    tangoktl.py -l -K integration
    tangoktl.py --full|--short -D DEVICE -K NAMESPACE
    tangoktl.py --full|--short -D DEVICE -H HOST
    tangoktl.py -f|-s -C COMMAND -K NAMESPACE
    tangoktl.py -f|-s -C COMMAND -H HOST
    tangoktl.py -f|-s -P PROPERTY -K NAMESPACE
    tangoktl.py -f|-s -P PROPERTY -H HOST
    tangoktl.py --json-dir=PATH
    tangoktl.py -J PATH
    tangoktl.py --namespace=NAMESPACE --input=FILE
    tangoktl.py -K NAMESPACE -O FILE

DESCRIPTION

tangoctl reads information fields, attributes, command and property configuration and 
values of all Tango devices with a single command. The ouput format is configurable. It
can be called from bash or Python. It can be configured with a JSON file. Regular 
expression filtering of Tango entities is supported. Support for Tango devices running 
in a Kubernetes cluster is built in.

OPTIONS

Generic Program Information

    --help Output a usage message and exit.

    -V, --version
        Output the version number of grep and exit.

General Input Control

    -a|--show-attribute             
        flag for reading attributes
    -c|--show-command               
        flag for reading commands
    -p|--show-property              
        flag for reading properties
    -e|--everything                 
        show all devices - do not skip sys, dserver
    -f|--full                       
        display in full

General Output Control

    -w|--html                       
        output in HTML format
    -j|--json                       
        output in JSON format
    -m|--md                         
        output in markdown format
    -y|--txt                        
        output in text format
    -y|--yaml                       
        output in YAML format

Parameters

    -X FILE, --cfg=FILE
        override configuration from file
    
    -J PATH, --json-dir=PATH               
        directory with JSON input file, e.g. 'resources'
    
    -D DEVICE, --device=DEVICE               device name, e.g. 'csp' (not case sensitive, only a part is needed)
    
    --namespace=NAMESPACE         Kubernetes namespace for Tango database, e.g. 'integration'
    -K NAMESPACE
    --host=HOST                   Tango database host and port, e.g. 10.8.13.15:10000
    -H HOST
    --attribute=ATTRIBUTE         attribute name, e.g. 'obsState' (not case sensitive)
    -A ATTRIBUTE
    --command=COMMAND             command name, e.g. 'Status' (not case sensitive)
    -C COMMAND
    --output=FILE                 output file name
    -O FILE
    --input=FILE                  input file name
    -I FILE

Other Options

    -i|--ip                         
        use IP address instead of FQDN
    -l|--list                       
        display device name and status on one line
    -s|--short                      
        display device name, status and query devices
    -q|--quiet                      
        do not display progress bars

EXIT STATUS
       
Normally the exit status is 0 if no error occured, 1 if an error occured.

BUGS

To be determined

AUTHOR

johan.coetzer@community.skao.int


SEE ALSO

PyTango is a python module that exposes to Python the complete Tango C++ API. 

https://www.tango-controls.org/
https://tango-controls.readthedocs.io/projects/pytango/en/latest/
https://tango-controls.github.io/cppTango-docs/index.html
