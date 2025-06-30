"""Configuraton data."""

import json
import logging
from typing import TextIO

TANGOKTL_CONFIG: dict = {
    "timeout_millis": 500,
    "service_name": "databaseds-tangodb-tango-databaseds",
    "top_level_domain": {
        "infra:za-aa-k8s-master01-k8s": "svc.mid.internal.skao.int",
        "infra:za-aa-ska036-k8s": "svc.ska036.miditf.internal.skao.int",
        "infra:za-itf-k8s-master01-k8s": "svc.miditf.internal.skao.int",
    },
    "databaseds_name": "tango-databaseds",
    "databaseds_port": 10000,
    "device_port": 45450,
    "run_commands": [
        "QueryClass",
        "QueryDevice",
        "QuerySubDevice",
        "GetVersionInfo",
        "State",
        "Status",
    ],
    "run_commands_name": ["DevLockStatus", "DevPollStatus", "GetLoggingTarget"],
    "long_attributes": ["internalModel", "transformedInternalModel"],
    "ignore_device": ["sys", "dserver"],
    "min_str_len": 4,
    "delimiter": ",",
    "list_items": {
        "attributes": {"adminMode": "<12", "versionId": "<10"},
        "attributes_str": ["adminMode"],
        "commands": {"State": "<10"},
        "properties": {"SkaLevel": ">9"},
    },
    "block_items": {
        "attributes": [],
        "commands": [],
        "properties": ["LibConfiguration"],
    },
}


def read_tangoktl_config(logger: logging.Logger, cfg_name: str | None = None) -> dict:
    """
    Read configuration data.

    :param logger: logging handle
    :param cfg_name: file name
    :return: dictionary with configuration
    """
    cfg_data: dict

    if cfg_name is None:
        cfg_data = TANGOKTL_CONFIG
    else:
        try:
            cfg_file: TextIO = open(cfg_name)
            cfg_data = json.load(cfg_file)
            cfg_file.close()
            for key in TANGOKTL_CONFIG:
                if key not in cfg_data:
                    cfg_data[key] = TANGOKTL_CONFIG[key]
                    logger.warning("Use default value for %s : %s", key, str(cfg_data[key]))
        except FileNotFoundError:
            logger.error("Could not read config file %s", cfg_name)
            cfg_data = TANGOKTL_CONFIG
    return cfg_data
