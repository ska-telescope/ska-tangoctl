"""Process item for attribute."""

import json
import logging

from ska_tangoctl.pypogo.pypogo_globals import EOL


def get_int_value(val_str: str) -> int | None:
    if val_str:
        return int(val_str)
    return None


def get_num_value(val_str: str) -> int | float | None:
    if not val_str:
        return None
    if "." in val_str:
        return float(val_str)
    return int(val_str)


def get_str_value(val_str: str) -> str | None:
    if val_str:
        return val_str
    return None


class PyPogoAttribute:

    def __init__(self, logger: logging.Logger, attrib: dict, default_type: str, get_set: bool):
        """
        Read dictionary derived from XML file.

        :param logger: logging handle
        :param attrib: dictionary of attribute used to build code
        :param get_set: use getter and setter functions
        :param default_type: default type
        """
        self.get_set = get_set
        self.logger = logger
        self.name: str = attrib["name"]
        self.logger.info("Read attribute %s", self.name)
        self.logger.debug("Attribute %s : %s", self.name, json.dumps(attrib, indent=4))
        self.description: str = attrib["properties"]["description"]
        self.min_value: int | float | None = None
        self.max_value: int | float | None = None
        self.min_alarm: int | float | None = None
        self.max_alarm: int | float | None = None
        self.min_warning: int | float | None = None
        self.max_warning : int | float | None = None
        self.value: int | float | None = None
        self.field_type: str = ""
        if attrib["dataType"]["xsi:type"] == "pogoDsl:FloatType":
            self.field_type = "float"
            if attrib["properties"]["maxWarning"]:
                self.max_warning = float(attrib["properties"]["maxWarning"])
                self.logger.debug("Max warning value '%s'", self.max_warning)
            if attrib["properties"]["minWarning"]:
                self.min_warning = float(attrib["properties"]["minWarning"])
                self.logger.debug("Min warning value '%s'", self.min_warning)
            if attrib["properties"]["maxValue"]:
                self.max_value = float(attrib["properties"]["maxValue"])
                self.logger.debug("Max value '%s'", self.max_value)
            else:
                self.max_value = self.max_warning
            if attrib["properties"]["minValue"]:
                self.min_value = float(attrib["properties"]["minValue"])
                self.logger.debug("Min value '%s'", self.min_value)
            else:
                self.min_value = self.min_warning
            if self.min_value is not None and self.max_value is not None:
                self.value = float((self.max_value - self.min_value) / 2)
                self.logger.debug("Value %e", self.value)
        elif attrib["dataType"]["xsi:type"] == "pogoDsl:IntType":
            self.field_type = "int"
            if attrib["properties"]["maxWarning"]:
                self.max_warning = int(attrib["properties"]["maxWarning"])
                self.logger.debug("Max warning value '%s'", self.max_warning)
            if attrib["properties"]["minWarning"]:
                self.min_warning = int(attrib["properties"]["minWarning"])
                self.logger.debug("Min warning value '%s'", self.min_warning)
            # TODO read this from the dictionary
            self.max_value = self.max_warning
            self.min_value = self.min_warning
            if self.min_value is not None and self.max_value is not None:
                self.value = int((self.max_value - self.min_value) / 2)
                self.logger.debug("Value %d", self.value)
        elif attrib["dataType"]["xsi:type"] == "pogoDsl:EnumType":
            self.field_type = "int"
            self.min_value = 0
            self.max_value = len(attrib["enumLabels"]) - 1
        elif attrib["dataType"]["xsi:type"] == "pogoDsl:BooleanType":
            self.field_type = "bool"
        elif attrib["dataType"]["xsi:type"] == "pogoDsl:ShortType":
            self.field_type = "int"
        elif attrib["dataType"]["xsi:type"] == "pogoDsl:UShortType":
            self.field_type = "int"
        elif attrib["dataType"]["xsi:type"] == "pogoDsl:StringType":
            self.field_type = "str"
        else:
            self.field_type = default_type
        self.rw_type: str = attrib["rwType"]
        self.display_level: str = attrib["displayLevel"]
        self.att_type: str = attrib["attType"]
        self.polled_period: int | None = get_int_value(attrib["polledPeriod"])
        self.max_x: int | None = get_int_value(attrib["maxX"])
        self.max_y: int | None = get_int_value(attrib["maxY"])
        self.unit: str | None = get_str_value(attrib["properties"]["unit"])
        self.standard_unit: str | None = get_str_value(attrib["properties"]["standardUnit"])
        self.display_unit: str | None = get_str_value(attrib["properties"]["displayUnit"])
        self.format: str | None = get_str_value(attrib["properties"]["format"])
        self.label: str = attrib["properties"]["label"]
        self.delta_time: int | float | None
        try:
            self.delta_time = get_num_value(attrib["properties"]["deltaTime"])
        except ValueError:
            self.delta_time = None
        self.delta_value: int | float | None
        try:
            self.delta_value = get_num_value(attrib["properties"]["deltaValue"])
        except ValueError:
            self.delta_value = None

    def __repr__(self) -> str:
        """
        Do the string thing.

        :returns: string representation
        """
        repr_str = f"{self.name:40} {self.field_type:10} {self.rw_type:10}"
        if self.min_value is not None:
            repr_str += f" min {self.min_value:<10}"
        if self.max_value is not None:
            repr_str += f" max {self.max_value:<10}"
        return repr_str

    def get_definition(self, tab: str = "    ") -> str:
        """
        Get definition of this Tango attribute.

        https://tango-controls.readthedocs.io/projects/pytango/en/latest/how-to/server_old_api.html#defining-attributes

        :param tab: indentation string
        :returns: multi-line @attribute definition
        """
        attrib_defs: list = []
        attrib_defs.append(f"dtype={self.field_type}")
        attrib_defs.append(f"display_level=DispLevel.{self.display_level}")
        attrib_defs.append(f"access=AttrWriteType.{self.rw_type}")
        if self.min_value is not None:
            attrib_defs.append(f"min_value={self.min_value}")
        if self.max_value is not None:
            attrib_defs.append(f"max_value={self.max_value}")
        if self.min_alarm is not None:
            attrib_defs.append(f"min_alarm={self.min_alarm}")
        if self.max_alarm is not None:
            attrib_defs.append(f"max_alarm={self.max_alarm}")
        if self.min_warning is not None:
            attrib_defs.append(f"min_warning={self.min_warning}")
        if self.max_warning is not None:
            attrib_defs.append(f"max_warning={self.max_warning}")
        if self.delta_time is not None:
            attrib_defs.append(f"delta_time={self.delta_time}")
        if self.delta_value is not None:
            attrib_defs.append(f"delta_time={self.delta_time}")
        if self.label:
            attrib_defs.append(f'doc="{self.label}"')
        if self.get_set:
            attrib_defs.append(f"fget=get_{self.name}")
            attrib_defs.append(f"fisallowed={self.name}_is_allowed")
            if self.rw_type == "READ_WRITE":
                attrib_defs.append(f"fset=set_{self.name}")

        attrib_definitn: str = f"attribute({EOL}"
        for attrib_def in attrib_defs:
            attrib_definitn += f"{tab*2}{attrib_def},{EOL}"
        attrib_definitn += f'{tab}){EOL}'
        return attrib_definitn
