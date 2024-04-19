How to run *tangoctl*
*********************

.. image:: https://readthedocs.org/projects/ska-tangoctl/badge/?version=latest
    :target: https://developer.skatelescope.org/projects/ska-tangoctl/en/latest/?badge=latest

Introduction
============

This project provides a command line utility for use with Tango. It reads information 
fields and also attributes, command and property configuration and values.

The utility reads all Tango devices from the Tango database, specified on the command 
line or with the TANGO_HOST environment variable. When reading Tango devices, there are 
three types of output:
* list output with one line per device (list)
* read and display values of attributes, properties and a selection of commands (short)
* read and display configuration and values in full (full)
Output can be in plain text, YAML, HTML, JSON or Markdown format.

There are no hard-coded attribute, command or property names. The columns in the list 
are configured in a JSON file.

By default, devices with names that start with _sys_ or _dserver_ are not shown. This
can be overridden using a command line flag or in the configuration file. The Tango 
devices can be filtered by attribute, command, property or class name. Matches can be 
done on full or partial matches.  To shorten the running time, there is an option to 
limit output to one device per class. 

An enhanced version of **tangoctl** (named **tangoktl**) has support for Tango devices 
running in a Kubernetes cluster. The namespaces in the cluster can be listed. By setting
a standard pod name for Tango database servers in the configuration file, the FQDN of 
the server can be derived and the IP address can be looked up.

By default, commands are not run since it might result in devices ending up in unwanted 
or unsafe states. The configuration file contain commands that are safe to be read, 
for example Status.

There is a basic test function. Values for attributes, commands or properties are 
specified in a JSON file. These are written and then read. The test fails if the 
expected value is not returned.

An experimental C++ version with a subset of the above functionality is available at:

https://gitlab.com/jcoetzer/tangoctl_cpp

How to get and set Tango host
=============================

Using **kubectl.py**
--------------------

Read the external IP address of the service *tango-databaseds* in the Kubernetes
namespace of interest, e.g. *integration*:

```
$ kubectl get service tango-databaseds --namespace integration
NAME               TYPE           CLUSTER-IP    EXTERNAL-IP     PORT(S)           AGE
tango-databaseds   LoadBalancer   10.110.24.5   10.164.10.161   10000:32207/TCP   6d7h
$ export TANGO_HOST=10.164.10.161:10000
```

Using **tangoktl**
------------------

If tangoktl is installed (see below) it can be used to get the Tango host setting::

    $ tangoktl -K integration -t
    TANGO_HOST=tango-databaseds.integration.svc.miditf.internal.skao.int:10000
    TANGO_HOST=10.164.10.161:10000
    $ export TANGO_HOST=10.164.10.161:10000

Tango control utility
=====================

Types of output
---------------

When reading Tango devices, there are three types of output:

* list output with one line per device (use `-l` or `--list`)
* read and display values of attributes, properties and some commands (`-s` or `--short`)
* read and display configuration and values in full (`-f` or `--full`)

Filtering output
----------------

The list of devices can be filtered by 

* device name (`-D` or `--device=`) 
* attribute (`-A` or `--attribute=`)
* command (`-C` or `--command`)
* property (`-P` or `--property`)

By default, devices with names that start with `sys` or `dserver` are not shown. This
is configurable (see below). To override this, use the flag `-e` or `--everything`.

To shorten the running time use `-u` or `--unique` to limit output to one device per class. 

Logging level
-------------

By default, the logging level is *WARNING**. Use `-v` to switch to *INFO* or `-V` to 
switch to *DEBUG*.

Progress bars can be turned off with `-q` or `--quiet`. They are disbled when logging 
level is set to *INFO* or *DEBUG*.

Output format
-------------

