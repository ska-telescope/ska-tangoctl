"""Read and display Tango stuff."""

import ast
import json
import logging
import os
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


class TangoJsonReader:
    """Read JSON and print as markdown or text."""

    logger: logging.Logger

    def __init__(
        self,
        logger: logging.Logger,
        indent: int,
        quiet_mode: bool,
        kube_namespace: str | None,
        devsdict: dict,
        outf: Any,
    ):
        """
        Rock and roll.

        :param logger: logging handle
        :param indent: indentation for JSON and YAML
        :param quiet_mode: flag for displaying progress bar
        :param kube_namespace: Kubernetes namespace
        :param devsdict: dictionary with device data
        :param outf: output file stream
        """
        self.outf: Any = outf
        self.tgo_space: str
        self.quiet_mode: bool
        self.devices_dict: dict
        tango_host: str | None

        self.logger = logger
        self.devices_dict = devsdict
        # Get Tango database host
        tango_host = os.getenv("TANGO_HOST")
        if kube_namespace is not None:
            self.tgo_space = f"namespace {kube_namespace}"
        else:
            self.tgo_space = f"host {tango_host}"
        self.quiet_mode = quiet_mode
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True
        self.indent: int
        if not indent:
            self.indent = indent
        else:
            self.indent = 4
        self.logger.debug("Load JSON : %s", json.dumps(self.devices_dict, indent=4, default=str))

    def __del__(self) -> None:
        """Destructor."""
        self.logger.debug("Shut down TangoJsonReader for %s", self.tgo_space)

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

    def print_html_large(self, html_body: bool) -> None:  # noqa: C901
        """
        Print the whole thing.

        :param html_body: print HTML header and footer
        """

        def print_html_attribute_data(dstr: str) -> None:
            """
            Print attribute data in various formats.

            :param dstr: itmen value
            """
            dstr = re.sub(" +", " ", dstr)
            if not dstr:
                print("&nbsp;", file=self.outf)
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
                    print(f"<pre>{dstr}</pre>", file=self.outf)
                    return
                if not self.indent:
                    self.indent = 4
                self.logger.debug("Print JSON :\n%s", json.dumps(ddict, indent=self.indent))
                for ditem in ddict:
                    print(f'<table><tr><td class="tangoctl">{ditem}</td>', file=self.outf)
                    if type(ddict[ditem]) is dict:
                        print('<td class="tangoctl"><table>', file=self.outf)
                        for ditem2 in ddict[ditem]:
                            print(
                                f'<tr><td class="tangoctl2">{ditem}</td>'
                                f'<td class="tangoctl2">{ditem2}</td>'
                                f'<td class="tangoctl2">{ddict[ditem][ditem2]}</td></tr>',
                                file=self.outf,
                            )
                        print("</table>", file=self.outf)
                    elif type(ddict[ditem]) is list or type(ddict[ditem]) is tuple:
                        print("<table>", file=self.outf)
                        for ditem2 in ddict[ditem]:
                            print("<tr>", file=self.outf)
                            self.logger.debug(
                                "Print attribute value list item %s (%s)", ditem2, type(ditem2)
                            )
                            print(f'<td class="tangoctl">{ditem}</td>', file=self.outf)
                            if type(ditem2) is dict:
                                print('<td class="tangoctl"><table>', file=self.outf)
                                for ditem3 in ditem2:
                                    print(
                                        f'<tr><td class="tangoctl2">{ditem3}</td>'
                                        f'<td class="tangoctl2">{ditem2[ditem3]}</td></tr>',
                                        file=self.outf,
                                    )
                                print("</table></td>", file=self.outf)
                            else:
                                print(f'<td colspan="2">{ditem2}</td>', file=self.outf)
                            print("</tr>", file=self.outf)
                        print("</table>", file=self.outf)
                    else:
                        print(
                            f'<td class="tangoctl">{ditem}</td>'
                            f'<td class="tangoctl">{ddict[ditem]}</td>',
                            file=self.outf,
                        )
                    print("</td></tr></table>", file=self.outf)
            elif dstr[0] == "[" and dstr[-1] == "]":
                dlist: Any = ast.literal_eval(dstr)
                self.logger.debug("Print attribute value list %s (%s)", dlist, type(dlist))
                n = 0
                print("<table>", file=self.outf)
                for ditem in dlist:
                    if type(ditem) is dict:
                        for ditem2 in ditem:
                            ditem_val = str(ditem[ditem2])
                            print(
                                f'<tr><td class="tangoctl">{ditem2}</td>', end="", file=self.outf
                            )
                            print(f'<td class="tangoctl">{ditem_val}</td></tr>', file=self.outf)
                    else:
                        print(f'<tr><td colspan="2">{str(ditem)}</td></tr>', file=self.outf)
                    n += 1
                print("</table>", file=self.outf)
            elif "\n" in dstr:
                line: str
                self.logger.debug("Print attribute value str %s (%s)", dstr, type(dstr))
                print("<pre>", file=self.outf)
                for line in dstr.split("\n"):
                    line = line.strip()
                    if line:
                        print(f"{line}", file=self.outf)
                print("</pre>", file=self.outf)
            else:
                print("<pre>", file=self.outf)
                print(f"{dstr}", file=self.outf)
                print("</pre>", file=self.outf)
            return

        def print_html_data(dstr: str) -> None:
            """
            Print device data.

            :param dstr: data string
            """
            line: str
            if not dstr:
                print("&nbsp;", file=self.outf)
            elif type(dstr) is not str:
                print(f"{str(dstr)}", file=self.outf)
            elif "\n" in dstr:
                self.logger.debug("Print '%s'", dstr)
                print("<pre>", file=self.outf)
                for line in dstr.split("\n"):
                    line = line.strip()
                    if line:
                        print(f"{line}", file=self.outf)
                print("</pre>", file=self.outf)
            elif "," in dstr:
                print("<pre>", file=self.outf)
                for line in dstr.split(","):
                    print(f"{line}", file=self.outf)
                print("</pre>", file=self.outf)
            else:
                print(f"{dstr}", file=self.outf)

        def print_html_attributes() -> None:
            """Print attributes."""
            attrib: str
            attrib_data: Any
            data: Any
            item2: Any
            config: Any

            print("<h3>Attributes</h3>", file=self.outf)
            for attrib in devdict["attributes"]:
                print(f"<h4>{attrib}</h4>\n", file=self.outf)
                print("<table>", file=self.outf)
                print(
                    '<tr><th class="tangoctl">ITEM</th>'
                    '<th colspan="2" class="tangoctl">VALUE</th></tr>',
                    file=self.outf,
                )
                attrib_data = devdict["attributes"][attrib]["data"]
                for item in attrib_data:
                    data = attrib_data[item]
                    print(
                        f'<tr><td style="vertical-align: top">{item}</td><td class="tangoctl">',
                        file=self.outf,
                    )
                    if type(data) is str:
                        self.logger.debug("Print attribute str %s : %s", item, data)
                        print_html_attribute_data(data)
                    elif type(data) is dict:
                        self.logger.debug("Print attribute dict %s : %s", item, data)
                        for item2 in data:
                            print_html_attribute_data(str(data[item2]))
                    elif type(data) is list:
                        self.logger.debug("Print attribute list %s : %s", item, data)
                        print("<table>", file=self.outf)
                        for item2 in data:
                            print(
                                '<tr><td class="tangoctl">&nbsp;<td class="tangoctl">',
                                end="",
                                file=self.outf,
                            )
                            print(f'<td class="tangoctl">{str(item2)}</td></tr>', file=self.outf)
                        print("</table>", file=self.outf)
                    else:
                        print(
                            "Data type for %s (%s) not supported", item, type(data), file=self.outf
                        )
                    print("</td></tr>", file=self.outf)
                if "config" in devdict["attributes"][attrib]:
                    for item in devdict["attributes"][attrib]["config"]:
                        print(
                            f'<tr><td class="tangoctl">{item}</td><td class="tangoctl">',
                            file=self.outf,
                        )
                        config = devdict["attributes"][attrib]["config"][item]
                        print_html_attribute_data(config)
                        print("</td></tr>", file=self.outf)
                print("</table>", file=self.outf)

        def print_html_commands() -> None:
            """Print commands."""
            cmd: str
            cmd_items: Any
            item: Any

            print("<h3>Commands</h3>", file=self.outf)
            print("<table>", file=self.outf)
            print(
                '<tr><th class="tangoctl">NAME</th><th class="tangoctl">FIELD VALUE</th></tr>',
                file=self.outf,
            )
            for cmd in devdict["commands"]:
                cmd_items = devdict["commands"][cmd]
                self.logger.debug("Print command %s : %s", cmd, cmd_items)
                print(
                    f'<tr><td style="vertical-align: top">{cmd}</td><td class="tangoctl">',
                    file=self.outf,
                )
                if cmd_items:
                    print("<table>", file=self.outf)
                    for item in cmd_items:
                        print(
                            f'<tr><td class="tangoctl2">{item}</td><td class="tangoctl2">',
                            end="",
                            file=self.outf,
                        )
                        print_html_data(devdict["commands"][cmd][item])
                        print("</td></tr>", file=self.outf)
                    print("</table>", file=self.outf)
                print("</td></tr>", file=self.outf)
            print("</table>", file=self.outf)

        def print_html_properties() -> None:
            """Print properties."""
            prop: str

            print("<h3>Properties</h3>", file=self.outf)
            print("<table>", file=self.outf)
            print(
                '<tr><th class="tangoctl">NAME</th><th class="tangoctl">VALUE</th></tr>',
                file=self.outf,
            )
            for prop in devdict["properties"]:
                self.logger.debug(
                    "Print command %s : %s", prop, devdict["properties"][prop]["value"]
                )
                print(
                    f'<tr><td style="vertical-align: top">{prop}</td><td class="tangoctl">',
                    file=self.outf,
                )
                print_html_data(devdict["properties"][prop]["value"])
                print("</td></tr>", file=self.outf)
            print("</table>", file=self.outf)

        if html_body:
            print("<html><body>", file=self.outf)
        print(f"<h1>Tango devices in {self.tgo_space}</h1>\n", file=self.outf)
        self.logger.debug("Reading %d HTML devices", len(self.devices_dict))
        for device in progress_bar(
            self.devices_dict,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices_dict)} JSON devices :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.logger.debug("Print device %s", device)
            devdict = self.devices_dict[device]
            print(f"<h2>Device {devdict['name']}</h2>\n", file=self.outf)
            print("<table>", file=self.outf)
            print(
                '<tr><th class="tangoctl">FIELD</th>'
                '<th colspan="3" class="tangoctl">VALUE</th></tr>',
                file=self.outf,
            )
            print(
                '<tr><td class="tangoctl">version</td>'
                f'<td colspan="3" class="tangoctl">{devdict["version"]}</td></tr>',
                file=self.outf,
            )
            print(
                f'<tr><td class="tangoctl">device access</td>'
                f'<td colspan="3" class="tangoctl">{devdict["device_access"]}</td></tr>',
                file=self.outf,
            )
            if "adminMode" in devdict:
                print(
                    "<tr>"
                    f'<td class="tangoctl">Admin mode</td>'
                    f'<td colspan="3" class="tangoctl">{devdict["adminMode"]}'
                    "</td></tr>",
                    file=self.outf,
                )
            if "info" in devdict:
                print(
                    '<tr><td class="tangoctl">Device class</td>'
                    f'<td colspan="3">{devdict["info"]["dev_class"]}</td></tr>',
                    file=self.outf,
                )
                print(
                    '<tr><td class="tangoctl">Server host</td>'
                    f'<td colspan="3" class="tangoctl">{devdict["info"]["server_host"]}</td></tr>',
                    file=self.outf,
                )
                print(
                    '<tr><td class="tangoctl">Server ID</td>'
                    f'<td colspan="3" class="tangoctl">{devdict["info"]["server_id"]}</td></tr>',
                    file=self.outf,
                )
            print("</table>", file=self.outf)
            print_html_attributes()
            print_html_commands()
            print_html_properties()
        if html_body:
            print("</body></html>", file=self.outf)

    def print_txt_large(self) -> None:  # noqa: C901
        """Print the whole thing."""
        # TODO use(d) for debugging
        DELIMS: dict
        # DELIMS = {
        #     "all": " ",
        #     "dict_list": "!",
        #     "dict_dict": "#",
        #     "dict_para": "@",
        #     "dict_csv": ";",
        #     "dict_int": "*",
        #     "dict_float": "%",
        #     "dict_str": "$",
        #     "list": "|",
        #     "str": "+",
        # }
        DELIMS = {
            "all": " ",
            "dict_list": " ",
            "dict_dict": " ",
            "dict_para": " ",
            "dict_csv": " ",
            "dict_int": " ",
            "dict_float": " ",
            "dict_str": " ",
            "list": " ",
            "str": " ",
        }

        delim_t: str = DELIMS["all"]

        def print_text_stuff(stuff: str) -> None:
            """
            Print attribute, command or property.

            :param stuff: name of the thing
            """

            def print_dict_list(l_tj: int) -> None:
                """
                Print list in dict.

                :param l_tj: item number
                """
                delim: str = DELIMS["dict_list"]
                self.logger.debug(
                    "Print list %d in dict %s : %s (%d)",
                    tj,
                    devkey2,
                    devkeyval2,
                    len(devkeyval2),
                )
                print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                if len(devkeyval2) == 0:
                    print("[]", file=self.outf)
                elif len(devkeyval2) == 1:
                    if type(devkeyval2[0]) is not str:
                        # TODO fix this
                        # if l_tj:
                        #     print(f"{' ':143}{delim}", file=self.outf, end="")
                        print(f"{str(devkeyval2[0])}", file=self.outf)
                    elif "," in devkeyval2[0]:
                        l_keyvals = devkeyval2[0].split(",")
                        l_keyval = l_keyvals[0]
                        print(f"{l_keyval}", file=self.outf)
                        for l_keyval in l_keyvals[1:]:
                            print(f"{' ':102}{delim}{l_keyval}", file=self.outf)
                    else:
                        if l_tj:
                            print(f"{' ':102}{delim}", file=self.outf, end="")
                        print(f"{devkeyval2[0]}", file=self.outf)
                else:
                    n = 0
                    for l_keyval in devkeyval2:
                        if n:
                            print(f"{' ':102}{delim}", file=self.outf, end="")
                        print(f"{l_keyval}", file=self.outf)
                        n += 1

            def print_dict_dict(d_tj: int) -> None:
                """
                Print dict in dict.

                :param d_tj: item number
                """
                delim: str = DELIMS["dict_dict"]
                self.logger.debug(
                    "Print %d/%d dict in dict %s : %s", d_tj, pi, devkey2, devkeyval2
                )
                print(f"{' ':102}{delim}{devkey2:40}", file=self.outf)
                n = 0
                for d_keyval in devkeyval2:
                    if type(devkeyval2[d_keyval]) is dict:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "Print %d/%d dict in dict in dict %s : %s",
                            n,
                            dd_len,
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}", end="", file=self.outf)
                        m = 0
                        for item2 in devkeyval2[d_keyval]:
                            if m:
                                print(f"{' ':143}{delim}{' ':40}{delim}", end="", file=self.outf)
                            print(
                                f"{' ':143}{delim}{' ':40} {item2} {devkeyval2[d_keyval][item2]}",
                                end="",
                                file=self.outf,
                            )
                            m += 1
                    elif type(devkeyval2[d_keyval]) is list:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "Print %d/%d list in dict in dict %s : %s",
                            n,
                            dd_len,
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if dd_len == 0:
                            print(f"{' ':102}{delim}{d_keyval:40}{delim}[]", file=self.outf)
                        elif dd_len == 1:
                            print(
                                f"{' ':102}{delim}{d_keyval:40}{delim}{devkeyval2[d_keyval][0]}",
                                file=self.outf,
                            )
                        else:
                            print(
                                f"{' ':102}{delim}{d_keyval:40}{delim}{devkeyval2[d_keyval][0]}",
                                file=self.outf,
                            )
                            m = 0
                            for d_item in devkeyval2[d_keyval][1:]:
                                print(f"{' ':143}{delim}", end="", file=self.outf)
                                if type(d_item) is dict:
                                    k = 0
                                    for key2 in d_item:
                                        if k:
                                            print(
                                                f"{' ':143}{delim}",
                                                end="",
                                                file=self.outf,
                                            )
                                        print(
                                            f" {key2:32}{delim}{d_item[key2]}",
                                            file=self.outf,
                                        )
                                        k += 1
                                else:
                                    print(f"{delim}{d_item}", file=self.outf)
                                m += 1
                    elif type(devkeyval2[d_keyval]) is not str:
                        self.logger.debug(
                            "Print %d %s in dict in dict %s : %s",
                            n,
                            type(devkeyval2[d_keyval]),
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not n:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        else:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}", end="", file=self.outf)
                        print(f"{devkeyval2[d_keyval]}", file=self.outf)
                    else:
                        self.logger.debug(
                            "Print %d/%d string in dict in dict %s : %s",
                            n,
                            len(devkeyval2[d_keyval]),
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not n:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        else:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}{devkeyval2[d_keyval]}", file=self.outf)
                    n += 1

            def print_dict_para(p_tj: int) -> None:
                """
                Print paragraph in dict.

                :param p_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("Print %d paragraph in dict : %s", p_tj, devkeyval2)
                if not p_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102} {devkey2:40}{delim}", file=self.outf, end="")
                p_keyvals = devkeyval2.split("\n")
                # Remove empty lines
                p_keyvals2 = []
                for p_keyval in p_keyvals:
                    p_keyval2 = p_keyval.strip()
                    if p_keyval2:
                        if len(p_keyval2) > 70:
                            lsp = p_keyval2[0:70].rfind(" ")
                            p_keyvals2.append(p_keyval2[0:lsp])
                            p_keyvals2.append(p_keyval2[lsp + 1 :])
                        else:
                            p_keyvals2.append(" ".join(p_keyval2.split()))
                print(f"{p_keyvals2[0]}", file=self.outf)
                for p_keyval2 in p_keyvals2[1:]:
                    print(f"{' ':102}{delim}{p_keyval2}", file=self.outf)

            def print_dict_csv(c_tj: int) -> None:
                """
                Print CSV string in dict.

                :param c_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("Print %d CSV in dict %s", c_tj, devkeyval2)
                if not c_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                c_keyvals = devkeyval2.split(",")
                c_keyval = c_keyvals[0]
                print(f"{c_keyval}", file=self.outf)
                for c_keyval in c_keyvals[1:]:
                    print(f"{' ':102}{c_keyval}", file=self.outf)

            def print_dict_int(s_tj: int) -> None:
                """
                Print int in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                print(f"{devkeyval2}", file=self.outf)

            def print_dict_float(s_tj: int) -> None:
                """
                Print float in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                print(f"{devkeyval2}", file=self.outf)

            def print_dict_str(s_tj: int) -> None:
                """
                Print string in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["dict_str"]
                self.logger.debug("Print %d string in dict %s : '%s'", s_tj, devkey2, devkeyval2)
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                s_keyvals2 = []
                if len(devkeyval2) > 70:
                    lsp = devkeyval2[0:70].rfind(" ")
                    s_keyvals2.append(devkeyval2[0:lsp])
                    s_keyvals2.append(devkeyval2[lsp + 1 :])
                else:
                    s_keyvals2.append(" ".join(devkeyval2.split()))
                print(f"{s_keyvals2[0]}{delim}", file=self.outf)
                for s_keyval2 in s_keyvals2[1:]:
                    print(f"{' ':102}{delim}{s_keyval2}", file=self.outf)

            def print_list(l_tj: int) -> None:
                """
                Print list.

                :param l_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("*** Print %d list %s : %s", l_tj, devkey, devkeyval)
                if not l_tj:
                    print(f"{devkey:40}{delim}", end="", file=self.outf)
                else:
                    print(f"{' ':102}{delim}{devkey:40}{delim}", end="", file=self.outf)
                if len(devkeyval) == 1:
                    if "," in devkeyval[0]:
                        l_keyvals = devkeyval[0].split(",")
                        l_keyval = l_keyvals[0]
                        print(f"{l_keyval.strip()}", file=self.outf)
                        for l_keyval in l_keyvals[1:]:
                            if "\n" in l_keyval:
                                n = 0
                                for line in l_keyval.split("\n"):
                                    if line:
                                        if n:
                                            print(f"{' ':102}", file=self.outf, end="")
                                        print(f" {line.strip()}", file=self.outf)
                                    n += 1
                            else:
                                print(f"{' ':102} {l_keyval.strip()}", file=self.outf)
                    else:
                        print(f"{' ':102} {devkeyval[0]}", file=self.outf)
                else:
                    print(f"{devkeyval}", file=self.outf)

            def print_str(s_tj: int) -> None:
                """
                Print string value.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("*** Print %d string %s : %s", s_tj, devkey, devkeyval)
                if not s_tj:
                    print(f"{devkey:40}{delim}", end="", file=self.outf)
                else:
                    print(f"{' ':102}{delim}{devkey:40}{delim}", end="", file=self.outf)
                if not devkeyval:
                    print(file=self.outf)
                elif type(devkeyval) is str:
                    if "\n" in devkeyval:
                        s_keyvals = devkeyval.split("\n")
                        # Remove empty lines
                        s_keyvals2 = []
                        for s_keyval in s_keyvals:
                            s_keyval2 = s_keyval.strip()
                            if s_keyval2:
                                if len(s_keyval2) > 70:
                                    lsp = s_keyval2[0:70].rfind(" ")
                                    s_keyvals2.append(s_keyval2[0:lsp])
                                    s_keyvals2.append(s_keyval2[lsp + 1 :])
                                else:
                                    s_keyvals2.append(" ".join(s_keyval2.split()))
                        print(f"{s_keyvals2[0]}", file=self.outf)
                        for s_keyval2 in s_keyvals2[1:]:
                            print(f"{' ':102}{delim}{s_keyval2}", file=self.outf)
                    elif "," in devkeyval:
                        s_keyvals = devkeyval.split(",")
                        s_keyval = s_keyvals[0]
                        print(f"{s_keyval.strip()}", file=self.outf)
                        for s_keyval in s_keyvals[1:]:
                            print(f"{' ':102} {s_keyval.strip()}", file=self.outf)
                    elif len(devkeyval) > 70:
                        s_keyvals2 = []
                        lsp = devkeyval[0:70].rfind(" ")
                        s_keyvals2.append(devkeyval[0:lsp])
                        s_keyvals2.append(devkeyval[lsp + 1 :])
                        print(f"{s_keyvals2[0]}", file=self.outf)
                        for s_keyval2 in s_keyvals2[1:]:
                            print(f"{' ':102} {s_keyval2}", file=self.outf)
                    else:
                        print(f"{devkeyval}", file=self.outf)
                elif type(devkeyval) is list:
                    print(f"{devkeyval[0]}", file=self.outf)
                    for s_keyval2 in devkeyval[1:]:
                        print(f"{' ':102} {s_keyval2}", file=self.outf)
                else:
                    print(f"{devkeyval}", file=self.outf)

            key: str
            ti: int
            tj: int
            devkeys: Any
            devkey: Any
            devkeyval: Any
            devkeyval2: Any

            self.logger.debug("Print %d %s: %s", len(devdict[stuff]), stuff, devdict[stuff])
            if not devdict[stuff]:
                return
            print(f"{stuff:20}{delim_t}", end="", file=self.outf)
            if not devdict[stuff]:
                print(file=self.outf)
                return
            ti = 0
            for item in devdict[stuff]:
                self.logger.debug("* Print %d item : %s", ti, item)
                for key in item:
                    if not ti:
                        try:
                            print(f"{key:40}{delim_t}", end="", file=self.outf)
                        except TypeError:
                            logging.warning("Could not print '%s' (%s)", key, type(key))
                    else:
                        print(f"{' ':20}{delim_t}{key:40}{delim_t}", end="", file=self.outf)
                    ti += 1
                    devkeys = item[key]
                    self.logger.debug("** Print item %s keys : %s", key, devkeys)
                    if type(devkeys) is not dict:
                        print(f"{devkeys}", file=self.outf)
                        continue
                    if not devkeys:
                        print("{}", file=self.outf)
                        continue
                    tj = 0
                    for devkey in devkeys:
                        devkeyval = devkeys[devkey]
                        if type(devkeyval) is dict:
                            pi = 0
                            self.logger.debug("*** Print %d dict %s : %s", tj, devkey, devkeyval)
                            print(f"{' ':61}{delim_t}{devkey:40}{delim_t}", file=self.outf)
                            # Read dictionary value
                            for devkey2 in devkeyval:
                                devkeyval2 = devkeyval[devkey2]
                                if type(devkeyval2) is list:
                                    print(file=self.outf)
                                    print_dict_list(tj)
                                elif type(devkeyval2) is dict:
                                    print(file=self.outf)
                                    print_dict_dict(tj)
                                    pi = tj
                                elif type(devkeyval2) is int:
                                    print_dict_int(tj)
                                elif type(devkeyval2) is float:
                                    print_dict_float(tj)
                                elif "\n" in devkeyval2:
                                    print_dict_para(tj)
                                elif "," in devkeyval2:
                                    print_dict_csv(tj)
                                elif not devkeyval2:
                                    print(file=self.outf)
                                else:
                                    print_dict_str(tj)
                                tj += 1
                        elif type(devkeyval) is list:
                            print_list(tj)
                            tj += 1
                        else:
                            self.logger.debug("Print %d string : %s", tj, devkeyval)
                            print_str(tj)
                            tj += 1

        def print_text_properties() -> None:
            """Print device properties in text format."""
            ti: int
            prop_name: str
            prop_vals: Any

            self.logger.debug(
                "Print %d properties: %s", len(devdict["properties"]), devdict["properties"]
            )
            if not devdict["properties"]:
                return
            print(f"{'properties':20} ", end="", file=self.outf)
            if not devdict["properties"]:
                print(file=self.outf)
                return
            ti = 0
            for propdict in devdict["properties"]:
                prop_name = propdict["name"]
                if not ti:
                    print(f"{prop_name:40} {'value':40} ", end="", file=self.outf)
                else:
                    print(f"{' ':20} {prop_name:40} {'value':40} ", end="", file=self.outf)
                ti += 1
                if "value" in propdict:
                    prop_vals = propdict["value"]
                else:
                    prop_vals = None
                if not prop_vals:
                    print(file=self.outf)
                    continue
                elif type(prop_vals) is list:
                    print(f"{prop_vals[0]}", file=self.outf)
                    for prop_val in prop_vals[1:]:
                        print(f"{' ':102} {prop_val}", file=self.outf)

        def print_text_pod() -> None:
            """Print pod information."""
            self.logger.debug("Print pod :\n%s", json.dumps(devdict, indent=4, default=str))
            if "pod" not in devdict:
                return
            if not devdict["pod"]:
                return
            print(f"{' ':20} {'pod':40} {'name':40} {devdict['pod']['metadata']['name']}")
            print(f"{' ':20} {' ':40} {'api_version':40} {devdict['pod']['api_version']}")
            print(f"{' ':20} {' ':40} {'phase':40} {devdict['pod']['status']['phase']}")
            print(f"{' ':20} {' ':40} {'start_time':40} {devdict['pod']['status']['start_time']}")
            print(f"{' ':20} {' ':40} {'host_ip':40} {devdict['pod']['status']['host_ip']}")
            print(f"{' ':20} {' ':40} {'pod_ip':40} {devdict['pod']['status']['pod_ip']}")
            ports: list = []
            for container in devdict["pod"]["spec"]["containers"]:
                for port in container["ports"]:
                    ports.append(str(port["container_port"]))
            print(f"{' ':20} {' ':40} {'ports':40} {','.join(ports)}")
            if devdict["processes"]["output"]:
                proc = devdict["processes"]["output"][0]
                psef = " ".join((" ".join(proc.split())).split(" ")[7:])
                print(f"{' ':20} {'process':40} {psef}")
                if len(devdict["processes"]["output"]) > 1:
                    for proc in devdict["processes"]["output"][1:]:
                        psef = " ".join((" ".join(proc.split())).split(" ")[7:])
                        print(f"{' ':20} {'process':40} {psef}")

        devdict: dict
        i: int
        j: int
        err_msg: str
        emsg: str
        info_key: str
        self.logger.debug("Print devices %s", self.devices_dict)
        for devdict in self.devices_dict["devices"]:
            self.logger.debug("Print device %s", devdict)
            print(f"{'name':20}{delim_t}{devdict['name']}", file=self.outf)
            print(f"{'version':20}{delim_t}{devdict['version']}", file=self.outf)
            print(f"{'green mode':20}{delim_t}{devdict['green_mode']}", file=self.outf)
            print(f"{'device access':20}{delim_t}{devdict['device_access']}", file=self.outf)
            print(f"{'logging level':20}{delim_t}{devdict['logging_level']}", file=self.outf)
            if "errors" in devdict and len(devdict["errors"]) and not self.quiet_mode:
                print(f"{'errors':20}", file=self.outf, end="")
                i = 0
                for err_msg in devdict["errors"]:
                    if "\n" in err_msg:
                        j = 0
                        for emsg in err_msg.split("\n"):
                            if not i and not j:
                                pass
                            if i and not j:
                                print(f"{' ':20}", file=self.outf, end="")
                            elif j:
                                print(f"{' ':20} ...", file=self.outf, end="")
                            else:
                                pass
                            print(f"{delim_t}{emsg}", file=self.outf)
                            j += 1
                    else:
                        if i:
                            print(f"{' ':20}", file=self.outf, end="")
                        print(f"{delim_t}{err_msg}", file=self.outf)
                    i += 1
            if "info" in devdict:
                i = 0
                for info_key in devdict["info"]:
                    if not i:
                        print(
                            f"{'info':20}{delim_t}{info_key:40}{delim_t}"
                            f"{devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    else:
                        print(
                            f"{' ':20}{delim_t}{info_key:40}{delim_t}{devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    i += 1
            print_text_stuff("attributes")
            print_text_stuff("commands")
            print_text_properties()
            print_text_pod()
            print(file=self.outf)

    def print_txt_medium(self) -> None:  # noqa: C901
        """Print the thing in medium size."""
        # TODO use(d) for debugging
        DELIMS: dict
        # DELIMS = {
        #     "all": " ",
        #     "dict_list": "!",
        #     "dict_dict": "#",
        #     "dict_para": "@",
        #     "dict_csv": ";",
        #     "dict_int": "*",
        #     "dict_float": "%",
        #     "dict_str": "$",
        #     "list": "|",
        #     "str": "+",
        # }
        DELIMS = {
            "all": " ",
            "dict_list": " ",
            "dict_dict": " ",
            "dict_para": " ",
            "dict_csv": " ",
            "dict_int": " ",
            "dict_float": " ",
            "dict_str": " ",
            "list": " ",
            "str": " ",
        }

        delim_t: str = DELIMS["all"]

        def print_text_stuff(stuff: str) -> None:
            """
            Print attribute, command or property.

            :param stuff: name of the thing
            """

            def print_dict_list(l_tj: int) -> None:
                """
                Print list in dict.

                :param l_tj: item number
                """
                delim: str = DELIMS["dict_list"]
                self.logger.debug(
                    "Print list %d in dict %s : %s (%d)",
                    tj,
                    devkey2,
                    devkeyval2,
                    len(devkeyval2),
                )
                print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                if len(devkeyval2) == 0:
                    print("[]", file=self.outf)
                elif len(devkeyval2) == 1:
                    if type(devkeyval2[0]) is not str:
                        # TODO fix this
                        # if l_tj:
                        #     print(f"{' ':143}{delim}", file=self.outf, end="")
                        print(f"{str(devkeyval2[0])}", file=self.outf)
                    elif "," in devkeyval2[0]:
                        l_keyvals = devkeyval2[0].split(",")
                        l_keyval = l_keyvals[0]
                        print(f"{l_keyval}", file=self.outf)
                        for l_keyval in l_keyvals[1:]:
                            print(f"{' ':102}{delim}{l_keyval}", file=self.outf)
                    else:
                        if l_tj:
                            print(f"{' ':102}{delim}", file=self.outf, end="")
                        print(f"{devkeyval2[0]}", file=self.outf)
                else:
                    n = 0
                    for l_keyval in devkeyval2:
                        if n:
                            print(f"{' ':102}{delim}", file=self.outf, end="")
                        print(f"{l_keyval}", file=self.outf)
                        n += 1

            def print_dict_dict(d_tj: int) -> None:
                """
                Print dict in dict.

                :param d_tj: item number
                """
                delim: str = DELIMS["dict_dict"]
                self.logger.debug(
                    "Print %d/%d dict in dict %s : %s", d_tj, pi, devkey2, devkeyval2
                )
                print(f"{' ':102}{delim}{devkey2:40}", file=self.outf)
                n = 0
                for d_keyval in devkeyval2:
                    if type(devkeyval2[d_keyval]) is dict:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "Print %d/%d dict in dict in dict %s : %s",
                            n,
                            dd_len,
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}", end="", file=self.outf)
                        m = 0
                        for item2 in devkeyval2[d_keyval]:
                            if m:
                                print(f"{' ':143}{delim}{' ':40}{delim}", end="", file=self.outf)
                            print(
                                f"{' ':143}{delim}{' ':40} {item2} {devkeyval2[d_keyval][item2]}",
                                end="",
                                file=self.outf,
                            )
                            m += 1
                    elif type(devkeyval2[d_keyval]) is list:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "Print %d/%d list in dict in dict %s : %s",
                            n,
                            dd_len,
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if dd_len == 0:
                            print(f"{' ':102}{delim}{d_keyval:40}{delim}[]", file=self.outf)
                        elif dd_len == 1:
                            print(
                                f"{' ':102}{delim}{d_keyval:40}{delim}{devkeyval2[d_keyval][0]}",
                                file=self.outf,
                            )
                        else:
                            print(
                                f"{' ':102}{delim}{d_keyval:40}{delim}{devkeyval2[d_keyval][0]}",
                                file=self.outf,
                            )
                            m = 0
                            for d_item in devkeyval2[d_keyval][1:]:
                                print(f"{' ':143}{delim}", end="", file=self.outf)
                                if type(d_item) is dict:
                                    k = 0
                                    for key2 in d_item:
                                        if k:
                                            print(
                                                f"{' ':143}{delim}",
                                                end="",
                                                file=self.outf,
                                            )
                                        print(
                                            f" {key2:32}{delim}{d_item[key2]}",
                                            file=self.outf,
                                        )
                                        k += 1
                                else:
                                    print(f"{delim}{d_item}", file=self.outf)
                                m += 1
                    elif type(devkeyval2[d_keyval]) is not str:
                        self.logger.debug(
                            "Print %d %s in dict in dict %s : %s",
                            n,
                            type(devkeyval2[d_keyval]),
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not n:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        else:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}", end="", file=self.outf)
                        print(f"{devkeyval2[d_keyval]}", file=self.outf)
                    else:
                        self.logger.debug(
                            "Print %d/%d string in dict in dict %s : %s",
                            n,
                            len(devkeyval2[d_keyval]),
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not n:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        else:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}{devkeyval2[d_keyval]}", file=self.outf)
                    n += 1

            def print_dict_para(p_tj: int) -> None:
                """
                Print paragraph in dict.

                :param p_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("Print %d paragraph in dict : %s", p_tj, devkeyval2)
                if not p_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102} {devkey2:40}{delim}", file=self.outf, end="")
                p_keyvals = devkeyval2.split("\n")
                # Remove empty lines
                p_keyvals2 = []
                for p_keyval in p_keyvals:
                    p_keyval2 = p_keyval.strip()
                    if p_keyval2:
                        if len(p_keyval2) > 70:
                            lsp = p_keyval2[0:70].rfind(" ")
                            p_keyvals2.append(p_keyval2[0:lsp])
                            p_keyvals2.append(p_keyval2[lsp + 1 :])
                        else:
                            p_keyvals2.append(" ".join(p_keyval2.split()))
                print(f"{p_keyvals2[0]}", file=self.outf)
                for p_keyval2 in p_keyvals2[1:]:
                    print(f"{' ':102}{delim}{p_keyval2}", file=self.outf)

            def print_dict_csv(c_tj: int) -> None:
                """
                Print CSV string in dict.

                :param c_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("Print %d CSV in dict %s", c_tj, devkeyval2)
                if not c_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                c_keyvals = devkeyval2.split(",")
                c_keyval = c_keyvals[0]
                print(f"{c_keyval}", file=self.outf)
                for c_keyval in c_keyvals[1:]:
                    print(f"{' ':102}{c_keyval}", file=self.outf)

            def print_dict_int(s_tj: int) -> None:
                """
                Print int in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                print(f"{devkeyval2}", file=self.outf)

            def print_dict_float(s_tj: int) -> None:
                """
                Print float in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                print(f"{devkeyval2}", file=self.outf)

            def print_dict_str(s_tj: int) -> None:
                """
                Print string in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["dict_str"]
                self.logger.debug("Print %d string in dict %s : '%s'", s_tj, devkey2, devkeyval2)
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                s_keyvals2 = []
                if len(devkeyval2) > 70:
                    lsp = devkeyval2[0:70].rfind(" ")
                    s_keyvals2.append(devkeyval2[0:lsp])
                    s_keyvals2.append(devkeyval2[lsp + 1 :])
                else:
                    s_keyvals2.append(" ".join(devkeyval2.split()))
                print(f"{s_keyvals2[0]}{delim}", file=self.outf)
                for s_keyval2 in s_keyvals2[1:]:
                    print(f"{' ':102}{delim}{s_keyval2}", file=self.outf)

            def print_list(l_tj: int) -> None:
                """
                Print list.

                :param l_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("*** Print %d list %s : %s", l_tj, devkey, devkeyval)
                if not l_tj:
                    print(f"{devkey:40}{delim}", end="", file=self.outf)
                else:
                    print(f"{' ':102}{delim}{devkey:40}{delim}", end="", file=self.outf)
                if len(devkeyval) == 1:
                    if "," in devkeyval[0]:
                        l_keyvals = devkeyval[0].split(",")
                        l_keyval = l_keyvals[0]
                        print(f"{l_keyval.strip()}", file=self.outf)
                        for l_keyval in l_keyvals[1:]:
                            if "\n" in l_keyval:
                                n = 0
                                for line in l_keyval.split("\n"):
                                    if line:
                                        if n:
                                            print(f"{' ':102}", file=self.outf, end="")
                                        print(f" {line.strip()}", file=self.outf)
                                    n += 1
                            else:
                                print(f"{' ':102} {l_keyval.strip()}", file=self.outf)
                    else:
                        print(f"{' ':102} {devkeyval[0]}", file=self.outf)
                else:
                    print(f"{devkeyval}", file=self.outf)

            def print_str(s_tj: int) -> None:
                """
                Print string value.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("*** Print %d string %s : %s", s_tj, devkey, devkeyval)
                if not s_tj:
                    print(f"{devkey:40}{delim}", end="", file=self.outf)
                else:
                    print(f"{' ':102}{delim}{devkey:40}{delim}", end="", file=self.outf)
                if not devkeyval:
                    print(file=self.outf)
                elif type(devkeyval) is str:
                    if "\n" in devkeyval:
                        s_keyvals = devkeyval.split("\n")
                        # Remove empty lines
                        s_keyvals2 = []
                        for s_keyval in s_keyvals:
                            s_keyval2 = s_keyval.strip()
                            if s_keyval2:
                                if len(s_keyval2) > 70:
                                    lsp = s_keyval2[0:70].rfind(" ")
                                    s_keyvals2.append(s_keyval2[0:lsp])
                                    s_keyvals2.append(s_keyval2[lsp + 1 :])
                                else:
                                    s_keyvals2.append(" ".join(s_keyval2.split()))
                        print(f"{s_keyvals2[0]}", file=self.outf)
                        for s_keyval2 in s_keyvals2[1:]:
                            print(f"{' ':102}{delim}{s_keyval2}", file=self.outf)
                    elif "," in devkeyval:
                        s_keyvals = devkeyval.split(",")
                        s_keyval = s_keyvals[0]
                        print(f"{s_keyval.strip()}", file=self.outf)
                        for s_keyval in s_keyvals[1:]:
                            print(f"{' ':102} {s_keyval.strip()}", file=self.outf)
                    elif len(devkeyval) > 70:
                        s_keyvals2 = []
                        lsp = devkeyval[0:70].rfind(" ")
                        s_keyvals2.append(devkeyval[0:lsp])
                        s_keyvals2.append(devkeyval[lsp + 1 :])
                        print(f"{s_keyvals2[0]}", file=self.outf)
                        for s_keyval2 in s_keyvals2[1:]:
                            print(f"{' ':102} {s_keyval2}", file=self.outf)
                    else:
                        print(f"{devkeyval}", file=self.outf)
                elif type(devkeyval) is list:
                    print(f"{devkeyval[0]}", file=self.outf)
                    for s_keyval2 in devkeyval[1:]:
                        print(f"{' ':102} {s_keyval2}", file=self.outf)
                else:
                    print(f"{devkeyval}", file=self.outf)

            key: str
            ti: int
            tj: int
            devkeys: Any
            devkey: Any
            devkeyval: Any
            devkeyval2: Any

            self.logger.debug("Print %d %s: %s", len(devdict[stuff]), stuff, devdict[stuff])
            if not devdict[stuff]:
                return
            print(f"{stuff:20}{delim_t}", end="", file=self.outf)
            if not devdict[stuff]:
                print(file=self.outf)
                return
            ti = 0
            for item in devdict[stuff]:
                self.logger.debug("* Print %d item : %s", ti, item)
                for key in item:
                    if not ti:
                        try:
                            print(f"{key:40}{delim_t}", end="", file=self.outf)
                        except TypeError:
                            logging.warning("Could not print '%s' (%s)", key, type(key))
                    else:
                        print(f"{' ':20}{delim_t}{key:40}{delim_t}", end="", file=self.outf)
                    ti += 1
                    devkeys = item[key]
                    self.logger.debug("** Print item %s keys : %s", key, devkeys)
                    if type(devkeys) is not dict:
                        print(f"{devkeys}", file=self.outf)
                        continue
                    if not devkeys:
                        print("{}", file=self.outf)
                        continue
                    tj = 0
                    for devkey in devkeys:
                        devkeyval = devkeys[devkey]
                        if type(devkeyval) is dict:
                            pi = 0
                            self.logger.debug("*** Print %d dict %s : %s", tj, devkey, devkeyval)
                            print(f"{' ':61}{delim_t}{devkey:40}{delim_t}", file=self.outf)
                            # Read dictionary value
                            for devkey2 in devkeyval:
                                devkeyval2 = devkeyval[devkey2]
                                if type(devkeyval2) is list:
                                    print(file=self.outf)
                                    print_dict_list(tj)
                                elif type(devkeyval2) is dict:
                                    print(file=self.outf)
                                    print_dict_dict(tj)
                                    pi = tj
                                elif type(devkeyval2) is int:
                                    print_dict_int(tj)
                                elif type(devkeyval2) is float:
                                    print_dict_float(tj)
                                elif "\n" in devkeyval2:
                                    print_dict_para(tj)
                                elif "," in devkeyval2:
                                    print_dict_csv(tj)
                                elif not devkeyval2:
                                    print(file=self.outf)
                                else:
                                    print_dict_str(tj)
                                tj += 1
                        elif type(devkeyval) is list:
                            print_list(tj)
                            tj += 1
                        else:
                            self.logger.debug("Print %d string : %s", tj, devkeyval)
                            print_str(tj)
                            tj += 1

        def print_text_properties() -> None:
            """Print device properties in text format."""
            ti: int
            prop_name: str
            prop_vals: Any

            self.logger.debug(
                "Print %d properties: %s", len(devdict["properties"]), devdict["properties"]
            )
            if not devdict["properties"]:
                return
            print(f"{'properties':20} ", end="", file=self.outf)
            if not devdict["properties"]:
                print(file=self.outf)
                return
            ti = 0
            for propdict in devdict["properties"]:
                prop_name = propdict["name"]
                if not ti:
                    print(f"{prop_name:40} {'value':40} ", end="", file=self.outf)
                else:
                    print(f"{' ':20} {prop_name:40} {'value':40} ", end="", file=self.outf)
                ti += 1
                if "value" in propdict:
                    prop_vals = propdict["value"]
                else:
                    prop_vals = None
                if not prop_vals:
                    print(file=self.outf)
                    continue
                elif type(prop_vals) is list:
                    print(f"{prop_vals[0]}", file=self.outf)
                    for prop_val in prop_vals[1:]:
                        print(f"{' ':102} {prop_val}", file=self.outf)

        def print_text_pod() -> None:
            """Print pod information."""
            self.logger.debug("Print pod :\n%s", json.dumps(devdict, indent=4, default=str))
            if "pod" not in devdict:
                return
            if not devdict["pod"]:
                return
            print(f"{' ':20} {'pod':40} {'name':40} {devdict['pod']['metadata']['name']}")
            print(f"{' ':20} {' ':40} {'api_version':40} {devdict['pod']['api_version']}")
            print(f"{' ':20} {' ':40} {'phase':40} {devdict['pod']['status']['phase']}")
            print(f"{' ':20} {' ':40} {'start_time':40} {devdict['pod']['status']['start_time']}")
            print(f"{' ':20} {' ':40} {'host_ip':40} {devdict['pod']['status']['host_ip']}")
            print(f"{' ':20} {' ':40} {'pod_ip':40} {devdict['pod']['status']['pod_ip']}")
            ports: list = []
            for container in devdict["pod"]["spec"]["containers"]:
                for port in container["ports"]:
                    ports.append(str(port["container_port"]))
            print(f"{' ':20} {' ':40} {'ports':40} {','.join(ports)}")
            if devdict["processes"]["output"]:
                proc = devdict["processes"]["output"][0]
                psef = " ".join((" ".join(proc.split())).split(" ")[7:])
                print(f"{' ':20} {'process':40} {psef}")
                if len(devdict["processes"]["output"]) > 1:
                    for proc in devdict["processes"]["output"][1:]:
                        psef = " ".join((" ".join(proc.split())).split(" ")[7:])
                        print(f"{' ':20} {'process':40} {psef}")

        devdict: dict
        i: int
        j: int
        err_msg: str
        emsg: str
        info_key: str
        self.logger.debug("Print devices %s", self.devices_dict)
        for devdict in self.devices_dict["devices"]:
            self.logger.debug("Print device %s", devdict)
            print(f"{'name':20}{delim_t}{devdict['name']}", file=self.outf)
            print(f"{'version':20}{delim_t}{devdict['version']}", file=self.outf)
            print(f"{'green mode':20}{delim_t}{devdict['green_mode']}", file=self.outf)
            print(f"{'device access':20}{delim_t}{devdict['device_access']}", file=self.outf)
            print(f"{'logging level':20}{delim_t}{devdict['logging_level']}", file=self.outf)
            if "errors" in devdict and len(devdict["errors"]) and not self.quiet_mode:
                print(f"{'errors':20}", file=self.outf, end="")
                i = 0
                for err_msg in devdict["errors"]:
                    if "\n" in err_msg:
                        j = 0
                        for emsg in err_msg.split("\n"):
                            if not i and not j:
                                pass
                            if i and not j:
                                print(f"{' ':20}", file=self.outf, end="")
                            elif j:
                                print(f"{' ':20} ...", file=self.outf, end="")
                            else:
                                pass
                            print(f"{delim_t}{emsg}", file=self.outf)
                            j += 1
                    else:
                        if i:
                            print(f"{' ':20}", file=self.outf, end="")
                        print(f"{delim_t}{err_msg}", file=self.outf)
                    i += 1
            if "info" in devdict:
                i = 0
                for info_key in devdict["info"]:
                    if not i:
                        print(
                            f"{'info':20}{delim_t}{info_key:40}{delim_t}"
                            f"{devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    else:
                        print(
                            f"{' ':20}{delim_t}{info_key:40}{delim_t}{devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    i += 1
            print_text_stuff("attributes")
            print_text_stuff("commands")
            print_text_properties()
            print_text_pod()
            print(file=self.outf)

    def print_txt_small(self) -> None:  # noqa: C901
        """Print text in short form."""

        def print_attributes() -> None:
            i: int
            attrib: Any
            attrib_item: str

            """Print attribute in short form."""
            print(f"{'attributes':20}", end="", file=self.outf)
            i = 0
            for attrib in devdict["attributes"]:  # type: ignore[call-overload]
                attrib_item = attrib["name"]  # type: ignore[index]
                if not i:
                    print(f" {attrib_item:40}", end="", file=self.outf)
                else:
                    print(
                        f"{' ':20} {attrib_item:40}",
                        end="",
                        file=self.outf,
                    )
                i += 1
                try:
                    print(f"{attrib['data']['value']}", file=self.outf)  # type: ignore[index]
                except KeyError as oerr:
                    self.logger.debug("Could not read attribute %s : %s", attrib, oerr)
                    print("N/A", file=self.outf)

        def print_commands() -> None:
            """Print commands with values."""
            i: int
            cmd: Any
            cmd_item: str

            self.logger.debug(
                "Print commands : %s", devdict["commands"]  # type: ignore[call-overload]
            )
            print(f"{'commands':20}", end="", file=self.outf)
            if not devdict["commands"]:  # type: ignore[call-overload]
                print("N/R", file=self.outf)
                return
            i = 0
            for cmd in devdict["commands"]:  # type: ignore[call-overload]
                if "value" in devdict["commands"][cmd]:  # type: ignore[call-overload]
                    if not i:
                        print(f" {cmd:40}", end="", file=self.outf)
                    else:
                        print(f"{' ':20} {cmd:40}", end="", file=self.outf)
                    i += 1
                    cmd_item = devdict["commands"][cmd]["value"]  # type: ignore[call-overload]
                    print(f"{cmd_item}", file=self.outf)
            if not i:
                print("N/R", file=self.outf)

        def print_properties() -> None:
            ti: int
            prop_name: str
            prop_vals: Any

            self.logger.debug(
                "Print %d properties", len(devdict["properties"])  # type: ignore[call-overload]
            )
            if not devdict["properties"]:  # type: ignore[call-overload]
                return
            print(f"{'properties':20} ", end="", file=self.outf)
            if not devdict["properties"]:  # type: ignore[call-overload]
                print(file=self.outf)
                return
            ti = 0
            for prop_name in devdict["properties"]:  # type: ignore[call-overload]
                if not ti:
                    print(f"{prop_name:40}", end="", file=self.outf)
                else:
                    print(f"{' ':20} {prop_name:40}", end="", file=self.outf)
                ti += 1
                prop_vals = devdict["properties"][prop_name][  # type: ignore[call-overload]
                    "value"
                ]
                if not prop_vals:
                    print(file=self.outf)
                    continue
                elif type(prop_vals) is list:
                    print(f"{prop_vals[0]}", file=self.outf)
                    for prop_val in prop_vals[1:]:
                        print(f"{' ':60} {prop_val}", file=self.outf)

        devdict: list

        dev_item: str
        self.logger.debug("Print devices %s", self.devices_dict)
        for devdict in self.devices_dict["devices"]:
            self.logger.debug("Print device %s", devdict)
            print(f"{'name':20} {devdict['name']}", file=self.outf)  # type: ignore[call-overload]
            dev_item = devdict["version"]  # type: ignore[call-overload]
            print(f"{'version':20} {dev_item}", file=self.outf)
            if "versioninfo" in devdict:
                dev_item = devdict["versioninfo"][0]  # type: ignore[call-overload]
                print(f"{'versioninfo':20} {dev_item}", file=self.outf)
            else:
                print(f"{'versioninfo':20} ---", file=self.outf)
            print_attributes()
            print_commands()
            print_properties()
            print(file=self.outf)

    def print_html_small(self, html_body: bool) -> None:  # noqa: C901
        """
        Print text in short form.

        :param html_body: Flag to print HTML header and footer
        """

        def print_attributes() -> None:
            """Print attribute in short form."""
            attrib: dict

            print(
                '<tr><td style="vertical-align: top">attributes</td><td class="tangoctl"><table>',
                file=self.outf,
            )
            for attrib in devdict["attributes"]:
                print(f'<tr><td class="tangoctl">{attrib["name"]}</td>', end="", file=self.outf)
                try:
                    print(
                        f'<td class="tangoctl">{attrib["data"]["value"]}</td>',
                        file=self.outf,
                    )
                except KeyError as oerr:
                    self.logger.warning("Could not read attribute %s : %s", attrib, oerr)
                    print('<td class="tangoctl">N/A</td>', file=self.outf)
                print("</td></tr>")
            print("</table></td></tr>")

        def print_commands() -> None:
            """Print commands with values."""
            cmd: dict

            self.logger.debug("Print commands : %s", devdict["commands"])
            print(
                '<tr><td class="tangoctl">commands</td><td class="tangoctl"><table>',
                end="",
                file=self.outf,
            )
            for cmd in devdict["commands"]:
                if "value" in cmd:
                    print(f'<tr><td class="tangoctl">{cmd["name"]}</td>', file=self.outf)
                    print(
                        f'<td class="tangoctl">{cmd["value"]}</td></tr>',
                        file=self.outf,
                    )
            print("</table></td></tr>")

        def print_properties() -> None:
            """Print properties with values."""
            prop: dict
            self.logger.debug("Print properties : %s", devdict["properties"])
            print(
                '<tr><td class="tangoctl">properties</td><td class="tangoctl"><table>',
                end="",
                file=self.outf,
            )
            for prop in devdict["properties"]:
                print(f'<tr><td class="tangoctl">{prop["name"]}</td>', file=self.outf)
                prop_val = prop["value"]
                if type(prop_val) is list:
                    if len(prop_val) > 1:
                        print('<td class="tangoctl"><table>', file=self.outf)
                        for pval in prop_val:
                            print(f'<tr><td class="tangoctl">{pval}</td></tr>', file=self.outf)
                        print("</table></td></tr>", file=self.outf)
                    else:
                        print(f'<td class="tangoctl">{prop_val[0]}</td></tr>', file=self.outf)
                else:
                    print(f'<td class="tangoctl">{prop_val}</td></tr>', file=self.outf)
            print("</table></td></tr>", file=self.outf)

        devdict: dict
        if html_body:
            print("<html><body>", file=self.outf)
        for devdict in self.devices_dict["devices"]:
            self.logger.debug("Device : %s", devdict)
            print(f"<h2>{devdict['name']}</h2>", file=self.outf)
            print("<table>", file=self.outf)
            print(
                '<tr><td class="tangoctl">version</td>'
                f'<td class="tangoctl">{devdict["version"]}</td></tr>',
                file=self.outf,
            )
            if "versioninfo" in devdict:
                print(
                    f'<tr><td class="tangoctl">versioninfo</td>'
                    f'<td class="tangoctl">{devdict["versioninfo"][0]}</td></tr>',
                    file=self.outf,
                )
            else:
                print(
                    '<tr><td class="tangoctl">versioninfo</td><td class="tangoctl">---</td></tr>'
                )
            print_attributes()
            print_commands()
            print_properties()
            print("</table>", file=self.outf)
        if html_body:
            print("</body></html>", file=self.outf)
