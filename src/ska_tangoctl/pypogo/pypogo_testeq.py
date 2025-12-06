"""Generate pytest code for test equipment."""

# pylint: disable=duplicate-code
# mypy: disable-error-code="attr-defined,union-attr"

import inspect
import json
import logging
import os
import sys
from typing import Any
import yaml

from ska_tangoctl.pypogo.pypogo_globals import CURRENT_TIME, EOL, HOME_PATH, PYTHON_PATH


class PyPogoTestEquipmentMixin:
    """Generate Python tests for test equipment."""

    logger: logging.Logger
    skip_tests: bool = False
    cls_name: str
    ofstream: Any
    protected_tests: dict = {}

    def init_testeq_protected_attributes(self, attributes: dict, special_attributes: dict) -> None:
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

    # pylint: disable-next=too-many-branches,too-many-statements
    def read_testeq_attributes(self) -> dict:  # noqa: C901
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
                field_type = self.default_type
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
    def read_testeq_commands(self) -> dict:  # noqa: C901
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

    def _read_write_testeq(self, attrib_name: str, field_type: str, attributes: dict):
        print(
            f"    # Read the {field_type} value, write it back and read it again{EOL}"
            f"    attrib_val = device_proxy.{attrib_name}{EOL}"
            f"    device_proxy.{attrib_name} = attrib_val{EOL}"
            f'    attrib_val2: {field_type} = device_proxy.{attrib_name}{EOL}'
            f'    assert attrib_val == attrib_val2{EOL}',
            file=self.ofstream,
            end="",
        )
        attribute_values: list
        try:
            attribute_value = attributes[attrib_name]["write"]["value"]
        except KeyError:
            attribute_value = '""'
        if "test_values" in attributes[attrib_name]["write"]:
            attribute_values = attributes[attrib_name]["write"]["test_values"].split(",")
        else:
            attribute_values = [attribute_value]
        # Write and read again
        for attribute_value in attribute_values:
            if str(attribute_value).replace('"', "") == "":
                self.logger.info("No value for attribute %s", attrib_name)
                continue
            if field_type == "bit":
                self.logger.info("Use int instead of bit for %s", attrib_name)
                field_type = "int"
            if field_type == "arbitrary_block":
                self.logger.info("Skip arbitrary block %s", attrib_name)
                continue
            self.logger.info("Add read/write test for %s (%s)", attrib_name, field_type)
            if field_type == "str":
                print(
                    f'    # String value{EOL}'
                    f'    print(\'Set attribute {attrib_name} to "{attribute_value}"\'){EOL}'
                    f'    device_proxy.{attrib_name} = "{attribute_value}"{EOL}'
                    f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
                    f'    assert device_proxy.{attrib_name} == "{attribute_value}"{EOL}',
                    file=self.ofstream,
                    end="",
                )
            elif field_type == "bool":
                print(
                    f'    # Boolean value{EOL}'
                    f'    print(\'Set attribute {attrib_name} to "{attribute_value}"\'){EOL}'
                    f'    device_proxy.{attrib_name} = {attribute_value}{EOL}'
                    f'    print("{attrib_name} : %s" % str(bool(device_proxy.{attrib_name}))){EOL}'
                    f'    assert device_proxy.{attrib_name} is {attribute_value}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            else:
                print(
                    f'    # Value with type {field_type}{EOL}'
                    f'    device_proxy.{attrib_name} = {attribute_value}{EOL}'
                    f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
                    f'    assert device_proxy.{attrib_name} == {attribute_value}{EOL}',
                    file=self.ofstream,
                    end="",
                )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_testeq_rw(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_rw"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        self.logger.info("Test %s Tango attribute %s (read/write)", field_type, attrib_name)
        # Read
        if self.skip_tests:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_{attrib_name}_rw(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test {field_type} Tango attribute {attrib_name} read/write.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        else:
            self._read_write_testeq(attrib_name, field_type, attributes)
        print(
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end=""
        )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_testeq_invalid(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_invalid"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        print(
            f'@pytest.mark.xfail{EOL}'
            f'def test_{attrib_name}_invalid(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test maximum value of {field_type} Tango attribute {attrib_name}.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        elif "valid_values" in attributes[attrib_name]["write"]:
            valid_values = attributes[attrib_name]["write"]["valid_values"].split(",")
            print(
                    f'    new_value = "{valid_values[0]}{valid_values[-1]}"{EOL}'
                    f'    device_proxy.{attrib_name} = new_value{EOL}'
                    f'    assert device_proxy.{attrib_name} == new_value{EOL}'
                    f'    # PROTECTED TEST END{EOL}'
                    f'{EOL}{EOL}',
                    file=self.ofstream,
                    end="",
                )
        else:
            print(
                f'    # Nothing to see here{EOL}'
                f'    pass{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_testeq_max(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_invalid"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        if "max_value" in attributes[attrib_name]["write"]:
            max_value = attributes[attrib_name]["write"]["max_value"]
            if max_value is None:
                self.logger.info("No max value for %s", attrib_name)
                return
            if field_type == "bit":
                self.logger.info("Use int instead of bit for %s", attrib_name)
                field_type = "int"
            if field_type == "arbitrary_block":
                self.logger.info("Skip arbitrary block %s", attrib_name)
                return
            self.logger.info("Add negative test for %s max (%s)", attrib_name, field_type)
            print(
                f'def test_{attrib_name}_max(device_proxy: tango.DeviceProxy) -> None:{EOL}'
                f'    """{EOL}'
                f'    Test maximum value of {field_type} Tango attribute {attrib_name}.{EOL}'
                f'{EOL}'
                f'    :param device_proxy: Tango device proxy{EOL}'
                f'    """{EOL}'
                f'    # PROTECTED TEST ({test_id}) START{EOL}',
                file=self.ofstream,
                end="",
            )
            if prot_code:
                print(f'{prot_code}', file=self.ofstream, end="")
            else:
                print(
                    f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
                    f'    new_value = {max_value} * 2{EOL}'
                    f'    device_proxy.{attrib_name} = new_value{EOL}'
                    f'    assert device_proxy.{attrib_name} != new_value{EOL}',
                    file=self.ofstream,
                    end="",
                )
            print(
                f'    # PROTECTED TEST END{EOL}'
                f'{EOL}{EOL}',
                file=self.ofstream,
                end="",
            )
        else:
            self.logger.info("No maximum value for attribute %s", attrib_name)

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_testeq_min(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_invalid"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        if "min_value" in attributes[attrib_name]["write"]:
            min_value = attributes[attrib_name]["write"]["min_value"]
            if min_value is None:
                self.logger.info("No min value for %s", attrib_name)
                return
            if field_type == "bit":
                self.logger.info("Use int instead of bit for %s", attrib_name)
                field_type = "int"
            if field_type == "arbitrary_block":
                self.logger.info("Skip arbitrary block %s", attrib_name)
                return
            self.logger.info("Add xfail test for %s min (%s)", attrib_name, field_type)
            print(
                f'@pytest.mark.xfail{EOL}'
                f'def test_{attrib_name}_min(device_proxy: tango.DeviceProxy) -> None:{EOL}'
                f'    """{EOL}'
                f'    Test minimum value of {field_type} Tango attribute {attrib_name}.{EOL}'
                f'{EOL}'
                f'    :param device_proxy: Tango device proxy{EOL}'
                f'    """{EOL}'
                f'    # PROTECTED TEST ({test_id}) START{EOL}',
                file=self.ofstream,
                end="",
            )
            if prot_code:
                print(f'{prot_code}', file=self.ofstream, end="")
            else:
                print(
                    f'    new_value: {field_type}{EOL}'
                    f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
                    f'    test_value = {min_value}{EOL}'
                    f'    if test_value == 0:{EOL}'
                    f'        new_value = {field_type}(test_value - 1){EOL}'
                    f'    elif test_value < 0:{EOL}'
                    f'        new_value = {field_type}(test_value * 2){EOL}'
                    f'    else:{EOL}'
                    f'        new_value = {field_type}(test_value / 2){EOL}'
                    f'    device_proxy.{attrib_name} = new_value{EOL}'
                    f'    assert device_proxy.{attrib_name} == new_value{EOL}',
                    file=self.ofstream,
                    end="",
                )
            print(
                f'    # PROTECTED TEST END{EOL}'
                f'{EOL}{EOL}',
                file=self.ofstream,
                end="",
            )
        else:
            self.logger.info("No minimum value for attribute %s", attrib_name)

    def print_attribute_testeq_ro(self, attrib_name: str, field_type: str) -> None:
        """
        Print read-only test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_ro"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        self.logger.info("Test %s Tango attribute %s (read)", field_type, attrib_name)
        # Read
        if self.skip_tests:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_{attrib_name}_ro(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test {field_type} Tango attribute {attrib_name} (read).{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        else:
            print(
                f'    attrib_val: {field_type} = device_proxy.{attrib_name}{EOL}'
                f'    print("{attrib_name} : %s" % str(attrib_val)){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attributes_testeq(self, attributes: dict, special_attributes: dict) -> None:
        """
        Print test code for device channels.

        :param attributes: dictionary with attributes
        :param special_attributes: dictionary with special attributes
        """
        self.logger.debug("Test Tango devices:\n%s", json.dumps(attributes, indent=4))
        for attrib_name in attributes:
            if attrib_name in special_attributes:
                self.logger.error("Skip special attribute %s ", attrib_name)
            elif "read" in attributes[attrib_name] and "write" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                self.print_attribute_testeq_rw(attrib_name, field_type, attributes)
                self.print_attribute_testeq_invalid(attrib_name, field_type, attributes)
                self.print_attribute_testeq_max(attrib_name, field_type, attributes)
                self.print_attribute_testeq_min(attrib_name, field_type, attributes)
            elif "read" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                self.print_attribute_testeq_ro(attrib_name, field_type)
            elif "write" in attributes[attrib_name]:
                self.logger.warning("Skip write only attribute %s", attrib_name)
                # self.print_command_testeq(attrib_name, attributes)
            else:
                self.logger.error("Attribute %s has no read or write values", attrib_name)

    def print_command_testeq(self, command_name: str, cmds: dict, skip_test: bool) -> None:
        """
        Print write-only test code for device channels.

        :param command_name: attribute name
        :param cmds: dictionary with attributes
        :param skip_test: skip this test
        """
        cmd_id = f"{self.cls_name}.{command_name}.command"
        prot_code: str = ""
        if cmd_id in self.protected_tests:
            prot_code = self.protected_tests[cmd_id]
        self.logger.info("Test Tango command %s (write-only)", command_name)
        if skip_test:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        elif "pytest" in cmds[command_name]:
            if skip_test or cmds[command_name] == "skip":
                print(
                    f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                    file=self.ofstream,
                    end="",
                )
        else:
            pass
        # Write command
        print(
            f'def test_cmd_{command_name}(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test Tango command {command_name}.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({cmd_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        else:
            print(
                f'    print("Send command {command_name}"){EOL}'
                f'    device_proxy.{command_name}(){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_commands_testeq(self, cmds: dict, skip_tests: bool) -> None:
        """
        Write test code for Python commands.

        :param cmds: dictionary with commands
        :param skip_tests: skip these tests
        """
        for cmd_name in cmds:
            self.print_command_testeq(cmd_name, cmds, skip_tests)

    def print_python_testeq(
        self,
        file_path: str | None,
        skip_tests: bool,
        special_attributes: dict,
    ) -> None:
        """
        Write code for device tests.

        :param file_path: output file e.g. "test_oscilloscope_device.py"
        :param skip_tests: flag all tests to be skipped
        :param special_attributes: attributes for which test code will not be geneated
        """
        dev_attributes: dict = self.read_testeq_attributes()
        dev_commands: dict = self.read_testeq_commands()
        self.skip_tests = skip_tests
        co_file = (
            inspect.currentframe()
            .f_code.co_filename.replace(HOME_PATH, "")
            .replace(PYTHON_PATH, "src")
        )
        if file_path is not None:
            self.logger.info("Write %s test file %s", self.cls_name, file_path)
            # pylint: disable-next=consider-using-with
            self.ofstream = open(file_path, "w+", encoding="utf-8")
        else:
            self.logger.info("Write %s tests", self.cls_name)
            self.ofstream = sys.stdout
        self.print_test_header(co_file)
        self.print_test_device_name()
        self.print_test_device_proxy()
        self.print_test_admin_mode()
        self.print_attributes_testeq(dev_attributes, special_attributes)
        self.skip_tests = True
        self.print_commands_testeq(dev_commands, self.skip_tests)
        if file_path is not None:
            self.ofstream.close()
            self.format_with_black(file_path)

    def print_testeq_yaml(self, file_path: str | None) -> int:
        """
        Write YAML as used for test equipment.

        :param file_path: output file e.g. "oscilloscope.yaml"
        :returns: error condition
        """
        if file_path is not None:
            file_name: str
            file_ext: str
            file_name, file_ext = os.path.splitext(os.path.basename(file_path))
            self.cls_name = file_name
        else:
            self.cls_name = "PyPogo"
        dev: dict = {}
        dev["attributes"] = self.read_testeq_attributes()
        dev["commands"] = self.read_testeq_commands()
        print(yaml.dump(dev))