Output can be in any of the following formats:
* text (default)
* YAML (`-y` or '--yaml`)
* HTML (`-j` or `--html`)
* JSON (`-w` or `--json`)
* Markdown (`-m` or `--md`)

Configuration files
===================

The items displayed in the list output are configurable. The configuration file 
also contain commands that can be read. 

tangoktl.json
-------------

This file should reside in the same directory as `tangoktl`. Here is an example::

    {
      "cluster_domain": "miditf.internal.skao.int",
      "databaseds_name": "tango-databaseds",
      "databaseds_port": 10000,
      "device_port": 45450,
      "run_commands":  ["QueryClass", "QueryDevice", "QuerySubDevice", "GetVersionInfo", "State", "Status"],
      "run_commands_name": ["DevLockStatus", "DevPollStatus", "GetLoggingTarget"],
      "ignore_device": ["sys", "dserver"],
      "min_str_len": 4,
      "delimiter": ",",
      "list_items" : {
        "attributes" : {"adminMode": ">11", "versionId": "<10"},
        "commands": {"State": "<10"},
        "properties": {"SkaLevel": ">9"}
      }
    }

Fields:
* min_str_len: mininum string length below which only exact matches are allowed
* ignore_device: device names that start with these string are ignored (unless the )
* run_commands: commands that can be run
* run_commands_name: commands that can be run with the device name as parameter
* databaseds_name: prefix used to set TANGO_HOST
* cluster_domain: domain name used to set TANGO_HOST
* databaseds_port: Tango database device port, used to set TANGO_HOST
* list_items: attributes, commands and properties to display in list (the values are used to construct Python f-strings)

The value for TANGO_HOST is set as follows:

`databaseds_name`.`namespace`.`cluster_domain`:`databaseds_port`

where `namespace` is specified on the command line

tangoctl.json
-------------

This file should reside in the same directory as `tangoctl`. Here is an example::

    {
      "device_port": 45450,
      "run_commands":  ["QueryClass", "QueryDevice", "QuerySubDevice", "GetVersionInfo", "State", "Status"],
      "run_commands_name": ["DevLockStatus", "DevPollStatus", "GetLoggingTarget"],
      "ignore_device": ["sys", "dserver"],
      "min_str_len": 4,
      "delimiter": ",",
      "list_items" : {
        "attributes" : {"adminMode": ">11", "versionId": "<10"},
        "commands": {"State": "<10"},
        "properties": {"SkaLevel": ">9"}
      }
    }

Fields:
* min_str_len: mininum string length below which only exact matches are allowed
* ignore_device: device names that start with these string are ignored (unless the )
* run_commands: commands that can be run
* run_commands_name: commands that can be run with the device name as parameter
* list_items: attributes, commands and properties to display in list (the values are used to construct Python f-strings)

Getting help
============

To obtain help::

    $ tangoktl --help
    Read Tango devices:

    Display version number
            tangoctl --version

    Display help
            tangoctl --help
            tangoctl -h

    Display Kubernetes namespaces
            tangoctl --show-ns
            tangoctl -k

    Display Tango database address
            tangoctl --show-db --k8s-ns=<NAMESPACE>
            tangoctl -t -K <NAMESPACE>
    e.g. tangoctl -t -K integration

    Display classes and Tango devices associated with them
            tangoctl -d|--class --k8s-ns=<NAMESPACE>|--host=<HOST>
            tangoctl -d\|--class -K <NAMESPACE>\|-H <HOST>
    e.g. tangoctl -d -K integration

    List Tango device names
            tangoctl --show-dev --k8s-ns=<NAMESPACE>\|--host=<HOST>
            tangoctl -l -K <NAMESPACE>\|-H <HOST>
    e.g. tangoctl -l -K integration

    Display all Tango devices (will take a long time)
            tangoctl --full\|--short -e|--everything [--namespace=<NAMESPACE>\|--host=<HOST>]
            tangoctl -l -K integration
            e.g. tangoctl -f|-s -K <NAMESPACE>|-H <HOST>

    Filter on device name
            tangoctl --full|--short -D <DEVICE> -K <NAMESPACE>|-H <HOST>
            tangoctl -f|-s --device=<DEVICE> --k8s-ns=<NAMESPACE>|--host=<HOST>
    e.g. tangoctl -f -K integration -D ska_mid/tm_leaf_node/csp_subarray01

    Filter on attribute name
            tangoctl --full|--short --attribute=<ATTRIBUTE> --k8s-ns=<NAMESPACE>|--host=<HOST>
            tangoctl -f|-s -A <ATTRIBUTE> -K <NAMESPACE>|-H <HOST>
    e.g. tangoctl -f -K integration -A timeout

    Filter on command name
            tangoctl --full|--short --command=<COMMAND> --k8s-ns=<NAMESPACE>|--host=<HOST>
            tangoctl -f|-s -C <COMMAND> -K <NAMESPACE>|-H <HOST>
    e.g. tangoctl -l -K integration -C status

    Filter on property name
            tangoctl --full|--list|--short --property=<PROPERTY> --k8s-ns=<NAMESPACE>|--host=<HOST>
            tangoctl -f|-s -P <PROPERTY> --k8s-ns=<NAMESPACE>|--host=<HOST>
    e.g. tangoctl -l -K integration -P power

    Display tangoctl test input files
            tangoctl --json-dir=<PATH>
            tangoctl -J <PATH>
    e.g. ADMIN_MODE=1 tangoctl -J resources/

    Run test, reading from input file
            tangoctl --k8s-ns=<NAMESPACE> --input=<FILE>
            tangoctl --K <NAMESPACE> -O <FILE>
    Files are in JSON format and contain values to be read and/or written, e.g:
    {
        "description": "Turn admin mode on and check status",
        "test_on": [
            {
                "attribute": "adminMode",
                "read" : ""
            },
            {
                "attribute": "adminMode",
                "write": 1
            },
            {
                "attribute": "adminMode",
                "read": 1
            },
            {
                "command": "State",
                "return": "OFFLINE"
            },
            {
                "command": "Status"
            }
        ]
    }

    Files can contain environment variables that are read at run-time:
    {
        "description": "Turn admin mode off and check status",
        "test_on": [
            {
                "attribute": "adminMode",
                "read": ""
            },
            {
                "attribute": "adminMode",
                "write": "${ADMIN_MODE}"
            },
            {
                "attribute": "adminMode",
                "read": "${ADMIN_MODE}"
            },
            {
                "command": "State",
                "return": "ONLINE"
            },
            {
                "command": "Status"
            }
        ]
    }

    To run the above:
    ADMIN_MODE=1 tangoctl --k8s-ns=integration -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V

    Test Tango devices:

    Test a Tango device
            tangoctl -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]

    Test a Tango device and read attributes
            tangoctl -a -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]

    Display attribute and command names for a Tango device
            tangoctl -c -K <NAMESPACE>|-H <HOST> -D <DEVICE>

    Turn a Tango device on
            tangoctl --on -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]

    Turn a Tango device off
            tangoctl --off -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]

    Set a Tango device to standby mode
            tangoctl --standby -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]

    Change admin mode on a Tango device
            tangoctl --admin=<0|1>

    Display status of a Tango device
            tangoctl --status -K <NAMESPACE>|-H <HOST> -D <DEVICE>

    Check events for attribute of a Tango device
            tangoctl -K <NAMESPACE>|-H <HOST> -D <DEVICE> -A <ATTRIBUTE>

    Parameters:

            -a                              flag for reading attributes during tests
            -c|--cmd                        flag for running commands during tests
            --simul=<0|1>                   set simulation mode off or on
            --admin=<0|1>                   set admin mode off or onn
            -e|--everything                 show all devices
            -f|--full                       display in full
            -l|--list                       display device name and status on one line
            -s|--short                      display device name, status and query devices
            -q|--quiet                      do not display progress bars
            -j|--html                       output in HTML format
            -j|--json                       output in JSON format
            -m|--md                         output in markdown format
            -y|--yaml                       output in YAML format
            --json-dir=<PATH>               directory with JSON input file, e.g. 'resources'
            -J <PATH>
            --device=<DEVICE>               device name, e.g. 'csp' (not case sensitive, only a part is needed)
            -D <DEVICE>
            --k8s-ns=<NAMESPACE>            Kubernetes namespace for Tango database, e.g. 'integration'
            -K <NAMESPACE>
            --host=<HOST>                   Tango database host and port, e.g. 10.8.13.15:10000
            -H <HOST>
            --attribute=<ATTRIBUTE>         attribute name, e.g. 'obsState' (not case sensitive)
            -A <ATTRIBUTE>
            --command=<COMMAND>             command name, e.g. 'Status' (not case sensitive)
            -C <COMMAND>
            --output=<FILE>                 output file name
            -O <FILE>
            --input=<FILE>                  input file name
            -I <FILE>

    Note that values for device, attribute, command or property are not case sensitive.
    Partial matches for strings longer than 4 charaters are OK.

    When a namespace is specified, the Tango database host will be made up as follows:
            tango-databaseds.<NAMESPACE>.miditf.internal.skao.int:10000

    Run the following commands where applicable:
            QueryClass,QueryDevice,QuerySubDevice,GetVersionInfo,State,Status

    Run commands with device name as parameter where applicable:
            DevLockStatus,DevPollStatus,GetLoggingTarget

    Examples:

            tangoctl --k8s-ns=integration -l
            tangoctl --k8s-ns=integration -D talon -l
            tangoctl --k8s-ns=integration -A timeout
            tangoctl --k8s-ns=integration -C Telescope
            tangoctl --k8s-ns=integration -P Power
            tangoctl --k8s-ns=integration -D mid_csp_cbf/talon_lru/001 -f
            tangoctl --k8s-ns=integration -D mid_csp_cbf/talon_lru/001 -q
            tangoctl --k8s-ns=integration -D mid_csp_cbf/talon_board/001 -f
            tangoctl --k8s-ns=integration -D mid_csp_cbf/talon_board/001 -f --dry
            tangoctl --k8s-ns=integration -D mid-sdp/control/0 --on
            ADMIN_MODE=1 tangoctl --k8s-ns=integration -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V


