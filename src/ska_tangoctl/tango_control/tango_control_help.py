"""Read all information about Tango devices in a Kubernetes cluster."""

from typing import Any

from ska_tangoctl.tango_control.disp_action import BOLD, UNDERL, UNFMT


class TangoControlHelpMixin:
    """Connect to Tango environment and retrieve information."""

    cfg_data: Any

    def usage1(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        print(f"{BOLD}Read Tango devices:{UNFMT}")

        # Reading devices
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help|-h")
        print(f"\t{p_name} -vh")
        print("\nSet logging level for a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] --log_level={UNDERL}0{UNFMT}-{UNDERL}5{UNFMT}")
        print("\nList Tango device names")
        print(f"\t{p_name} -d|--show-dev [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -k|--show-class [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay all Tango devices")
        print(f"\t{p_name} [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] [FORMAT] [MISC]")
        print("\nFilter on attribute, command or property name")
        print(f"\t{p_name} [TANGODB] [SELECT] [FORMAT] [MISC]")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")

        # Testing Tango devices
        print(f"\n{BOLD}Test Tango devices:{UNFMT}")
        print("\nTest a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] [TEST]")
        print("\nTest a Tango device and read attributes")
        print(f"\t{p_name} -a [TANGODB] [DEVICE] [SELECT] [TEST]")
        print("\nTurn a Tango device on")
        print(f"\t{p_name} --on [TANGODB] [DEVICE] [TEST]")
        print("\nTurn a Tango device off")
        print(f"\t{p_name} --off [TANGODB] [DEVICE] [TEST]")
        print("\nSet a Tango device to standby mode")
        print(f"\t{p_name} --standby [TANGODB] [DEVICE] [TEST]")
        print("\nChange admin mode for a Tango device")
        print(f"\t{p_name} --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT} [TANGODB] [DEVICE]")
        print("\nSet status of Tango device")
        print(f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT} [TANGODB] [DEVICE]")
        # print("\nCheck events for attribute of a Tango device")
        # print(
        #     f"\t{p_name} -K {UNDERL}CLASS{UNFMT}|-H {UNDERL}HOST{UNFMT}"
        #     f" [DEVICE] -A {UNDERL}CLASS{UNFMT}"
        # )
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir={UNDERL}PATH{UNFMT}|-J {UNDERL}PATH{UNFMT} [MISC]")
        print("\nRun test, reading from input file")
        print(f"\t{p_name} [TANGODB] --input={UNDERL}FILE{UNFMT}|-I {UNDERL}FILE{UNFMT} [MISC]")
        # print(
        #     f"{italic}e.g.\tADMIN_MODE=1 {p_name} --K integration"
        #     f" -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V{UNFMT}"
        # )

        # Options and parameters
        print(f"\n{BOLD}Set Tango database{UNFMT} [TANGODB]\n")
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            "\t\t\tTango database host and port, e.g. 10.8.13.15:10000"
        )

        print(f"\n{BOLD}Tango device selection{UNFMT} [DEVICE]\n")
        print(
            f"\t-D {UNDERL}DEVICE{UNFMT}, --device={UNDERL}DEVICE{UNFMT}"
            f"\t\tdevice name, e.g. 'csp' (not case sensitive, only a part is needed)"
        )

        # Selecting what to read
        print(f"\n{BOLD}Data selection{UNFMT} [SELECT]\n")
        ign = ", ".join(self.cfg_data["ignore_device"])  # type: ignore[arg-type]
        print(f"\t-e, --everything\t\t\tshow all devices - do not skip {ign}")
        print("\t-a, --show-attribute\t\t\tflag for reading attributes")
        print(
            f"\t-A {UNDERL}ATTRIBUTE{UNFMT}, --attribute={UNDERL}ATTRIBUTE{UNFMT}"
            f"\tattribute name e.g. 'obsState' (not case sensitive)"
        )
        print("\t-c, --show-command\t\t\tflag for reading commands")
        print(
            f"\t-C {UNDERL}COMMAND{UNFMT}, --command={UNDERL}COMMAND{UNFMT}"
            "\t\tcommand name, e.g. 'Status' (not case sensitive)"
        )
        print("\t-k, --show-class\t\t\tflag for reading classes")
        print(
            f"\t-K {UNDERL}CLASS{UNFMT}, --class={UNDERL}CLASS{UNFMT}"
            "\t\t\tclass name, e.g. 'DishLogger' (not case sensitive)"
        )
        print("\t-p, --show-property\t\t\tread properties")
        print(
            f"\t-P {UNDERL}PROPERTY{UNFMT}, --property={UNDERL}PROPERTY{UNFMT}"
            "\tproperty name, e.g. 'Status' (not case sensitive)"
        )
        print("\t    --exact\t\t\t\tmatch names exactly")
        print("\t-u, --unique\t\t\t\tonly read one device for each class")

        print(f"\n{BOLD}Format control{UNFMT} [FORMAT]\n")
        print("\t-s, --short, --small\t\t\tdisplay name and value only")
        print("\t-m, --medium\t\t\t\tdisplay with important information")
        print("\t-f, --full, --large\t\t\tdisplay all information")
        print("\t-l, --list\t\t\t\tdisplay device name, status and values")
        print("\t-j, --json\t\t\t\toutput in JSON format")
        print("\t-t, --txt\t\t\t\toutput in text format")
        print("\t-u, --md\t\t\t\toutput in markdown format")
        print("\t-w, --html\t\t\t\toutput in HTML format")
        print("\t-y, --yaml\t\t\t\toutput in YAML format")
        print(f"\t    ---indent={UNDERL}INDENT{UNFMT}\t\t\tindentation for JSON, default is 4")

        # Running tests
        print(f"\n{BOLD}Simple testing{UNFMT} [TEST]\n")
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT}\t\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            f"\t\tdirectory with JSON input file, e.g. 'resources'"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\t\toutput file name")
        print("\t-0, --on\t\t\t\tturn device on")
        print("\t-1, --off\t\t\t\tturn device off")
        print("\t    --ping\t\t\t\tping device")
        print(f"\t    --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\t\tset admin mode off or on")
        print(
            f"\t    --simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\t\tset simulation mode off or on"
        )

        # Other
        print(f"\n{BOLD}Miscellaneous{UNFMT} [MISC]\n")
        print("\t-v\t\t\t\t\tset logging level to INFO")
        print("\t-V\t\t\t\t\tset logging level to DEBUG")
        print("\t-q\t\t\t\t\tdo not display progress bars and set log level to WARNING")
        print("\t-Q\t\t\t\t\tdo not display progress bars and set log level to ERROR")
        print(
            f"\t-F {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            "\t\t\toverride configuration from file"
        )

        # Configuration
        print(f"\n{BOLD}Default configuration:{UNFMT}\n")
        print(f"\ttimeout: {self.cfg_data['timeout_millis']}ms")
        print(f"\tTango database port\t: {self.cfg_data['databaseds_port']}")
        print(f"\tTango device port\t: {self.cfg_data['device_port']}")
        cfg_vals: str = ",".join(self.cfg_data["run_commands"])  # type: ignore[arg-type]
        print(f"\tCommands safe to run: {cfg_vals}")
        cfg_vals = ",".join(self.cfg_data["run_commands_name"])  # type: ignore[arg-type]
        print(f"\tCommands safe to run with name as parameter: {cfg_vals}")
        cfg_vals = ",".join(self.cfg_data["long_attributes"])  # type: ignore[arg-type]
        print(f"\tLong attributes: {cfg_vals}")
        cfg_vals = ",".join(self.cfg_data["ignore_device"])  # type: ignore[arg-type]
        print(f"\tIgnore devices: {cfg_vals}")
        print(f"\tMinimum string length for matches: {self.cfg_data['min_str_len']}")
        print(f"\tDelimiter: '{self.cfg_data['delimiter']}'")
        cfg_vals = ",".join(list(self.cfg_data["list_items"]["attributes"].keys()))
        print(f"\tListed attributes: {cfg_vals}")
        print(
            "\tListed commands:"
            f" {','.join(list(self.cfg_data['list_items']['commands'].keys()))}"
        )
        print(
            "\tListed properties:"
            f" {','.join(list(self.cfg_data['list_items']['properties'].keys()))}"
        )

        # Further reading
        print(f"\n{BOLD}See also:{UNFMT}\n")
        print(f"\t{BOLD}man tangoctl{UNFMT}")
        print()

    def usage2(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        print(f"{BOLD}Read Tango devices:{UNFMT}")

        # Reading devices
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help")
        print(f"\t{p_name} -h")
        print("\nSet logging level for a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] --log_level={UNDERL}0{UNFMT}-{UNDERL}5{UNFMT}")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -k|--show-class [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -k|--show-class [-H {UNDERL}HOST{UNFMT}]")
        print("\nList Tango device names")
        print(f"\t{p_name} --show-dev [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -l [-H {UNDERL}HOST{UNFMT}]")
        print("\nDisplay list of Tango devices")
        print(f"\t{p_name} --list [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -l")
        print("\nFilter on device name")
        print(f"\t{p_name} -D {UNDERL}DEVICE{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} --device={UNDERL}DEVICE{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
        print("\nFilter on attribute name")
        print(f"\t{p_name} --attribute={UNDERL}ATTRIBUTE{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -A {UNDERL}ATTRIBUTE{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print("\nFilter on command name")
        print(f"\t{p_name} --command={UNDERL}COMMAND{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -C {UNDERL}COMMAND{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print("\nFilter on property name")
        print(f"\t{p_name} --property={UNDERL}PROPERTY{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -P {UNDERL}COMMAND{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir={UNDERL}PATH{UNFMT}")
        print(f"\t{p_name} -J {UNDERL}PATH{UNFMT}")

        print(
            "\nRun test, reading from input file"
            " (in JSON format with values to be read and/or written)."
        )
        print(f"\t{p_name} --input={UNDERL}FILE{UNFMT}")
        print(f"\t{p_name} -I {UNDERL}FILE{UNFMT}")

        # Testing
        print(f"\n{BOLD}Test Tango devices:{UNFMT}")
        print("\nTest a Tango device")
        print(
            f"\t{p_name} [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
            f""
        )
        print("\nTest a Tango device and read attributes")
        print(
            f"\t{p_name} -a [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nDisplay attribute and command names for a Tango device")
        print(f"\t{p_name} -c [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}DEVICE{UNFMT}")
        print("\nTurn a Tango device on")
        print(
            f"\t{p_name} --on [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nTurn a Tango device off")
        print(
            f"\t{p_name} --off [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nSet a Tango device to standby mode")
        print(
            f"\t{p_name} --standby [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nChange admin mode on a Tango device")
        print(f"\t{p_name} --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}")
        print("\nDisplay status of a Tango device")
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" [--host {UNDERL}HOST{UNFMT}] --device {UNDERL}DEVICE{UNFMT}"
        )
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}DEVICE{UNFMT}"
        )
        print("\nCheck events for attribute of a Tango device")
        print(
            f"\t{p_name} [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}DEVICE{UNFMT}"
            f" -A {UNDERL}ATTRIBUTE{UNFMT}"
        )
        # Options and parameters
        print(f"\n{BOLD}Parameters:{UNFMT}\n")
        print("\t-a, --show-attribute\t\t\tflag for reading attributes")
        print("\t-b, --tree\t\t\t\tdisplay tree of devices")
        print("\t-c, --show-command\t\t\tread commands")
        print("\t-d, --show-dev\t\t\t\tlist Tango device names")
        ign = ", ".join(self.cfg_data["ignore_device"])
        print(f"\t-e, --everything\t\t\tshow all devices - do not skip {ign}")
        print("\t    --exact\t\t\t\texact matches only")
        print("\t-f, --full, --large\t\t\tsdisplay all information")
        print("\t-i, --show-db\t\t\t\tdisplay hostname and IP address of Tango host")
        print("\t-j, --json\t\t\t\toutput in JSON format")
        print("\t-k, --show-class\t\t\tlist Tango device classes")
        print("\t-l, --list\t\t\t\tdisplay device name and status on one line")
        print("\t-m, --medium\t\t\tdisplay important information")
        print("\t-p, --show-property\t\t\tread properties")
        print("\t-q\t\t\t\t\tdo not display progress bars")
        print("\t-Q\t\t\t\t\tdo not display progress bars or error messages")
        print("\t    --reverse\t\t\t\treverse sort order")
        print("\t-s, --short, --small\t\t\tdisplay name and value only")
        print("\t-t, --txt\t\t\t\toutput in text format")
        print("\t-u, --md\t\t\t\toutput in markdown format")
        print("\t    --unique\t\t\t\tonly read one device for each class")
        print("\t-v\t\t\t\t\tset logging level to INFO")
        print("\t-V\t\t\t\t\tset logging level to DEBUG")
        print("\t-w, --html\t\t\t\toutput in HTML format")
        print("\t-y, --yaml\t\t\t\toutput in YAML format")
        print("\t-0, --off\t\t\t\tturn device off")
        print("\t-1, --on\t\t\t\tturn device on")
        print("\t    --ping\t\t\tping device")
        print(f"\t    --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\t\tset admin mode off or on")
        print(
            f"\t    --simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\t\tset simulation mode off or on"
        )
        print(
            f"\t-A {UNDERL}ATTRIBUTE{UNFMT}, --attribute={UNDERL}ATTRIBUTE{UNFMT}\tattribute name"
        )
        print(f"\t-C {UNDERL}ATTRIBUTE{UNFMT}, --command={UNDERL}COMMAND{UNFMT}\t\tcommand name")
        print(f"\t-D {UNDERL}ATTRIBUTE{UNFMT}, --device={UNDERL}DEVICE{UNFMT}\t\tdevice name")
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            f"\t\t\tTango database host and port"
        )
        print(f"\t---indent={UNDERL}INDENT{UNFMT}\t\tindentation for JSON, default is 4")
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT}\t\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            "\t\tdirectory with JSON input file"
        )
        print(
            f"\t-K {UNDERL}PATH{UNFMT}, --class={UNDERL}PATH{UNFMT}"
            f"\t\t\tTango device class, e.g. 'MidCspSubarray' (not case sensitive)"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\t\t\toutput file name")
        print(f"\t-P {UNDERL}PROPERTY{UNFMT}, --property={UNDERL}PROPERTY{UNFMT}\t\tproperty name")
        print(
            f"\t-W {UNDERL}VALUE{UNFMT}, --value={UNDERL}VALUE{UNFMT}"
            "\t\tvalue for Tango attribute"
        )
        print(
            f"\t-X {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            f"\t\toverride configuration from file"
        )
        # Configuration
        print(f"\n{BOLD}Default configuration:{UNFMT}\n")
        print(f"\ttimeout: {self.cfg_data['timeout_millis']}ms")
        print(f"\tTango database port\t: {self.cfg_data['databaseds_port']}")
        print(f"\tTango device port\t: {self.cfg_data['device_port']}")
        print(f"\tcommands safe to run: {','.join(self.cfg_data['run_commands'])}")
        print(
            "\tcommands safe to run with name as parameter:"
            f" {','.join(self.cfg_data['run_commands_name'])}"
        )
        print(f"\tlong attributes: {','.join(self.cfg_data['long_attributes'])}")
        print(f"\tignore devices: {','.join(self.cfg_data['ignore_device'])}")
        print(f"\tminimum string length for matches: {self.cfg_data['min_str_len']}")
        print(f"\tdelimiter: '{self.cfg_data['delimiter']}'")
        print(
            "\tlisted attributes:"
            f" {','.join(list(self.cfg_data['list_items']['attributes'].keys()))}"
        )
        print(
            "\tlisted commands:"
            f" {','.join(list(self.cfg_data['list_items']['commands'].keys()))}"
        )
        print(
            "\tlisted properties:"
            f" {','.join(list(self.cfg_data['list_items']['properties'].keys()))}"
        )
        # Et cetera
        print(f"\n{BOLD}See also:{UNFMT}\n")
        print(f"\t{BOLD}man tangoctl{UNFMT}")
        print()
