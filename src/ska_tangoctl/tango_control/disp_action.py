"""Constants to make for more readable code."""

from typing import Any


class DispAction:
    """Control the format here."""

    TANGOCTL_NONE: int = 0
    TANGOCTL_FULL: int = 1
    TANGOCTL_CFG: int = 2
    TANGOCTL_SHORT: int = 4
    TANGOCTL_LIST: int = 8
    TANGOCTL_CLASS: int = 16
    TANGOCTL_JSON: int = 32
    TANGOCTL_MD: int = 64
    TANGOCTL_TXT: int = 128
    TANGOCTL_YAML: int = 256
    TANGOCTL_HTML: int = 512
    TANGOCTL_DEFAULT: int = TANGOCTL_TXT

    def __init__(self, disp_action: int):
        """
        Set the value.

        :param disp_action: format flag
        """
        self.disp_action: int = disp_action

    @property
    def value(self) -> int:
        """
        Get the value.

        :returns: current value
        """
        return self.disp_action

    @value.setter
    def value(self, disp_action: int) -> None:
        """
        Set the value.

        :param disp_action: format flag
        """
        self.disp_action |= disp_action

    def check(self, disp_action: Any) -> bool:
        """
        Check the value.

        :param disp_action: format flag
        :returns: true or false
        """
        if type(disp_action) is list:
            for disp in disp_action:
                if self.disp_action & disp:
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
        rval: str
        if self.disp_action == self.TANGOCTL_FULL:
            rval = "text"
        elif self.disp_action == self.TANGOCTL_CFG:
            rval = "configuration"
        elif self.disp_action == self.TANGOCTL_SHORT:
            rval = "short"
        elif self.disp_action == self.TANGOCTL_LIST:
            rval = "list"
        elif self.disp_action == self.TANGOCTL_CLASS:
            rval = "class"
        elif self.disp_action == self.TANGOCTL_JSON:
            rval = "JSON"
        elif self.disp_action == self.TANGOCTL_MD:
            rval = "markdown"
        elif self.disp_action == self.TANGOCTL_TXT:
            rval = "text"
        elif self.disp_action == self.TANGOCTL_YAML:
            rval = "YAML"
        elif self.disp_action == self.TANGOCTL_HTML:
            rval = "HTML"
        else:
            rval = "unknown"
        return rval

    def __str__(self) -> str:  # noqa: C901
        """
        Set up the string thing.

        :returns: string thing
        """
        rval: str
        if self.disp_action == self.TANGOCTL_FULL:
            rval = "txt"
        elif self.disp_action == self.TANGOCTL_CFG:
            rval = "cfg"
        elif self.disp_action == self.TANGOCTL_SHORT:
            rval = "txt"
        elif self.disp_action == self.TANGOCTL_LIST:
            rval = "txt"
        elif self.disp_action == self.TANGOCTL_CLASS:
            rval = "txt"
        elif self.disp_action == self.TANGOCTL_JSON:
            rval = "json"
        elif self.disp_action == self.TANGOCTL_MD:
            rval = "md"
        elif self.disp_action == self.TANGOCTL_TXT:
            rval = "txt"
        elif self.disp_action == self.TANGOCTL_YAML:
            rval = "yaml"
        elif self.disp_action == self.TANGOCTL_HTML:
            rval = "html"
        else:
            rval = f"unknown {self.disp_action}"
        return rval