Read all namespaces in Kubernetes cluster
=========================================

The user must be logged into the Mid ITF VPN, otherwise this will time out.

Run this command to list namespaces::

    $ tangoktl --show-ns
    Namespaces : 53
            advanced-tango-training
            advanced-tango-training-sdp
            binderhub
            calico-apiserver
            calico-operator
            calico-system
            ci-dish-lmc-ska001-at-1838-update-main
            ci-dish-lmc-ska036-at-1838-update-main
            integration
            integration-sdp
            ci-ska-mid-itf-at-1838-update-main
            ci-ska-mid-itf-at-1838-update-main-sdp
            ci-ska-mid-itf-sah-1486
            ci-ska-mid-itf-sah-1486-sdp
            default
            dish-lmc-ska001
            dish-lmc-ska036
            dish-lmc-ska063
            dish-lmc-ska100
            dish-structure-simulators
            dishlmc-integration-ska001
            ds-sim-ska001
            extdns
            file-browser
            gitlab
            infra
            ingress-nginx
            integration
            integration-sdp
            integration-ska-mid-dish-spfc
            itf-ska-dish-lmc-spf
            kube-node-lease
            kube-public
            kube-system
            kyverno
            metallb-system
            miditf-lmc-002-ds
            miditf-lmc-003-karoo-sims
            miditf-lmc-005-spfrx
            register-spfc
            rook-ceph
            secrets-store-csi-driver
            ska-db-oda
            ska-tango-archiver
            ska-tango-operator
            sonobuoy
            spookd
            tango-tar-pvc
            tango-util
            taranta
            test-equipment
            test-spfc
            vault

Read Tango devices
==================

Read all Tango devices
----------------------

