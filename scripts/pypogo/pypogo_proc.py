"""Generate Python code from XML file."""

# mypy: disable-error-code=attr-defined
# mypy: disable-error-code=operator
# mypy: disable-error-code=import-untyped

# pylint: disable-next=redefined-builtin
__package__ = "ska_mid_dish_spfc_builder"

import json
import logging
import subprocess
import sys

import xmltodict

from pypogo_code import PyPogoCodeMixin
from pypogo_pytest import PyPogoTestsMixin


class PyPogoPrintCode(PyPogoCodeMixin, PyPogoTestsMixin):
    """Generate Python code for a Tango device."""

    logger: logging.Logger
    cls_name: str

    def __init__(self, logger: logging.Logger, xml_input: str):
        """
        Generate the Python code.

        :param logger: logging handle
        :param xml_input: input file
        """
        self.logger = logger

        # Open XML file and read contents
        if xml_input == "-":
            py_xml = sys.stdin.read()
        else:
            with open(xml_input, "r", encoding="utf-8") as xfile:
                py_xml = xfile.read()
        self.logger.debug("Read XML from %s:\n%s", xml_input, py_xml)

        # Parse and convert XML document
        self.py_dict = xmltodict.parse(py_xml, attr_prefix="")
        self.cls_name = self.py_dict["pogoDsl:PogoSystem"]["classes"]["name"]

        self.py_class = self.py_dict["pogoDsl:PogoSystem"]["classes"]["name"]
        self.logger.info("Class : %s", self.py_class)
        self.logger.debug("XML dictionary:\n%s", json.dumps(self.py_dict, indent=4))

    def __repr__(self) -> str:
        """
        Do the string thing.

        :returns: dictionary string
        """
        return json.dumps(self.py_dict, indent=4)

    # pylint: disable-next=too-many-branches,too-many-statements
    def read_xml_attributes(self) -> dict:  # noqa: C901
        """
        Read dictionary derived from XML file.

        :returns: dictionary of attributes used to build code
        """
        attribs: dict = {}
        self.logger.info("Read attributes for class %s", self.cls_name)
        for attrib in self.py_dict["pogoDsl:PogoSystem"]["classes"]["attributes"]:
            attrib_name = attrib["name"]
            self.logger.info("Read attribute %s", attrib_name)
            self.logger.debug("Attribute %s : %s", attrib_name, json.dumps(attrib, indent=4))
            attribs[attrib_name] = {}
            attribs[attrib_name]["description"] = attrib["properties"]["description"]
            min_value: int | float | None = None
            max_value: int | float | None = None
            value: int | float | None = None
            if attrib["dataType"]["xsi:type"] == "pogoDsl:FloatType":
                field_type = "float"
                max_warning = attrib["properties"]["maxWarning"]
                if max_warning:
                    self.logger.debug("Max warning value '%s'", max_warning)
                    max_value = float(max_warning)
                    min_warning = attrib["properties"]["minWarning"]
                    if min_warning:
                        self.logger.debug("Min warning value '%s'", min_warning)
                        min_value = float(min_warning)
                        value = float((max_value - min_value) / 2)
                        self.logger.debug("Value %e", value)
            elif attrib["dataType"]["xsi:type"] == "pogoDsl:IntType":
                field_type = "int"
                max_warning = attrib["properties"]["maxWarning"]
                if max_warning:
                    self.logger.debug("Max warning value '%s'", max_warning)
                    max_value = int(max_warning)
                    min_warning = attrib["properties"]["minWarning"]
                    if min_warning:
                        self.logger.debug("Min warning value '%s'", min_warning)
                        min_value = int(min_warning)
                        value = int((max_value - min_value) / 2)
                        self.logger.debug("Value %d", value)
            elif attrib["dataType"]["xsi:type"] == "pogoDsl:EnumType":
                field_type = "int"
                min_value = 0
                max_value = len(attrib["enumLabels"]) - 1
            elif attrib["dataType"]["xsi:type"] == "pogoDsl:BooleanType":
                field_type = "bool"
            elif attrib["dataType"]["xsi:type"] == "pogoDsl:ShortType":
                field_type = "int"
            elif attrib["dataType"]["xsi:type"] == "pogoDsl:UShortType":
                field_type = "int"
            elif attrib["dataType"]["xsi:type"] == "pogoDsl:StringType":
                field_type = "str"
            else:
                field_type = "None"
            if attrib["rwType"] == "READ" or attrib["rwType"] == "READ_WRITE":
                attribs[attrib_name]["read"] = {}
                attribs[attrib_name]["read"]["field_type"] = field_type
                attribs[attrib_name]["read"]["value"] = value
                attribs[attrib_name]["read"]["max_value"] = max_value
                attribs[attrib_name]["read"]["min_value"] = min_value
            if attrib["rwType"] == "WRITE" or attrib["rwType"] == "READ_WRITE":
                attribs[attrib_name]["write"] = {}
                attribs[attrib_name]["write"]["field_type"] = field_type
                attribs[attrib_name]["write"]["value"] = value
                attribs[attrib_name]["write"]["max_value"] = max_value
                attribs[attrib_name]["write"]["min_value"] = min_value
        self.logger.debug("Attributes from XML:\n%s", json.dumps(attribs, indent=4))
        return attribs

    # pylint: disable-next=too-many-branches,too-many-statements
    def read_xml_commands(self) -> dict:  # noqa: C901
        """
        Read dictionary derived from XML file.

        :returns: dictionary of commands used to build code
        """

        def get_arg_type(cmd_arg) -> str:
            """
            Get argument type.

            :param cmd_arg: XSI type (from XML)
            :returns: argument type
            """
            if cmd_arg == "pogoDsl:VoidType":
                dtype = "None"
            elif cmd_arg in ("pogoDsl:StringType", "pogoDsl:ConstStringType"):
                dtype = "str"
            elif cmd_arg in (
                "pogoDsl:UShortType", "pogoDsl:StateType", "pogoDsl:EnumType"
            ):
                dtype = "int"
            else:
                self.logger.warning("Unknown argin %s", cmd_argin)
                dtype = "None"
            self.logger.debug("Map %s to %s", cmd_arg, dtype)
            return dtype


        self.logger.info("Read commands for class %s", self.cls_name)
        cmds: dict = {}
        for cmd in self.py_dict["pogoDsl:PogoSystem"]["classes"]["commands"]:
            cmd_name = cmd["name"]
            cmds[cmd_name] = {}
            cmds[cmd_name]["description"] = cmd["description"]
            cmds[cmd_name]["dtype_in"] = get_arg_type(cmd["argin"]["type"]["xsi:type"])
            cmds[cmd_name]["dtype_out"] = get_arg_type(cmd["argout"]["type"]["xsi:type"])
            cmds[cmd_name]["displayLevel"] = cmd["displayLevel"]
            cmds[cmd_name]["polledPeriod"] = cmd["polledPeriod"]
        self.logger.debug("Commands from XML:\n%s", json.dumps(cmds, indent=4))
        return cmds

    def format_with_black(self, file_name: str, line_length: int = 99) -> None:
        """
        Format Python code file using the Black formatter via subprocess.

        :param file_name: Python code file
        :param line_length: columns per line
        """
        cmd_line = ["black", "--line-length", f"{line_length}", file_name]
        self.logger.info("Run: %s", " ".join(cmd_line))
        try:
            subprocess.run(cmd_line, check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error("Error formatting code: %s", e.stderr.decode("utf-8"))
