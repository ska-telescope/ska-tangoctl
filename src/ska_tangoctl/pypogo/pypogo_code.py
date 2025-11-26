"""Generate test code for instrument."""

# mypy: disable-error-code="attr-defined,union-attr"

import inspect
import json
import logging
import os
import sys
import textwrap
from typing import Any

from abc import ABC, abstractmethod

from ska_tangoctl.pypogo.pypogo_globals import CURRENT_TIME, DEFAULT_VALUE, EOL, HOME_PATH, PYTHON_PATH, TAB
from ska_tangoctl.pypogo.pypogo_attribute import PyPogoAttribute


class PyPogoCodeMixin(ABC):
    """Generate code for Python tests."""

    logger: logging.Logger
    skip_tests: bool = False
    ofstream: Any
    cls_name: str
    py_dict: dict
    protected_attributes: dict = {}
    protected_commands: dict = {}
    default_type: str
    get_set: bool
    tab: str

    @abstractmethod
    def read_xml_attributes(self):
        """Stub for the function in the enclosing class."""
        pass

    @abstractmethod
    def read_xml_commands(self):
        """Stub for the function in the enclosing class."""
        pass

    @abstractmethod
    def format_with_black(self, file_path):
        """Stub for the function in the enclosing class."""
        pass

    # TODO deprecated
    # def init_protected_attributes(self, attributes: dict, special_attributes: dict) -> None:
    #     """
    #     Initialize protected attributes.
    #
    #     :param attributes: list of dictionaries with attribute definitions
    #     :param special_attributes: special cases that are skipped for now
    #     """
    #     attribute: PyPogoAttribute
    #     for attrib_name in attributes:
    #         attribute = attributes[attrib_name]
    #         if attrib_name in special_attributes:
    #             self.logger.error("Skip special attribute %s ", attrib_name)
    #         elif attribute.rw_type == "READ_WRITE":
    #             self.protected_attributes[f"{self.cls_name}.{attrib_name}.read"] = ""
    #             self.protected_attributes[f"{self.cls_name}.{attrib_name}.write"] = ""
    #             self.protected_attributes[f"{self.cls_name}.{attrib_name}.read_is_allowed"] = ""
    #             self.protected_attributes[f"{self.cls_name}.{attrib_name}.write_is_allowed"] = ""
    #         elif attribute.rw_type == "READ":
    #             self.protected_attributes[f"{self.cls_name}.{attrib_name}.read"] = ""
    #             self.protected_attributes[f"{self.cls_name}.{attrib_name}.read_is_allowed"] = ""
    #         else:
    #             pass
    #     self.protected_attributes[f"{self.cls_name}.adminMode.read"] = ""
    #     self.protected_attributes[f"{self.cls_name}.adminMode.write"] = ""
    #     self.logger.debug(
    #         "Protected attributes:\n%s", json.dumps(self.protected_attributes, indent=4)
    #     )

    def init_protected_commands(self, commands: dict) -> None:
        """
        Initialize protected commands.

        :param commands: dictionary with command definitions
        """
        for cmd_name in commands:
            self.protected_commands[cmd_name] = ""
        self.logger.debug(
            "Protected commands:\n%s", json.dumps(self.protected_commands, indent=4)
        )

    def read_protected_attributes(self, py_file_name: str | None) -> None:
        """
        Read code for protected attributes.

        :param py_file_name: file name
        """
        if not os.path.isfile(py_file_name):
            self.logger.warning("File %s does not exist", py_file_name)
            return
        py_code: str = ""
        py_key: str = ""
        self.logger.info("Read code file %s", py_file_name)
        with open(py_file_name, "r", encoding="utf-8") as py_file:
            for py_line in py_file:
                py_line = py_line.rstrip()
                self.logger.debug("Read code line '%s'", py_line)
                if "# PROTECTED ATTRIBUTE (" in py_line and py_line[-5:] == "START":
                    # Find the index of the opening bracket
                    start_index = py_line.find('(')

                    # Find the index of the closing bracket after the opening bracket
                    end_index = py_line.find(')', start_index)

                    # Check if both brackets were found
                    if start_index != -1 and end_index != -1:
                        # Extract the substring
                        py_key = py_line[start_index + 1 : end_index]
                        # print(py_key)
                        self.logger.debug("Start PROTECTED ATTRIBUTE '%s'", py_key)
                elif "# PROTECTED ATTRIBUTE END" in py_line:
                    self.logger.debug("End PROTECTED ATTRIBUTE '%s' :\n%s", py_key, py_code)
                    self.protected_attributes[py_key] = py_code
                    py_key = ""
                    py_code = ""
                elif py_key:
                    py_code += f'{py_line}{EOL}'
                else:
                    pass
        self.logger.debug(
            "Read PROTECTED ATTRIBUTES:\n%s", json.dumps(self.protected_attributes, indent=4)
        )

    def read_protected_commands(self, py_file_name: str | None) -> None:
        """
        Read code for protected attributes.

        :param py_file_name: file name
        """
        if not os.path.isfile(py_file_name):
            self.logger.warning("File %s does not exist", py_file_name)
            return
        py_code: str = ""
        py_key: str = ""
        self.logger.info("Read code file %s", py_file_name)
        with open(py_file_name, "r", encoding="utf-8") as py_file:
            for py_line in py_file:
                py_line = py_line.rstrip()
                self.logger.debug("Read code line '%s'", py_line)
                if "# PROTECTED COMMAND (" in py_line and py_line[-5:] == "START":
                    # Find the index of the opening bracket
                    start_index = py_line.find('(')

                    # Find the index of the closing bracket after the opening bracket
                    end_index = py_line.find(')', start_index)

                    # Check if both brackets were found
                    if start_index != -1 and end_index != -1:
                        # Extract the substring
                        py_key = py_line[start_index + 1 : end_index]
                        # print(py_key)
                        self.logger.debug("Start PROTECTED COMMAND '%s'", py_key)
                elif "# PROTECTED COMMAND END" in py_line:
                    self.logger.debug("End PROTECTED COMMAND '%s' :\n%s", py_key, py_code)
                    self.protected_commands[py_key] = py_code
                    py_key = ""
                    py_code = ""
                elif py_key:
                    py_code += f'{py_line}{EOL}'
                else:
                    pass
        self.logger.debug(
            "Read PROTECTED COMMANDS:\n%s", json.dumps(self.protected_commands, indent=4)
        )

    def print_component_manager(self):
        """
        Print code for component manager.
        """
        print(
            f'class {self.cls_name}CM:{EOL}'
            f'{TAB}"""Component manager for {self.cls_name}."""{EOL}'
            f'{EOL}'
            f'{TAB}logger: logging.Logger{EOL}'
            f'{TAB}max_executing_tasks = 1{EOL}'
            f'{TAB}max_queued_tasks = 0{EOL}'
            f'{EOL}'
            f'{TAB}def __init__(self) -> None:{EOL}'
            f'{TAB}{TAB}"""You can start me up."""{EOL}'
            f'{EOL}'
            f'{TAB}def start_communicating(self) -> None:{EOL}'
            f'{TAB}{TAB}"""Start communication."""{EOL}'
            f'{TAB}{TAB}self.logger.info("Start communicating"){EOL}'
            f'{EOL}'
            f'{TAB}def stop_communicating(self) -> None:{EOL}'
            f'{TAB}{TAB}"""Stop communication."""{EOL}'
            f'{TAB}{TAB}self.logger.info("Stop communicating")  {EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_file_header(self, co_file: str) -> None:
        """
        Print start of file with imports e.a.

        :param co_file: file name
        """
        print(
            f'#!/usr/bin/env python{EOL}'
            f'"""{EOL}'
            f'Implement Tango device.{EOL}'
            f'{EOL}'
            f'Last update {CURRENT_TIME} by {inspect.currentframe().f_code.co_name}{EOL}'
            f'See {co_file}{EOL}'
            f'"""{EOL}'
            f'{EOL}'
            f'# pylint:disable=too-many-lines{EOL}'
            f'# pylint:disable=too-many-instance-attributes{EOL}'
            f'# pylint:disable=too-many-public-methods{EOL}'
            f'# pylint:disable=duplicate-code{EOL}'
            f'# pylint:disable=line-too-long{EOL}'
            f'# pylint:disable=invalid-name{EOL}'
            f'{EOL}'
            f'import ast{EOL}'
            f'import logging{EOL}'
            f'import os{EOL}'
            f'import sys{EOL}'
            f'from typing import Any{EOL}'
            f'{EOL}'
            f'import tango{EOL}'
            f'from ska_control_model import AdminMode{EOL}'
            f'from ska_tango_base import SKABaseDevice{EOL}'
            f'from tango import AttReqType, AttrWriteType, DispLevel{EOL}'
            f'from tango.server import attribute, command{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_create_component_manager(self) -> None:
        """
        Print code to create component manager.
        """
        print(
            f'{TAB}def create_component_manager(self) -> Any:{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{TAB}{TAB}Create and return a component manager for this device.{EOL}'
            f'{EOL}'
            f'{TAB}{TAB}:returns: a component manager for this device.{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{TAB}{TAB}# pylint: disable-next=fixme{EOL}'
            f'{TAB}{TAB}# TODO this causes an error in SKABaseDevice{EOL}'
            f'{TAB}{TAB}self.logger.warning("Dummy component manager"){EOL}'
            f'{TAB}{TAB}cm = {self.cls_name}CM(){EOL}'
            f'{TAB}{TAB}cm.logger = self.logger{EOL}'
            f'{TAB}{TAB}return cm{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_class_header(self) -> None:
        """
        Print start of class.
        """
        print(
            f'class {self.cls_name}(SKABaseDevice):{EOL}'
            f'{TAB}"""Implementation of yet another Tango device."""{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_vars(self, attributes: dict, special_attributes: dict) -> None:
        """
        Print code to initialise the variables.

        :param attributes: dictionary with attribute definitions
        :param special_attributes: special cases that are skipped for now
        """

        def default_value(f_type, f_value) -> str:
            if f_type == "str":
                if f_value is not None:
                    return '"{f_value}"'
                return '""'
            if f_value is not None:
                return f"{f_value}"
            if f_type == "bool":
                return "False"
            if f_type == "int":
                return "sys.maxsize"
            if f_type == "float":
                return 'float("nan")'
            return DEFAULT_VALUE

        attribute: PyPogoAttribute
        print(f'{TAB}_admin_mode: AdminMode{EOL}', file=self.ofstream, end="")
        for name in attributes:
            attribute = attributes[name]
            attrib_name = attribute.name
            if attrib_name in special_attributes:
                self.logger.error("Skip special attribute %s ", attrib_name)
            elif attribute.rw_type == "READ_WRITE":
                print(
                    f'{TAB}_{attrib_name}: {attribute.field_type}'
                    f' = {default_value(attribute.field_type, attribute.value)}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            elif attribute.rw_type == "READ":
                print(
                    f'{TAB}_{attrib_name}: {attribute.field_type}'
                    f' = {default_value(attribute.field_type, attribute.value)}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            else:
                self.logger.error("Skip attribute type %s", attribute.rw_type)
        print(f'{EOL}', file=self.ofstream, end="")

    # def print_admin_mode(self):
    #     """Print code to set admin mode for the device."""
    #     atrr_id = f"{self.cls_name}.adminMode.read"
    #     prot_code: str = ""
    #     if atrr_id in self.protected_attributes:
    #         prot_code = self.protected_attributes[atrr_id]
    #     if not prot_code:
    #         prot_code = f'{TAB}{TAB}return self._adminMode{EOL}'
    #     print(
    #         f'{TAB}@attribute(dtype=bool){EOL}'
    #         f'{TAB}def adminMode(self) -> bool:{EOL}'
    #         f'{TAB}{TAB}"""{EOL}'
    #         f'{TAB}{TAB}Get admin mode.{EOL}'
    #         f'{EOL}'
    #         f'{TAB}{TAB}:returns: current admin mode{EOL}'
    #         f'{TAB}{TAB}"""{EOL}'
    #         f'{TAB}{TAB}# PROTECTED ATTRIBUTE ({self.cls_name}.adminMode) START{EOL}'
    #         f'{prot_code}'
    #         f'{TAB}{TAB}# PROTECTED ATTRIBUTE END{EOL}'
    #         f'{EOL}',
    #         file=self.ofstream,
    #         end="",
    #     )
    #     atrr_id = f"{self.cls_name}.adminMode.write"
    #     prot_code: str = ""
    #     if atrr_id in self.protected_attributes:
    #         prot_code = self.protected_attributes[atrr_id]
    #     if not prot_code:
    #         prot_code = (
    #             f'{TAB}{TAB}self.logger.debug("Set adminMode to %s", value){EOL}'
    #             f'{TAB}{TAB}self._adminMode = value{EOL}'
    #         )
    #     print(
    #         f'{TAB}@adminMode.write{EOL}'
    #         f'{TAB}def adminMode(self, value: bool) -> None:{EOL}'
    #         f'{TAB}{TAB}"""{EOL}'
    #         f'{TAB}{TAB}Set admin mode.{EOL}'
    #         f'{EOL}'
    #         f'{TAB}{TAB}"""{EOL}'
    #         f'{TAB}{TAB}# PROTECTED ATTRIBUTE ({self.cls_name}.adminMode.write) START{EOL}'
    #         f'{prot_code}'
    #         f'{TAB}{TAB}# PROTECTED ATTRIBUTE END{EOL}'
    #         f'{EOL}',
    #         file=self.ofstream,
    #         end="",
    #     )

    def get_description_lines(
        self,
        tgo_name: str,
        decscrptn: str,
        actn: str,
        tgo_thing: str,
        line_length,
    ) -> list:
        """
        Set description for use in comments.

        :param tgo_name: attribute name
        :param decscrptn: attribute decscrption
        :param actn: what is being done
        :param tgo_thing: attribute, command or property
        :param line_length: number of characters
        :returns: updated description
        """
        decscrptns: list = []
        if not decscrptn:
            decscrptns.append(f"{actn} Tango {tgo_thing} {tgo_name}.")
        elif f"{EOL}" in decscrptn:
            decscrptns.append(f"{actn} Tango {tgo_thing} {tgo_name}.")
            decscrptns.append("")
            for dline in decscrptn.split(EOL):
                decscrptns.append(dline)
        elif len(decscrptn) > line_length:
            decscrptns.append(f"{actn} Tango {tgo_thing} {tgo_name}.")
            decscrptns.append("")
            new_desc = textwrap.wrap(decscrptn, width=line_length)
            for newd in new_desc:
                decscrptns.append(newd)
        else:
            if decscrptn[-1] != ".":
                decscrptn += "."
            decscrptns.append(decscrptn)
        self.logger.debug("Descriptions for %s : %s", tgo_name, decscrptns)
        return decscrptns

    def get_description(
        self,
        tgo_name: str,
        decscrptn: str,
        actn: str,
        tgo_thing: str,
        tab: str,
        dstart: str | None = None,
        dend: str | None = None,
        dline: str | None = None,
        line_length = 80,
    ) -> str:
        """
        Set description for use in comments.

        :param tgo_name: attribute name
        :param decscrptn: attribute decscrption
        :param actn: what is being done
        :param tgo_thing: attribute, command or property
        :param tab: line it up
        :param dstart: start of block
        :param dend: end of block
        :param dline: start of line
        :param line_length: number of characters
        :returns: updated description
        """
        sdecscrptn: str
        decscrptns = self.get_description_lines(tgo_name, decscrptn, actn, tgo_thing, line_length)
        if len(decscrptns) == 1:
            if (dstart is not None) and (dend is not None):
                sdecscrptn = f"{tab}{dstart}{decscrptns[0]}{dend}{EOL}"
            elif dline is not None:
                sdecscrptn = f"{tab}{dline}{decscrptns[0]}{EOL}"
            else:
                sdecscrptn = f"{tab}{decscrptns[0]}{EOL}"
        elif dline is not None:
            sdecscrptn = ""
            for decscrptn in decscrptns:
                sdecscrptn += f"{tab}{dline}{decscrptn}{EOL}"
        elif (dstart is not None) and (dend is not None):
            sdecscrptn = f"{tab}{dstart}{EOL}"
            for decscrptn in decscrptns:
                sdecscrptn += f"{tab}{decscrptn}{EOL}"
            sdecscrptn += f"{tab}{dend}{EOL}"
        else:
            sdecscrptn = ""
            for decscrptn in decscrptns:
                sdecscrptn += f"{tab}{decscrptn}{EOL}"
        self.logger.debug("Description for %s : %s", tgo_name, sdecscrptn)
        return sdecscrptn.replace("*", "")


    def print_attribute(
        self,
        attrib_name: str,
        attrib_def: str,
        decscrptn: str,
    ) -> None:
        """
        Write code for reading Python attribute.

        :param attrib_name: attribute name
        :param attrib_def: attribute defintion
        :param decscrptn: attribute decscrption
        """
        decscrptn = self.get_description(attrib_name, decscrptn, "Add", "attribute", TAB, None, None, "# ")
        print(
            f'{decscrptn}'
            f'{TAB}{attrib_name} = {attrib_def}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_read(
        self,
        attrib_name: str,
        attrib_def: str,
        decscrptn: str,
        field_type: str,
    ) -> None:
        """
        Write code for reading Python attribute.

        :param attrib_name: attribute name
        :param attrib_def: attribute defintion
        :param decscrptn: attribute decscrption
        :param field_type: data type, e.g. int, str, float...
        """
        decscrptn = self.get_description(attrib_name, decscrptn, "Read", "attribute", TAB*2)
        atrr_id = f"{self.cls_name}.{attrib_name}.read"
        self.logger.info("Read %s : %s", atrr_id, decscrptn)
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
            self.logger.debug("Read %s code:\n%s", atrr_id, prot_code)
        if not prot_code:
            if self.get_set:
                prot_code = (
                    f'{TAB}{TAB}value = self.get_{attrib_name}(){EOL}'
                    f'{TAB}{TAB}self.logger.debug("Value of {attrib_name} is %s", str(value)){EOL}'
                )
            else:
                prot_code = (
                    f'{TAB}{TAB}value = self._{attrib_name}{EOL}'
                    f'{TAB}{TAB}self.logger.debug("Value of {attrib_name} is %s", str(value)){EOL}'
                )
            if field_type == "int":
                prot_code += (
                    f'{TAB}{TAB}if value == sys.maxsize:{EOL}'
                    f'{TAB}{TAB}{TAB}self.logger.warning("Attribute {attrib_name} not initialised"){EOL}'
                )
            elif field_type == "float":
                prot_code += (
                    f'{TAB}{TAB}if math.isnan(value):{EOL}'
                    f'{TAB}{TAB}{TAB}self.logger.warning("Attribute {attrib_name} not initialised"){EOL}'
                )
            elif field_type == "str":
                prot_code += (
                    f'{TAB}{TAB}if value == "":{EOL}'
                    f'{TAB}{TAB}{TAB}self.logger.warning("Attribute {attrib_name} not initialised"){EOL}'
                )
            elif field_type == "bool":
                pass
            else:
                prot_code += (
                    f'{TAB}{TAB}if value is None:{EOL}'
                    f'{TAB}{TAB}{TAB}self.logger.warning("Attribute {attrib_name} not initialised"){EOL}'
                )
        print(
            f'{TAB}@{attrib_def}'
            f'{TAB}def {attrib_name}(self) -> {field_type}:{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{decscrptn}'
            f'{EOL}'
            f'{TAB}{TAB}:returns: value of {attrib_name}{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{TAB}{TAB}value: {field_type}{EOL}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE ({atrr_id}) START{EOL}'
            f'{prot_code}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE END{EOL}'
            f'{TAB}{TAB}return value{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_read_is_allowed(self, attrib_name: str, decscrptn: str, field_type: str) -> None:
        """
        Write code for reading Python attribute.

        :param attrib_name: attribute name
        :param decscrptn: attribute decscrption
        :param field_type: data type, e.g. int, str, float...
        """
        decscrptn = self.get_description(attrib_name, decscrptn, "Check read", "attribute", TAB*2)
        atrr_id = f"{self.cls_name}.{attrib_name}.read_is_allowed"
        self.logger.info("Read %s allowed", atrr_id)
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
            self.logger.debug("Read %s code:\n%s", atrr_id, prot_code)
        if not prot_code:
            prot_code = f'{TAB}{TAB}return self._admin_mode == AdminMode.ONLINE{EOL}'
        if not self.get_set:
            print(
                f'{TAB}@{attrib_name}.is_allowed{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'{TAB}# pylint: disable-next=unused-argument{EOL}'
            f'{TAB}def {attrib_name}_is_allowed(self, request_type: Any) -> bool:{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{decscrptn}'
            f'{EOL}'
            f'{TAB}{TAB}:param request_type: read or write{EOL}'
            f'{TAB}{TAB}:returns: operation can proceed{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE ({atrr_id}) START{EOL}'
            f'{prot_code}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE END{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_getter(self, attrib_name: str, field_type: str):
        """
        Write code for reading Python attribute.

        :param attrib_name: attribute name
        :param field_type: data type, e.g. int, str, float...
        """
        atrr_id = f"{self.cls_name}.{attrib_name}.get"
        print(
            f'{TAB}def get_{attrib_name}(self) -> {field_type}:{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{TAB}{TAB}Get value of attribute {attrib_name}.{EOL}'
            f'{EOL}'
            f'{TAB}{TAB}:returns: attribute value{EOL}'
            f'{TAB}{TAB}"""{EOL}',
            file=self.ofstream,
            end="",
        )
        print(
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE ({atrr_id}) START{EOL}'
            f'{TAB}{TAB}value: {field_type} = self._{attrib_name}{EOL}'
            f'{TAB}{TAB}self.logger.debug("Value of {attrib_name} is %s", str(value)){EOL}'
            f'{TAB}{TAB}return value{EOL}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE END{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_write(self, attrib_name: str, decscrptn: str, field_type: str) -> None:
        """
        Write code for writing Python attribute.

        :param attrib_name: attribute name
        :param decscrptn: attribute decscrption
        :param field_type: data type, e.g. int, str, float...
        """
        decscrptn = self.get_description(attrib_name, decscrptn, "Write", "attribute", TAB*2)
        atrr_id = f"{self.cls_name}.{attrib_name}.write"
        self.logger.info("Write %s : %s", atrr_id, decscrptn)
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
            self.logger.debug("Write %s code:\n%s", atrr_id, prot_code)
        if not prot_code:
            if self.get_set:
                prot_code = (
                    f'{TAB}{TAB}self.logger.debug("Set {attrib_name} to %s", str(value)){EOL}'
                    f'{TAB}{TAB}self.set_{attrib_name}(value){EOL}'
                )
            else:
                prot_code = (
                    f'{TAB}{TAB}self.logger.debug("Set {attrib_name} to %s", str(value)){EOL}'
                    f'{TAB}{TAB}self._{attrib_name} = value{EOL}'
                )
        print(
            f'{TAB}@{attrib_name}.write  # type: ignore[no-redef]{EOL}'
            f'{TAB}def {attrib_name}(self, value: {field_type}) -> None:{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{decscrptn}'
            f'{EOL}'
            f'{TAB}{TAB}:param value: change to this{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE ({atrr_id}.write) START{EOL}'
            f'{prot_code}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE END{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_write_is_allowed(
        self, attrib_name: str, decscrptn: str, field_type: str
    ) -> None:
        """
        Write code for reading Python attribute.

        :param attrib_name: attribute name
        :param decscrptn: attribute decscrption
        :param field_type: data type, e.g. int, str, float...
        """
        decscrptn = self.get_description(attrib_name, decscrptn, "Check write", "attribute", TAB*2)
        atrr_id = f"{self.cls_name}.{attrib_name}.write_is_allowed"
        self.logger.info("Write %s is allowed", atrr_id)
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
            self.logger.debug("Read %s code:\n%s", atrr_id, prot_code)
        if not prot_code:
            prot_code = (
                f'{TAB}{TAB}if request_type == AttReqType.READ_REQ:{EOL}'
                f'{TAB}{TAB}{TAB}return self._admin_mode == AdminMode.ONLINE{EOL}'
                f'{TAB}{TAB}return self._admin_mode == AdminMode.ONLINE{EOL}'
            )
        if not self.get_set:
            print(
                f'{TAB}@{attrib_name}.is_allowed{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'{TAB}def {attrib_name}_is_allowed(self, request_type: Any) -> bool:{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{decscrptn}'
            f'{EOL}'
            f'{TAB}{TAB}:param request_type: read or write{EOL}'
            f'{TAB}{TAB}:returns: operation can proceed{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE ({atrr_id}) START{EOL}'
            f'{prot_code}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE END{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_setter(self, attrib_name: str, field_type: str):
        """
        Write code for writing Python attribute.

        :param attrib_name: attribute name
        :param field_type: data type, e.g. int, str, float...
        """
        atrr_id = f"{self.cls_name}.{attrib_name}.set"
        print(
            f'{TAB}def set_{attrib_name}(self, value: {field_type}) -> None:{EOL}'
            f'{TAB}{TAB}"""{EOL}'
            f'{TAB}{TAB}Set value of attribute {attrib_name}.{EOL}'
            f'{EOL}'
            f'{TAB}{TAB}:param value: new attribute value{EOL}'
            f'{TAB}{TAB}"""{EOL}',
            file=self.ofstream,
            end="",
        )
        print(
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE ({atrr_id}) START{EOL}'
            f'{TAB}{TAB}self._{attrib_name} = value{EOL}'
            f'{TAB}{TAB}self.logger.debug("Value of {attrib_name} set to %s", str(value)){EOL}'
            f'{TAB}{TAB}# PROTECTED ATTRIBUTE END{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attributes_code(self, attributes: dict, special_attributes: dict) -> None:
        """
        Write code for Python attribute.

        :param attributes: dictionary with attribute definitions
        :param special_attributes: special cases that are skipped for now
        """
        self.logger.info("Print %d Tango attributes", len(attributes))
        attribute: PyPogoAttribute
        for name in attributes:
            attribute = attributes[name]
            attrib_name = attribute.name
            decscrptn = attribute.description
            field_type = attribute.field_type
            rw_type = attribute.rw_type
            if attrib_name in special_attributes:
                self.logger.error("Skip special attribute %s ", attrib_name)
            elif rw_type == "READ_WRITE":
                attrib_def: str = attribute.get_definition()
                if self.get_set:
                    self.print_attribute_getter(attrib_name, field_type)
                    self.print_attribute_setter(attrib_name, field_type)
                    self.print_attribute_write_is_allowed(attrib_name, decscrptn, field_type)
                    self.print_attribute(attrib_name, attrib_def, decscrptn)
                else:
                    self.print_attribute_read(attrib_name, attrib_def, decscrptn, field_type)
                    self.print_attribute_write(attrib_name, decscrptn, field_type)
                    self.print_attribute_write_is_allowed(attrib_name, decscrptn, field_type)
            elif rw_type == "READ":
                attrib_def: str = attribute.get_definition()
                if self.get_set:
                    self.print_attribute_getter(attrib_name, field_type)
                    self.print_attribute_read_is_allowed(attrib_name, decscrptn, field_type)
                    self.print_attribute(attrib_name, attrib_def, decscrptn)
                else:
                    self.print_attribute_read(attrib_name, attrib_def, decscrptn, field_type)
                    self.print_attribute_read_is_allowed(attrib_name, decscrptn, field_type)
            elif rw_type == "WRITE":
                # field_type = attributes[attrib_name]["write"]["field_type"]
                # self.print_command(attrib_name, decscrptn, field_type)
                self.logger.warning("Write-only attribute %s skipped", attrib_name)
            else:
                self.logger.error("Attribute %s has no read or write values", attrib_name)

    def print_command_code(
        self, cmd_name: str, decscrptn: str, dtype_in: str, dtype_out: str
    ) -> None:
        """
        Write code for Python command.

        :param cmd_name: attribute name
        :param decscrptn: attribute descrption
        :param dtype_in: data type, e.g. int, str, float...
        :param dtype_out: data type, e.g. int, str, float...
        """
        dtype_spec: str
        if dtype_in != "None" and dtype_out != "None":
            dtype_spec = f"dtype_in={dtype_in}, dtype_out={dtype_out}"
        elif dtype_in != "None":
            dtype_spec = f"dtype_in={dtype_in}"
        elif dtype_out != "None":
            dtype_spec = f"dtype_out={dtype_out}"
        else:
            dtype_spec = ""
        if dtype_in != "None":
            decscrptn = self.get_description(cmd_name, decscrptn, "Run", "command", TAB*2)
            print(
                f'{TAB}@command({dtype_spec}){EOL}'
                f'{TAB}def {cmd_name}(self, args: {dtype_in}) -> {dtype_out}:{EOL}'
                f'{TAB}{TAB}"""{EOL}'
                f'{decscrptn}'
                f'{EOL}'
                f'{TAB}{TAB}:param args: command argument(s){EOL}',
                file=self.ofstream,
                end="",
            )
            if dtype_out != "None":
                print(f'{TAB}{TAB}:returns: {dtype_out} value{EOL}', file=self.ofstream, end="")
            print(
                f'{TAB}{TAB}:raises Exception: error{EOL}'
                f'{TAB}{TAB}"""{EOL}',
                file=self.ofstream,
                end="",
            )
            print(
                f'{TAB}{TAB}# PROTECTED COMMAND ({self.cls_name}.{cmd_name}) START{EOL}'
                f'{TAB}{TAB}self.logger.info("Run command {cmd_name}(%s)"){EOL}'
                f'{TAB}{TAB}kwargs = ast.literal_eval(args){EOL}'
                f'{TAB}{TAB}try:{EOL}'
                f'{TAB}{TAB}{TAB}value = kwargs["value"]{EOL}'
                f'{TAB}{TAB}except Exception as kerr:{EOL}'
                f'{TAB}{TAB}{TAB}self.logger.error("Could not read arguments: %s", kerr){EOL}'
                f'{TAB}{TAB}{TAB}raise kerr{EOL}'
                f'{TAB}{TAB}self.logger.info("Load value %s", str(value)){EOL}'
                f'{TAB}{TAB}# TODO add code for command {cmd_name}{EOL}',
                file=self.ofstream,
                end="",
            )
            if dtype_out == "None":
                pass
            elif dtype_out == "str":
                print(f'{TAB}{TAB}return ""{EOL}', file=self.ofstream, end="")
            elif dtype_out == "int":
                print(f'{TAB}{TAB}return 0{EOL}', file=self.ofstream, end="")
            elif dtype_out == "float":
                print(f'{TAB}{TAB}return 0.0{EOL}', file=self.ofstream, end="")
            else:
                pass
            print(
                f'{TAB}{TAB}# PROTECTED COMMAND END{EOL}'
                f'{EOL}',
                file=self.ofstream,
                end="",
            )
        else:
            if dtype_out == "None":
                decscrptn = self.get_description(cmd_name, decscrptn, "Run", "command", TAB*2, '"""', '"""')
                print(
                    f'{TAB}@command({dtype_spec}){EOL}'
                    f'{TAB}def {cmd_name}(self) -> {dtype_out}:{EOL}'
                    f'{decscrptn}'
                    f'{TAB}{TAB}# PROTECTED COMMAND ({self.cls_name}.{cmd_name}) START{EOL}'
                    f'{TAB}{TAB}self.logger.info("Run command {cmd_name}()"){EOL}'
                    f'{TAB}{TAB}# TODO add code for command {cmd_name}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            else:
                decscrptn = self.get_description(cmd_name, decscrptn, "Run", "command", TAB*2)
                print(
                    f'{TAB}@command({dtype_spec}){EOL}'
                    f'{TAB}def {cmd_name}(self) -> {dtype_out}:{EOL}'
                    f'{TAB}{TAB}"""{EOL}'
                    f'{decscrptn}'
                    f'{EOL}',
                    file=self.ofstream,
                    end="",
                )
                if dtype_out != "None":
                    print(f'{TAB}{TAB}:returns: {dtype_out} value{EOL}', file=self.ofstream, end="")
                print(
                    f'{TAB}{TAB}"""{EOL}'
                    f'{TAB}{TAB}# PROTECTED COMMAND ({self.cls_name}.{cmd_name}) START{EOL}'
                    f'{TAB}{TAB}self.logger.info("Run command {cmd_name}()"){EOL}'
                    f'{TAB}{TAB}# TODO add code for command {cmd_name}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            if dtype_out == "None":
                pass
            elif dtype_out == "str":
                print(f'{TAB}{TAB}return ""{EOL}', file=self.ofstream, end="")
            elif dtype_out == "int":
                print(f'{TAB}{TAB}return 0{EOL}', file=self.ofstream, end="")
            elif dtype_out == "float":
                print(f'{TAB}{TAB}return 0.0{EOL}', file=self.ofstream, end="")
            else:
                pass
            print(
                f'{TAB}{TAB}# PROTECTED COMMAND END{EOL}'
                f'{EOL}',
                file=self.ofstream,
                end="",
            )

    def print_commands_code(self, cmds: dict) -> None:
        """
        Write code for Python commands.

        :param cmds: dictionary with commands
        """
        for cmd_name in cmds:
            self.print_command_code(
                cmd_name,
                cmds[cmd_name]["description"],
                cmds[cmd_name]["dtype_in"],
                cmds[cmd_name]["dtype_out"],
            )

    def print_init_device(self) -> None:
        """Print code to initialise the device."""
        print(
            f'{TAB}def init_device(self) -> None:{EOL}'
            f'{TAB}{TAB}"""Initialize the device."""{EOL}'
            f'{TAB}{TAB}super().init_device(){EOL}'
            f'{TAB}{TAB}self.device_name = self.get_name(){EOL}'
            f'{TAB}{TAB}log_level: str = os.getenv("LOG_LEVEL", "WARNING").upper(){EOL}'
            f'{TAB}{TAB}self.logger.setLevel(log_level){EOL}'
            f'{TAB}{TAB}self.logger.info("Initialize device %s", self.device_name){EOL}'
            f'{TAB}{TAB}self.set_status("DISABLE"){EOL}'
            f'{TAB}{TAB}self.set_state(tango.DevState.DISABLE){EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_main(self) -> None:
        print(
            f'{EOL}'
            f'def main(args: Any = None, **kwargs: Any) -> int:{EOL}'
            f'{TAB}"""{EOL}'
            f'{TAB}Launch a server instance for {self.cls_name}.{EOL}'
            f'{EOL}'
            f'{TAB}:param args: arguments to the {self.cls_name} device.{EOL}'
            f'{TAB}:param kwargs: keyword arguments to the tango device server.{EOL}'
            f'{EOL}'
            f'{TAB}:returns: exit code of the Tango server.{EOL}'
            f'{TAB}"""{EOL}'
            f'{TAB}return tango.server.run(({self.cls_name},), args=args, **kwargs){EOL}'
            f'{EOL}{EOL}'
            f'if __name__ == "__main__":{EOL}'
            f'{TAB}main(){EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_python_code(
        self,
        file_path: str | None,
        skip_tests: bool,
        special_attributes: dict,
    ) -> None:
        """
        Write code for Python attributes.

        :param file_path: output file e.g. "test_oscilloscope_device.py"
        :param skip_tests: flag all tests to be skipped
        :param special_attributes: attributes for which test code will not be geneated
        """
        self.skip_tests = skip_tests
        co_file: str = (
            inspect.currentframe()
            .f_code.co_filename.replace(HOME_PATH, "")
            .replace(PYTHON_PATH, "src")
        )
        # dev_attributes: dict = self.read_xml_attributes()
        dev_attribs: dict = self.read_xml_attributes()
        # self.init_protected_attributes(dev_attribs, special_attributes)
        dev_cmds: dict = self.read_xml_commands()
        self.init_protected_commands(dev_cmds)
        if file_path is not None:
            self.read_protected_attributes(file_path)
            self.read_protected_commands(file_path)
            self.logger.info("Write %s code file %s", self.cls_name, file_path)
            # pylint: disable-next=consider-using-with
            self.ofstream = open(file_path, "w+", encoding="utf-8")
        else:
            self.logger.info("Write %s code", self.cls_name)
            self.ofstream = sys.stdout
        self.print_file_header(co_file)
        self.print_component_manager()
        self.print_class_header()
        self.print_vars(dev_attribs, special_attributes)
        self.print_create_component_manager()
        self.print_init_device()
        # self.print_admin_mode()
        self.print_attributes_code(dev_attribs, special_attributes)
        self.print_commands_code(dev_cmds)
        self.print_main()
        if file_path is not None:
            self.ofstream.close()
            self.format_with_black(file_path)
