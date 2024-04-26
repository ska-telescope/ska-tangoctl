""" Configuraton data. """

TANGOKTL_CONFIG = {
    "timeout_millis": 500,
    "cluster_domain": "miditf.internal.skao.int",
    "databaseds_name": "tango-databaseds",
    "databaseds_port": 10000,
    "device_port": 45450,
    "run_commands":  [
        "QueryClass",
        "QueryDevice",
        "QuerySubDevice",
        "GetVersionInfo",
        "State",
        "Status"
    ],
    "run_commands_name": ["DevLockStatus", "DevPollStatus", "GetLoggingTarget"],
    "long_attributes": ["internalModel", "transformedInternalModel"],
    "ignore_device": ["sys", "dserver"],
    "min_str_len": 4,
    "delimiter": ",",
    "list_items" : {
        "attributes" : {"adminMode": ">11", "versionId": "<10"},
        "commands": {"State": "<10"},
        "properties": {"SkaLevel": ">9"}
    }
}
