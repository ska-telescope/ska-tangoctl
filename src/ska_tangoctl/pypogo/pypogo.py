#!/usr/bin/env python
"""Generate Python code for Tango devices."""

# pylint: disable-next=redefined-builtin
__package__ = "ska_mid_dish_spfc_builder"

import getopt
import logging
import os
import sys

from ska_tangoctl.pypogo.pypogo_proc import PyPogoPrintCode
from ska_tangoctl.pypogo.pypogo_globals import DEFAULT_TYPE

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
_module_logger = logging.getLogger("pypogo")


def usage(p_name) -> None:
    """
    Print a helpful message.

    :param p_name: program name
    """
    print(f"Usage:\n\t{p_name} --input=<FILE> [--output=<FILE>]")
    print(f"Usage:\n\t{p_name} --python --input=<FILE> [--output=<FILE>]")
    print(f"Usage:\n\t{p_name} --pytest --input=<FILE> [--attribute=<ATTRIB>] [--command=<CMD>] [--fdelta=<FLOAT>] [--idelta=<INT>]] [--output=<FILE>]")
    print(f"Where:")
    print("\t--python\t\t Generate Python code")
    print("\t--pytest\t\t Generate Python tests")
    print("\t--attribute=<ATTRIB>\t Filter attributes")
    print("\t--command=<CMD>\t\t Filter commands")
    print("\t--fdelta\t\t Float value change")
    print("\t--idelta\t\t Integer value change")
    print("\t--get-set\t\t Use getter and setter functions")
    print("\t--test-equipment\t Generate YAML file in test equipment format")


# pylint: disable-next=too-many-branches
def main() -> int:  # noqa: C901
    """
    Start here.

    :returns: error condition
    """
    input_filename: str | None = None
    output_filename: str | None = None
    attrib_filter: str | None = None
    cmd_filter: str | None = None
    do_list: bool = False
    do_tests: bool = False
    do_testeq: bool = False
    do_code: bool = False
    do_get_set: bool = False
    default_type: str = DEFAULT_TYPE
    fdelta: float | None = None
    idelta: int | None = None

    y_arg: list = sys.argv
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "hvV",
            [
                "help",
                "get-set",
                "list",
                "pytest",
                "python",
                "test-equipment",
                "attribute=",
                "command=",
                "fdelta=",
                "idelta=",
                "input=",
                "output=",
            ],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt == "--get-set":
            logging.info("Use getter and setter functions")
            do_get_set = True
        elif opt == "--list":
            logging.info("List attributes")
            do_list = True
        elif opt == "--pytest":
            logging.info("Generate Python tests")
            do_tests = True
        elif opt == "--test-equipment":
            logging.info("Generate YAML file in test equipment format")
            do_testeq = True
        elif opt == "--python":
            logging.info("Generate Python code")
            do_code = True
        elif opt == "--attribute":
            attrib_filter = arg
        elif opt == "--command":
            cmd_filter = arg
        elif opt == "--fdelta":
            fdelta = float(arg)
        elif opt == "--idelta":
            idelta = int(arg)
        elif opt == "--input":
            input_filename = arg
        elif opt == "--output":
            output_filename = arg
        elif opt == "--type":
            default_type = arg
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    if input_filename is None:
        logging.error("No XML file specified")
        return 1

    pypogo = PyPogoPrintCode(_module_logger, default_type, do_get_set)
    if do_tests:
        _module_logger.debug("Print Python tests:\n%s", pypogo)
        pypogo.read_file(input_filename)
        pypogo.print_python_tests(
            output_filename, False, {}, idelta, fdelta, attrib_filter, cmd_filter,
        )
    elif do_testeq:
        _module_logger.debug("Print YAML in test equipment format:\n%s", pypogo)
        pypogo.read_file(input_filename)
        pypogo.print_testeq_yaml(output_filename)
    elif do_code:
        pypogo.read_file(input_filename)
        pypogo.print_python_code(output_filename, False, {})
    elif do_list:
        pypogo.read_file(input_filename)
        pypogo.read_xml_attributes(attrib_filter)
        pypogo.read_xml_commands(cmd_filter)
        pypogo.list()
    else:
        pypogo.read_file(input_filename)
        print(pypogo)

    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        if sys.argv[1] == "-v":
            _module_logger.setLevel(logging.INFO)
        elif sys.argv[1] == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            pass
    main()