This will display the name, current state and admin mode setting for each Tango device 
in the database. Note that output has been shorteneded. By default, device names starting 
with **dserver** or **sys** are not listed::

    $ tangoktl --namespace=integration --list
    DEVICE NAME                              STATE      ADMIN MODE  VERSION  CLASS
    mid-csp/capability-fsp/0                 ON         ONLINE      2        MidCspCapabilityFsp
    mid-csp/capability-vcc/0                 ON         ONLINE      2        MidCspCapabilityVcc
    mid-csp/control/0                        DISABLE    OFFLINE     2        MidCspController
    mid-csp/subarray/01                      DISABLE    OFFLINE     2        MidCspSubarray
    mid-csp/subarray/02                      DISABLE    OFFLINE     2        MidCspSubarray
    mid-csp/subarray/03                      DISABLE    OFFLINE     2        MidCspSubarray
    mid-eda/cm/01                            ON         N/A         N/A      HdbConfigurationManager
    mid-eda/es/01                            ON         N/A         N/A      HdbEventSubscriber
    mid-sdp/control/0                        N/A        N/A         N/A      N/A
    mid-sdp/queueconnector/01                N/A        N/A         N/A      N/A
    mid-sdp/queueconnector/02                N/A        N/A         N/A      N/A
    mid-sdp/queueconnector/03                N/A        N/A         N/A      N/A
    mid-sdp/subarray/01                      N/A        N/A         N/A      N/A
    mid-sdp/subarray/02                      N/A        N/A         N/A      N/A
    mid-sdp/subarray/03                      N/A        N/A         N/A      N/A
    mid_csp_cbf/fs_links/000                 DISABLE    OFFLINE     0.11.4   SlimLink
    ...
    mid_csp_cbf/fs_links/015                 DISABLE    OFFLINE     0.11.4   SlimLink
    mid_csp_cbf/fsp/01                       DISABLE    OFFLINE     0.11.4   Fsp
    mid_csp_cbf/fsp/02                       DISABLE    OFFLINE     0.11.4   Fsp
    mid_csp_cbf/fsp/03                       DISABLE    OFFLINE     0.11.4   Fsp
    mid_csp_cbf/fsp/04                       DISABLE    OFFLINE     0.11.4   Fsp
    mid_csp_cbf/fspCorrSubarray/01_01        DISABLE    OFFLINE     0.11.4   FspCorrSubarray
    ...
    mid_csp_cbf/fspCorrSubarray/04_03        DISABLE    OFFLINE     0.11.4   FspCorrSubarray
    mid_csp_cbf/fspPssSubarray/01_01         DISABLE    OFFLINE     0.11.4   FspPssSubarray
    ...
    mid_csp_cbf/fspPssSubarray/04_03         DISABLE    OFFLINE     0.11.4   FspPssSubarray
    mid_csp_cbf/fspPstSubarray/01_01         DISABLE    OFFLINE     0.11.4   FspPstSubarray
    ...
    mid_csp_cbf/fspPstSubarray/04_03         DISABLE    OFFLINE     0.11.4   FspPstSubarray
    mid_csp_cbf/power_switch/001             DISABLE    OFFLINE     0.11.4   PowerSwitch
    mid_csp_cbf/power_switch/002             DISABLE    OFFLINE     0.11.4   PowerSwitch
    mid_csp_cbf/power_switch/003             DISABLE    OFFLINE     0.11.4   PowerSwitch
    mid_csp_cbf/slim/slim-fs                 DISABLE    OFFLINE     0.11.4   Slim
    mid_csp_cbf/slim/slim-vis                DISABLE    OFFLINE     0.11.4   Slim
    mid_csp_cbf/sub_elt/controller           DISABLE    OFFLINE     0.11.4   CbfController
    mid_csp_cbf/sub_elt/subarray_01          DISABLE    OFFLINE     0.11.4   CbfSubarray
    mid_csp_cbf/sub_elt/subarray_02          DISABLE    OFFLINE     0.11.4   CbfSubarray
    mid_csp_cbf/sub_elt/subarray_03          DISABLE    OFFLINE     0.11.4   CbfSubarray
    mid_csp_cbf/talon_board/001              DISABLE    OFFLINE     0.11.4   TalonBoard
    ...
    mid_csp_cbf/talon_board/008              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_lru/001                DISABLE    OFFLINE     0.11.4   TalonLRU
    ...
    mid_csp_cbf/talon_lru/004                DISABLE    OFFLINE     0.11.4   TalonLRU
    mid_csp_cbf/talondx_log_consumer/001     DISABLE    OFFLINE     0.11.4   TalonDxLogConsumer
    mid_csp_cbf/vcc/001                      DISABLE    OFFLINE     0.11.4   Vcc
    ...
    mid_csp_cbf/vcc/008                      DISABLE    OFFLINE     0.11.4   Vcc
    mid_csp_cbf/vcc_sw1/001                  DISABLE    OFFLINE     0.11.4   VccSearchWindow
    ...
    mid_csp_cbf/vcc_sw2/008                  DISABLE    OFFLINE     0.11.4   VccSearchWindow
    mid_csp_cbf/vis_links/000                DISABLE    OFFLINE     0.11.4   SlimLink
    mid_csp_cbf/vis_links/001                DISABLE    OFFLINE     0.11.4   SlimLink
    mid_csp_cbf/vis_links/002                DISABLE    OFFLINE     0.11.4   SlimLink
    mid_csp_cbf/vis_links/003                DISABLE    OFFLINE     0.11.4   SlimLink
    ska_mid/tm_central/central_node          ON         OFFLINE     0.12.2   CentralNodeMid
    ska_mid/tm_leaf_node/csp_master          ON         OFFLINE     0.10.3   CspMasterLeafNode
    ska_mid/tm_leaf_node/csp_subarray01      ON         OFFLINE     0.10.3   CspSubarrayLeafNodeMid
    ska_mid/tm_leaf_node/csp_subarray_01     INIT       OFFLINE     0.11.4   TmCspSubarrayLeafNodeTest
    ska_mid/tm_leaf_node/csp_subarray_02     INIT       OFFLINE     0.11.4   TmCspSubarrayLeafNodeTest
    ska_mid/tm_leaf_node/d0001               ON         OFFLINE     0.8.1    DishLeafNode
    ...
    ska_mid/tm_leaf_node/d0100               ON         OFFLINE     0.8.1    DishLeafNode
    ska_mid/tm_leaf_node/sdp_master          ON         OFFLINE     0.14.2   SdpMasterLeafNode
    ska_mid/tm_leaf_node/sdp_subarray01      ON         OFFLINE     0.14.2   SdpSubarrayLeafNode
    ska_mid/tm_subarray_node/1               ON         OFFLINE     0.13.19  SubarrayNodeMid


