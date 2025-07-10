"""Read all information about Tango devices in a Kubernetes cluster."""

import getopt
import json
import logging
import os
import sys
from typing import Any

import tango
import yaml

try:
    from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
except ModuleNotFoundError:
    KubernetesInfo = None  # type: ignore[assignment,misc]
from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_devices import FILE_MODE, NumpyEncoder, TangoctlDevices
from ska_tangoctl.tango_control.tango_control import TangoControl
from ska_tangoctl.tango_kontrol.tango_kontrol_help import TangoKontrolHelpMixin
from ska_tangoctl.tango_kontrol.tangoktl_config import TANGOKTL_CONFIG, read_tangoktl_config


class TangoKontrol(TangoControl, TangoKontrolHelpMixin):
    """Read Tango devices running in a Kubernetes cluster."""

    def __init__(
        self,
        logger: logging.Logger,
        k8s_ctx: str | None,
        k8s_cluster: str | None,
        domain_name: str | None,
    ):
        """
        Initialize this thing.

        :param logger: logging handle
        :param k8s_ctx: Kubernetes context
        :param k8s_cluster: Kubernetes
        :param domain_name: Kubernetes domain name
        """
        super().__init__(logger)
        self.cfg_data: Any = TANGOKTL_CONFIG
        self.pod_cmd: str = ""
        self.show_svc: bool = False
        self.use_fqdn: bool = True
        self.k8s_ns: str | None = None
        self.k8s_ctx: str | None = k8s_ctx
        self.k8s_cluster: str | None = k8s_cluster
        self.k8s_pod: str | None = None
        self.domain_name: str | None = domain_name
        self.outf: Any = sys.stdout
        self.logger.info("Initialize with context %s", self.k8s_ctx)

    def __repr__(self) -> str:
        """
        Do the string thing.

        :returns: string representation
        """
        rval = f"\tDisplay format {repr(self.disp_action)}"
        rval += f"\n\tShow {'attributes' if self.disp_action.show_attrib else ''}"
        rval += f" {'commands' if self.disp_action.show_cmd else ''}"
        rval += f" {'properties' if self.disp_action.show_prop else ''}"
        rval += f"\n\tNamespace: {self.k8s_ns}"
        rval += f"\n\tConfiguration: {self.cfg_data}"
        return rval

    def reset(self) -> None:
        """Reset it to defaults."""
        self.logger.debug("Reset")
        super().reset()
        self.cfg_data = TANGOKTL_CONFIG
        self.pod_cmd = ""
        self.disp_action.show_ctx = False
        self.disp_action.show_ns = False
        self.disp_action.show_svc = False
        self.use_fqdn = True
        self.k8s_ns = None
        # self.k8s_ctx: str | None = k8s_ctx
        # self.k8s_cluster: str | None = k8s_cluster

    def setup(  # noqa: C901
        self,
        cfg_name: str | None = None,
        cfg_data: Any = TANGOKTL_CONFIG,
        dev_on: bool | None = None,
        dev_off: bool | None = None,
        dev_ping: bool | None = None,
        dev_standby: bool | None = None,
        dev_status: dict = {},
        dev_test: bool | None = None,
        dev_admin: int | None = None,
        dev_sim: int | None = None,
        disp_action: DispAction = DispAction(DispAction.TANGOCTL_NONE),
        dry_run: bool | None = None,
        evrythng: bool | None = None,
        indent: int = 0,
        input_file: str | None = None,
        json_dir: str | None = None,
        logging_level: int | None = None,
        output_file: str | None = None,
        quiet_mode: bool | None = None,
        reverse: bool | None = None,
        show_attrib: bool | None = None,
        show_class: bool | None = None,
        show_cmd: bool | None = None,
        show_jargon: bool | None = None,
        show_prop: bool | None = None,
        show_tango: bool | None = None,
        show_tree: bool | None = None,
        show_version: bool | None = None,
        tango_host: str | None = None,
        tgo_attrib: str | None = None,
        tgo_class: str | None = None,
        tgo_cmd: str | None = None,
        tgo_in_type: str | None = None,
        tgo_name: str | None = None,
        tgo_prop: str | None = None,
        tgo_value: str | None = None,
        timeout_millis: int | None = None,
        uniq_cls: bool | None = None,
        xact_match: bool | None = None,
        ns_name: str | None = None,
        show_ctx: bool | None = None,
        pod_cmd: str | None = None,
        show_ns: bool | None = None,
        show_svc: bool | None = None,
        use_fqdn: bool | None = None,
    ) -> None:
        """
        Set it up.

        TODO find a use for this

        :param cfg_name: config file name
        :param dev_on: device on
        :param dev_off: device off
        :param dev_ping: ping the device
        :param dev_standby: device standby
        :param dev_status: device status
        :param dev_test: device test
        :param dev_admin: device admin
        :param dev_sim: device simulation
        :param disp_action: display action
        :param dry_run: dry run
        :param evrythng: evrything
        :param indent: indentation for JSON
        :param input_file: input file
        :param json_dir: json file directory
        :param logging_level: Tango device logging level
        :param output_file: output file
        :param quiet_mode: quiet mode
        :param reverse: reverse
        :param show_attrib: show attributes
        :param show_class: show classes
        :param show_cmd: show commands
        :param show_ctx: show K8S contexts
        :param show_jargon: show jargon
        :param show_prop: show properties
        :param dev_status: show status
        :param show_tango: show tango
        :param show_tree: show tree
        :param show_version: show version
        :param tango_host: tango host
        :param tgo_attrib: attribute name
        :param tgo_class: class name
        :param tgo_cmd: command name
        :param tgo_in_type: input type
        :param tgo_name: device name
        :param tgo_prop: property name
        :param tgo_value: value
        :param timeout_millis: Tango device timeout in milliseconds
        :param uniq_cls: unique class
        :param cfg_data: TANGOKTL config
        :param xact_match: exact matches only
        :param ns_name: K8S namespace
        :param pod_cmd: show K8S pods
        :param show_ns: show namespace
        :param show_svc: show services
        :param use_fqdn: use FQDN for database server
        """
        if cfg_name is not None:
            self.cfg_name = cfg_name
        if dev_on is not None:
            self.dev_on = dev_on
        if dev_off is not None:
            self.dev_off = dev_off
        if dev_ping is not None:
            self.dev_ping = dev_ping
        if dev_standby is not None:
            self.dev_standby = dev_standby
        if dev_status:
            self.dev_status = dev_status
        if dev_test is not None:
            self.dev_test = dev_test
        if dev_admin is not None:
            self.dev_admin = dev_admin
        if dev_sim is not None:
            self.dev_sim = dev_sim
        if not disp_action.check(DispAction.TANGOCTL_NONE):
            self.disp_action = disp_action
        if dry_run is not None:
            self.dry_run = dry_run
        if evrythng is not None:
            self.disp_action.evrythng = evrythng
        if indent:
            self.disp_action.indent = indent
        if input_file is not None:
            self.input_file = input_file
        if json_dir is not None:
            self.json_dir = json_dir
        if logging_level is not None:
            self.logging_level = logging_level
        if output_file is not None:
            self.output_file = output_file
        if quiet_mode is not None:
            self.disp_action.quiet_mode = quiet_mode
        if reverse is not None:
            self.disp_action.reverse = reverse
        if show_attrib is not None:
            self.disp_action.show_attrib = show_attrib
        if show_cmd is not None:
            self.disp_action.show_cmd = show_cmd
        if show_jargon is not None:
            self.disp_action.show_jargon = show_jargon
        if show_prop is not None:
            self.disp_action.show_prop = show_prop
        if dev_status:
            self.dev_status = dev_status
        if show_svc is not None:
            self.show_svc = show_svc
        if show_tango is not None:
            self.disp_action.show_tango = show_tango
        if show_tree is not None:
            self.disp_action.show_tree = show_tree
        if show_version is not None:
            self.disp_action.show_version = show_version
        if tango_host is not None:
            self.tango_host = tango_host
        if tgo_attrib is not None:
            self.tgo_attrib = tgo_attrib
        if tgo_class is not None:
            self.tgo_class = tgo_class
        if tgo_cmd is not None:
            self.tgo_cmd = tgo_cmd
        # TODO Feature to search by input type not implemented yet
        if tgo_in_type is not None:
            self.tgo_in_type = tgo_in_type
        if tgo_name is not None:
            self.tgo_name = tgo_name
        if tgo_prop is not None:
            self.tgo_prop = tgo_prop
        if tgo_value is not None:
            self.tgo_value = tgo_value
        if cfg_data:
            self.cfg_data = cfg_data
        if uniq_cls is not None:
            self.uniq_cls = uniq_cls
        if ns_name is not None:
            self.k8s_ns = ns_name
        if pod_cmd is not None:
            self.pod_cmd = pod_cmd
        if show_ns is not None:
            self.disp_action.show_ns = show_ns
        if use_fqdn is not None:
            self.use_fqdn = use_fqdn
        if timeout_millis is not None:
            self.timeout_millis = timeout_millis

    def set_output(self):
        """Open output file."""
        if self.output_file is not None:
            self.logger.info("Write output file %s", self.output_file)
            self.outf = open(self.output_file, FILE_MODE)
        else:
            self.outf = sys.stdout

    def unset_output(self):
        """Close output file."""
        if self.output_file is not None:
            self.logger.info("Close output file %s", self.output_file)
            self.outf.close()

    def read_config(self) -> None:
        """Read configuration."""
        self.cfg_data = read_tangoktl_config(self.logger, self.cfg_name)

    def read_command_line(self, cli_args: list) -> int:  # noqa: C901
        """
        Read the command line interface.

        :param cli_args: arguments
        :return: error condition
        """
        self.logger.debug("Read options : %s", cli_args)
        try:
            opts, _args = getopt.getopt(
                cli_args[1:],
                "acdefghijklmnopqQrstuvwxxyzV01A:C:D:F:H:I:J:K:N:O:P:R:X:T:X:Z:",
                [
                    "dry-run",
                    "everything",
                    "exact",
                    "full",
                    "help",
                    "html",
                    "ip",
                    "json",
                    "list",
                    "md",
                    "medium",
                    "off",
                    "on",
                    "ping",
                    "pod-df",
                    "pod-domain",
                    "pod-env",
                    "pod-free",
                    "pod-host",
                    "pod-lscpu",
                    "pod-mpstat",
                    "pod-ps",
                    "pod-top",
                    "pod-uptime",
                    "reverse",
                    "standby",
                    "status",
                    "short",
                    "show-acronym",
                    "show-attribute",
                    "show-class",
                    "show-command",
                    "show-context",
                    "show-db",
                    "show-dev",
                    "show-log",
                    "show-ns",
                    "show-pod",
                    "show-property",
                    "show-proc",
                    "show-svc",
                    "small",
                    "table",
                    "test",
                    "tree",
                    "txt",
                    "unique",
                    "version",
                    "yaml",
                    "admin=",
                    "attribute=",
                    "class=",
                    "cfg=",
                    "command=",
                    "context=",
                    "count=",
                    "device=",
                    "host=",
                    "indent=",
                    "input=",
                    "json-dir=",
                    "log-level=",
                    "ns=",
                    "namespace=",
                    "pod=",
                    "output=",
                    "port=",
                    "property=",
                    "simul=",
                    "timeout=",
                    "type=",
                    "value=",
                ],
            )
        except getopt.GetoptError as opt_err:
            self.logger.error("Could not read command line: %s", opt_err)
            return 1

        for opt, arg in opts:
            if opt in ("-a", "--show-attribute"):
                self.disp_action.show_attrib = True
            elif opt in ("-A", "--attribute"):
                self.tgo_attrib = arg
                self.disp_action.show_attrib = True
            elif opt == "--admin":
                self.dev_admin = int(arg)
            elif opt in ("-c", "--show-command"):
                self.disp_action.show_cmd = True
            elif opt in ("-C", "--command"):
                self.tgo_cmd = arg.lower()
                self.disp_action.show_cmd = True
            elif opt == "--count":
                self.dev_count = int(arg)
            elif opt in ("-d", "--show-dev"):
                self.disp_action.value = DispAction.TANGOCTL_NAMES
            elif opt in ("-D", "--device"):
                self.tgo_name = arg.lower()
            # TODO Undocumented and unused feature for dry runs
            elif opt == "--dry-run":
                self.dry_run = True
            elif opt in ("-e", "--everything"):
                self.disp_action.evrythng = True
            elif opt == "--exact":
                self.disp_action.xact_match = True
            elif opt in ("-f", "--full"):
                self.disp_action.size = "L"
            elif opt in ("-F", "--cfg"):
                self.cfg_name = arg
            elif opt in ("-g", "--show-log"):
                self.disp_action.show_log = True
            elif opt == "--log-level":
                self.logging_level = int(arg)
            elif opt in ("-h", "--help"):
                if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
                    self.usage4(os.path.basename(cli_args[0]))
                else:
                    self.usage3(os.path.basename(cli_args[0]))
                return 1
            elif opt in ("-H", "--host"):
                self.tango_host = arg
                self.logger.debug("Set host to %s", self.tango_host)
            elif opt in ("-i", "--show-db"):
                self.disp_action.show_tango = True
            elif opt in ("-I", "--input"):
                self.input_file = arg
            elif opt == "--indent":
                self.disp_action.indent = int(arg)
            elif opt in ("-j", "--json"):
                self.disp_action.value = DispAction.TANGOCTL_JSON
            elif opt in ("-J", "--json-dir"):
                self.json_dir = arg
            elif opt in ("-k", "--show-class"):
                self.disp_action.show_class = True
            elif opt in ("-K", "--class"):
                self.tgo_class = arg
            elif opt in ("-l", "--list"):
                self.disp_action.value = DispAction.TANGOCTL_LIST
            elif opt == "--log-level":
                self.logging_level = int(arg)
            elif opt in ("-m", "--md"):
                self.disp_action.value = DispAction.TANGOCTL_MD
            elif opt in ("-n", "--show-ns"):
                self.disp_action.show_ns = True
            elif opt in ("-N", "--ns", "--namespace"):
                self.k8s_ns = arg
            elif opt in ("-o", "--show-pod"):
                self.disp_action.show_pod = True
            elif opt == "--pod-df":
                self.pod_cmd = "df -h"
            elif opt == "--pod-domain":
                self.pod_cmd = "domainname"
            elif opt == "--pod-env":
                self.pod_cmd = "env"
            elif opt == "--pod-free":
                self.pod_cmd = "free -h"
            elif opt == "--pod-host":
                self.pod_cmd = "hostname"
            elif opt == "--pod-lscpu":
                self.pod_cmd = "lscpu -e"
            elif opt == "--pod-mpstat":
                self.pod_cmd = "mpstat"
            elif opt == "--pod-ps":
                self.pod_cmd = "ps -ef"
            elif opt == "--pod-top":
                self.pod_cmd = "top -b -n1"
            elif opt == "--pod-uptime":
                self.pod_cmd = "uptime"
            elif opt in ("-O", "--output"):
                self.output_file = arg
            elif opt == "--ping":
                self.dev_ping = True
            elif opt in ("-p", "--show-property"):
                self.disp_action.show_prop = True
            elif opt in ("-P", "--property"):
                self.tgo_prop = arg.lower()
                self.disp_action.show_prop = True
            elif opt == "-q":
                self.disp_action.quiet_mode = True
                self.logger.setLevel(logging.WARNING)
            elif opt == "-Q":
                self.disp_action.quiet_mode = True
                self.logger.setLevel(logging.ERROR)
            elif opt == "--reverse":
                self.disp_action.reverse = True
            elif opt in ("-r", "--show-proc"):
                self.disp_action.show_proc = True
            elif opt in ("-R", "--pod"):
                self.k8s_pod = arg
            # TODO simulation to be deprecated
            elif opt == "--simul":
                self.dev_sim = int(arg)
            elif opt in ("-s", "--short", "--small"):
                self.disp_action.size = "S"
            elif opt == "--standby":
                self.dev_standby = True
            elif opt == "--status":
                dev_status = {
                    "attributes": list(self.cfg_data["list_items"]["attributes"].keys()),
                    "commands": list(self.cfg_data["list_items"]["commands"].keys()),
                    "properties": list(self.cfg_data["list_items"]["properties"].keys()),
                }
                self.logger.info("Status set to %s", dev_status)
            elif opt == "--table":
                self.disp_action.value = DispAction.TANGOCTL_TABL
            elif opt == "--test":
                self.dev_test = True
            elif opt == "--tree":
                self.disp_action.show_tree = True
            elif opt in ("-t", "--txt"):
                self.disp_action.value = DispAction.TANGOCTL_TXT
            # TODO Feature to search by input type, not implemented yet
            elif opt in ("-T", "--type"):
                self.tgo_in_type = arg.lower()
                self.logger.info("Input type %s not implemented", self.tgo_in_type)
                return 1
            elif opt in ("-u", "--medium"):
                self.disp_action.size = "M"
            elif opt == "--unique":
                self.uniq_cls = True
            elif opt == "-v":
                self.disp_action.quiet_mode = False
                self.logger.setLevel(logging.INFO)
            elif opt == "-V":
                self.disp_action.quiet_mode = False
                self.logger.setLevel(logging.DEBUG)
            elif opt == "--version":
                self.disp_action.show_version = True
            elif opt in ("-w", "--html"):
                self.disp_action.value = DispAction.TANGOCTL_HTML
            elif opt in ("-W", "--value"):
                self.tgo_value = str(arg)
            elif opt in ("-x", "show-context"):
                self.disp_action.show_ctx = True
            elif opt in ("-X", "--context"):
                self.k8s_ctx = arg
            elif opt in ("-y", "--yaml"):
                self.disp_action.value = DispAction.TANGOCTL_YAML
            elif opt in ("-z", "--show-svc"):
                self.show_svc = True
            elif opt in ("-Z", "--timeout"):
                self.timeout_millis = int(arg)
            elif opt in ("0", "--off"):
                self.dev_off = True
            elif opt in ("1", "--on"):
                self.dev_on = True
            else:
                self.logger.error("Invalid option %s", opt)
                return 1

        if self.disp_action.check(DispAction.TANGOCTL_NONE):
            self.disp_action.value = DispAction.TANGOCTL_DEFAULT
            self.logger.info("Use default format %s", self.disp_action)

        return 0

    def get_pods_dict(self, ns_name: str | None) -> dict:
        """
        Read pods in Kubernetes namespace.

        :param ns_name: namespace name
        :return: dictionary with devices
        """
        self.logger.debug("Read Kubernetes pods")
        pods_dict: dict = {}
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return pods_dict
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        pods_dict = k8s.get_pods(ns_name, None)
        self.logger.info("Read %d pods", len(pods_dict))
        return pods_dict

    def print_pod_names(self, ns_name: str | None) -> None:  # noqa: C901
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        """
        self.logger.debug("Print Kubernetes pods")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return
        pods_dict: dict = self.get_pods_dict(ns_name)
        print(f"Pods in namespace {ns_name} : {len(pods_dict)}")
        pod_name: str
        for pod_name in pods_dict:
            print(f"\t{pod_name}")

    def print_pod_procs(self) -> int:
        """Print processes running in pod."""
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        if self.k8s_ns is None:
            self.logger.error("Namespace not set")
            return 1
        if self.k8s_pod is None:
            self.logger.error("Pod name not set")
            return 1
        pod = self.pod_run_cmd(k8s, self.k8s_ns, self.k8s_pod, "ps -ef")
        for line in pod["output"]:
            print(f"{line}")
        return 0

    def pod_run_cmd(self, k8s: KubernetesInfo, ns_name: str, pod_name: str, pod_cmd: str) -> dict:
        """
        Run a command in specified pod.

        :param k8s: K8S info handle
        :param ns_name: namespace
        :param pod_name: pod name
        :param pod_cmd: command to run
        :returns: dictionary with output information
        """
        pod: dict = {}
        pod["name"] = pod_name
        pod["command"] = pod_cmd
        self.logger.info("Run command in pod %s: %s", pod_name, pod_cmd)
        pod_exec: list = pod_cmd.split(" ")
        resps: str = k8s.exec_command(ns_name, pod_name, pod_exec)
        pod["output"] = []
        if not resps:
            pod["output"].append("N/A")
        elif "\n" in resps:
            resp: str
            for resp in resps.split("\n"):
                if not resp:
                    pass
                elif resp[-6:] == "ps -ef":
                    pass
                elif resp[0:3] == "UID":
                    pass
                elif resp[0:3] == "PID":
                    pass
                else:
                    pod["output"].append(resp)
        else:
            pod["output"].append(resps)
        return pod

    def print_pod(self, ns_name: str | None, pod_name: str | None, pod_cmd: str) -> None:  # noqa: C901
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param pod_name: pod name
        :param pod_cmd: command to run
        """
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        pod_exec: list = pod_cmd.split(" ")
        print(f"Pod in namespace {ns_name} : '{pod_cmd}'")
        print(f"\t{pod_name}")
        if not self.disp_action.quiet_mode:
            resps: str = k8s.exec_command(ns_name, pod_name, pod_exec)
            if not resps:
                pass
            elif "\n" in resps:
                resp: str
                for resp in resps.split("\n"):
                    self.logger.debug("Got '%s'", resp)
                    if not resp:
                        pass
                    elif resp[-6:] == "ps -ef":
                        pass
                    elif resp[0:3] == "UID":
                        pass
                    elif resp[0:3] == "PID":
                        pass
                    # TODO to show nginx or not to show nginx
                    # elif "nginx" in resp:
                    #     pass
                    elif resp[0:5] in ("tango", "root ", "mysql") or resp[0:3] == "100":
                        respl = resp.split()
                        print(f"\t\t* {respl[0]:8} {' '.join(respl[7:])}")
                    else:
                        print(f"\t\t  {resp}")
            else:
                print(f"\t\t- {resps}")

    def print_pods(self, ns_name: str | None, pod_cmd: str) -> None:  # noqa: C901
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param pod_cmd: command to run
        """
        self.logger.debug("Print Kubernetes pods: %s", pod_cmd)
        pod_exec: list = pod_cmd.split(" ")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        pods_dict: dict = self.get_pods_dict(ns_name)
        print(f"{len(pods_dict)} pods in namespace {ns_name} : '{pod_cmd}'")
        pod_name: str
        for pod_name in pods_dict:
            print(f"\t{pod_name}")
            if not self.disp_action.quiet_mode:
                resps: str = k8s.exec_command(ns_name, pod_name, pod_exec)
                if not resps:
                    pass
                elif "\n" in resps:
                    resp: str
                    for resp in resps.split("\n"):
                        self.logger.debug("Got '%s'", resp)
                        if not resp:
                            pass
                        elif resp[-6:] == "ps -ef":
                            pass
                        elif resp[0:3] == "UID":
                            pass
                        elif resp[0:3] == "PID":
                            pass
                        # TODO to show nginx or not to show nginx
                        # elif "nginx" in resp:
                        #     pass
                        elif resp[0:5] in ("tango", "root ", "mysql") or resp[0:3] == "100":
                            respl = resp.split()
                            print(f"\t\t* {respl[0]:8} {' '.join(respl[7:])}")
                        else:
                            print(f"\t\t  {resp}")
                else:
                    print(f"\t\t- {resps}")

    def get_pods_json(self, ns_name: str | None, pod_cmd: str) -> list:  # noqa: C901
        """
        Read pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param pod_cmd: command to run on pod
        :return: dictionary with pod information
        """
        self.logger.debug("Get Kubernetes pods as JSON: %s", pod_cmd)
        pods: list = []
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return pods
        # pod_exec: list = ["ps", "-ef"]
        # pod_exec: list = pod_cmd.split(" ")
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return pods
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        self.logger.debug("Read pods running in namespace %s", ns_name)
        pods_list: dict = k8s.get_pods(ns_name, None)
        self.logger.info("Found %d pods running in namespace %s", len(pods_list), ns_name)
        pod_name: str
        for pod_name in pods_list:
            pod: dict = self.pod_run_cmd(k8s, ns_name, pod_name, pod_cmd)
            pods.append(pod)
        return pods

    def show_pod(self, pod_cmd: str) -> None:
        """
        Display pods in Kubernetes namespace.

        :param pod_cmd: command to run
        """
        self.set_output()
        if self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.print_pod(self.k8s_ns, self.k8s_pod, pod_cmd)
        else:
            self.logger.warning("Output format %s not supported", self.disp_action)
        self.unset_output()

    def show_pods(self, pod_cmd: str) -> None:
        """
        Display pods in Kubernetes namespace.

        :param pod_cmd: command to run
        """
        self.logger.debug("Show Kubernetes pods as JSON")
        pods: list
        self.set_output()
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            if not self.disp_action.indent:
                self.disp_action.indent = 4
            pods = self.get_pods_json(self.k8s_ns, pod_cmd)
            print(json.dumps(pods, indent=self.disp_action.indent), file=self.outf)
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            if not self.disp_action.indent:
                self.disp_action.indent = 2
            pods = self.get_pods_json(self.k8s_ns, pod_cmd)
            print(yaml.dump(pods, indent=self.disp_action.indent), file=self.outf)
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            if pod_cmd == "?":
                self.print_pod_names(self.k8s_ns)
            else:
                self.print_pods(self.k8s_ns, pod_cmd)
        else:
            self.logger.warning("Output format %s not supported", self.disp_action)
        self.unset_output()

    def print_k8s_info(self) -> None:
        """Print kubernetes context and namespace."""
        if self.k8s_ctx:
            print(f"Active context : {self.k8s_ctx}", file=self.outf)
        if self.k8s_ctx:
            print(f"Active cluster : {self.k8s_cluster}", file=self.outf)
        if self.k8s_ns:
            print(f"K8S namespace : {self.k8s_ns}", file=self.outf)
        if self.domain_name:
            print(f"Domain : {self.domain_name}", file=self.outf)

    def run_info(self) -> int:  # noqa: C901
        """
        Read information on Tango devices.

        :return: error condition
        """
        rc: int
        devices: TangoctlDevices
        self.logger.info(
            "Run info display %s : device %s attribute %s command %s property %s for K8S...",
            repr(self.disp_action),
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_cmd,
            self.tgo_prop,
        )
        self.set_output()

        # List Tango devices
        if self.disp_action.size == "S" and not (
            self.disp_action.show_attrib
            or self.disp_action.show_cmd
            or self.disp_action.show_attrib
        ):
            rc = self.list_devices()
            self.unset_output()
            return rc

        # Get device classes
        if self.disp_action.check(DispAction.TANGOCTL_CLASS):
            rc = self.list_classes()
            self.unset_output()
            return rc

        # Check if there is something to do
        if (
            self.tgo_name is None
            and self.tgo_attrib is None
            and self.tgo_cmd is None
            and self.tgo_prop is None
            and self.disp_action.check(0)
            and not (
                self.disp_action.show_attrib
                or self.disp_action.show_cmd
                or self.disp_action.show_prop
                or self.dev_status
            )
            and self.disp_action.check(
                [DispAction.TANGOCTL_JSON, DispAction.TANGOCTL_TXT, DispAction.TANGOCTL_YAML]
            )
        ):
            self.logger.error(
                "No filters specified, use '-l' flag to list all devices"
                " or '-e' for a full display of every device in the namespace",
            )
            self.unset_output()
            return 1

        # Get a dictionary of devices
        try:
            devices = TangoctlDevices(
                self.logger,
                self.tango_host,
                self.outf,
                self.timeout_millis,
                self.dev_status,
                self.cfg_data,
                self.tgo_name,
                self.uniq_cls,
                self.disp_action,
                self.k8s_ctx,
                self.k8s_cluster,
                self.k8s_ns,
                self.domain_name,
                self.tgo_attrib,
                self.tgo_cmd,
                self.tgo_prop,
                self.tgo_class,
                dev_count=self.dev_count,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for K8S info failed")
            self.unset_output()
            return 1

        self.logger.debug("Read devices running for K8S (action %s)", str(self.disp_action))

        # Display in specified format
        if self.disp_action.show_class:
            self.logger.debug("Read device classes")
            devices.read_devices()
            if self.disp_action.check(DispAction.TANGOCTL_JSON):
                if not self.disp_action.indent:
                    self.disp_action.indent = 4
                klasses = devices.get_classes()
                klasses["namespace"] = self.k8s_ns
                klasses["active_context"] = self.k8s_ctx
                klasses["active_cluster"] = self.k8s_cluster
                print(
                    json.dumps(klasses, indent=self.disp_action.indent, cls=NumpyEncoder),
                    file=self.outf,
                )
            elif self.disp_action.check(DispAction.TANGOCTL_YAML):
                if not self.disp_action.indent:
                    self.disp_action.indent = 2
                klasses = devices.get_classes()
                klasses["namespace"] = self.k8s_ns
                klasses["active_context"] = self.k8s_ctx
                klasses["active_cluster"] = self.k8s_cluster
                print(
                    yaml.safe_dump(klasses, default_flow_style=False, sort_keys=False),
                    file=self.outf,
                )
            else:
                devices.print_classes()
        elif self.disp_action.check(DispAction.TANGOCTL_LIST):
            self.logger.debug("List devices")
            # TODO this is messy
            self.print_k8s_info()
            devices.read_devices()
            devices.read_device_values()
            if (
                self.disp_action.show_attrib
                or self.disp_action.show_cmd
                or self.disp_action.show_prop
            ):
                if self.disp_action.show_attrib:
                    devices.print_txt_list_attributes(True)
                if self.disp_action.show_cmd:
                    devices.print_txt_list_commands(True)
                if self.disp_action.show_prop:
                    devices.print_txt_list_properties(True)
            else:
                devices.print_txt_list()
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.logger.debug("List devices as txt")
            self.print_k8s_info()
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt()
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            self.logger.debug("List devices as HTML")
            devices.read_devices()
            devices.read_device_values()
            devices.print_html()
        elif self.disp_action.check(DispAction.TANGOCTL_JSON):
            self.logger.debug("List devices as JSON")
            devices.read_devices()
            devices.read_device_values()
            devices.print_json()
        elif self.disp_action.check(DispAction.TANGOCTL_MD):
            self.logger.debug("List devices as markdown")
            devices.read_devices()
            devices.read_device_values()
            devices.print_markdown()
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            self.logger.debug("List devices as YAML")
            devices.read_devices()
            devices.read_device_values()
            devices.print_yaml()
        elif self.disp_action.check(DispAction.TANGOCTL_NAMES):
            self.logger.debug("List device names")
            self.print_k8s_info()
            devices.print_names_list()
        elif self.disp_action.check(DispAction.TANGOCTL_TABL):
            self.logger.debug("List devices in table")
            devices.read_devices()
            devices.read_device_values()
            devices.print_json_table()
        else:
            self.logger.error("Display action %s not supported", self.disp_action)

        self.unset_output()
        return 0

    def get_contexts_dict(self) -> dict:
        """
        Read contexts/clusters in Kubernetes.

        :return: dictionary with host and context names
        """
        ctx_dict: dict = {}
        self.logger.debug("Read Kubernetes contexts")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return ctx_dict
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        ctx_dict = k8s.get_contexts_dict()
        return ctx_dict

    def get_contexts_list(self) -> tuple:
        """
        Read contexts/clusters in Kubernetes.

        :return: tuple with host and context names
        """
        active_host: str
        active_ctx: str
        active_cluster: str
        k8s_list: list
        ns_list: list = []
        self.logger.debug("List Kubernetes contexts")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return None, ns_list
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        active_host, active_ctx, active_cluster, k8s_list = k8s.get_contexts_list()
        return active_host, active_ctx, active_cluster, k8s_list

    def get_namespaces_list(self) -> tuple:
        """
        Read namespaces in Kubernetes cluster.

        :return: tuple with context name, cluster name and list with devices
        """
        ns_list: list = []
        k8s_list: list
        _ctx_name: str | None
        self.logger.debug("List Kubernetes namespaces")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return None, None, ns_list
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        _ctx_name, _cluster_name, k8s_list = k8s.get_namespaces_list(self.k8s_ns)
        if self.k8s_ns is None:
            return k8s.context, k8s.cluster, k8s_list
        for k8s_name in k8s_list:
            if k8s_name == self.k8s_ns:
                ns_list.append(k8s_name)
        self.logger.info("Read %d namespaces: %s", len(ns_list), ",".join(ns_list))
        return k8s.context, k8s.cluster, ns_list

    def get_namespaces_dict(self) -> dict:
        """
        Read namespaces in Kubernetes cluster.

        :return: dictionary with devices
        """
        ns_dict: dict = {}
        self.logger.debug("Read Kubernetes namespaces")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return ns_dict
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        ns_dict = k8s.get_namespaces_dict()
        self.logger.info("Read %d namespaces", len(ns_dict))
        return ns_dict

    def show_contexts(self) -> None:
        """Display contexts in Kubernetes."""
        active_host: str
        active_ctx: str
        ctx_list: list

        self.set_output()
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            if not self.disp_action.indent:
                self.disp_action.indent = 4
            ctx_dict = self.get_contexts_dict()
            print(json.dumps(ctx_dict, indent=self.disp_action.indent), file=self.outf)
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            if not self.disp_action.indent:
                self.disp_action.indent = 2
            ctx_dict = self.get_contexts_dict()
            print(yaml.dump(ctx_dict, indent=self.disp_action.indent), file=self.outf)
        else:
            active_host, active_ctx, active_cluster, ctx_list = self.get_contexts_list()
            print(f"Active host : {active_host}", file=self.outf)
            print("Contexts :", file=self.outf)
            for ctx in ctx_list:
                print(f"\t{ctx}", file=self.outf)
            print(f"Active context : {active_ctx}", file=self.outf)
            print(f"Active cluster : {active_cluster}", file=self.outf)
            print(f"Domain name : {self.domain_name}", file=self.outf)
        self.unset_output()

    def show_namespaces(self) -> None:
        """Display namespaces in Kubernetes cluster."""
        self.logger.debug("Show Kubernetes namespaces")
        ns_dict: dict
        ctx_name: str | None
        ns_list: list
        ns_name: str

        self.set_output()

        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return

        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            if not self.disp_action.indent:
                self.disp_action.indent = 4
            ns_dict = self.get_namespaces_dict()
            print(json.dumps(ns_dict, indent=self.disp_action.indent), file=self.outf)
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            if not self.disp_action.indent:
                self.disp_action.indent = 2
            ns_dict = self.get_namespaces_dict()
            print(yaml.dump(ns_dict, indent=self.disp_action.indent), file=self.outf)
        else:
            ctx_name, cluster_name, ns_list = self.get_namespaces_list()
            print(f"Context : {ctx_name}", file=self.outf)
            print(f"Cluster : {cluster_name}", file=self.outf)
            print(f"Namespaces : {len(ns_list)}", file=self.outf)
            for ns_name in sorted(ns_list, reverse=self.disp_action.reverse):
                print(f"\t{ns_name}", file=self.outf)

        self.unset_output()

    def show_services(self) -> None:
        """Display services in Kubernetes namespace."""
        self.logger.debug("Show Kubernetes services (%s)", self.disp_action)
        self.set_output()
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            if not self.disp_action.indent:
                self.disp_action.indent = 4
            service_dict = k8s.get_services_dict(self.k8s_ns)
            print(
                f"***\n{json.dumps(service_dict, indent=self.disp_action.indent)}", file=self.outf
            )
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            if not self.disp_action.indent:
                self.disp_action.indent = 2
            service_dict = k8s.get_services_dict(self.k8s_ns)
            print(yaml.dump(service_dict, indent=self.disp_action.indent), file=self.outf)
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            service_list = k8s.get_services_data(self.k8s_ns)
            self.logger.debug("Kubernetes services:\n%s", service_list)
            if not service_list.items:
                self.logger.error("No services found in namespace %s", self.k8s_ns)
                return
            for service in service_list.items:
                print(f"Service Name: {service.metadata.name}", file=self.outf)
                print(f"  Type: {service.spec.type}", file=self.outf)
                print(f"    IP: {service.spec.cluster_ip}", file=self.outf)
                if service.spec.ports:
                    for port in service.spec.ports:
                        print(
                            f"  Port: {port.port}, Target Port: {port.target_port},"
                            f" Protocol: {port.protocol}",
                            file = self.outf,
                        )
                print("-" * 20, file=self.outf)
        else:
            self.logger.warning("Nothing to do!")
        self.unset_output()

    def show_pod_log(self) -> int:
        """Read pod logs."""
        self.set_output()
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        if self.k8s_pod is None:
            self.logger.error("Pod name not set")
            return 1
        pod_log = k8s.get_pod_log(self.k8s_ns, self.k8s_pod)
        print(f"{pod_log}", file=self.outf)
        self.unset_output()
        return 0

    def read_tango_host(self, ntango: int, ntangos: int) -> int:  # noqa: C901
        """
        Read info from Tango host.

        :param ntango: index number,
        :param ntangos: index count
        :return: error condition
        """
        rc: int = 0

        # Fork just in case, so that ctrl-C will work (most of the time)
        pid: int = os.fork()
        if pid == 0:
            # Do the actual reading
            self.logger.info("Processing namespace %s", self.k8s_ns)
            rc = self.run_info()
            self.logger.info("Processed namespace %s", self.k8s_ns)
            sys.exit(rc)
        else:
            # Wait for the reading process
            try:
                os.waitpid(pid, 0)
            except OSError:
                pass
            self.logger.info("Processing %s finished (PID %d)", self.k8s_ns, pid)

        return rc
