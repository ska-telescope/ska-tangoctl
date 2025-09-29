"""Print Tango configuration in Markdown format."""

import ast
import json
import logging
import re
import sys
from typing import Any

from ska_tangoctl.tango_control.progress_bar import progress_bar


def md_format(inp: str) -> str:
    """
    Change string to safe format.

    :param inp: input
    :return: output
    """
    outp: str

    if type(inp) is not str:
        return str(inp)
    outp = inp.replace("/", "\\/").replace("_", "\\_").replace("-", "\\-")
    return outp


def md_print(inp: str, file: Any = sys.stdout, end: str = "\n") -> None:
    """
    Print markdown string.

    :param inp: input
    :param file: output file stream
    :param end: at the end of the line
    """
    print(inp.replace("_", "\\_").replace("-", "\\-"), end=end, file=file)


class TangoJsonReaderMarkdownMixin:
    """Read JSON and print as markdown."""

    outf: Any
    logger: logging.Logger
    tgo_space: str
    devices_dict: dict
    quiet_mode: bool

    def print_markdown_large(self) -> None:  # noqa: C901
        """Print the whole thing."""

        def print_attribute_data(item: str, dstr: str) -> None:
            """
            Print attribute data in various formats.

            :param item: item name
            :param dstr: itmen value
            """
            dstr = re.sub(" +", " ", dstr)
            md_print(f"| {item:30} ", self.outf, end="")
            if not dstr:
                print(f"| {' ':143} ||", file=self.outf)
            elif dstr[0] == "{" and dstr[-1] == "}":
                if "'" in dstr:
                    dstr = dstr.replace("'", '"')
                try:
                    ddict = json.loads(dstr)
                except json.decoder.JSONDecodeError as jerr:
                    # TODO this string breaks it
                    # {
                    # "state": "DevState.ON", "healthState": "HealthState.OK", "ping": "545",
                    # "last_event_arrived": "1709799240.7604482", "unresponsive": "False",
                    # "exception": "", "isSubarrayAvailable": True, "resources": [],
                    # "device_id ": -1, "obsState": "ObsState.EMPTY"
                    # }
                    self.logger.info("Could not read %s- : %s", dstr, str(jerr))
                    print(f"| {dstr:143} ||", file=self.outf)
                    return
                if not self.indent:
                    self.indent = 4
                self.logger.debug("Print JSON :\n%s", json.dumps(ddict, indent=self.indent))
                n = 0
                for ditem in ddict:
                    if n:
                        print(f"| {' ':30} ", end="", file=self.outf)
                    if type(ddict[ditem]) is dict:
                        m = 0
                        for ditem2 in ddict[ditem]:
                            md_print(
                                f"| {ditem:50} | {ditem2:42} | {ddict[ditem][ditem2]:45} |",
                                self.outf,
                            )
                            m += 1
                    elif type(ddict[ditem]) is list or type(ddict[ditem]) is tuple:
                        m = 0
                        for ditem2 in ddict[ditem]:
                            self.logger.debug(
                                "Print attribute value list item %s (%s)", ditem2, type(ditem2)
                            )
                            dname = f"{ditem} {m}"
                            if not m:
                                md_print(f"| {dname:90} ", self.outf, "")
                            else:
                                md_print(f"| {' ':30} | {' ':50} | {dname:90} ", self.outf, "")
                            md_print(f"| {dname:50} ", self.outf, "")
                            if type(ditem2) is dict:
                                p = 0
                                for ditem3 in ditem2:
                                    md_print(f"| {ditem3:42} | {ditem2[ditem3]:45} |", self.outf)
                                    p += 1
                            else:
                                md_print(f"| {ditem2:143}  ||", self.outf)
                            m += 1
                    else:
                        md_print(f"| {ditem:50} | {ddict[ditem]:90} ||", self.outf)
                    n += 1
            elif dstr[0] == "[" and dstr[-1] == "]":
                dlist = ast.literal_eval(dstr)
                self.logger.debug("Print attribute value list %s (%s)", dlist, type(dlist))
                n = 0
                for ditem in dlist:
                    if n:
                        print(f"| {' ':30} ", end="", file=self.outf)
                    if type(ditem) is dict:
                        m = 0
                        for ditem2 in ditem:
                            ditem_val = str(ditem[ditem2])
                            if m:
                                print(f"| {' ':30} ", self.outf, "")
                            md_print(f"| {ditem2:50} ", self.outf, "")
                            md_print(f"| {ditem_val:90} |", self.outf, "")
                            m += 1
                    else:
                        md_print(f"| {str(ditem):143} ||", self.outf)
                    n += 1
            elif "\n" in dstr:
                self.logger.debug("Print attribute value str %s (%s)", dstr, type(dstr))
                n = 0
                for line in dstr.split("\n"):
                    line = line.strip()
                    if line:
                        if n:
                            print(f"| {' ':30} ", self.outf, "")
                        md_print(f"| {line:143} ||", self.outf)
                        n += 1
            else:
                if len(dstr) > 140:
                    lsp = dstr[0:140].rfind(" ")
                    md_print(f" | {dstr[0:lsp]:143} ||", self.outf)
                    md_print(f"| {' ':30}  | {dstr[lsp + 1 :]:143} ||", self.outf)
                else:
                    md_print(f"| {dstr:143} ||", self.outf)
            return

        def print_data(dstr: Any, dc1: int, dc2: int, dc3: int) -> None:
            """
            Print device data.

            :param dstr: data string
            :param dc1: column 1 width
            :param dc2: column 2 width
            :param dc3: column 2 width
            """
            if not dstr:
                md_print(f"| {' ':{dc3}} |", self.outf)
            # elif type(dstr) is list:
            #     for dst in dstr:
            elif type(dstr) is not str:
                md_print(f"| {str(dstr):{dc3}} |", self.outf)
            elif "\n" in dstr:
                self.logger.debug("Print '%s'", dstr)
                n = 0
                for line in dstr.split("\n"):
                    line = line.strip()
                    if line:
                        if n:
                            print(f"| {' ':{dc1}} | {' ':{dc2}}.", self.outf, "")
                        md_print(f"| {line:{dc3}} |", self.outf)
                        n += 1
            elif len(dstr) > dc3 and "," in dstr:
                n = 0
                for line in dstr.split(","):
                    if n:
                        if dc2:
                            print(f"| {' ':{dc1}} | {' ':{dc2}}.", self.outf, "")
                        else:
                            print(f"| {' ':{dc1}} ", self.outf, "")
                    md_print(f"| {line:{dc3}} |", self.outf)
                    n += 1
            else:
                md_print(f"| {str(dstr):{dc3}} |", self.outf)

        def print_md_attributes() -> None:
            """Print attributes."""
            print("### Attributes\n", file=self.outf)
            for attrib in devdict["attributes"]:
                self.logger.debug("Print attribute : %s", attrib)
                print(f"#### {attrib}\n", file=self.outf)
                print("| ITEM | VALUE |       |", file=self.outf)
                print("|:-----|:------|:------|", file=self.outf)
                attrib_data = attrib["data"]
                for item in attrib_data:
                    data = attrib_data[item]
                    if type(data) is str:
                        self.logger.debug("Print attribute str %s : %s", item, data)
                        print_attribute_data(item, data)
                    elif type(data) is dict:
                        self.logger.debug("Print attribute dict %s : %s", item, data)
                        n = 0
                        for item2 in data:
                            print_attribute_data(item2, str(data[item2]))
                            n += 1
                    elif type(data) is list:
                        self.logger.debug("Print attribute list %s : %s", item, data)
                        n = 0
                        for item2 in data:
                            if not n:
                                md_print(f"| {str(item):30} ", self.outf, "")
                            else:
                                print(f"| {' ':30} ", self.outf, "")
                            md_print(f"| {str(item2):143} ||", self.outf)
                            n += 1
                    else:
                        self.logger.warning(
                            "Data type for %s (%s) not supported", item, type(data)
                        )
                if "config" in attrib:
                    for item in attrib["config"]:
                        config = attrib["config"][item]
                        try:
                            print_attribute_data(item, str(config))
                        except TypeError:
                            # TODO handle this properly
                            pass
                print("\n*******\n", file=self.outf)
            print("\n", file=self.outf)

        def print_md_commands() -> None:
            """Print commands."""
            cc1: int = 30
            cc2: int = 50
            cc3: int = 90
            n: int = 0
            cmd: str

            print("### Commands\n", file=self.outf)
            print(f"| {'NAME':{cc1}} | {'FIELD':{cc2}} | {'VALUE':{cc3}} |", file=self.outf)
            print(f"|:{'-' * cc1}-|:{'-' * cc2}-|:{'-' * cc3}-|", file=self.outf)
            for cmd in devdict["commands"]:
                print(f"| {cmd:{cc1}} ", end="", file=self.outf)
                m = 0
                cmd_items = devdict["commands"][cmd]
                self.logger.debug("Print command %s : %s", cmd, cmd_items)
                if cmd_items:
                    for item in cmd_items:
                        if m:
                            print(f"| {' ':{cc1}} ", end="", file=self.outf)
                        md_print(f"| {item:{cc2}} ", end="", file=self.outf)
                        print_data(devdict["commands"][cmd][item], cc1, cc2, cc3)
                        m += 1
                else:
                    md_print(f"| {' ':{cc2}} | {' ':{cc3}} |", file=self.outf)
                n += 1
            print("\n*******\n", file=self.outf)

        def print_md_properties() -> None:
            """Print properties."""
            pc1: int = 40
            pc2: int = 133
            prop: str

            print("### Properties\n", file=self.outf)
            print(f"| {'NAME':{pc1}} | {'VALUE':{pc2}} |", file=self.outf)
            print(f"|:{'-' * pc1}-|:{'-' * pc2}-|", file=self.outf)
            for prop in devdict["properties"]:
                self.logger.debug(
                    "Print command %s : %s", prop, devdict["properties"][prop]["value"]
                )
                md_print(f"| {prop:{pc1}} ", end="", file=self.outf)
                print_data(devdict["properties"][prop]["value"], pc1, 0, pc2)
            print("\n*******\n", file=self.outf)

        device: str

        print(f"# Tango devices in {self.tgo_space}\n", file=self.outf)
        self.logger.debug("Reading %d JSON devices", len(self.devices_dict))
        for devdict in progress_bar(
            self.devices_dict["devices"],
            not self.quiet_mode,
            prefix=f"Read {len(self.devices_dict)} JSON devices :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            device = devdict["name"]
            self.logger.debug("Print device %s", device)
            md_print(f"## Device {devdict['name']}\n", file=self.outf)
            print("| FIELD | VALUE |", file=self.outf)
            print("|:------|:------|", file=self.outf)
            print(f"| version | {devdict['version']} |", file=self.outf)
            print(f"| device access| {devdict['device_access']} |", file=self.outf)
            if "adminMode" in devdict:
                print(f"| Admin mode | {devdict['adminMode']} |", file=self.outf)
            if "info" in devdict:
                md_print(f"| Device class | {devdict['info']['dev_class']} |", file=self.outf)
                md_print(f"| Server host | {devdict['info']['server_host']} |", file=self.outf)
                md_print(f"| Server ID | {devdict['info']['server_id']} |", file=self.outf)
            print("\n*******\n", file=self.outf)
            print_md_attributes()
            print_md_commands()
            print_md_properties()
            print("\n", file=self.outf)
