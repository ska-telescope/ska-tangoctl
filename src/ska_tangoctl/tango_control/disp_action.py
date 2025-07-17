"""Constants to make for more readable code."""

from typing import Any

BOLD: str = "\033[1m"
ITALIC: str = "\033[3m"
UNDERL: str = "\033[4m"
UNFMT: str = "\033[0m"


class DispAction:
    """Control the format here."""

    TANGOCTL_NONE: int = 0
    # TANGOCTL_FULL: int = 1
    TANGOCTL_CFG: int = 2
    # TANGOCTL_SHORT: int = 4
    TANGOCTL_LIST: int = 8
    TANGOCTL_CLASS: int = 16
    TANGOCTL_JSON: int = 32
    TANGOCTL_MD: int = 64
    TANGOCTL_TXT: int = 128
    TANGOCTL_YAML: int = 256
    TANGOCTL_HTML: int = 512
    TANGOCTL_NAMES: int = 1024
    TANGOCTL_TABL: int = 2048
    TANGOCTL_DEFAULT: int = TANGOCTL_TXT

    def __init__(self, disp_action: int):
        """
        Set up the values.

        :param disp_action: format flag
        """
        self.disp_action: int = disp_action
        self.evrythng: bool = False
        self.indent_value: int = 0
        self.show_attrib: bool = False
        self.show_class: bool = False
        self.show_cmd: bool = False
        self.show_log: bool = False
        self.show_ns: bool = False
        self.show_svc: bool = False
        self.show_ctx: bool = False
        self.show_jargon: bool = False
        self.show_pod: bool = False
        self.show_proc: bool = False
        self.show_prop: bool = False
        self.show_tango: bool = False
        self.show_tree: bool = False
        self.show_version: bool = False
        self.quiet_mode: bool = False
        self.reverse: bool = False
        self.xact_match = False
        self.size: str = "M"

    def show(self) -> str:
        """
        Print the setup.

        :returns: details about current format and output flags
        """
        rval: str = f"{self.__repr__()} {self.size}"
        rval += f"{' attributes' if self.show_attrib else ''}"
        rval += f"{' class' if self.show_class else ''}"
        rval += f"{' commands' if self.show_cmd else ''}"
        rval += f"{' logs' if self.show_log else ''}"
        rval += f"{' namespaces' if self.show_ns else ''}"
        rval += f"{' services' if self.show_svc else ''}"
        rval += f"{' contexts' if self.show_ctx else ''}"
        rval += f"{' jargon' if self.show_jargon else ''}"
        rval += f"{' pods' if self.show_pod else ''}"
        rval += f"{' properties' if self.show_prop else ''}"
        rval += f"{' processes' if self.show_proc else ''}"
        rval += f"{' properties' if self.show_prop else ''}"
        rval += f"{' tango' if self.show_tango else ''}"
        rval += f"{' tree' if self.show_tree else ''}"
        return rval

    @property
    def format(self) -> int:
        """
        Get the format.

        :returns: current format
        """
        return self.disp_action

    @format.setter
    def format(self, disp_action: int) -> None:
        """
        Set the format.

        :param disp_action: format flag
        """
        self.disp_action |= disp_action

    @property
    def indent(self) -> int:
        """
        Get the indentation.

        :returns: indentation for JSON
        """
        return self.indent_value

    @indent.setter
    def indent(self, indent_value: int) -> None:
        """
        Set the indentation for JSON and YAML.

        :param indent_value: indentation for JSON and YAML
        """
        self.indent_value = indent_value

    def check(self, disp_action: Any) -> bool:
        """
        Check the form.

        :param disp_action: format flag
        :returns: true or false
        """
        if type(disp_action) is list:
            for disp in disp_action:
                if self.disp_action & disp:
                    return True
        elif disp_action == DispAction.TANGOCTL_NONE:
            if self.disp_action == DispAction.TANGOCTL_NONE:
                return True
        else:
            if self.disp_action & disp_action:
                return True
        return False

    def __repr__(self) -> str:  # noqa: C901
        """
        Set up the string thing.

        :returns: string thing
        """
        rval: str = ""
        if self.disp_action & self.TANGOCTL_NONE:
            rval += " none"
        if self.disp_action & self.TANGOCTL_CFG:
            rval += " configuration"
        if self.disp_action & self.TANGOCTL_LIST:
            rval += " list"
        if self.disp_action & self.TANGOCTL_CLASS:
            rval += " class"
        if self.disp_action & self.TANGOCTL_JSON:
            rval += " JSON"
        if self.disp_action & self.TANGOCTL_MD:
            rval += " markdown"
        if self.disp_action & self.TANGOCTL_TXT:
            rval += " text"
        if self.disp_action & self.TANGOCTL_YAML:
            rval += " YAML"
        if self.disp_action & self.TANGOCTL_HTML:
            rval += " HTML"
        if self.disp_action & self.TANGOCTL_NAMES:
            rval += " names"
        if self.disp_action & self.TANGOCTL_TABL:
            rval += " table"
        return rval[1:]

    def __str__(self) -> str:  # noqa: C901
        """
        Set up the string thing used for file extensions.

        :returns: string thing
        """
        rval: str
        if self.disp_action & self.TANGOCTL_NONE:
            rval = "asc"
        elif self.disp_action & self.TANGOCTL_CFG:
            rval = "cfg"
        elif self.disp_action & self.TANGOCTL_LIST:
            rval = "lst"
        elif self.disp_action & self.TANGOCTL_CLASS:
            rval = "class.txt"
        elif self.disp_action & self.TANGOCTL_JSON:
            rval = "json"
        elif self.disp_action & self.TANGOCTL_MD:
            rval = "md"
        elif self.disp_action & self.TANGOCTL_TXT:
            rval = "txt"
        elif self.disp_action & self.TANGOCTL_YAML:
            rval = "yaml"
        elif self.disp_action & self.TANGOCTL_HTML:
            rval = "html"
        elif self.disp_action & self.TANGOCTL_NAMES:
            rval = "names.txt"
        elif self.disp_action & self.TANGOCTL_TABL:
            rval = "table.txt"
        else:
            rval = f"unknown{self.disp_action}.txt"
        return rval
