#!/usr/bin/env python
"""Generate Python code for Tango devices."""

# pylint: disable-next=redefined-builtin
__package__ = "ska_mid_dish_spfc_builder"

import getopt
import logging
import os
import sys

from pypogo_proc import PyPogoPrintCode

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
_module_logger = logging.getLogger("pypogo")


def usage(p_name) -> None:
    """
    Print a helpful message.

    :param p_name: program name
    """
    print(f"Usage:\n\t{p_name} --input=<FILE> [--tests] [--output=<FILE>]")


# pylint: disable-next=too-many-branches
def main() -> int:  # noqa: C901
    """
    Start here.

    :returns: error condition
    """
    xml_filename: str | None = None
    python_filename: str | None = None
    do_tests: bool = False
    do_code: bool = False

    y_arg: list = sys.argv
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "hvV",
            [
                "help",
                "pytest",
                "python",
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
        elif opt == "--pytest":
            logging.info("Generate Python tests")
            do_tests = True
        elif opt == "--python":
            logging.info("Generate Python code")
            do_code = True
        elif opt == "--input":
            xml_filename = arg
        elif opt == "--output":
            python_filename = arg
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    if xml_filename is None:
        logging.error("No XML file specified")
        return 1

    pypogo = PyPogoPrintCode(_module_logger, xml_filename)
    if do_tests:
        _module_logger.debug("Print Python tests:\n%s", pypogo)
        pypogo.print_attribute_tests(python_filename, False, {})
    elif do_code:
        pypogo.print_python_code(python_filename, False, {})
    else:
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
