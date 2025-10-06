"""Generate test code for instrument."""

# pylint: disable=duplicate-code
# mypy: disable-error-code="attr-defined,union-attr"

import inspect
import json
import logging
import sys
from typing import Any

from pypogo_globals import CURRENT_TIME, EOL, HOME_PATH, PYTHON_PATH


class PyPogoTestsMixin:
    """Generate code for Python tests."""

    logger: logging.Logger
    skip_tests: bool = False
    py_class: str
    ofstream: Any

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_test_rw(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        self.logger.info("Test %s Tango attribute %s (read/write)", field_type, attrib_name)
        # Read
        if self.skip_tests:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_{attrib_name}_rw(test_device: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test {field_type} Tango attribute {attrib_name} read/write.{EOL}'
            f'{EOL}'
            f'    :param test_device: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    attrib_val: {field_type} = test_device.{attrib_name}{EOL}'
            f'    print("{attrib_name} : %s" % str(attrib_val)){EOL}',
            file=self.ofstream,
            end="",
        )
        print(
            f"    # Write back the {field_type} value and read it again{EOL}"
            f"    test_device.{attrib_name} = attrib_val{EOL}"
            f'    attrib_val2: {field_type} = test_device.{attrib_name}{EOL}'
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
                    f'    test_device.{attrib_name} = "{attribute_value}"{EOL}'
                    f'    print("{attrib_name} : %s" % str(test_device.{attrib_name})){EOL}'
                    f'    assert test_device.{attrib_name} == "{attribute_value}"{EOL}',
                    file=self.ofstream,
                    end="",
                )
            elif field_type == "bool":
                print(
                    f'    # Boolean value{EOL}'
                    f'    print(\'Set attribute {attrib_name} to "{attribute_value}"\'){EOL}'
                    f'    test_device.{attrib_name} = {attribute_value}{EOL}'
                    f'    print("{attrib_name} : %s" % str(bool(test_device.{attrib_name}))){EOL}'
                    f'    assert test_device.{attrib_name} is {attribute_value}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            else:
                print(
                    f'    # Value with type {field_type}{EOL}'
                    f'    test_device.{attrib_name} = {attribute_value}{EOL}'
                    f'    print("{attrib_name} : %s" % str(test_device.{attrib_name})){EOL}'
                    f'    assert test_device.{attrib_name} == {attribute_value}{EOL}',
                    file=self.ofstream,
                    end="",
                )
        print(
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )
        if "valid_values" in attributes[attrib_name]["write"]:
            valid_values = attributes[attrib_name]["write"]["valid_values"].split(",")
            print(
                f'@pytest.mark.xfail{EOL}'
                f'def test_{attrib_name}_invalid(test_device: tango.DeviceProxy) -> None:{EOL}'
                f'    """{EOL}'
                f'    Test maximum value of {field_type} Tango attribute {attrib_name}.{EOL}'
                f'{EOL}'
                f'    :param test_device: Tango device proxy{EOL}'
                f'    """{EOL}'
                f'    print("{attrib_name} : %s" % str(test_device.{attrib_name})){EOL}'
                f'    new_value = "{valid_values[0]}{valid_values[-1]}"{EOL}'
                f'    test_device.{attrib_name} = new_value{EOL}'
                f'    assert test_device.{attrib_name} == new_value{EOL}'
                f'{EOL}{EOL}',
                file=self.ofstream,
                end="",
            )
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
            self.logger.info("Add xfail test for %s max (%s)", attrib_name, field_type)
            print(
                f'@pytest.mark.xfail{EOL}'
                f'def test_{attrib_name}_max(test_device: tango.DeviceProxy) -> None:{EOL}'
                f'    """{EOL}'
                f'    Test maximum value of {field_type} Tango attribute {attrib_name}.{EOL}'
                f'{EOL}'
                f'    :param test_device: Tango device proxy{EOL}'
                f'    """{EOL}'
                f'    print("{attrib_name} : %s" % str(test_device.{attrib_name})){EOL}'
                f'    new_value = {max_value} * 2{EOL}'
                f'    test_device.{attrib_name} = new_value{EOL}'
                f'    assert test_device.{attrib_name} == new_value{EOL}'
                f'{EOL}{EOL}',
                file=self.ofstream,
                end="",
            )
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
                f'def test_{attrib_name}_min(test_device: tango.DeviceProxy) -> None:{EOL}'
                f'    """{EOL}'
                f'    Test minimum value of {field_type} Tango attribute {attrib_name}.{EOL}'
                f'{EOL}'
                f'    :param test_device: Tango device proxy{EOL}'
                f'    """{EOL}'
                f'    new_value: {field_type}{EOL}'
                f'    print("{attrib_name} : %s" % str(test_device.{attrib_name})){EOL}'
                f'    if {min_value} == 0:{EOL}'
                f'        new_value = {field_type}({min_value} - 1){EOL}'
                f'    elif {min_value} < 0:{EOL}'
                f'        new_value = {field_type}({min_value} * 2){EOL}'
                f'    else:{EOL}'
                f'        new_value = {field_type}({min_value} / 2){EOL}'
                f'    test_device.{attrib_name} = new_value{EOL}'
                f'    assert test_device.{attrib_name} == new_value{EOL}'
                f'{EOL}{EOL}',
                file=self.ofstream,
                end="",
            )

    def print_attribute_test_ro(self, attrib_name: str, field_type: str) -> None:
        """
        Print read-only test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        """
        self.logger.info("Test %s Tango attribute %s (read)", field_type, attrib_name)
        # Read
        if self.skip_tests:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_{attrib_name}_ro(test_device: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test {field_type} Tango attribute {attrib_name} (read).{EOL}'
            f'{EOL}'
            f'    :param test_device: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    attrib_val: {field_type} = test_device.{attrib_name}{EOL}'
            f'    print("{attrib_name} : %s" % str(attrib_val)){EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_command_test(self, command_name: str, attributes: dict) -> None:
        """
        Print write-only test code for device channels.

        :param command_name: attribute name
        :param attributes: dictionary with attributes
        """
        self.logger.info("Test Tango command %s (write-only)", command_name)
        if self.skip_tests:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        elif "pytest" in attributes[command_name]["write"]:
            if self.skip_tests or attributes[command_name]["write"]["pytest"] == "skip":
                print(
                    f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                    file=self.ofstream,
                    end="",
                )
        else:
            pass
        # Write command
        print(
            f'def test_cmd_{command_name}(test_device: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test Tango command {command_name}.{EOL}'
            f'{EOL}'
            f'    :param test_device: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    print("Send command {command_name}"){EOL}'
            f'    test_device.{command_name}(){EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_test(self, attributes: dict, special_attributes: dict) -> None:
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
                self.print_attribute_test_rw(attrib_name, field_type, attributes)
            elif "read" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                self.print_attribute_test_ro(attrib_name, field_type)
            elif "write" in attributes[attrib_name]:
                self.print_command_test(attrib_name, attributes)
            else:
                self.logger.error("Attribute %s has no read or write values", attrib_name)

    def print_attribute_tests(
        self,
        file_path: str | None,
        skip_tests: bool,
        special_attributes: dict,
    ):
        """
        Write code for instrument tests.

        :param file_path: output file e.g. "test_oscilloscope_device.py"
        :param skip_tests: flag all tests to be skipped
        :param special_attributes: attributes for which test code will not be geneated
        """
        dev_attributes: dict
        dev_attributes = self.read_xml_attributes()
        self.skip_tests = skip_tests
        co_file = (
            inspect.currentframe()
            .f_code.co_filename.replace(HOME_PATH, "")
            .replace(PYTHON_PATH, "src")
        )
        if file_path is not None:
            self.logger.info("Write %s test file %s", self.py_class, file_path)
            # pylint: disable-next=consider-using-with
            self.ofstream = open(file_path, "w+", encoding="utf-8")
        else:
            self.logger.info("Write %s tests", self.py_class)
            self.ofstream = sys.stdout
        print(
            f'"""{EOL}'
            f'Tests for instrument Tango device.{EOL}'
            f'{EOL}'
            f'Last update {CURRENT_TIME} by {inspect.currentframe().f_code.co_name}{EOL}'
            f'See {co_file}{EOL}'
            f'"""{EOL}'
            f'{EOL}'
            f'# pylint: disable=too-many-lines{EOL}'
            f'# pylint: disable=too-many-instance-attributes{EOL}'
            f'# pylint: disable=too-many-public-methods{EOL}'
            f'# pylint: disable=duplicate-code{EOL}'
            f'# pylint: disable=line-too-long{EOL}'
            f'{EOL}'
            f'import pytest  # noqa: F401{EOL}'
            f'import tango{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )
        if self.skip_tests:
            print(
                f'@pytest.mark.xfail{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_admin_mode(test_device: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test admin mode read/write.{EOL}'
            f'{EOL}'
            f'    :param test_device: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    print("Set admin mode to 0"){EOL}'
            f'    test_device.adminMode = 0{EOL}'
            f'    assert test_device.adminMode == 0{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )
        self.print_attribute_test(dev_attributes, special_attributes)
        if file_path is not None:
            self.ofstream.close()
            self.format_with_black(file_path)
