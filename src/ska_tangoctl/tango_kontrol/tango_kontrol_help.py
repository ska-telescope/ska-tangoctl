"""Read all information about Tango devices in a Kubernetes cluster."""

from typing import Any

try:
    from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
except ModuleNotFoundError:
    KubernetesInfo = None  # type: ignore[assignment,misc]
from ska_tangoctl.tango_control.disp_action import BOLD, UNDERL, UNFMT


class TangoKontrolHelpMixin:
    """Read Tango devices running in a Kubernetes cluster."""

    cfg_data: Any

    def usage3(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        # if KubernetesInfo is None:
        #     super().usage(p_name)
        #     return
        # Reading devices
        print(f"{BOLD}Read Tango devices in Kubernetes:{UNFMT}")
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help|-h")
        print(f"\t{p_name} -vh")
        print("\nDisplay Kubernetes namespaces")
        print(f"\t{p_name} --show-ns|-n [MISC]")
        print("\nDisplay information on pods in Kubernetes namespaces")
        print(f"\t{p_name} [NAMESPACE] [K8S]")
        print("\nSet logging level for a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] --log_level={UNDERL}0{UNFMT}-{UNDERL}5{UNFMT}")
        print("\nDisplay Tango database address for Kubernetes namespace")
        print(f"\t{p_name} -i|--show-db [NAMESPACE] [MISC]")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -g|--show-class [TANGODB] [FORMAT] [MISC]")
        print("\nList Tango device names")
        print(f"\t{p_name} -d|--show-dev [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay all Tango devices")
        print(f"\t{p_name} [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] [FORMAT] [MISC]")
        print("\nFilter on attribute, command or property name")
        print(f"\t{p_name} [TANGODB] [SELECT] [FORMAT] [MISC]")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")
        # Testing
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
        print("\nDisplay status of a Tango device")
        print(f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT} [TANGODB] [DEVICE]")
        # print("\nCheck events for attribute of a Tango device")
        # print(
        #     f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT}|-H {UNDERL}HOST{UNFMT}"
        #     f" [DEVICE] -A {UNDERL}ATTRIBUTE{UNFMT}"
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
        print(f"\n{BOLD}Tango database{UNFMT} [TANGODB]\n")
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            "\t\tTango database host and port, e.g. 10.8.13.15:10000"
        )
        print(
            f"\t-N {UNDERL}K8S_NS{UNFMT}, --ns={UNDERL}K8S_NS{UNFMT}"
            "\t\tKubernetes namespace for Tango database, e.g. 'integration'"
        )

        print(f"\n{BOLD}Tango device selection{UNFMT} [DEVICE]\n")
        print(
            f"\t-D {UNDERL}DEVICE{UNFMT}, --device={UNDERL}DEVICE{UNFMT}"
            f"\tdevice name, e.g. 'csp' (not case sensitive, only a part is needed)"
        )

        print(f"\n{BOLD}Kubernetes namespace{UNFMT} [NAMESPACE]\n")
        print(
            f"\t-K {UNDERL}K8S_NS{UNFMT}, --ns={UNDERL}K8S_NS{UNFMT},"
            f" --namespace={UNDERL}K8S_NS{UNFMT}\n\t\t\t\t\tKubernetes namespace"
        )

        print(f"\n{BOLD}Kubernetes information{UNFMT} [K8S]\n")
        print("\t-o, --show-pod\t\t\tread pod names")
        print("\t    --pod-df\t\t\tread pod file systems space usage")
        print("\t    --pod-domain\t\tread pod domain names")
        print("\t    --pod-env\t\t\tread pod environment variables")
        print("\t    --pod-free\t\t\tread free memory for pod host")
        print("\t    --pod-host\t\t\tread pod host names")
        print("\t    --pod-mpstat\t\tread processor related statistics for pod host")
        print("\t    --pod-ps\t\t\tread active processes in pods")
        print("\t    --pod-top\t\t\tread system summary information in pods")
        print("\t    --pod-uptime\t\tread how long pods have been running")
        print("\t-x, show-context\t\tdisplay contexts")

        print(f"\n{BOLD}Data selection{UNFMT} [SELECT]\n")
        print("\t-e, --everything\t\tread attributes, commands and properties")
        print("\t-a, --show-attribute\t\tflag for reading attributes")
        print(
            f"\t-A {UNDERL}ATTRIBUTE{UNFMT}, --attribute={UNDERL}ATTRIBUTE{UNFMT}"
            f"\n\t\t\t\t\tattribute name e.g. 'obsState' (not case sensitive)"
        )
        print("\t-c, --show-command\t\tflag for reading commands")
        print(
            f"\t-C {UNDERL}COMMAND{UNFMT}, --command={UNDERL}COMMAND{UNFMT}"
            "\tcommand name, e.g. 'Status' (not case sensitive)"
        )
        print("\t-k, --show-class\t\tflag for reading classes")
        print(
            f"\t-K {UNDERL}CLASS{UNFMT}, --class={UNDERL}CLASS{UNFMT}"
            "\t\tclass name, e.g. 'DishLogger' (not case sensitive)"
        )
        print("\t-p, --show-property\t\tread properties")
        print(
            f"\t-P {UNDERL}PROPERTY{UNFMT}, --property={UNDERL}PROPERTY{UNFMT}"
            "\n\t\t\t\t\tproperty name, e.g. 'Status' (not case sensitive)"
        )
        ign = ", ".join(self.cfg_data["ignore_device"])
        print(f"\t-f, --full\t\t\tshow all devices - do not skip {ign}")
        print("\t-u, --unique\t\t\tonly read one device for each class")

        print(f"\n{BOLD}Format control{UNFMT} [FORMAT]\n")
        print("\t-s, --short\t\t\tdisplay device name and status")
        print("\t-l, --list\t\t\tdisplay device name, status and values")
        print("\t-j, --json\t\t\toutput in JSON format")
        print("\t-m, --md\t\t\toutput in markdown format")
        print("\t-t, --txt\t\t\toutput in text format")
        print("\t-w, --html\t\t\toutput in HTML format")
        print("\t-y, --yaml\t\t\toutput in YAML format")
        print(f"\t    ---indent={UNDERL}INDENT{UNFMT}\t\tindentation for JSON, default is 4")
        # print("\t-i, --ip\t\t\tuse IP address instead of FQDN")

        print(f"\n{BOLD}Simple testing{UNFMT} [TEST]\n")
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT},\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            f"\tdirectory with JSON input file, e.g. 'resources'"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\toutput file name")
        print("\t-0, --on\t\t\tturn device on")
        print("\t-1, --off\t\t\tturn device off")
        print("\t    --ping\t\t\tping device")
        print(f"\t    --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset admin mode off or on")
        print(
            f"\t    --simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset simulation mode off or on"
        )

        print(f"\n{BOLD}Miscellaneous{UNFMT} [MISC]\n")
        print("\t-v\t\t\t\tset logging level to INFO")
        print("\t-V\t\t\t\tset logging level to DEBUG")
        print("\t-q\t\t\t\tdo not display progress bars")
        print("\t-Q\t\t\t\tdo not display progress bars and set log level to WARNING")
        print(
            f"\t-X {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            "\t\toverride configuration from file"
        )

        # Configuration
        print(f"\n{BOLD}Default configuration:{UNFMT}\n")
        print(f"\ttimeout: {self.cfg_data['timeout_millis']}ms")
        print(f"\tTango database port\t: {self.cfg_data['databaseds_port']}")
        print(f"\tTango device port\t: {self.cfg_data['device_port']}")
        print(f"\tCommands safe to run: {','.join(self.cfg_data['run_commands'])}")
        print(
            "\tcommands safe to run with name as parameter:"
            f" {','.join(self.cfg_data['run_commands_name'])}"
        )
        print(f"\tLong attributes: {','.join(self.cfg_data['long_attributes'])}")
        print(f"\tMgnore devices: {','.join(self.cfg_data['ignore_device'])}")
        print(f"\tMinimum string length for matches: {self.cfg_data['min_str_len']}")
        print(f"\tDelimiter: '{self.cfg_data['delimiter']}'")
        print(
            "\tListed attributes:"
            f" {','.join(list(self.cfg_data['list_items']['attributes'].keys()))}"
        )
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
        print(f"\t{BOLD}man tangoktl{UNFMT}")
        print()

    def usage4(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        # if KubernetesInfo is None:
        #     super().usage2(p_name)
        #     return
        # Reading devices
        print(f"{BOLD}Read Tango devices:{UNFMT}")
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help")
        print(f"\t{p_name} -h")
        print("\nDisplay Kubernetes namespaces")
        print(f"\t{p_name} --show-ns")
        print(f"\t{p_name} -n")
        print("\nDisplay Tango database address")
        print(f"\t{p_name} --show-db --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -i -N {UNDERL}K8S_NS{UNFMT}")
        print("\nSet logging level for a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] --log_level={UNDERL}0{UNFMT}-{UNDERL}5{UNFMT}")
        print("\nShow device:")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -D {UNDERL}DEVICE{UNFMT} -f")
        print("\nSearch for matching devices:")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -D talon -l")
        print("\nSearch for devices with matching command:")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -C {UNDERL}COMMAND{UNFMT}")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -C {UNDERL}COMMAND{UNFMT}")
        print("\nSearch for devices with matching property:")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -D {UNDERL}DEVICE{UNFMT}")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} --show-class --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --show-class --host={UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} -k -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -k -H {UNDERL}HOST{UNFMT}")
        print("\nList Tango device names")
        print(f"\t{p_name} --show-dev --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --show-dev --host={UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} -l -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -l -H {UNDERL}HOST{UNFMT}")
        print("\nDisplay attribute and command names for a Tango device")
        print(f"\t{p_name} -c -N {UNDERL}K8S_NS{UNFMT} -D {UNDERL}DEVICE{UNFMT}")
        print(f"\t{p_name} -c -H {UNDERL}HOST{UNFMT} -D {UNDERL}DEVICE{UNFMT}")
        print("\nDisplay all Tango devices (will take a long time)")
        print(f"\t{p_name} -e -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --everything --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --everything --namespace={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -e -H {UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} --everything --host={UNDERL}HOST{UNFMT}")
        print("\nFilter on device name")
        print(f"\t{p_name} -D {UNDERL}DEVICE{UNFMT} -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -D {UNDERL}DEVICE{UNFMT} -H {UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} --device={UNDERL}DEVICE{UNFMT} --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --device={UNDERL}DEVICE{UNFMT} --namespace={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --device={UNDERL}DEVICE{UNFMT} --host={UNDERL}HOST{UNFMT}")
        print("\nFilter on attribute name")
        print(f"\t{p_name} --attribute={UNDERL}ATTRIBUTE{UNFMT} --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --attribute={UNDERL}ATTRIBUTE{UNFMT} --namespace={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --attribute={UNDERL}ATTRIBUTE{UNFMT} --host={UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} -A {UNDERL}ATTRIBUTE{UNFMT} -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -A {UNDERL}ATTRIBUTE{UNFMT} -H {UNDERL}HOST{UNFMT}")
        print("\nFilter on command name")
        print(f"\t{p_name} --command={UNDERL}COMMAND{UNFMT} --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --command={UNDERL}COMMAND{UNFMT} --namespace={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --command={UNDERL}COMMAND{UNFMT} --host={UNDERL}HOST{UNFMT}")
        print(
            f"\t{p_name} -f|-s -C {UNDERL}COMMAND{UNFMT} -N {UNDERL}K8S_NS{UNFMT}|-H"
            f" {UNDERL}HOST{UNFMT}"
        )
        print("\nFilter on property name")
        print(f"\t{p_name} --property={UNDERL}PROPERTY{UNFMT} --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --property={UNDERL}PROPERTY{UNFMT} --host={UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} -P {UNDERL}PROPERTY{UNFMT} -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -P {UNDERL}PROPERTY{UNFMT} -H {UNDERL}HOST{UNFMT}")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")

        # Testing of devices
        print(f"\n{BOLD}Test Tango devices:{UNFMT}")
        print("\nTest a Tango device")
        print(
            f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print(
            f"\t{p_name} -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nTest a Tango device and read attributes")
        print(
            f"\t{p_name} -a -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print(
            f"\t{p_name} -a -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nTurn a Tango device on")
        print(
            f"\t{p_name} --on -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nTurn a Tango device off")
        print(
            f"\t{p_name} --off -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print(
            f"\t{p_name} --off -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nSet a Tango device to standby mode")
        print(
            f"\t{p_name} --standby -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print(
            f"\t{p_name} --standby -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nChange admin mode on a Tango device")
        print(f"\t{p_name} --admin=<0|1>")
        print("\nDisplay status of a Tango device")
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" -H {UNDERL}HOST{UNFMT} -D {UNDERL}DEVICE{UNFMT}"
        )
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" --ns={UNDERL}K8S_NS{UNFMT} --device={UNDERL}DEVICE{UNFMT}"
        )
        print("\nCheck events for attribute of a Tango device")
        print(
            f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} -A {UNDERL}ATTRIBUTE{UNFMT}"
        )
        print(
            f"\t{p_name} -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} -A {UNDERL}ATTRIBUTE{UNFMT}"
        )
        # print(
        #     f"\t{p_name} --ns={UNDERL}K8S_NS{UNFMT}|--host={UNDERL}HOST{UNFMT}"
        #     f" --device={UNDERL}DEVICE{UNFMT} --attribute={UNDERL}ATTRIBUTE{UNFMT}"
        # )
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir={UNDERL}PATH{UNFMT}")
        print(f"\t{p_name} -J {UNDERL}PATH{UNFMT}")
        print("\nRun test, reading from input file")
        print(f"\t{p_name} --ns={UNDERL}K8S_NS{UNFMT} --input={UNDERL}FILE{UNFMT}")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -O {UNDERL}FILE{UNFMT}")
        print("\nRun test file:")
        print(
            f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -D {UNDERL}DEVICE{UNFMT} -f"
            f" --in {UNDERL}PATH{UNFMT} -V"
        )
        # print(
        #     f"{italic}e.g.\tADMIN_MODE=1 {p_name} --K integration"
        #     f" -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V{UNFMT}"
        # )

        # Options and parameters
        print(f"\n{BOLD}Parameters:{UNFMT}\n")
        print("\t-a, --show-attribute\t\tflag for reading attributes")
        print("\t-b, --tree\t\t\tdisplay Tango device names as a tree")
        print("\t-c, --show-command\t\tflag for reading commands")
        print("\t-d, --show-dev\t\t\tlist Tango device names")
        ign = ", ".join(self.cfg_data["ignore_device"])
        print(f"\t-e, --everything\t\tshow all devices - do not skip {ign}")
        print("\t    --exact\t\t\t\tmatch names exactly")
        print("\t-f, --full\t\t\tdisplay in full")
        print("\t-i, --show-db\t\t\tdisplay hostname and IP address of Tango host")
        print("\t-j, --json\t\t\toutput in JSON format")
        print("\t-k, --show-class\t\tlist Tango device classes")
        print("\t-l, --list\t\t\tlist status of Tango devices")
        print("\t-m, --md\t\t\toutput in markdown format")
        # print("\t-l|--list\t\t\tdisplay device name and status on one line")
        print("\t-n, --show-ns\t\t\tread Kubernetes namespaces")
        print("\t-o, --show-pod\t\t\tread pod names")
        print("\t    --pod-df\t\t\tread pod file system space usage")
        print("\t    --pod-domain\t\tread pod domain name")
        print("\t    --pod-env\t\t\tread pod environment variables")
        print("\t    --pod-free\t\t\tread pod free memory")
        print("\t    --pod-host\t\t\tread pod host name")
        print("\t    --pod-mpstat\t\tread pod processor related statistics")
        print("\t    --pod-ps\t\t\tread active processes in pod")
        print("\t    --pod-top\t\t\tread system summary information in pod")
        print("\t    --pod-uptime\t\tread how long pods have been running")
        print("\t-p, --show-property\t\tread properties")
        print("\t-q,\t\t\t\tdo not display progress bars")
        print("\t-Q\t\t\t\tdo not display progress bars or error messages")
        print("\t    --reverse\t\t\treverse sort order")
        print("\t-s, --short\t\t\tdisplay attribute and command values in short format")
        print("\t-t, --txt\t\t\toutput in text format")
        print("\t    --unique\t\t\tonly read one device for each class")
        print("\t-v\t\t\t\tset logging level to INFO")
        print("\t-V\t\t\t\tset logging level to DEBUG")
        print("\t-w, --html\t\t\toutput in HTML format")
        print("\t    --exact\t\t\texact matches only")
        print("\t-x, show-context\t\tdisplay Kubernetes context information")
        print("\t-y, --yaml\t\t\toutput in YAML format")
        print("\t-z, --show-svc\t\t\tread Kubernetes service names")
        print("\t-0, --off\t\t\tturn device off")
        print("\t-1, --on\t\t\tturn device on")
        print("\t    --ping\t\t\tping device")
        print(f"\t    --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset admin mode off or on")
        print(
            f"\t    --simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset simulation mode off or on"
        )
        print(
            f"\t-A {UNDERL}ATTRIBUTE{UNFMT}, --attribute={UNDERL}ATTRIBUTE{UNFMT}"
            f"\n\t\t\t\t\tattribute name e.g. 'obsState' (not case sensitive)"
        )
        print(
            f"\t-C {UNDERL}COMMAND{UNFMT}, --command={UNDERL}COMMAND{UNFMT}"
            "\tcommand name, e.g. 'Status' (not case sensitive)"
        )
        print(
            f"\t-D {UNDERL}device{UNFMT}, --device={UNDERL}DEVICE{UNFMT}"
            f"\tdevice name, e.g. 'csp' (not case sensitive, only a part is needed)"
        )
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            "\t\tTango database host and port, e.g. 10.8.13.15:10000"
        )
        print(f"\t---indent={UNDERL}INDENT{UNFMT}\t\tindentation for JSON, default is 4")
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT},\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            f"\tdirectory with JSON input file, e.g. 'resources'"
        )
        print(
            f"\t-K {UNDERL}PATH{UNFMT}, --class={UNDERL}PATH{UNFMT}"
            f"\t\tTango device class, e.g. 'MidCspSubarray' (not case sensitive)"
        )
        print(
            f"\t-N {UNDERL}K8S_NS{UNFMT}, --namespace={UNDERL}K8S_NS{UNFMT},"
            f" --ns={UNDERL}K8S_NS{UNFMT}"
            "\n\t\t\t\t\tKubernetes namespace for Tango database, e.g. 'staging'"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\toutput file name")
        print(
            f"\t-P {UNDERL}PROPERTY{UNFMT}, --property={UNDERL}PROPERTY{UNFMT}"
            "\n\t\t\t\t\tproperty name, e.g. 'Status' (not case sensitive)"
        )
        print(
            f"\t-W {UNDERL}VALUE{UNFMT}, --value={UNDERL}VALUE{UNFMT}"
            "\t\tvalue for Tango attribute"
        )
        print(
            f"\t-X {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            "\t\toverride configuration from file"
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

        # Further reading
        print(f"\n{BOLD}See also:{UNFMT}\n")
        print(f"\t{BOLD}man tangoktl{UNFMT}")
        print()