Filter by device name
---------------------

To find all devices with **talon** in the name::

    $ tangoktl --namespace=integration -D talon -l
    DEVICE NAME                              STATE      ADMIN MODE  VERSION  CLASS
    mid_csp_cbf/talon_board/001              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_board/002              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_board/003              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_board/004              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_board/005              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_board/006              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_board/007              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_board/008              DISABLE    OFFLINE     0.11.4   TalonBoard
    mid_csp_cbf/talon_lru/001                DISABLE    OFFLINE     0.11.4   TalonLRU
    mid_csp_cbf/talon_lru/002                DISABLE    OFFLINE     0.11.4   TalonLRU
    mid_csp_cbf/talon_lru/003                DISABLE    OFFLINE     0.11.4   TalonLRU
    mid_csp_cbf/talon_lru/004                DISABLE    OFFLINE     0.11.4   TalonLRU
    mid_csp_cbf/talondx_log_consumer/001     DISABLE    OFFLINE     0.11.4   TalonDxLogConsumer


Find attributes, commands or properties
---------------------------------------

It is possible to search for attributes, commands or properties by part of the name. This is not case-sensitive.

Find attributes
^^^^^^^^^^^^^^^

To find all devices with attributes that contain **timeout**::

    $ tangoktl --namespace=integration -A timeout
    DEVICE                                           ATTRIBUTE                                VALUE
    mid-csp/control/0                                commandTimeout                           5
                                                     offCmdTimeoutExpired                     False
                                                     onCmdTimeoutExpired                      False
                                                     standbyCmdTimeoutExpired                 False
    mid-csp/subarray/01                              commandTimeout                           5
                                                     timeoutExpiredFlag                       False
    mid-csp/subarray/02                              commandTimeout                           5
                                                     timeoutExpiredFlag                       False
    mid-csp/subarray/03                              commandTimeout                           5
                                                     timeoutExpiredFlag                       False
    mid_csp_cbf/sub_elt/subarray_01                  assignResourcesTimeoutExpiredFlag        False
                                                     configureScanTimeoutExpiredFlag          False
                                                     releaseResourcesTimeoutExpiredFlag       False
    mid_csp_cbf/sub_elt/subarray_02                  assignResourcesTimeoutExpiredFlag        False
                                                     configureScanTimeoutExpiredFlag          False
                                                     releaseResourcesTimeoutExpiredFlag       False
    mid_csp_cbf/sub_elt/subarray_03                  assignResourcesTimeoutExpiredFlag        False
                                                     configureScanTimeoutExpiredFlag          False
                                                     releaseResourcesTimeoutExpiredFlag       False


To find all devices with attributes that contain **timeout**, without displaying values::

    $ tangoktl --namespace=integration -A timeout --dry-run
    DEVICE                                           ATTRIBUTE
    mid-csp/control/0                                commandTimeout
                                                     offCmdTimeoutExpired
                                                     onCmdTimeoutExpired
                                                     standbyCmdTimeoutExpired
    mid-csp/subarray/01                              commandTimeout
                                                     timeoutExpiredFlag
    mid-csp/subarray/02                              commandTimeout
                                                     timeoutExpiredFlag
    mid-csp/subarray/03                              commandTimeout
                                                     timeoutExpiredFlag
    mid_csp_cbf/sub_elt/subarray_01                  assignResourcesTimeoutExpiredFlag
                                                     configureScanTimeoutExpiredFlag
                                                     releaseResourcesTimeoutExpiredFlag
    mid_csp_cbf/sub_elt/subarray_02                  assignResourcesTimeoutExpiredFlag
                                                     configureScanTimeoutExpiredFlag
                                                     releaseResourcesTimeoutExpiredFlag
    mid_csp_cbf/sub_elt/subarray_03                  assignResourcesTimeoutExpiredFlag
                                                     configureScanTimeoutExpiredFlag
                                                     releaseResourcesTimeoutExpiredFlag

