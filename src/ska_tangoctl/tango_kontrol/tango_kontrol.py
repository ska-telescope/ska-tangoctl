"""Read all information about Tango devices in a Kubernetes cluster."""

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
from ska_tangoctl.tango_control.read_tango_devices import NumpyEncoder, TangoctlDevices
from ska_tangoctl.tango_control.tango_control import TangoControl
from ska_tangoctl.tango_kontrol.tango_kontrol_help import TangoKontrolHelpMixin
from ska_tangoctl.tango_kontrol.tango_kontrol_setup import TangoKontrolSetupMixin
from ska_tangoctl.tango_kontrol.tangoktl_config import TANGOKTL_CONFIG, read_tangoktl_config


class TangoKontrol(  # type:ignore[misc]
    TangoControl, TangoKontrolHelpMixin, TangoKontrolSetupMixin
):
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
        self.logger.info("Initialize with context %s", self.k8s_ctx)

    def __repr__(self) -> str:
        """
        Do the string thing.

        :returns: string representation
        """
        rval = f"\tDisplay format {repr(self.disp_action)}"
        rval += "\n\tShow"
        rval += f"{' attributes' if self.disp_action.show_attrib else ''}"
        rval += f"{' commands' if self.disp_action.show_cmd else ''}"
        rval += f"{' properties' if self.disp_action.show_prop else ''}"
        rval += f"{' pods' if self.disp_action.show_pod else ''}"
        rval += f"{' processes' if self.disp_action.show_proc else ''}"
        if self.tgo_name:
            rval += f"\n\tDevices: {self.tgo_name}"
        if self.tgo_attrib:
            rval += f"\n\tAttributes: {self.tgo_attrib}"
        if self.tgo_cmd:
            rval += f"\n\tCommands: {self.tgo_attrib}"
        if self.tgo_prop:
            rval += f"\n\tProperties: {self.tgo_prop}"
        rval += f"\n\tContext: {self.k8s_ctx}"
        rval += f"\n\tNamespace: {self.k8s_ns}"
        rval += f"\n\tDomain: {self.domain_name}"
        rval += f"\n\tDetail: {self.disp_action.size}"
        if self.logger.getEffectiveLevel() == logging.DEBUG:
            rval += f"\n\tConfiguration:\n{json.dumps(self.cfg_data, indent=4)}"
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

    def read_config(self) -> None:
        """Read configuration."""
        self.cfg_data = read_tangoktl_config(self.logger, self.cfg_name)

    def get_pods_dict(self, ns_name: str | None) -> dict:
        """
        Read pods in Kubernetes namespace.

        :param ns_name: namespace name
        :return: dictionary with devices
        """
        self.logger.debug("Get Kubernetes pods")
        pods_dict: dict = {}
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return pods_dict
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        pods_dict = k8s.get_pods(ns_name, None)
        self.logger.info("Got %d pods", len(pods_dict))
        self.logger.debug("Pods", json.dumps(pods_dict, indent=4, default=str))
        return pods_dict

    def list_pod_names(self, ns_name: str | None) -> int:  # noqa: C901
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :returns: error condition
        """
        self.logger.debug("List Kubernetes pod names")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return 1
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return 1
        pods_dict: dict = self.get_pods_dict(ns_name)
        if not pods_dict:
            self.logger.error("Could not read pods")
            return 1
        print(f"Pods in namespace {ns_name} : {len(pods_dict)}")
        pod_name: str
        for pod_name in pods_dict:
            print(f"\t{pod_name}")
        self.logger.info("Listed %d Kubernetes pod names", len(pods_dict))
        return 0

    def print_pod_procs(self) -> int:
        """
        Print processes running in pod.

        :returns: error condition
        """
        self.logger.debug("Print Kubernetes pod processes")
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
        self.logger.info("Printed %d Kubernetes pod processes", len(pod["output"]))
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
        resps: str = k8s.exec_pod_command(ns_name, pod_name, pod_exec)
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

    def print_pod(  # noqa: C901
        self, ns_name: str | None, pod_name: str | None, pod_cmd: str
    ) -> int:
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param pod_name: pod name
        :param pod_cmd: command to run
        :returns: error condition
        """
        self.logger.info("Print output of command '%s' in pod %s", pod_cmd, pod_name)
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        pod_exec: list = pod_cmd.split(" ")
        print(f"Pod in namespace {ns_name} : '{pod_cmd}'")
        print(f"\t{pod_name}")
        if ns_name is not None and pod_name is not None:
            resps: str = k8s.exec_pod_command(ns_name, pod_name, pod_exec)
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
        return 0

    def print_pods(self, ns_name: str | None, pod_cmd: str) -> int:  # noqa: C901
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param pod_cmd: command to run
        :returns: error condition
        """
        self.logger.debug("Print Kubernetes pods: %s", pod_cmd)
        pod_exec: list = pod_cmd.split(" ")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return 1
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return 1
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        pods_dict: dict = self.get_pods_dict(ns_name)
        print(f"{len(pods_dict)} pods in namespace {ns_name} : '{pod_cmd}'")
        pod_name: str
        for pod_name in pods_dict:
            print(f"\t{pod_name}")
            if not self.disp_action.quiet_mode:
                resps: str = k8s.exec_pod_command(ns_name, pod_name, pod_exec)
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
        self.logger.debug("Printed %d Kubernetes pods: %s", len(pods_dict), pod_cmd)
        return 0

    def get_pods_json(self, ns_name: str | None, pod_cmd: str) -> list:  # noqa: C901
        """
        Read pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param pod_cmd: command to run on pod
        :returns: dictionary with pod information
        """
        self.logger.debug("Get Kubernetes pods as JSON: %s", pod_cmd)
        pods: list = []
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return pods
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return pods
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        self.logger.debug("Read pods running in namespace %s", ns_name)
        pods_dict: dict = k8s.get_pods(ns_name, None)
        self.logger.info("Found %d pods running in namespace %s", len(pods_dict), ns_name)
        pod_name: str
        for pod_name in pods_dict:
            pod: dict = self.pod_run_cmd(k8s, ns_name, pod_name, pod_cmd)
            pods.append(pod)
        self.logger.info("Got %d Kubernetes pods as JSON: %s", len(pods), pod_cmd)
        return pods

    def show_pod(self, pod_cmd: str) -> int:
        """
        Display pods in Kubernetes namespace.

        :param pod_cmd: command to run
        :returns: error condition
        """
        self.logger.info("Show pod %s : %s", self.k8s_pod, pod_cmd)
        self.set_output()
        if self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.print_pod(self.k8s_ns, self.k8s_pod, pod_cmd)
        else:
            self.logger.warning("Output format %s not supported", self.disp_action)
        self.unset_output()
        return 0

    def show_pods(self, pod_cmd: str) -> int:
        """
        Display pods in Kubernetes namespace.

        :param pod_cmd: command to run
        :returns: error condition
        """
        self.logger.debug("Show Kubernetes pods as JSON")
        pods: list
        self.set_output()
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            if not self.disp_action.indent:
                self.disp_action.indent = 4
            pods = self.get_pods_json(self.k8s_ns, pod_cmd)
            print(json.dumps(pods, indent=self.disp_action.indent), file=self.outf)
            self.logger.info("Showed %d Kubernetes pods as JSON", len(pods))
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            if not self.disp_action.indent:
                self.disp_action.indent = 2
            pods = self.get_pods_json(self.k8s_ns, pod_cmd)
            print(yaml.dump(pods, indent=self.disp_action.indent), file=self.outf)
            self.logger.info("Showed %d Kubernetes pods as YAML", len(pods))
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.print_pods(self.k8s_ns, pod_cmd)
            self.logger.info("Showed Kubernetes pods")
        else:
            self.logger.warning("Output format %s not supported", self.disp_action)
            self.unset_output()
            return 1
        self.unset_output()
        return 0

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
            self.disp_action.show(),
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_cmd,
            self.tgo_prop,
        )
        self.set_output()

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
            self.logger.debug("Reading device classes")
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
            self.logger.debug("Listing devices")
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
            self.logger.debug("Listing devices as txt")
            self.print_k8s_info()
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt()
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            self.logger.debug("Listing devices as HTML")
            devices.read_devices()
            devices.read_device_values()
            devices.print_html()
        elif self.disp_action.check(DispAction.TANGOCTL_JSON):
            self.logger.debug("Listing devices as JSON")
            devices.read_devices()
            devices.read_device_values()
            devices.print_json()
        elif self.disp_action.check(DispAction.TANGOCTL_MD):
            self.logger.debug("Listing devices as markdown")
            devices.read_devices()
            devices.read_device_values()
            devices.print_markdown()
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            self.logger.debug("Listing devices as YAML")
            devices.read_devices()
            devices.read_device_values()
            devices.print_yaml()
        elif self.disp_action.check(DispAction.TANGOCTL_NAMES):
            self.logger.debug("Listing device names")
            self.print_k8s_info()
            devices.print_names_list()
        elif self.disp_action.check(DispAction.TANGOCTL_TABL):
            self.logger.debug("Listing devices in table")
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
        self.logger.info(
            "Read Kubernetes contexts: %s", json.dumps(ctx_dict, indent=4, default=str)
        )
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
        self.logger.debug("Listed Kubernetes contexts : %s", k8s_list)
        return active_host, active_ctx, active_cluster, k8s_list

    def get_namespaces_list(self) -> tuple:
        """
        Read namespaces in Kubernetes cluster.

        :return: tuple with context name, cluster name and list with devices
        """
        self.logger.debug("List Kubernetes namespaces")
        ns_list: list = []
        k8s_list: list
        _ctx_name: str | None
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
        self.logger.info("Listed %d namespaces: %s", len(ns_list), ",".join(ns_list))
        return k8s.context, k8s.cluster, ns_list

    def get_namespaces_dict(self) -> dict:
        """
        Read namespaces in Kubernetes cluster.

        :return: dictionary with devices
        """
        self.logger.debug("Get Kubernetes namespaces")
        ns_dict: dict = {}
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return ns_dict
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        ns_dict = k8s.get_namespaces_dict()
        self.logger.info("Got %d namespaces", len(ns_dict))
        self.logger.debug("Namespaces", json.dumps(ns_dict, indent=4, default=str))
        return ns_dict

    def show_contexts(self) -> int:
        """
        Display contexts in Kubernetes.

        :returns: error condition
        """
        active_host: str
        active_ctx: str
        ctx_list: list
        self.logger.debug("Display contexts in Kubernetes")

        self.set_output()
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return 1
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
        return 0

    def show_namespaces(self) -> int:
        """
        Display namespaces in Kubernetes cluster.

        :returns: error condition
        """
        self.logger.debug("Show Kubernetes namespaces")
        ns_dict: dict
        ctx_name: str | None
        ns_list: list
        ns_name: str

        self.set_output()

        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return 1

        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            if not self.disp_action.indent:
                self.disp_action.indent = 4
            ns_dict = self.get_namespaces_dict()
            print(json.dumps(ns_dict, indent=self.disp_action.indent), file=self.outf)
            self.logger.info("Showed %d Kubernetes namespaces as JSON", len(ns_dict))
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            if not self.disp_action.indent:
                self.disp_action.indent = 2
            ns_dict = self.get_namespaces_dict()
            print(yaml.dump(ns_dict, indent=self.disp_action.indent), file=self.outf)
            self.logger.info("Showed %d Kubernetes namespaces as YAML", len(ns_dict))
        else:
            ctx_name, cluster_name, ns_list = self.get_namespaces_list()
            print(f"Context : {ctx_name}", file=self.outf)
            print(f"Cluster : {cluster_name}", file=self.outf)
            print(f"Namespaces : {len(ns_list)}", file=self.outf)
            for ns_name in sorted(ns_list, reverse=self.disp_action.reverse):
                print(f"\t{ns_name}", file=self.outf)
            self.logger.info("Showed %d Kubernetes namespaces", len(ns_list))

        self.unset_output()
        return 0

    def show_services(self) -> int:
        """
        Display services in Kubernetes namespace.

        :returns: error condition
        """
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
            self.logger.debug(
                "Showed %d Kubernetes services as JSON", len(service_dict), self.disp_action
            )
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            if not self.disp_action.indent:
                self.disp_action.indent = 2
            service_dict = k8s.get_services_dict(self.k8s_ns)
            print(yaml.dump(service_dict, indent=self.disp_action.indent), file=self.outf)
            self.logger.debug(
                "Showed %d Kubernetes services as JSON", len(service_dict), self.disp_action
            )
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            service_list = k8s.get_services_data(self.k8s_ns)
            self.logger.debug("Kubernetes services:\n%s", service_list)
            if not service_list.items:
                self.logger.error("No services found in namespace %s", self.k8s_ns)
                return 1
            for service in service_list.items:
                print(f"Service Name: {service.metadata.name}", file=self.outf)
                print(f"  Type: {service.spec.type}", file=self.outf)
                print(f"    IP: {service.spec.cluster_ip}", file=self.outf)
                if service.spec.ports:
                    for port in service.spec.ports:
                        print(
                            f"  Port: {port.port}, Target Port: {port.target_port},"
                            f" Protocol: {port.protocol}",
                            file=self.outf,
                        )
                print("-" * 20, file=self.outf)
            self.logger.debug(
                "Showed %d Kubernetes services", len(service_list.items), self.disp_action
            )
        else:
            self.logger.warning("Could not show Kubernetes services as %s", self.disp_action)
        self.unset_output()
        return 0

    def show_pod_log(self) -> int:
        """
        Read pod logs.

        :returns: error condition
        """
        self.logger.debug("Read pod logs")
        if self.k8s_pod is None:
            self.logger.error("Pod name not set")
            return 1
        self.set_output()
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        pod_log = k8s.get_pod_log(self.k8s_ns, self.k8s_pod)
        print(f"{pod_log}", file=self.outf)
        self.unset_output()
        self.logger.info("Read logs for pod %s", self.k8s_pod)
        return 0

    def read_tango_host(self, ntango: int, ntangos: int) -> int:  # noqa: C901
        """
        Read info from Tango host.

        :param ntango: index number,
        :param ntangos: index count
        :return: error condition
        """
        self.logger.debug("Read Tango host")
        rc: int = 0

        # Fork just in case, so that ctrl-C will work (most of the time)
        pid: int = os.fork()
        if pid == 0:
            # Do the actual reading
            self.logger.debug("Processing namespace %s", self.k8s_ns)
            rc = self.run_info()
            self.logger.info("Processed namespace %s", self.k8s_ns)
            sys.exit(rc)
        else:
            # Wait for the reading process
            self.logger.info("Processing %s (PID %d)", self.k8s_ns, pid)
            try:
                os.waitpid(pid, 0)
            except OSError:
                pass
            self.logger.info("Processed %s (PID %d)", self.k8s_ns, pid)

        return rc
