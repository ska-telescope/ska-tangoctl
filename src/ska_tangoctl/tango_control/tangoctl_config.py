"""Configuraton data."""

import json
import logging
from typing import TextIO

TANGOCTL_CONFIG = {
    "timeout_millis": 500,
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
        "attributes": {"adminMode": ">11", "versionId": "<10"},
        "commands": {"State": "<10"},
        "properties": {"SkaLevel": ">9"},
    },
    "block_items": {
        "attributes": [],
        "commands": [],
        "properties": ["LibConfiguration"],
    },
}


def read_tangoctl_config(logger: logging.Logger, cfg_name: str | None = None) -> dict:
    """
    Read configuration data.

    :param logger: logging handle
    :param cfg_name: file name
    :return: dictionary with configuration
    """
    cfg_data: dict

    if cfg_name is None:
        cfg_data = TANGOCTL_CONFIG
    else:
        try:
            cfg_file: TextIO = open(cfg_name)
            cfg_data = json.load(cfg_file)
            cfg_file.close()
            for key in TANGOCTL_CONFIG:
                if key not in cfg_data:
                    cfg_data[key] = TANGOCTL_CONFIG[key]
                    logger.warning("Use default value for %s : %s", key, str(cfg_data[key]))
        except FileNotFoundError:
            logger.error("Could not read config file %s", cfg_name)
            cfg_data = TANGOCTL_CONFIG
    return cfg_data