Find commands
^^^^^^^^^^^^^

To find all devices with commands that have **Telescope** in the name::

    $ tangoktl --namespace=integration -C Telescope
    ska_mid/tm_central/central_node                  TelescopeOff
                                                     TelescopeOn
                                                     TelescopeStandby

To find all devices with commands that have **Outlet** in the name::

    $ tangoktl --namespace=integration -C Outlet
    mid_csp_cbf/power_switch/001                     GetOutletPowerMode
                                                     TurnOffOutlet
                                                     TurnOnOutlet
    mid_csp_cbf/power_switch/002                     GetOutletPowerMode
                                                     TurnOffOutlet
                                                     TurnOnOutlet
    mid_csp_cbf/power_switch/003                     GetOutletPowerMode
                                                     TurnOffOutlet
                                                     TurnOnOutlet

Find properties
^^^^^^^^^^^^^^^

To find all devices with properties that have **Power** in the name::

    $ tangoktl --namespace=integration -P Power
    mid_csp_cbf/power_switch/001                     PowerSwitchIp
                                                     PowerSwitchLogin
                                                     PowerSwitchModel
                                                     PowerSwitchPassword
    mid_csp_cbf/power_switch/002                     PowerSwitchIp
                                                     PowerSwitchLogin
                                                     PowerSwitchModel
                                                     PowerSwitchPassword
    mid_csp_cbf/power_switch/003                     PowerSwitchIp
                                                     PowerSwitchLogin
                                                     PowerSwitchModel
                                                     PowerSwitchPassword
    mid_csp_cbf/sub_elt/controller                   PowerSwitch
    mid_csp_cbf/talon_lru/001                        PDU1PowerOutlet
                                                     PDU2PowerOutlet
    mid_csp_cbf/talon_lru/002                        PDU1PowerOutlet
                                                     PDU2PowerOutlet
    mid_csp_cbf/talon_lru/003                        PDU1PowerOutlet
                                                     PDU2PowerOutlet
    mid_csp_cbf/talon_lru/004                        PDU1PowerOutlet
                                                     PDU2PowerOutlet


Information on device
=====================

Full description of device
--------------------------

This display all information about a device. The input and output of commands are displayed where available::

    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -f
    Device            : mid_csp_cbf/talon_lru/001
    Admin mode        : 1
    State             : DISABLE
    Status            : The device is in DISABLE state.
    Description       : A Tango device
    Acronyms          : Correlator Beam Former (CBF), Central Signal Processor (CSP), Line Replaceable Unit (LRU)
    Database used     : True
    Server host       : ds-talonlru-talonlru-001-0
    Server ID         : TalonLRU/talonlru-001
    Device class      : TalonLRU
    Commands          : DebugDevice                    N/A
                                                       Not polled
                                                       OUT The TCP port the debugger is listening on.
                        GetVersionInfo                 TalonLRU, ska_tango_base, 0.11.4, A set of generic base devices for SKA Telescope.
                                                       Not polled
                                                       OUT Version strings
                        Init                           N/A
                                                       Not polled
                        Off                            N/A
                                                       Not polled
                                                       OUT (ReturnType, 'informational message')
                        On                             N/A
                                                       Not polled
                                                       OUT (ReturnType, 'informational message')
                        Reset                          N/A
                                                       Not polled
                                                       OUT (ReturnType, 'informational message')
                        Standby                        N/A
                                                       Not polled
                                                       OUT (ReturnType, 'informational message')
                        State                          DISABLE
                                                       Polled
                                                       OUT Device state
                        Status                         The device is in DISABLE state.
                                                       Not polled
                                                       OUT Device status
    Attributes        : PDU1PowerMode                  '0'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        PDU2PowerMode                  '0'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        State                          'DISABLE'
                                                       Polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        Status                         'The device is in DISABLE state.'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        adminMode                      '1'
                                                       Polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        buildState                     'ska_tango_base, 0.11.4, A set of generic base devices for SKA Telescope.'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        controlMode                    '0'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        healthState                    '0'
                                                       Polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        loggingLevel                   '4'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        loggingTargets                 tango::logger
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        simulationMode                 '1'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        testMode                       '0'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        versionId                      '0.11.4'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
    Properties        : PDU1                           002
                        PDU1PowerOutlet                AA41
                        PDU2                           002
                        PDU2PowerOutlet                AA41
                        PDUCommandTimeout              20
                        TalonDxBoard1                  001
                        TalonDxBoard2                  002
                        polled_attr                    state  1000
                                                       healthstate  3000
                                                       adminmode  3000

Short display
-------------

