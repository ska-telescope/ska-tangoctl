"""Generate test code for instrument."""

# mypy: disable-error-code="attr-defined,union-attr"

import inspect
import json
import logging
import os
import sys
from typing import Any

from pypogo_globals import CURRENT_TIME, EOL, HOME_PATH, PYTHON_PATH


class PyPogoCodeMixin:
    """Generate code for Python tests."""

    logger: logging.Logger
    skip_tests: bool = False
    py_class: str
    ofstream: Any
    cls_name: str
    protected_attributes: dict = {}
    protected_commands: dict = {}

    def init_protected_attributes(self, attributes: dict, special_attributes: dict) -> None:
        """
        Initialize protected attributes.

        :param attributes: dictionary with attribute definitions
        :param special_attributes: special cases that are skipped for now
        """
        for attrib_name in attributes:
            if attrib_name in special_attributes:
                self.logger.error("Skip special attribute %s ", attrib_name)
            elif "read" in attributes[attrib_name] and "write" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                self.protected_attributes[f"{self.cls_name}.{attrib_name}"] = ""
                self.protected_attributes[f"{self.cls_name}.{attrib_name}.write"] = ""
            elif "read" in attributes[attrib_name]:
                self.protected_attributes[f"{self.cls_name}.{attrib_name}"] = ""
            else:
                pass
        self.logger.debug(
            "Protected attributes:\n%s", json.dumps(self.protected_attributes, indent=4)
        )

    def init_protected_commands(self, commands: dict) -> None:
        """
        Initialize protected commands.

        :param attributes: dictionary with command definitions
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
            f'    """Component manager for {self.cls_name}."""{EOL}'
            f'{EOL}'
            f'    logger: logging.Logger{EOL}'
            f'    max_executing_tasks = 1{EOL}'
            f'    max_queued_tasks = 0{EOL}'
            f'{EOL}'
            f'    def __init__(self) -> None:{EOL}'
            f'        """You can start me up."""{EOL}'
            f'{EOL}'
            f'    def start_communicating(self) -> None:{EOL}'
            f'        """Start communication."""{EOL}'
            f'        self.logger.info("Start communicating"){EOL}'
            f'{EOL}'
            f'    def stop_communicating(self) -> None:{EOL}'
            f'        """Stop communication."""{EOL}'
            f'        self.logger.info("Stop communicating")  {EOL}'
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
            f'{EOL}'
            f'import logging{EOL}'
            f'import os{EOL}'
            f'import sys{EOL}'
            f'from typing import Any{EOL}'
            f'{EOL}'
            f'import tango{EOL}'
            f'from ska_tango_base import SKABaseDevice{EOL}'
            f'from ska_control_model import AdminMode{EOL}'
            f'from tango import AttReqType, AttrQuality, TimeVal{EOL}'
            f'from tango.server import attribute{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_create_component_manager(self) -> None:
        """
        Print code to create component manager.
        """
        print(
            f'    def create_component_manager(self) -> Any:{EOL}'
            f'        """{EOL}'
            f'        Create and return a component manager for this device.{EOL}'
            f'{EOL}'
            f'        :returns: a component manager for this device.{EOL}'
            f'        """{EOL}'
            f'        # pylint: disable-next=fixme{EOL}'
            f'        # TODO this causes an error in SKABaseDevice{EOL}'
            f'        self.logger.warning("Dummy component manager"){EOL}'
            f'        cm = {self.cls_name}CM(){EOL}'
            f'        cm.logger = self.logger{EOL}'
            f'        return cm{EOL}'
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
            f'    """Implementation of yet another Tango device."""{EOL}'
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

        def default_value(f_type, value) -> str:
            if f_type == "str":
                if value is not None:
                    return '"{value}"'
                return '""'
            if value is not None:
                return f"{value}"
            if f_type == "bool":
                return "False"
            if f_type == "int":
                return "sys.maxsize"
            if f_type == "float":
                return 'float("nan")'
            return "None"

        print(f'    _adminMode: bool = True{EOL}', file=self.ofstream, end="")
        for attrib_name in attributes:
            if attrib_name in special_attributes:
                self.logger.error("Skip special attribute %s ", attrib_name)
            elif "read" in attributes[attrib_name] and "write" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                value = attributes[attrib_name]["read"]["value"]
                print(
                    f'    _{attrib_name}: {field_type} = {default_value(field_type, value)}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            elif "read" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                value = attributes[attrib_name]["read"]["value"]
                print(
                    f'    _{attrib_name}: {field_type} = {default_value(field_type, value)}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            else:
                pass
        print(f'{EOL}', file=self.ofstream, end="")

    def print_admin_mode(self):
        """Print code to set admin mode for the device."""
        atrr_id = f"{self.cls_name}.adminMode"
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
        if not prot_code:
            prot_code = f'        return self._adminMode{EOL}'
        print(
            f'    @attribute(dtype=bool){EOL}'
            f'    def adminMode(self) -> bool:{EOL}'
            f'        """{EOL}'
            f'        Get admin mode.{EOL}'
            f'{EOL}'
            f'        :returns: current admin mode{EOL}'
            f'        """{EOL}'
            f'        # PROTECTED ATTRIBUTE ({self.cls_name}.adminMode) START{EOL}'
            f'{prot_code}'
            f'        # PROTECTED ATTRIBUTE END{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )
        atrr_id = f"{self.cls_name}.adminMode.write"
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
        if not prot_code:
            prot_code = (
                f'        self.logger.debug("Set adminMode to %s", value){EOL}'
                f'        self._adminMode = value{EOL}'
            )
        print(
            f'    @adminMode.write{EOL}'
            f'    def adminMode(self, value: bool) -> None:{EOL}'
            f'        """{EOL}'
            f'        Set admin mode.{EOL}'
            f'{EOL}'
            f'        """{EOL}'
            f'        # PROTECTED ATTRIBUTE ({self.cls_name}.adminMode.write) START{EOL}'
            f'{prot_code}'
            f'        # PROTECTED ATTRIBUTE END{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def get_description(
        self, tgo_name: str, decscrptn: str, actn: str, tgo_thing: str
    ) -> str:
        """
        Set description for use in comments.

        :param tgo_name: attribute name
        :param decscrptn: attribute decscrption
        :param tgo_thing: attribute, command or property
        :returns: updated description
        """
        if not decscrptn:
            decscrptn = f"{actn} Tango {tgo_thing} {tgo_name}."
        elif "\n" in decscrptn:
            decscrptn = (
                f"{actn} Tango {tgo_thing} {tgo_name}."
                + f"{EOL}{EOL}        "
                + decscrptn.replace("\n", "\n        ")
            )
        else:
            decscrptn = f"{decscrptn}"
            if decscrptn[-1] != ".":
                decscrptn += "."
        return decscrptn

    def print_attribute_read(self, attrib_name: str, decscrptn: str, field_type: str) -> None:
        """
        Write code for reading Python attribute.

        :param attrib_name: attribute name
        :param decscrptn: attribute decscrption
        :param field_type: data type, e.g. int, str, float...
        """
        decscrptn = self.get_description(attrib_name, decscrptn, "Read", "attribute")
        atrr_id = f"{self.cls_name}.{attrib_name}.read"
        self.logger.info("Read %s : %s", atrr_id, decscrptn)
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
            self.logger.debug("Read %s code:\n%s", atrr_id, prot_code)
        if not prot_code:
            prot_code = (
                f'        value = self._{attrib_name}{EOL}'
                f'        self.logger.debug("Value of {attrib_name} is %s", str(value)){EOL}'
            )
            if field_type == "int":
                prot_code += (
                    f'        if value == sys.maxsize:{EOL}'
                    f'            self.logger.warning("Attribute {attrib_name} not initialised"){EOL}'
                )
            elif field_type == "float":
                prot_code += (
                    f'        if math.isnan(value):{EOL}'
                    f'            self.logger.warning("Attribute {attrib_name} not initialised"){EOL}'
                )
            elif field_type == "str":
                prot_code += (
                    f'        if value == "":{EOL}'
                    f'            self.logger.warning("Attribute {attrib_name} not initialised"){EOL}'
                )
            elif field_type == "bool":
                pass
            else:
                prot_code += (
                    f'        if value is None:{EOL}'
                    f'            self.logger.warning("Attribute {attrib_name} not initialised"){EOL}'
                )
        print(
            f'    @attribute(dtype={field_type}){EOL}'
            f'    def {attrib_name}(self) -> {field_type}:{EOL}'
            f'        """{EOL}'
            f'        {decscrptn}{EOL}'
            f'{EOL}'
            f'        :returns: value of {attrib_name}{EOL}'
            f'        """{EOL}'
            f'        value: {field_type}{EOL}'
            f'        # PROTECTED ATTRIBUTE ({atrr_id}) START{EOL}'
            f'{prot_code}'
            f'        # PROTECTED ATTRIBUTE END{EOL}'
            f'        return value{EOL}'
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
        decscrptn = self.get_description(attrib_name, decscrptn, "Check read", "attribute")
        atrr_id = f"{self.cls_name}.{attrib_name}.read_is_allowed"
        self.logger.info("Read %s allowed", atrr_id)
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
            self.logger.debug("Read %s code:\n%s", atrr_id, prot_code)
        if not prot_code:
            prot_code = f'        return True{EOL}'
        print(
            f'    @{attrib_name}.is_allowed{EOL}'
            f'    # pylint: disable-next=unused-argument{EOL}'
            f'    def {attrib_name}_is_allowed(self, request_type: Any) -> {field_type}:{EOL}'
            f'        """{EOL}'
            f'        {decscrptn}{EOL}'
            f'{EOL}'
            f'        :param request_type: read or write{EOL}'
            f'        :returns: operation can proceed{EOL}'
            f'        """{EOL}'
            f'        # PROTECTED ATTRIBUTE ({atrr_id}) START{EOL}'
            f'{prot_code}'
            f'        # PROTECTED ATTRIBUTE END{EOL}'
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
        decscrptn = self.get_description(attrib_name, decscrptn, "Write", "attribute")
        atrr_id = f"{self.cls_name}.{attrib_name}.write"
        self.logger.info("Write %s : %s", atrr_id, decscrptn)
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
            self.logger.debug("Write %s code:\n%s", atrr_id, prot_code)
        if not prot_code:
            prot_code = (
                f'        self.logger.debug("Set {attrib_name} to %s", str(value)){EOL}'
                f'        self._{attrib_name} = value{EOL}'
            )
        print(
            f'    @{attrib_name}.write  # type: ignore[no-redef]{EOL}'
            f'    def {attrib_name}(self, value: {field_type}) -> None:{EOL}'
            f'        """{EOL}'
            f'        {decscrptn}{EOL}'
            f'{EOL}'
            f'        :param value: change to this{EOL}'
            f'        """{EOL}'
            f'        # PROTECTED ATTRIBUTE ({atrr_id}.write) START{EOL}'
            f'{prot_code}'
            f'        # PROTECTED ATTRIBUTE END{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_write_is_allowed(
        self, attrib_name: str, decscrptn: str, field_type: str, min_value: Any, max_value: Any
    ) -> None:
        """
        Write code for reading Python attribute.

        :param attrib_name: attribute name
        :param decscrptn: attribute decscrption
        :param field_type: data type, e.g. int, str, float...
        """
        decscrptn = self.get_description(attrib_name, decscrptn, "Check write", "attribute")
        atrr_id = f"{self.cls_name}.{attrib_name}.write_is_allowed"
        self.logger.info("Write %s is allowed", atrr_id)
        prot_code: str = ""
        if atrr_id in self.protected_attributes:
            prot_code = self.protected_attributes[atrr_id]
            self.logger.debug("Read %s code:\n%s", atrr_id, prot_code)
        if not prot_code:
            prot_code = (
                f'        if request_type == AttReqType.READ_REQ:{EOL}'
                f'            return True{EOL}'
                f'        return not self._admin_mode{EOL}'
            )
        print(
            f'    @{attrib_name}.is_allowed{EOL}'
            f'    # pylint: disable-next=unused-argument{EOL}'
            f'    def {attrib_name}_is_allowed(self, request_type: Any) -> {field_type}:{EOL}'
            f'        """{EOL}'
            f'        {decscrptn}{EOL}'
            f'{EOL}'
            f'        :param request_type: read or write{EOL}'
            f'        :returns: operation can proceed{EOL}'
            f'        """{EOL}'
            f'        # PROTECTED ATTRIBUTE ({atrr_id}) START{EOL}'
            f'{prot_code}'
            f'        # PROTECTED ATTRIBUTE END{EOL}'
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
        self.logger.debug("Tango attributes:\n%s", json.dumps(attributes, indent=4))
        for attrib_name in attributes:
            decscrptn = attributes[attrib_name]["description"]
            if attrib_name in special_attributes:
                self.logger.error("Skip special attribute %s ", attrib_name)
            elif "read" in attributes[attrib_name] and "write" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                min_value = attributes[attrib_name]["read"]["min_value"]
                max_value = attributes[attrib_name]["read"]["max_value"]
                self.print_attribute_read(attrib_name, decscrptn, field_type)
                self.print_attribute_write(attrib_name, decscrptn, field_type)
                self.print_attribute_write_is_allowed(attrib_name, decscrptn, field_type, min_value, max_value)
            elif "read" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                self.print_attribute_read(attrib_name, decscrptn, field_type)
                self.print_attribute_read_is_allowed(attrib_name, decscrptn, field_type)
            elif "write" in attributes[attrib_name]:
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
        decscrptn = self.get_description(cmd_name, decscrptn, "Run", "command")
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
            print(
                f'    @command({dtype_spec}){EOL}'
                f'    def {cmd_name}(self, args: {dtype_in}) -> {dtype_out}:{EOL}'
                f'        """{EOL}'
                f'        {decscrptn}{EOL}'
                f'{EOL}'
                f'        :param args: command argument(s){EOL}'
                f'        :raises Exception: error{EOL}'
                f'        """{EOL}',
                file=self.ofstream,
                end="",
            )
        else:
            print(
                f'    @command({dtype_spec}){EOL}'
                f'    def {cmd_name}(self) -> {dtype_out}:{EOL}'
                f'        """{EOL}'
                f'        {decscrptn}{EOL}'
                f'{EOL}'
                f'        :raises Exception: error{EOL}'
                f'        """{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'        # PROTECTED COMMAND ({self.cls_name}.{cmd_name}) START{EOL}'
            f'        kwargs = ast.literal_eval(args){EOL}'
            f'        try:{EOL}'
            f'            value = kwargs["value"]{EOL}'
            f'        except Exception as kerr:{EOL}'
            f'            self.logger.error("Could not read arguments: %s", kerr){EOL}'
            f'            raise kerr{EOL}'
            f'        self.logger.info("Load value %s", str(value)){EOL}'
            f'        # PROTECTED COMMAND END{EOL}'
            f'        return{EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_commands_code(self, cmds: dict) -> None:
        """
        Write code for Python commands.

        :param dev_cmds: dictionary with commands
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
            f'    def init_device(self) -> None:{EOL}'
            f'        """Initialize the device."""{EOL}'
            f'        super().init_device(){EOL}'
            f'        self.device_name = self.get_name(){EOL}'
            f'        log_level: str = os.getenv("LOG_LEVEL", "WARNING").upper(){EOL}'
            f'        self.logger.setLevel(log_level){EOL}'
            f'        self.logger.info("Initialize device %s", self.device_name){EOL}'
            f'        self.set_status("DISABLE"){EOL}'
            f'        self.set_state(tango.DevState.DISABLE){EOL}'
            f'{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_main(self) -> None:
        print(
            f'{EOL}'
            f'def main(args: Any = None, **kwargs: Any) -> int:{EOL}'
            f'    """{EOL}'
            f'    Launch a server instance for {self.cls_name}.{EOL}'
            f'{EOL}'
            f'    :param args: arguments to the {self.cls_name} device.{EOL}'
            f'    :param kwargs: keyword arguments to the tango device server.{EOL}'
            f'{EOL}'
            f'    :returns: exit code of the Tango server.{EOL}'
            f'    """{EOL}'
            f'    return tango.server.run(({self.cls_name},), args=args, **kwargs){EOL}'
            f'{EOL}{EOL}'
            f'if __name__ == "__main__":{EOL}'
            f'    main(){EOL}'
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
        dev_attributes: dict = self.read_xml_attributes()
        self.init_protected_attributes(dev_attributes, special_attributes)
        dev_cmds: dict = self.read_xml_commands()
        self.init_protected_commands(dev_cmds)
        if file_path is not None:
            self.read_protected_attributes(file_path)
            self.read_protected_commands(file_path)
            self.logger.info("Write %s code file %s", self.py_class, file_path)
            # pylint: disable-next=consider-using-with
            self.ofstream = open(file_path, "w+", encoding="utf-8")
        else:
            self.logger.info("Write %s code", self.py_class)
            self.ofstream = sys.stdout
        self.print_file_header(co_file)
        self.print_component_manager()
        self.print_class_header()
        self.print_vars(dev_attributes, special_attributes)
        self.print_create_component_manager()
        self.print_init_device()
        self.print_admin_mode()
        self.print_attributes_code(dev_attributes, special_attributes)
        self.print_commands_code(dev_cmds)
        self.print_main()
        if file_path is not None:
            self.ofstream.close()
            self.format_with_black(file_path)
