"""Print Tango configuration in HTML format."""

import ast
import json
import logging
import re
from typing import Any

from ska_tangoctl.tango_control.progress_bar import progress_bar

class TangoJsonReaderHtmlMixin:
    """Read JSON and print as markdown or text."""

    outf: Any
    logger: logging.Logger
    tgo_space: str
    devices_dict: dict
    quiet_mode: bool

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