This displays only the values for status, commands, attributes and properties::

    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -s
    Device            : mid_csp_cbf/talon_lru/001
    Admin mode        : 1
    Commands          : DebugDevice                    N/A
                        GetVersionInfo                 TalonLRU, ska_tango_base, 0.11.4, A set of generic base devices for SKA Telescope.
                        Init                           N/A
                        Off                            N/A
                        On                             N/A
                        Reset                          N/A
                        Standby                        N/A
                        State                          DISABLE
                        Status                         The device is in DISABLE state.
    Attributes        : PDU1PowerMode                  '0'
                        PDU2PowerMode                  '0'
                        State                          'DISABLE'
                        Status                         'The device is in DISABLE state.'
                        adminMode                      '1'
                        buildState                     'ska_tango_base, 0.11.4, A set of generic base devices for SKA Telescope.'
                        controlMode                    '0'
                        healthState                    '0'
                        loggingLevel                   '4'
                        loggingTargets                 tango::logger
                        simulationMode                 '1'
                        testMode                       '0'
                        versionId                      '0.11.4'
    Properties        : PDU1                           002
                        PDU1PowerOutlet                AA41
                        PDU2                           002
                        PDU2PowerOutlet                AA41
                        PDUCommandTimeout              20
                        TalonDxBoard1                  001
                        TalonDxBoard2                  002
                        polled_attr                    state  1000
                                                       healthstate  3000
                                                       adminmode  3000

Display names only, without reading values::

    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -s --dry-run
    Device            : mid_csp_cbf/talon_lru/001
    Admin mode        : 1
    Commands          : DebugDevice
                        GetVersionInfo
                        Init
                        Off
                        On
                        Reset
                        Standby
                        State
                        Status
    Attributes        : PDU1PowerMode
                        PDU2PowerMode
                        State
                        Status
                        adminMode
                        buildState
                        controlMode
                        healthState
                        loggingLevel
                        loggingTargets
                        simulationMode
                        testMode
                        versionId
    Properties        : PDU1
                        PDU1PowerOutlet
                        PDU2
                        PDU2PowerOutlet
                        PDUCommandTimeout
                        TalonDxBoard1
                        TalonDxBoard2
                        polled_attr


Quick/query mode
----------------

This displays a shortened form, with query sub-devices where available::

    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -q
    Device            : mid_csp_cbf/talon_lru/001 9 commands, 13 attributes
    Admin mode        : 1
    State             : DISABLE
    Status            : The device is in DISABLE state.
    Description       : A Tango device
    Acronyms          : Correlator Beam Former (CBF), Central Signal Processor (CSP), Line Replaceable Unit (LRU)
    Device class      : TalonLRU
    Server host       : ds-talonlru-talonlru-001-0
    Server ID         : TalonLRU/talonlru-001
    Logging target    : <N/A>
    Query sub-devices : <N/A>


Error output
============

When a device attribute can not be read, a shortened error message is displayed::

    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_board/001 -f
    Tango host        : tango-databaseds.integration.svc.miditf.internal.skao.int:10000

    Device            : mid_csp_cbf/talon_board/001
    Admin mode        : 1
    State             : DISABLE
    Status            : The device is in DISABLE state.
    Description       : A Tango device
    Acronyms          : Correlator Beam Former (CBF), Central Signal Processor (CSP)
    Database used     : True
    Device class      : TalonBoard
    Server host       : ds-talonboard-talon-001-0
    Server ID         : TalonBoard/talon-001
    Commands            DebugDevice                    Not polled  OUT The TCP port the debugger is listening on.
                        GetVersionInfo                 Not polled  OUT Version strings
                        Init                           Not polled
                        Off                            Not polled  OUT (ReturnType, 'informational message')
                        On                             Not polled  OUT (ReturnType, 'informational message')
                        Reset                          Not polled  OUT (ReturnType, 'informational message')
                        Standby                        Not polled  OUT (ReturnType, 'informational message')
                        State                          Polled      OUT Device state
                        Status                         Not polled  OUT Device status
    Attributes        : BitstreamChecksum              <ERROR> System ID Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        BitstreamVersion               <ERROR> System ID Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        DIMMTemperatures               <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        FansFault                      <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        FansPwm                        <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>

Dry run
=======

