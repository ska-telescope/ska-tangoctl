"""Set up options for tangoctl."""

import getopt
import logging
from typing import Any

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.tangoctl_config import TANGOCTL_CONFIG


class TangoControlSetupMixin:
    """Read Tango devices running in a Kubernetes cluster."""

    cfg_data: Any
    cfg_name: str | None
    dev_admin: int | None
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

    def setup(  # noqa: C901
        self,
        cfg_name: str | None = None,
        cfg_data: dict = TANGOCTL_CONFIG,
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
        :param cfg_data: TANGOCTL config
        :param xact_match: exact matches only
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
        if timeout_millis is not None:
            self.timeout_millis = timeout_millis
        if uniq_cls is not None:
            self.uniq_cls = uniq_cls

    def read_command_line(self, cli_args: list) -> int:  # noqa: C901
        """
        Read the command line interface.

        :param cli_args: arguments
        :return: error condition
        """
        try:
            opts, _args = getopt.getopt(
                cli_args[1:],
                "acdefhijklmpqQstuvwyV01A:C:D:F:H:I:J:K:O:P:T:W:X:Z:",
                [
                    "dry-run",
                    "everything",
                    "exact",
                    "full",
                    "help",
                    "html",
                    "json",
                    "large",
                    "list",
                    "md",
                    "medium",
                    "off",
                    "on",
                    "ping",
                    "standby",
                    "status",
                    "short",
                    "show-attribute",
                    "show-acronym",
                    "show-class",
                    "show-command",
                    "show-db",
                    "show-dev",
                    "show-property",
                    "small",
                    "test",
                    "tree",
                    "txt",
                    "unique",
                    "version",
                    "yaml",
                    "admin=",
                    "attribute=",
                    "cfg=",
                    "command=",
                    "device=",
                    "host=",
                    "indent=",
                    "input=",
                    "json-dir=",
                    "log-level=",
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
            print(f"Could not read command line: {opt_err}")
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
            # C
            elif opt in ("-c", "--show-command"):
                self.disp_action.show_cmd = True
            elif opt in ("-C", "--command"):
                self.tgo_cmd = arg.lower()
                self.disp_action.show_cmd = True
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
            elif opt in ("-f", "--full", "--large"):
                self.disp_action.size = "L"
            elif opt in ("-F", "--cfg"):
                self.cfg_name = arg
            # H
            elif opt in ("-h", "--help"):
                if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
                    return 2
                return 1
            elif opt in ("-H", "--host"):
                self.tango_host = arg
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
                self.disp_action.format = DispAction.TANGOCTL_CLASS
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
            # Q
            elif opt == "-q":
                self.disp_action.quiet_mode = True
                self.logger.setLevel(logging.WARNING)
            elif opt == "-Q":
                self.disp_action.quiet_mode = True
                self.logger.setLevel(logging.ERROR)
            # R
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
                self.dev_status = {"attributes": ["Status", "adminMode"]}
            # T
            elif opt in ("-t", "--txt"):
                self.disp_action.format = DispAction.TANGOCTL_TXT
            # TODO Feature to search by input type not implemented yet
            elif opt in ("-T", "--type"):
                tgo_in_type = arg.lower()
                self.logger.warning("Input type '%s' not implemented", tgo_in_type)
            elif opt == "--table":
                self.disp_action.format = DispAction.TANGOCTL_TABL
            elif opt == "--test":
                self.dev_test = True
            elif opt == "--tree":
                self.disp_action.show_tree = True
            # U
            elif opt in ("-u", "--md"):
                self.disp_action.format = DispAction.TANGOCTL_MD
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
            # Y
            elif opt in ("-y", "--yaml"):
                self.disp_action.format = DispAction.TANGOCTL_YAML
            # Z
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
        return 0
