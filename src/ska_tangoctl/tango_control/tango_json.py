"""Read and display Tango stuff."""

import ast
import json
import logging
import os
import re
import sys
from typing import Any

from ska_tangoctl.tango_control.progress_bar import progress_bar

from ska_tangoctl.tango_control.tango_json_html import TangoJsonReaderHtmlMixin
from ska_tangoctl.tango_control.tango_json_md import TangoJsonReaderMarkdownMixin
from ska_tangoctl.tango_control.tango_json_txt import TangoJsonReaderTextMixin
from ska_tangoctl.tango_control.tango_json_xml import TangoJsonReaderXmlMixin


class TangoJsonReader(
    TangoJsonReaderHtmlMixin,
    TangoJsonReaderMarkdownMixin,
    TangoJsonReaderTextMixin,
    TangoJsonReaderXmlMixin
):
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
