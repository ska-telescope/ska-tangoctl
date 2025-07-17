"""Set up options for tangoktl."""

import getopt
import logging
from typing import Any

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_kontrol.tangoktl_config import TANGOKTL_CONFIG


class TangoKontrolSetupMixin:
    """Read Tango devices running in a Kubernetes cluster."""

    cfg_data: Any
    cfg_name: str | None
    dev_admin: int | None
    dev_count: int
    dev_off: bool
    dev_on: bool
    dev_ping: bool
    dev_sim: int | None
    dev_standby: bool
    dev_status: dict
    dev_test: bool
    disp_action: DispAction
    dry_run: bool
    input_file: str | None
    json_dir: str | None
    k8s_ctx: str | None
    k8s_ns: str | None
    k8s_pod: str | None
    logger: logging.Logger
    logging_level: int | None
    output_file: str | None
    pod_cmd: str | None
    show_ctx: bool
    show_svc: bool
    tango_host: str | None
    tgo_attrib: str | None
    tgo_class: str | None
    tgo_cmd: str | None
    tgo_in_type: str | None
    tgo_name: str | None
    tgo_prop: str | None
    tgo_value: str | None
    timeout_millis: int | None
    uniq_cls: bool
    use_fqdn: bool
    xact_match: bool

    def setup_k8s(  # noqa: C901
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
        if show_class is not None:
            self.disp_action.show_class = show_class
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
        if xact_match is not None:
            self.disp_action.xact_match = xact_match
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
        if xact_match is not None:
            self.xact_match = xact_match
        if timeout_millis is not None:
            self.timeout_millis = timeout_millis

    def read_command_line_k8s(self, cli_args: list) -> int:  # noqa: C901
        """
        Read the command line interface.

        :param cli_args: arguments
        :return: error condition
        """
        self.logger.debug("Read options : %s", cli_args)
        try:
            opts, _args = getopt.getopt(
                cli_args[1:],
                "abcdefghijklmnpqQrstuvwxxyzV01A:B:C:D:F:H:I:J:K:N:O:P:X:T:X:Z:",
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
            # A
            if opt in ("-a", "--show-attribute"):
                self.disp_action.show_attrib = True
            elif opt in ("-A", "--attribute"):
                self.tgo_attrib = arg
                self.disp_action.show_attrib = True
            elif opt == "--admin":
                self.dev_admin = int(arg)
            # B
            elif opt in ("-b", "--show-pod"):
                self.disp_action.show_pod = True
            elif opt in ("-B", "--pod"):
                self.k8s_pod = arg
            # C
            elif opt in ("-c", "--show-command"):
                self.disp_action.show_cmd = True
            elif opt in ("-C", "--command"):
                self.tgo_cmd = arg.lower()
                self.disp_action.show_cmd = True
            elif opt == "--count":
                self.dev_count = int(arg)
            # D
            elif opt in ("-d", "--show-dev"):
                self.disp_action.format = DispAction.TANGOCTL_NAMES
            elif opt in ("-D", "--device"):
                self.tgo_name = arg.lower()
            # TODO Undocumented and unused feature for dry runs
            elif opt == "--dry-run":
                self.dry_run = True
            # E
            elif opt in ("-e", "--everything"):
                self.disp_action.evrythng = True
            elif opt == "--exact":
                self.disp_action.xact_match = True
            # F
            elif opt in ("-f", "--full"):
                self.disp_action.size = "L"
            elif opt in ("-F", "--cfg"):
                self.cfg_name = arg
            # G
            elif opt in ("-g", "--show-log"):
                self.disp_action.show_log = True
            # H
            elif opt in ("-h", "--help"):
                if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
                    return 4
                return 3
            elif opt in ("-H", "--host"):
                self.tango_host = arg
                self.logger.debug("Set host to %s", self.tango_host)
            # I
            elif opt in ("-i", "--show-db"):
                self.disp_action.show_tango = True
            elif opt in ("-I", "--input"):
                self.input_file = arg
            elif opt == "--indent":
                self.disp_action.indent = int(arg)
            # J
            elif opt in ("-j", "--json"):
                self.disp_action.format = DispAction.TANGOCTL_JSON
            elif opt in ("-J", "--json-dir"):
                self.json_dir = arg
            # K
            elif opt in ("-k", "--show-class"):
                self.disp_action.show_class = True
            elif opt in ("-K", "--class"):
                self.tgo_class = arg
            # L
            elif opt in ("-l", "--list"):
                self.disp_action.format = DispAction.TANGOCTL_LIST
            elif opt == "--log-level":
                self.logging_level = int(arg)
            # M
            elif opt in ("-m", "--medium"):
                self.disp_action.size = "M"
            # N
            elif opt in ("-n", "--show-ns"):
                self.disp_action.show_ns = True
            elif opt in ("-N", "--ns", "--namespace"):
                self.k8s_ns = arg
            # O
            elif opt in ("-O", "--output"):
                self.output_file = arg
            # P
            elif opt in ("-p", "--show-property"):
                self.disp_action.show_prop = True
            elif opt in ("-P", "--property"):
                self.tgo_prop = arg.lower()
                self.disp_action.show_prop = True
            elif opt == "--ping":
                self.dev_ping = True
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
            # Q
            elif opt == "-q":
                self.disp_action.quiet_mode = True
                self.logger.setLevel(logging.WARNING)
            elif opt == "-Q":
                self.disp_action.quiet_mode = True
                self.logger.setLevel(logging.ERROR)
            # R
            elif opt in ("-r", "--show-proc"):
                self.disp_action.show_proc = True
            elif opt == "--reverse":
                self.disp_action.reverse = True
            # S
            elif opt in ("-s", "--short", "--small"):
                self.disp_action.size = "S"
            # TODO simulation to be deprecated
            elif opt == "--simul":
                self.dev_sim = int(arg)
            elif opt == "--standby":
                self.dev_standby = True
            elif opt == "--status":
                dev_status = {
                    "attributes": list(self.cfg_data["list_items"]["attributes"].keys()),
                    "commands": list(self.cfg_data["list_items"]["commands"].keys()),
                    "properties": list(self.cfg_data["list_items"]["properties"].keys()),
                }
                self.logger.info("Status set to %s", dev_status)
            # T
            elif opt in ("-t", "--txt"):
                self.disp_action.format = DispAction.TANGOCTL_TXT
            elif opt == "--table":
                self.disp_action.format = DispAction.TANGOCTL_TABL
            elif opt == "--test":
                self.dev_test = True
            elif opt == "--tree":
                self.disp_action.show_tree = True
            # TODO Feature to search by input type, not implemented yet
            elif opt in ("-T", "--type"):
                self.tgo_in_type = arg.lower()
                self.logger.info("Input type %s not implemented", self.tgo_in_type)
                return 1
            elif opt in ("-u", "--md"):
                self.disp_action.format = DispAction.TANGOCTL_MD
            # U
            elif opt == "--unique":
                self.uniq_cls = True
            # V
            elif opt == "-v":
                self.disp_action.quiet_mode = False
                self.logger.setLevel(logging.INFO)
            elif opt == "-V":
                self.disp_action.quiet_mode = False
                self.logger.setLevel(logging.DEBUG)
            elif opt == "--version":
                self.disp_action.show_version = True
            # W
            elif opt in ("-w", "--html"):
                self.disp_action.format = DispAction.TANGOCTL_HTML
            elif opt in ("-W", "--value"):
                self.tgo_value = str(arg)
            # X
            elif opt in ("-x", "show-context"):
                self.disp_action.show_ctx = True
            elif opt in ("-X", "--context"):
                self.k8s_ctx = arg
            # Y
            elif opt in ("-y", "--yaml"):
                self.disp_action.format = DispAction.TANGOCTL_YAML
            # Z
            elif opt in ("-z", "--show-svc"):
                self.show_svc = True
            elif opt in ("-Z", "--timeout"):
                self.timeout_millis = int(arg)
            # 0-9
            elif opt in ("0", "--off"):
                self.dev_off = True
            elif opt in ("1", "--on"):
                self.dev_on = True
            else:
                self.logger.error("Invalid option %s", opt)
                return 1

        if self.disp_action.check(DispAction.TANGOCTL_NONE):
            self.disp_action.format = DispAction.TANGOCTL_DEFAULT
            self.logger.info("Use default format %s", self.disp_action)

        return 0