To skip reading attribute values, use this option::

    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_board/001 -f
    Device            : mid_csp_cbf/talon_board/001
    Admin mode        : 1
    State             : DISABLE
    Status            : The device is in DISABLE state.
    Description       : A Tango device
    Acronyms          : Correlator Beam Former (CBF), Central Signal Processor (CSP)
    Database used     : True
    Server host       : ds-talonboard-talon-001-0
    Server ID         : TalonBoard/talon-001
    Device class      : TalonBoard
    Commands          : DebugDevice                    N/A
                                                       Not polled
                                                       OUT The TCP port the debugger is listening on.
                        GetVersionInfo                 TalonBoard, ska_tango_base, 0.11.4, A set of generic base devices for SKA Telescope.
                                                       Not polled
                                                       OUT Version strings
                        Init                           N/A
                                                       Not polled
                        Off                            N/A
                                                       Not polled
                                                       OUT (ReturnType, 'informational message')
                        On                             N/A
                                                       Not polled
                                                       OUT (ReturnType, 'informational message')
                        Reset                          N/A
                                                       Not polled
                                                       OUT (ReturnType, 'informational message')
                        Standby                        N/A
                                                       Not polled
                                                       OUT (ReturnType, 'informational message')
                        State                          DISABLE
                                                       Polled
                                                       OUT Device state
                        Status                         The device is in DISABLE state.
                                                       Not polled
                                                       OUT Device status
    Attributes        : BitstreamChecksum              <ERROR> System ID Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        BitstreamVersion               <ERROR> System ID Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        DIMMTemperatures               <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        FansFault                      <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        FansPwm                        <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        FansPwmEnable                  <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        FpgaDieTemperature             <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        HumiditySensorTemperature      <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        MboRxLOLStatus                 <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        MboRxLOSStatus                 <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        MboRxVccVoltages               <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        MboTxFaultStatus               <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        MboTxLOLStatus                 <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        MboTxLOSStatus                 <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        MboTxTemperatures              <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        MboTxVccVoltages               <ERROR> AttributeError: 'TalonBoardComponentManager' object has no attribute '_hostname'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        State                          'DISABLE'
                                                       Polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        Status                         'The device is in DISABLE state.'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        adminMode                      '1'
                                                       Polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        buildState                     'ska_tango_base, 0.11.4, A set of generic base devices for SKA Telescope.'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        comms_iopll_locked_fault       <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        controlMode                    '0'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        e100g_0_pll_fault              <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        e100g_1_pll_fault              <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        emif_bl_fault                  <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        emif_br_fault                  <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        emif_tr_fault                  <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        fs_iopll_locked_fault          <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        healthState                    '0'
                                                       Polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        iopll_locked_fault             <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        loggingLevel                   '4'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        loggingTargets                 tango::logger
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        simulationMode                 '0'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        slim_pll_fault                 <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        system_clk_fault               <ERROR> Talon Status Device is not available
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : <N/A>
                        testMode                       '0'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
                        versionId                      '0.11.4'
                                                       Not polled
                                                       Event change : Not specified
                                                       Quality : ATTR_VALID
    Properties        : HpsMasterServer                dshpsmaster
                        InfluxDbAuthToken              ikIDRLicRaMxviUJRqyE8bKF1Y_sZnaHc9MkWZY92jxg1isNPIGCyLtaC8EjbOhsT_kTzjt12qenB4g7-UOrog==
                        InfluxDbBucket                 talon
                        InfluxDbOrg                    ska
                        InfluxDbPort                   8086
                        Instance                       talon1_test
                        TalonDx100GEthernetServer      ska-talondx-100-gigabit-ethernet-ds
                        TalonDxBoardAddress            192.168.8.1
                        TalonDxSysIdServer             ska-talondx-sysid-ds
                        TalonStatusServer              ska-talondx-status-ds
                        polled_attr                    state  1000
                                                       healthstate  3000
                                                       adminmode  3000

Examples
========

Some useful ways of using **tangoktl**::

    $ tangoktl --namespace=integration --show-dev
    $ tangoktl --namespace=integration -D talon -l
    $ tangoktl --namespace=integration -A timeout
    $ tangoktl --namespace=integration -C Telescope
    $ tangoktl --namespace=integration -P Power
    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -f
    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -s
    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -q
    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_board/001 -f
    $ tangoktl --namespace=integration -D mid_csp_cbf/talon_board/001 -f --dry-run
    $ ADMIN_MODE=1 tangoctl --k8s-ns=integration -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V

Testing
=======

Build a new Docker image for the project::

    $ make oci-build
    [...]
    [+] Building 111.7s (14/14) FINISHED
    [...]

Install python requirements::

    $ poetry install

Run python-test::

    $ poetry shell
    $ make python-test

    pytest 6.2.5
    PYTHONPATH=/home/ubuntu/ska-tangoctl/src:/app/src:  pytest  \
     --cov=src --cov-report=term-missing --cov-report html:build/reports/code-coverage --cov-report xml:build/reports/code-coverage.xml --junitxml=build/reports/unit-tests.xml tests/
    =============================================================================================== test session starts ================================================================================================
    platform linux -- Python 3.10.12, pytest-6.2.5, py-1.11.0, pluggy-1.3.0
    rootdir: /home/ubuntu/ska-tangoctl, configfile: pyproject.toml
    plugins: cov-4.1.0, metadata-2.0.4, bdd-5.0.0, json-report-1.5.0, repeat-0.9.3, ska-ser-skallop-2.29.6
    collected 4 items

    tests/functional/tmc/test_deployment.py ....                                                                                                                                                                 [100%]

    ----------------------------------------------------------- generated xml file: /home/ubuntu/ska-tangoctl/build/reports/unit-tests.xml ------------------------------------------------------------

    ---------- coverage: platform linux, python 3.10.12-final-0 ----------
    Name                                                Stmts   Miss  Cover   Missing
    ---------------------------------------------------------------------------------
    src/ska_mid_itf_engineering_tools/__init__.py           0      0   100%
    src/ska_mid_itf_engineering_tools/tmc_dish_ids.py      47     12    74%   74, 167, 169, 171, 173, 199-205, 209-214
    ---------------------------------------------------------------------------------
    TOTAL                                                  47     12    74%
    Coverage HTML written to dir build/reports/code-coverage
    Coverage XML written to file build/reports/code-coverage.xml

    ================================================================================================ 4 passed in 0.10s =================================================================================================


Python linting
==============

To check for errors and correctly formatted code::

    $ make python-lint
    [...]
    --------------------------------------------------------------------
    Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)


.. image:: img/logo.webp
