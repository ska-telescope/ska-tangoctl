"""Read and display Tango stuff."""

import ast
import json
import logging
import os
import re
import sys
from typing import Any, TextIO

# from ska_mid_itf_engineering_tools.tango_control.read_tango_device import progress_bar


def progress_bar(
    iterable: list | dict,
    show: bool,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 100,
    fill: str = "*",
    print_end: str = "\r",
) -> Any:
    r"""
    Call this in a loop to create a terminal progress bar.

    :param iterable: Required - iterable object (Iterable)
    :param show: print the actual thing
    :param prefix: prefix string
    :param suffix: suffix string
    :param decimals: positive number of decimals in percent complete
    :param length: character length of bar
    :param fill: fill character for bar
    :param print_end: end character (e.g. "\r", "\r\n")
    :yields: the next one in line
    """

    def print_progress_bar(iteration: Any) -> None:
        """
        Progress bar printing function.

        :param iteration: the thing
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + "-" * (length - filled_length)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=print_end)

    if show:
        total = len(iterable)
        # Do not divide by zero
        if total == 0:
            total = 1
        # Initial call
        print_progress_bar(0)
        # Update progress bar
        for i, item in enumerate(iterable):
            yield item
            print_progress_bar(i + 1)
        # Erase line upon completion
        sys.stdout.write("\033[K")
    else:
        # Nothing to see here
        for i, item in enumerate(iterable):
            yield item


def md_format(inp: str) -> str:
    """
    Change string to safe format.

    :param inp: input
    :return: output
    """
    if type(inp) is not str:
        return str(inp)
    outp = inp.replace("/", "\\/").replace("_", "\\_").replace("-", "\\-")
    return outp


def md_print(inp: str, end: str = "\n", file: TextIO = sys.stdout) -> None:
    """
    Print markdown string.

    :param inp: input
    :param end: at the end of the line
    :param file: output file pointer
    """
    print(inp.replace("_", "\\_").replace("-", "\\-"), end=end, file=file)


class TangoJsonReader:
    """Read JSON and print as markdown or text."""

    outf: TextIO
    tgo_space: str
    quiet_mode: bool = True

    def __init__(
        self,
        logger: logging.Logger,
        quiet_mode: bool,
        kube_namespace: str | None,
        devsdict: dict,
        file_name: str | None = None,
    ):
        """
        Rock and roll.

        :param logger: logging handle
        :param quiet_mode: flag for displaying progress bar
        :param kube_namespace: Kubernetes namespace
        :param devsdict: dictionary with device data
        :param file_name: output file name
        """
        self.logger = logger
        self.devices_dict = devsdict
        if file_name is not None:
            self.logger.info("Write output file %s", file_name)
            self.outf = open(file_name, "w")
        else:
            self.outf = sys.stdout
        # Get Tango database host
        tango_host = os.getenv("TANGO_HOST")
        if kube_namespace is not None:
            self.tgo_space = f"namespace {kube_namespace}"
        else:
            self.tgo_space = f"host {tango_host}"
        self.quiet_mode = quiet_mode
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True

    def print_markdown_all(self) -> None:  # noqa: C901
        """Print the whole thing."""

        def print_attribute_data(item: str, dstr: str) -> None:
            """
            Print attribute data in various formats.

            :param item: item name
            :param dstr: itmen value
            """
            dstr = re.sub(" +", " ", dstr)
            md_print(f"| {item:30} ", end="", file=self.outf)
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
                self.logger.debug("Print JSON :\n%s", json.dumps(ddict, indent=4))
                n = 0
                for ditem in ddict:
                    if n:
                        print(f"| {' ':30} ", end="", file=self.outf)
                    if type(ddict[ditem]) is dict:
                        m = 0
                        for ditem2 in ddict[ditem]:
                            md_print(
                                f"| {ditem:50} | {ditem2:42} | {ddict[ditem][ditem2]:45} |",
                                file=self.outf,
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
                                md_print(f"| {dname:90} ", end="", file=self.outf)
                            else:
                                md_print(
                                    f"| {' ':30} | {' ':50} | {dname:90} ", end="", file=self.outf
                                )
                            md_print(f"| {dname:50} ", end="", file=self.outf)
                            if type(ditem2) is dict:
                                p = 0
                                for ditem3 in ditem2:
                                    md_print(
                                        f"| {ditem3:42} | {ditem2[ditem3]:45} |", file=self.outf
                                    )
                                    p += 1
                            else:
                                md_print(f"| {ditem2:143}  ||", file=self.outf)
                            m += 1
                    else:
                        md_print(f"| {ditem:50} | {ddict[ditem]:90} ||", file=self.outf)
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
                                print(f"| {' ':30} ", end="", file=self.outf)
                            md_print(f"| {ditem2:50} ", end="", file=self.outf)
                            md_print(f"| {ditem_val:90} |", file=self.outf)
                            m += 1
                    else:
                        md_print(f"| {str(ditem):143} ||", file=self.outf)
                    n += 1
            elif "\n" in dstr:
                self.logger.debug("Print attribute value str %s (%s)", dstr, type(dstr))
                n = 0
                for line in dstr.split("\n"):
                    line = line.strip()
                    if line:
                        if n:
                            print(f"| {' ':30} ", end="", file=self.outf)
                        md_print(f"| {line:143} ||", file=self.outf)
                        n += 1
            else:
                if len(dstr) > 140:
                    lsp = dstr[0:140].rfind(" ")
                    md_print(f" | {dstr[0:lsp]:143} ||", file=self.outf)
                    md_print(f"| {' ':30}  | {dstr[lsp + 1 :]:143} ||", file=self.outf)
                else:
                    md_print(f"| {dstr:143} ||", file=self.outf)
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
                md_print(f"| {' ':{dc3}} |", file=self.outf)
            # elif type(dstr) is list:
            #     for dst in dstr:
            elif type(dstr) is not str:
                md_print(f"| {str(dstr):{dc3}} |", file=self.outf)
            elif "\n" in dstr:
                self.logger.debug("Print '%s'", dstr)
                n = 0
                for line in dstr.split("\n"):
                    line = line.strip()
                    if line:
                        if n:
                            print(f"| {' ':{dc1}} | {' ':{dc2}}.", end="", file=self.outf)
                        md_print(f"| {line:{dc3}} |", file=self.outf)
                        n += 1
            elif len(dstr) > dc3 and "," in dstr:
                n = 0
                for line in dstr.split(","):
                    if n:
                        if dc2:
                            print(f"| {' ':{dc1}} | {' ':{dc2}}.", end="", file=self.outf)
                        else:
                            print(f"| {' ':{dc1}} ", end="", file=self.outf)
                    md_print(f"| {line:{dc3}} |", file=self.outf)
                    n += 1
            else:
                md_print(f"| {str(dstr):{dc3}} |", file=self.outf)

        def print_md_attributes() -> None:
            """Print attributes."""
            print("### Attributes\n", file=self.outf)
            for attrib in devdict["attributes"]:
                print(f"#### {attrib}\n", file=self.outf)
                print("| ITEM | VALUE |       |", file=self.outf)
                print("|:-----|:------|:------|", file=self.outf)
                attrib_data = devdict["attributes"][attrib]["data"]
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
                                md_print(f"| {str(item):30} ", end="", file=self.outf)
                            else:
                                print(f"| {' ':30} ", end="", file=self.outf)
                            md_print(f"| {str(item2):143} ||", file=self.outf)
                            n += 1
                    else:
                        self.logger.warning(
                            "Data type for %s (%s) not supported", item, type(data)
                        )
                if "config" in devdict["attributes"][attrib]:
                    for item in devdict["attributes"][attrib]["config"]:
                        config = devdict["attributes"][attrib]["config"][item]
                        print_attribute_data(item, config)
                print("\n*******\n", file=self.outf)
            print("\n", file=self.outf)

        def print_md_commands() -> None:
            """Print commands."""
            cc1 = 30
            cc2 = 50
            cc3 = 90
            print("### Commands\n", file=self.outf)
            print(f"| {'NAME':{cc1}} | {'FIELD':{cc2}} | {'VALUE':{cc3}} |", file=self.outf)
            print(f"|:{'-'*cc1}-|:{'-'*cc2}-|:{'-'*cc3}-|", file=self.outf)
            n = 0
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
            pc1 = 40
            pc2 = 133
            print("### Properties\n", file=self.outf)
            print(f"| {'NAME':{pc1}} | {'VALUE':{pc2}} |", file=self.outf)
            print(f"|:{'-'*pc1}-|:{'-'*pc2}-|", file=self.outf)
            for prop in devdict["properties"]:
                self.logger.debug(
                    "Print command %s : %s", prop, devdict["properties"][prop]["value"]
                )
                md_print(f"| {prop:{pc1}} ", end="", file=self.outf)
                print_data(devdict["properties"][prop]["value"], pc1, 0, pc2)
            print("\n*******\n", file=self.outf)

        print(f"# Tango devices in {self.tgo_space}\n", file=self.outf)
        # Run "for device in self.devices_dict:"
        for device in progress_bar(
            self.devices_dict,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices_dict)} JSON devices :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.logger.info("Print device %s", device)
            devdict = self.devices_dict[device]
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

    def print_html_all(self, html_body: bool) -> None:  # noqa: C901
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
                self.logger.debug("Print JSON :\n%s", json.dumps(ddict, indent=4))
                for ditem in ddict:
                    print(f"<table><tr><td>{ditem}</td>", file=self.outf)
                    if type(ddict[ditem]) is dict:
                        print("<td><table>", file=self.outf)
                        for ditem2 in ddict[ditem]:
                            print(
                                f"<tr><td>{ditem}</td><td>{ditem2}</td>"
                                f"<td>{ddict[ditem][ditem2]}</td></tr>",
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
                            print(f"<td>{ditem}</td>", file=self.outf)
                            if type(ditem2) is dict:
                                print("<td><table>", file=self.outf)
                                for ditem3 in ditem2:
                                    print(
                                        f"<tr><td>{ditem3}</td><td>{ditem2[ditem3]}</td></tr>",
                                        file=self.outf,
                                    )
                                print("</table></td>", file=self.outf)
                            else:
                                print(f'<td colspan="2">{ditem2}</td>', file=self.outf)
                            print("</tr>", file=self.outf)
                        print("</table>", file=self.outf)
                    else:
                        print(f"<td>{ditem}</td><td>{ddict[ditem]}</td>", file=self.outf)
                    print("</td></tr></table>", file=self.outf)
            elif dstr[0] == "[" and dstr[-1] == "]":
                dlist = ast.literal_eval(dstr)
                self.logger.debug("Print attribute value list %s (%s)", dlist, type(dlist))
                n = 0
                print("<table>", file=self.outf)
                for ditem in dlist:
                    if type(ditem) is dict:
                        for ditem2 in ditem:
                            ditem_val = str(ditem[ditem2])
                            print(f"<tr><td>{ditem2}</td>", end="", file=self.outf)
                            print(f"<td>{ditem_val}</td></tr>", file=self.outf)
                    else:
                        print(f'<tr><td colspan="2">{str(ditem)}</td></tr>', file=self.outf)
                    n += 1
                print("</table>", file=self.outf)
            elif "\n" in dstr:
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
            print("<h3>Attributes</h3>", file=self.outf)
            for attrib in devdict["attributes"]:
                print(f"<h4>{attrib}</h4>\n", file=self.outf)
                print("<table>", file=self.outf)
                print('<tr><th>ITEM</th><th colspan="2">VALUE</th></tr>', file=self.outf)
                attrib_data = devdict["attributes"][attrib]["data"]
                for item in attrib_data:
                    data = attrib_data[item]
                    print(f'<tr><td style="vertical-align: top">{item}</td><td>', file=self.outf)
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
                            print("<tr><td>&nbsp;<td>", end="", file=self.outf)
                            print(f"<td>{str(item2)}</td></tr>", file=self.outf)
                        print("</table>", file=self.outf)
                    else:
                        print(
                            "Data type for %s (%s) not supported", item, type(data), file=self.outf
                        )
                    print("</td></tr>", file=self.outf)
                if "config" in devdict["attributes"][attrib]:
                    for item in devdict["attributes"][attrib]["config"]:
                        print(f"<tr><td>{item}</td><td>", file=self.outf)
                        config = devdict["attributes"][attrib]["config"][item]
                        print_html_attribute_data(config)
                        print("</td></tr>", file=self.outf)
                print("</table>", file=self.outf)

        def print_html_commands() -> None:
            """Print commands."""
            print("<h3>Commands</h3>", file=self.outf)
            print("<table>", file=self.outf)
            print("<tr><th>NAME</th><th>FIELD VALUE</th></tr>", file=self.outf)
            for cmd in devdict["commands"]:
                cmd_items = devdict["commands"][cmd]
                self.logger.debug("Print command %s : %s", cmd, cmd_items)
                print(f'<tr><td style="vertical-align: top">{cmd}</td><td>', file=self.outf)
                if cmd_items:
                    print("<table>", file=self.outf)
                    for item in cmd_items:
                        print(f"<tr><td>{item}</td><td>", end="", file=self.outf)
                        print_html_data(devdict["commands"][cmd][item])
                        print("</td></tr>", file=self.outf)
                    print("</table>", file=self.outf)
                print("</td></tr>", file=self.outf)
            print("</table>", file=self.outf)

        def print_html_properties() -> None:
            """Print properties."""
            print("<h3>Properties</h3>", file=self.outf)
            print("<table>", file=self.outf)
            print("<tr><th>NAME</th><th>VALUE</th></tr>", file=self.outf)
            for prop in devdict["properties"]:
                self.logger.debug(
                    "Print command %s : %s", prop, devdict["properties"][prop]["value"]
                )
                print(f'<tr><td style="vertical-align: top">{prop}</td><td>', file=self.outf)
                print_html_data(devdict["properties"][prop]["value"])
                print("</td></tr>", file=self.outf)
            print("</table>", file=self.outf)

        if html_body:
            print("<html><body>", file=self.outf)
        print(f"<h1>Tango devices in {self.tgo_space}</h1>\n", file=self.outf)
        # Run "for device in self.devices_dict:"
        for device in progress_bar(
            self.devices_dict,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices_dict)} JSON devices :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.logger.info("Print device %s", device)
            devdict = self.devices_dict[device]
            print(f"<h2>Device {devdict['name']}</h2>\n", file=self.outf)
            print("<table>", file=self.outf)
            print('<tr><th>FIELD</th><th colspan="3">VALUE</th></tr>', file=self.outf)
            print(
                f'<tr><td>version</td><td colspan="3">{devdict["version"]}</td></tr>',
                file=self.outf,
            )
            print(
                f"<tr><td>device access</td>"
                f"<td colspan=\"3\">{devdict['device_access']}</td></tr>",
                file=self.outf,
            )
            if "adminMode" in devdict:
                print(
                    f"<tr><td>Admin mode</td><td colspan=\"3\">{devdict['adminMode']}</td></tr>",
                    file=self.outf,
                )
            if "info" in devdict:
                print(
                    f"<tr><td>Device class</td>"
                    f"<td colspan=\"3\">{devdict['info']['dev_class']}</td></tr>",
                    file=self.outf,
                )
                print(
                    f"<tr><td>Server host</td>"
                    f"<td colspan=\"3\">{devdict['info']['server_host']}</td></tr>",
                    file=self.outf,
                )
                print(
                    f"<tr><td>Server ID</td>"
                    f"<td colspan=\"3\">{devdict['info']['server_id']}</td></tr>",
                    file=self.outf,
                )
            print("</table>", file=self.outf)
            print_html_attributes()
            print_html_commands()
            print_html_properties()
        if html_body:
            print("</body></html>", file=self.outf)

    def print_txt_all(self) -> None:  # noqa: C901
        """Print the whole thing."""

        def print_txt(stuff: str) -> None:
            """
            Print attribute, command or property.

            :param stuff: name of the thing
            """
            self.logger.debug("Print %d %s", len(devdict[stuff]), stuff)
            if not devdict[stuff]:
                return
            print(f"{stuff:20} ", end="", file=self.outf)
            if not devdict[stuff]:
                print(file=self.outf)
                return
            ti = 0
            for key in devdict[stuff]:
                if not ti:
                    print(f"{key:40} ", end="", file=self.outf)
                else:
                    print(f"{' ':20} {key:40} ", end="", file=self.outf)
                ti += 1
                devkeys = devdict[stuff][key]
                if not devkeys:
                    print(file=self.outf)
                    continue
                tj = 0
                for devkey in devkeys:
                    devkeyval = devkeys[devkey]
                    if type(devkeyval) is dict:
                        self.logger.debug("Print dict %s : %s", devkey, devkeyval)
                        # Read dictionary value
                        for devkey2 in devkeyval:
                            devkeyval2 = devkeyval[devkey2]
                            if not tj:
                                print(f"{devkey2:40} ", file=self.outf, end="")
                            else:
                                print(f"{' ':61} {devkey2:40} ", file=self.outf, end="")
                            if not devkeyval2:
                                print(file=self.outf)
                            elif type(devkeyval2) is list:
                                self.logger.debug(
                                    "Print list in dict : %s (%d) %s",
                                    devkeyval2,
                                    len(devkeyval2),
                                    type(devkeyval2[0]),
                                )
                                if len(devkeyval2) == 1:
                                    if type(devkeyval2[0]) is not str:
                                        if tj:
                                            print(f"{' ':102} ", file=self.outf, end="")
                                        print(f"{str(devkeyval2[0])}", file=self.outf)
                                    elif "," in devkeyval2[0]:
                                        keyvals = devkeyval2[0].split(",")
                                        keyval = keyvals[0]
                                        print(f"{keyval}", file=self.outf)
                                        for keyval in keyvals[1:]:
                                            print(f"{' ':102} {keyval}", file=self.outf)
                                    else:
                                        if tj:
                                            print(f"{' ':102} ", file=self.outf, end="")
                                        print(f"{devkeyval2[0]}", file=self.outf)
                                else:
                                    n = 0
                                    for keyval in devkeyval2:
                                        if n:
                                            print(f"{' ':102} ", file=self.outf, end="")
                                        print(f"{keyval}", file=self.outf)
                                        n += 1
                            elif type(devkeyval2) is dict:
                                self.logger.debug("Print dict in dict : %s", devkeyval2)
                                n = 0
                                for keyval in devkeyval2:
                                    if n:
                                        print(f"{' ':102} ", end="", file=self.outf)
                                    if type(devkeyval2[keyval]) is dict:
                                        print(f"{keyval:24} ", end="", file=self.outf)
                                        m = 0
                                        for item2 in devkeyval2[keyval]:
                                            if m:
                                                print(
                                                    f"{' ':102} {' ':24} ", end="", file=self.outf
                                                )
                                            print(
                                                f"{item2} {devkeyval2[keyval][item2]}",
                                                file=self.outf,
                                            )
                                            m += 1
                                    elif type(devkeyval2[keyval]) is list:
                                        m = 0
                                        for item in devkeyval2[keyval][1:]:
                                            if m:
                                                print(f"{' ':102} ", end="", file=self.outf)
                                            print(f"{keyval:24}", end="", file=self.outf)
                                            if type(item) is dict:
                                                k = 0
                                                for key2 in item:
                                                    if k:
                                                        print(
                                                            f"{' ':126} ", end="", file=self.outf
                                                        )
                                                    print(
                                                        f" {key2:32} {item[key2]}", file=self.outf
                                                    )
                                                    k += 1
                                            else:
                                                print(f" {item}", file=self.outf)
                                            m += 1
                                    elif type(devkeyval2[keyval]) is not str:
                                        print(f"{keyval:24} ", end="", file=self.outf)
                                        print(f"{devkeyval2[keyval]}", file=self.outf)
                                    else:
                                        print(f"{keyval:24} {devkeyval2[keyval]}", file=self.outf)
                                    n += 1
                            elif "\n" in devkeyval2:
                                self.logger.debug("Print paragraph in dict : %s", devkeyval2)
                                keyvals = devkeyval2.split("\n")
                                # Remove empty lines
                                keyvals2 = []
                                for keyval in keyvals:
                                    keyval2 = keyval.strip()
                                    if keyval2:
                                        if len(keyval2) > 70:
                                            lsp = keyval2[0:70].rfind(" ")
                                            keyvals2.append(keyval2[0:lsp])
                                            keyvals2.append(keyval2[lsp + 1 :])
                                        else:
                                            keyvals2.append(" ".join(keyval2.split()))
                                print(f"{keyvals2[0]}", file=self.outf)
                                for keyval2 in keyvals2[1:]:
                                    print(f"{' ':102} {keyval2}", file=self.outf)
                            elif "," in devkeyval2:
                                self.logger.debug("Print CSV in dict %s", devkeyval2)
                                keyvals = devkeyval2.split(",")
                                keyval = keyvals[0]
                                print(f"{keyval}", file=self.outf)
                                for keyval in keyvals[1:]:
                                    print(f"{' ':102}{keyval}", file=self.outf)
                            else:
                                self.logger.debug("Print string in dict : %s", devkeyval2)
                                keyvals2 = []
                                if len(devkeyval2) > 70:
                                    lsp = devkeyval2[0:70].rfind(" ")
                                    keyvals2.append(devkeyval2[0:lsp])
                                    keyvals2.append(devkeyval2[lsp + 1 :])
                                else:
                                    keyvals2.append(" ".join(devkeyval2.split()))
                                print(f"{keyvals2[0]}", file=self.outf)
                                for keyval2 in keyvals2[1:]:
                                    print(f"{' ':102} {keyval2}", file=self.outf)
                            tj += 1
                    elif type(devkeyval) is list:
                        self.logger.debug("Print list : %s", devkeyval)
                        if not tj:
                            print(f"{devkey:40} ", end="", file=self.outf)
                        else:
                            print(f"{' ':61} {devkey:40} ", end="", file=self.outf)
                        if len(devkeyval) == 1:
                            if "," in devkeyval[0]:
                                keyvals = devkeyval[0].split(",")
                                keyval = keyvals[0]
                                print(f"{keyval.strip()}", file=self.outf)
                                for keyval in keyvals[1:]:
                                    if "\n" in keyval:
                                        n = 0
                                        for line in keyval.split("\n"):
                                            if line:
                                                if n:
                                                    print(f"{' ':102}", file=self.outf, end="")
                                                print(f" {line.strip()}", file=self.outf)
                                            n += 1
                                    else:
                                        print(f"{' ':102} {keyval.strip()}", file=self.outf)
                            else:
                                print(f"{' ':102} {devkeyval[0]}", file=self.outf)
                        else:
                            print(f"{devkeyval}", file=self.outf)
                    else:
                        self.logger.debug("Print string : %s", devkeyval)
                        # Read string value
                        if not tj:
                            print(f"{devkey:40} ", end="", file=self.outf)
                        else:
                            print(f"{' ':61} {devkey:40} ", end="", file=self.outf)
                        tj += 1
                        if not devkeyval:
                            print(file=self.outf)
                        elif type(devkeyval) is str:
                            if "\n" in devkeyval:
                                keyvals = devkeyval.split("\n")
                                # Remove empty lines
                                keyvals2 = []
                                for keyval in keyvals:
                                    keyval2 = keyval.strip()
                                    if keyval2:
                                        if len(keyval2) > 70:
                                            lsp = keyval2[0:70].rfind(" ")
                                            keyvals2.append(keyval2[0:lsp])
                                            keyvals2.append(keyval2[lsp + 1 :])
                                        else:
                                            keyvals2.append(" ".join(keyval2.split()))
                                print(f"{keyvals2[0]}", file=self.outf)
                                for keyval2 in keyvals2[1:]:
                                    print(f"{' ':102} {keyval2}", file=self.outf)
                            elif "," in devkeyval:
                                keyvals = devkeyval.split(",")
                                keyval = keyvals[0]
                                print(f"{keyval.strip()}", file=self.outf)
                                for keyval in keyvals[1:]:
                                    print(f"{' ':102} {keyval.strip()}", file=self.outf)
                            elif len(devkeyval) > 70:
                                keyvals2 = []
                                lsp = devkeyval[0:70].rfind(" ")
                                keyvals2.append(devkeyval[0:lsp])
                                keyvals2.append(devkeyval[lsp + 1 :])
                                print(f"{keyvals2[0]}", file=self.outf)
                                for keyval2 in keyvals2[1:]:
                                    print(f"{' ':102} {keyval2}", file=self.outf)
                            else:
                                print(f"{devkeyval}", file=self.outf)
                        elif type(devkeyval) is list:
                            print(f"{devkeyval[0]}", file=self.outf)
                            for keyval2 in devkeyval[1:]:
                                print(f"{' ':102} {keyval2}", file=self.outf)
                        else:
                            print(f"{devkeyval}", file=self.outf)

        def print_properties() -> None:
            self.logger.debug("Print %d properties", len(devdict["properties"]))
            if not devdict["properties"]:
                return
            print(f"{'properties':20} ", end="", file=self.outf)
            if not devdict["properties"]:
                print(file=self.outf)
                return
            ti: int = 0
            for prop_name in devdict["properties"]:
                if not ti:
                    print(f"{prop_name:40} {'value':40} ", end="", file=self.outf)
                else:
                    print(f"{' ':20} {prop_name:40} {'value':40} ", end="", file=self.outf)
                ti += 1
                prop_vals = devdict["properties"][prop_name]["value"]
                if not prop_vals:
                    print(file=self.outf)
                    continue
                elif type(prop_vals) is list:
                    print(f"{prop_vals[0]}", file=self.outf)
                    for prop_val in prop_vals[1:]:
                        print(f"{' ':102} {prop_val}", file=self.outf)

        devdict: dict
        i: int
        j: int
        err_msg: str
        emsg: str
        info_key: str
        for device in self.devices_dict:
            self.logger.info("Print device %s", device)
            devdict = self.devices_dict[device]
            print(f"{'name':20} {devdict['name']}", file=self.outf)
            print(f"{'version':20} {devdict['version']}", file=self.outf)
            print(f"{'green mode':20} {devdict['green_mode']}", file=self.outf)
            print(f"{'device access':20} {devdict['device_access']}", file=self.outf)
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
                            print(f" {emsg}", file=self.outf)
                            j += 1
                    else:
                        if i:
                            print(f"{' ':20}", file=self.outf, end="")
                        print(f" {err_msg}", file=self.outf)
                    i += 1
            if "info" in devdict:
                i = 0
                for info_key in devdict["info"]:
                    if not i:
                        print(
                            f"{'info':20} {info_key:40} {devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    else:
                        print(
                            f"{' ':20} {info_key:40} {devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    i += 1
            print_txt("attributes")
            print_txt("commands")
            print_properties()
            print(file=self.outf)

    def print_txt_quick(self) -> None:  # noqa: C901
        """Print text in short form."""

        def print_attributes() -> None:
            i: int
            attrib: str
            """Print attribute in short form."""
            print(f"{'attributes':20}", end="", file=self.outf)
            i = 0
            for attrib in devdict["attributes"]:
                if not i:
                    print(f" {attrib:40}", end="", file=self.outf)
                else:
                    print(f"{' ':20} {attrib:40}", end="", file=self.outf)
                i += 1
                try:
                    print(f"{devdict['attributes'][attrib]['data']['value']}", file=self.outf)
                except KeyError as oerr:
                    self.logger.debug("Could not read attribute %s : %s", attrib, oerr)
                    print("N/A", file=self.outf)

        def print_commands() -> None:
            """Print commands with values."""
            i: int
            cmd: str
            self.logger.debug("Print commands : %s", devdict["commands"])
            print(f"{'commands':20}", end="", file=self.outf)
            if not devdict["commands"]:
                print("N/A", file=self.outf)
                return
            i = 0
            for cmd in devdict["commands"]:
                if "value" in devdict["commands"][cmd]:
                    if not i:
                        print(f" {cmd:40}", end="", file=self.outf)
                    else:
                        print(f"{' ':20} {cmd:40}", end="", file=self.outf)
                    i += 1
                    print(f"{devdict['commands'][cmd]['value']}", file=self.outf)
            if not i:
                print("N/A", file=self.outf)

        devdict: dict
        for device in self.devices_dict:
            devdict = self.devices_dict[device]
            print(f"{'name':20} {devdict['name']}", file=self.outf)
            print(f"{'version':20} {devdict['version']}", file=self.outf)
            if "versioninfo" in devdict:
                print(f"{'versioninfo':20} {devdict['versioninfo'][0]}", file=self.outf)
            else:
                print(f"{'versioninfo':20} ---", file=self.outf)
            print_attributes()
            print_commands()
            print(file=self.outf)

    def print_html_quick(self, html_body: bool) -> None:  # noqa: C901
        """
        Print text in short form.

        :param html_body: Flag to print HTML header and footer
        """

        def print_attributes() -> None:
            """Print attribute in short form."""
            print('<tr><td style="vertical-align: top">attributes</td><td><table>', file=self.outf)
            for attrib in devdict["attributes"]:
                print(f"<tr><td>{attrib}</td>", end="", file=self.outf)
                try:
                    print(
                        f"<td>{devdict['attributes'][attrib]['data']['value']}</td>",
                        file=self.outf,
                    )
                except KeyError as oerr:
                    self.logger.debug("Could not read attribute %s : %s", attrib, oerr)
                    print("<td>N/A</td>", file=self.outf)
                print("</td></tr>")
            print("</table></td></tr>")

        def print_commands() -> None:
            """Print commands with values."""
            self.logger.debug("Print commands : %s", devdict["commands"])
            print("<tr><td>commands</td><td><table>", end="", file=self.outf)
            for cmd in devdict["commands"]:
                if "value" in devdict["commands"][cmd]:
                    print(f"<tr><td>{cmd}</td>", file=self.outf)
                    print(f"<td>{devdict['commands'][cmd]['value']}</td></tr>", file=self.outf)
            print("</table></td></tr>")

        device: str
        devdict: dict
        if html_body:
            print("<html><body>", file=self.outf)
        for device in self.devices_dict:
            devdict = self.devices_dict[device]
            print(f"<h2>{devdict['name']}</h2>", file=self.outf)
            print("<table>", file=self.outf)
            print(f"<tr><td>version</td><td>{devdict['version']}</td></tr>", file=self.outf)
            if "versioninfo" in devdict:
                print(
                    f"<tr><td>versioninfo</td><td>{devdict['versioninfo'][0]}</td></tr>",
                    file=self.outf,
                )
            else:
                print("<tr><td>versioninfo</td><td>---</td></tr>")
            print_attributes()
            print_commands()
            print("</table>", file=self.outf)
        if html_body:
            print("</body></html>", file=self.outf)
