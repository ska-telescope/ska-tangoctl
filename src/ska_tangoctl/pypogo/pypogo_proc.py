"""Generate Python code from XML file."""

# mypy: disable-error-code=attr-defined
# mypy: disable-error-code=operator
# mypy: disable-error-code=import-untyped

# pylint: disable-next=redefined-builtin
__package__ = "ska_mid_dish_spfc_builder"

import json
import logging
import os
import subprocess
import sys
from typing import AnyStr

import yaml

import xmltodict

from ska_tangoctl.pypogo.pypogo_code import PyPogoCodeMixin
from ska_tangoctl.pypogo.pypogo_pytest import PyPogoTestsMixin
from ska_tangoctl.pypogo.pypogo_testeq import PyPogoTestEquipmentMixin
from ska_tangoctl.pypogo.pypogo_attribute import PyPogoAttribute


class PyPogoPrintCode(PyPogoCodeMixin, PyPogoTestsMixin, PyPogoTestEquipmentMixin):
    """Generate Python code for a Tango device."""

    logger: logging.Logger
    cls_name: str
    default_type: str
    tab: str

    def __init__(self, logger: logging.Logger, default_type: str, get_set: bool):
        """
        Generate the Python code.

        :param logger: logging handle
        :param default_type: use this type when none is specified
        :param get_set: use getter and setter functions
        """
        self.logger = logger
        self.default_type = default_type
        self.get_set = get_set
        self.py_dict = {}
        self.tab = "    "

    def read_xml_file(self, input_file: str | None) -> int:
        """
        Open XML file and read contents.

        :param input_file: input file in XML format
        :returns: error condition
        """
        py_xml: AnyStr
        if input_file is None:
            self.logger.error("Input file name not specified")
            return 1
        if input_file == "-":
            py_xml = sys.stdin.read()
        else:
            with open(input_file, "r", encoding="utf-8") as xfile:
                py_xml = xfile.read()
        self.logger.debug("Read XML from %s:\n%s", input_file, py_xml)
        if py_xml:
            # Parse and convert XML document
            self.py_dict = xmltodict.parse(py_xml, attr_prefix="")
            self.cls_name = self.py_dict["pogoDsl:PogoSystem"]["classes"]["name"]
            self.logger.info("Read class %s with %d items", self.cls_name, len(self.py_dict))
        else:
            self.py_dict = {}
            self.logger.error("No data read from %s", input_file)
            return 1
        return 0

    def read_yaml_file(self, input_file: str | None) -> int:
        """
        Open XML file and read contents.

        :param input_file: input file in XML format
        :returns: error condition
        """
        py_yaml: AnyStr
        if input_file is None:
            self.logger.error("Input file name not specified")
            return 1
        if input_file == "-":
            py_yaml = sys.stdin.read()
        else:
            with open(input_file, "r", encoding="utf-8") as yfile:
                py_yaml = yfile.read()
        self.logger.debug("Read YAML from %s:\n%s", input_file, py_yaml)
        if py_yaml:
            self.py_dict = yaml.safe_load(py_yaml)
        return 0

    def read_file(self, input_file: str | None) -> int:
        """
        Open XML file and read contents.

        :param input_file: input file in XML format
        :returns: error condition
        """
        py_yaml: AnyStr
        rc: int = 0
        if input_file is None:
            self.logger.error("Input file name not specified")
            return 1
        if input_file == "-":
            # TODO assume that stdin is in XML format
            self.read_xml_file(input_file)
        else:
            file_name, file_ext = os.path.splitext(input_file)
            self.logger.info("Read file %s of type %s", file_name, file_ext)
            if file_ext in (".xmi", ".xml"):
                rc = self.read_xml_file(input_file)
            elif file_ext in (".yml", ".yaml"):
                self.cls_name = os.path.basename(file_name)
                self.logger.info("Read YAML for class %s", self.cls_name)
                rc = self.read_xml_file(input_file)
            else:
                self.logger.error("Can not read file with extionsion %s as XML", file_ext)
                return 1
        self.logger.debug("Input dictionary:\n%s", json.dumps(self.py_dict, indent=4))
        return rc

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
        for attribute in self.py_dict["pogoDsl:PogoSystem"]["classes"]["attributes"]:
            attrib = PyPogoAttribute(self.logger, attribute, self.default_type, self.get_set)
            self.logger.info("Read attribute %s", attrib)
            attrib_name = attrib.name
            attribs[attrib_name] = attrib
        self.logger.debug("Read %d attributes from XML", len(attribs))
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
                self.logger.warning("Unknown argument %s", cmd_arg)
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
