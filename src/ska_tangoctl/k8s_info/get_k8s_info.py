"""
A class for doing all sorts of Kubernetes stuff.

Avoids calling 'kubectl' in a subprocess, which is not Pythonic.
"""

import json
import logging
import re
from typing import Any, Tuple

import urllib3  # type: ignore[import]
from kubernetes import client, config  # type: ignore[import]
from kubernetes.client import configuration  # type: ignore[import]
from kubernetes.client.rest import ApiException  # type: ignore[import]
from kubernetes.stream import stream  # type: ignore[import]

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class KubernetesInfo:
    """Do weird and wonderful things in a Kubernetes cluser."""

    k8s_client: Any = None
    logger: logging.Logger

    def __init__(self, logger: logging.Logger) -> None:
        """
        Get Kubernetes client.

        :param logger: logging handle
        """
        self.logger = logger
        self.logger.debug("Get Kubernetes client")
        config.load_kube_config()
        self.k8s_client = client.CoreV1Api()

        # Get current context
        _contexts, active_context = config.list_kube_config_contexts()
        self.context: str = active_context["name"]
        self.cluster: str = active_context["context"]["cluster"]
        self.logger.info("Current context: %s", self.context)
        self.logger.info("Current cluster: %s", self.cluster)

    def __del__(self) -> None:
        """Destructor."""
        self.k8s_client.api_client.close()

    def get_contexts_list(self) -> tuple:
        """
        Get a list of Kubernetes contexts.

        :return: tuple with active host, active context, active cluster and list of contexts
        """
        active_host: str = configuration.Configuration().host
        ctx_list: list = []
        self.logger.info("Active host : %s", active_host)
        contexts, active_context = config.list_kube_config_contexts()
        if not contexts:
            self.logger.error("Could find any context in kube-config file.")
        for context in contexts:
            self.logger.info("Context : %s", context)
            ctx_list.append(context["name"])
        self.logger.info("Active context : %s", active_context)
        active_cluster: str = active_context["context"]["cluster"]
        self.logger.info("Active cluster : %s", active_cluster)
        active_ctx: str = active_context["name"]
        return active_host, active_ctx, active_cluster, ctx_list

    def get_contexts_dict(self) -> dict:
        """
        Get a dictionary of Kubernetes contexts.

        :return: dictionary of contexts
        """
        ctx_dict: dict = {}
        active_host: str = configuration.Configuration().host
        self.logger.info("Active host : %s", active_host)
        ctx_dict["active_host"] = active_host
        contexts, active_context = config.list_kube_config_contexts()
        if not contexts:
            self.logger.error("Could find any context in kube-config file.")
        self.logger.info("Active conext : %s", active_context)
        ctx_dict["active_context"] = active_context["name"]
        ctx_dict["active_cluster"] = active_context["context"]["cluster"]
        ctx_dict["contexts"] = []
        for context in contexts:
            self.logger.info("Context : %s", context)
            ctx_dict["contexts"].append(
                {
                    "name": context["name"],
                    "cluster": context["context"]["cluster"],
                    "user": context["context"]["user"],
                }
            )
        self.logger.info("Context : %s", ctx_dict)
        return ctx_dict

    def get_services_data(self, kube_namespace: str | None) -> Any:
        """
        Read K8S services.

        :param kube_namespace: K8S namespace
        :returns: list of services
        """
        services_list = self.k8s_client.list_namespaced_service(namespace=kube_namespace)
        self.logger.debug("Services data:\n%s", services_list)
        return services_list

    def get_services_dict(self, kube_namespace: str | None) -> Any:
        """
        Read K8S services.

        :param kube_namespace: K8S namespace
        :returns: dictionary of services
        """
        service_list = self.get_services_data(kube_namespace)
        # services_str = str(self.get_services_data(kube_namespace))
        svc: dict = {}
        svc["api_version"] = service_list.api_version
        svc["items"] = []
        self.logger.debug("Kubernetes services:\n%s", service_list)
        if not service_list.items:
            self.logger.error("No services found in namespace %s", kube_namespace)
            return
        for service in service_list.items:
            service_item: dict = {}
            service_item["metadata"] = {}
            service_item["metadata"]["name"] = service.metadata.name
            service_item["spec"] = {}
            service_item["spec"]["type"] = service.spec.type
            service_item["spec"]["cluster_ip"] = service.spec.cluster_ip
            service_item["spec"]["ports"] = []
            if service.spec.ports:
                for port in service.spec.ports:
                    service_item["spec"]["ports"].append(
                        {"target_port": port.target_port, "protocol": port.protocol}
                    )
            svc["items"].append(service_item)
        return svc

    def get_namespaces_list(self, kube_namespace: str | None) -> tuple:
        """
        Get a list of Kubernetes namespaces.

        :param kube_namespace: K8S namespace regex
        :return: tuple with context, cluster and list of namespaces
        """
        ns_list: list = []
        try:
            namespaces: list = self.k8s_client.list_namespace(_request_timeout=(1, 5))
        except client.exceptions.ApiException:
            self.logger.error("Could not read Kubernetes namespaces")
            return self.context, self.cluster, ns_list
        except TimeoutError:
            self.logger.error("Timemout error")
            return self.context, self.cluster, ns_list
        except urllib3.exceptions.ConnectTimeoutError:
            self.logger.error("Timemout while reading Kubernetes namespaces")
            return self.context, self.cluster, ns_list
        except urllib3.exceptions.MaxRetryError:
            self.logger.error("Max retries while reading Kubernetes namespaces")
            return self.context, self.cluster, ns_list
        if kube_namespace is not None:
            pat = re.compile(kube_namespace)
            for namespace in namespaces.items:  # type: ignore[attr-defined]
                ns_name = namespace.metadata.name
                if re.fullmatch(pat, ns_name):
                    self.logger.info("Found namespace: %s", ns_name)
                    ns_list.append(ns_name)
                else:
                    self.logger.debug("Skip namespace: %s", ns_name)
        else:
            for namespace in namespaces.items:  # type: ignore[attr-defined]
                ns_name = namespace.metadata.name
                self.logger.debug("Namespace: %s", ns_name)
                ns_list.append(ns_name)
        return self.context, self.cluster, ns_list

    def get_namespaces_dict(self) -> dict:
        """
        Get a list of Kubernetes namespaces.

        :return: dictionary of namespaces
        """
        ns_dict: dict = {
            "active_context": self.context,
            "active_cluster": self.cluster,
            "namespaces": [],
        }
        try:
            namespaces: list = self.k8s_client.list_namespace()  # type: ignore[union-attr]
        except client.exceptions.ApiException:
            self.logger.error("Could not read Kubernetes namespaces")
            return ns_dict
        for namespace in namespaces.items:  # type: ignore[attr-defined]
            self.logger.debug("Namespace: %s", namespace)
            ns_name = namespace.metadata.name
            item_dict = {}
            item_dict["namespace"] = ns_name
            item_dict["status"] = namespace.status.phase
            creation_dt = namespace.metadata.creation_timestamp
            item_dict["creation"] = creation_dt.strftime("%Y-%m-%d %H:%M:%S")
            item_dict["uid"] = namespace.metadata.uid
            item_dict["labels"] = namespace.metadata.labels
            item_dict["version"] = int(namespace.metadata.resource_version)
            ns_dict["namespaces"].append(item_dict)
        return ns_dict

    def exec_command(self, ns_name: str, pod_name: str, exec_command: list) -> str:
        """
        Execute command in pod.

        :param ns_name: namespace name
        :param pod_name: pod name
        :param exec_command: list making up command string
        :return: output
        """
        self.logger.debug(f"Run command : {' '.join(exec_command)}")
        resp = None
        try:
            resp = self.k8s_client.read_namespaced_pod(  # type: ignore[union-attr]
                name=pod_name, namespace=ns_name
            )
        except ApiException as e:
            if e.status != 404:
                print(f"Unknown error: {e}")
                exit(1)
        if not resp:
            self.logger.warning(f"Pod {pod_name} does not exist")
            return ""

        # Call exec and wait for response
        try:
            resp = stream(
                self.k8s_client.connect_get_namespaced_pod_exec,  # type: ignore[union-attr]
                pod_name,
                ns_name,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )
        except client.exceptions.ApiException as kerr:
            self.logger.info("Could not run command API %s : %s", exec_command, str(kerr))
            resp = f"ERROR {str(kerr)}"
        except Exception as kerr:
            self.logger.info("Could not run command %s : %s", exec_command, str(kerr))
            resp = f"ERROR {str(kerr)}"
        self.logger.debug("Response:\n%s", resp)
        return resp

    def get_pod(
        self, ipod: Any, ns_name: str | None, pod_name: str | None
    ) -> Tuple[str | None, str | None, str | None]:
        """
        Read pod information.

        :param ipod: pod handle
        :param ns_name: namespace name
        :param pod_name: pod name
        :return: pod name, IP address and namespace
        """
        i_ns_name = ipod.metadata.namespace
        if ns_name is not None:
            if i_ns_name != ns_name:
                return None, None, None
        i_pod_name = ipod.metadata.name
        if pod_name is not None:
            if i_pod_name != pod_name:
                return None, None, None
        i_pod_ip = ipod.status.pod_ip
        if i_pod_ip is None:
            i_pod_ip = "---"
        self.logger.debug("Found pod %s:\n%s", i_pod_name, ipod)
        return i_pod_name, i_pod_ip, i_ns_name

    def get_pods(self, ns_name: str | None, pod_name: str | None) -> dict:
        """
        Read pods information.

        :param ns_name: namespace name
        :param pod_name: pod name
        :return: dict with pod name, IP address and namespace
        """
        # Configs can be set in Configuration class directly or using helper utility
        # config.load_kube_config()
        #
        self.logger.info("Listing pods with their IPs for namespace %s", ns_name)
        ipods = {}
        if pod_name:
            self.logger.info("Read pod %s", pod_name)
        else:
            self.logger.info("Read pods")
        if ns_name:
            self.logger.info("Use namespace %s", ns_name)
        ret = self.k8s_client.list_pod_for_all_namespaces(watch=False)  # type: ignore[union-attr]
        for ipod in ret.items:
            self.logger.debug("Read pod : %s", json.dumps(ipod.to_dict(), default=str, indent=4))
            pod_nm, pod_ip, pod_ns = self.get_pod(ipod, ns_name, pod_name)
            if pod_nm is not None:
                ipods[pod_nm] = (pod_ip, pod_ns)
        self.logger.info("Found %d pods", len(ipods))
        return ipods

    def get_service(
        self, isvc: Any, ns_name: str | None, svc_name: str | None
    ) -> Tuple[Any, Any, Any, str | None, Any]:
        """
        Read service information.

        :param isvc: service handle
        :param ns_name: namespace name
        :param svc_name: service name
        :return: tuple with pod name, IP address and namespace
        """
        isvc_ns = isvc.metadata.namespace
        if ns_name is not None:
            if isvc_ns != ns_name:
                return None, None, None, None, None
        isvc_name = isvc.metadata.name
        if svc_name is not None:
            if svc_name != isvc_name:
                return None, None, None, None, None
        self.logger.debug("Service %s:\n%s", isvc_name, isvc)
        try:
            svc_ip = isvc.status.load_balancer.ingress[0].ip
            svc_port = str(isvc.spec.ports[0].port)
            svc_prot = isvc.spec.ports[0].protocol
        except TypeError:
            svc_ip = "---"
            svc_port = ""
            svc_prot = ""
        return isvc_name, isvc_ns, svc_ip, svc_port, svc_prot

    def get_service_desc(self, ns_name: str | None, svc_name: str | None) -> Any:
        """
        Read service information.

        :param ns_name: namespace name
        :param svc_name: service name
        :return: API response
        """
        api_response: Any
        try:
            api_response = self.k8s_client.read_namespaced_service(
                name=svc_name, namespace=ns_name, pretty=True
            )
            self.logger.info("Desc %s: %s", type(api_response), api_response)
        except ApiException as e:
            api_response = None
            self.logger.error("Could not read service describe: %s", e)
        return api_response

    def get_service_status(self, ns_name: str | None, svc_name: str | None) -> Any:
        """
        Read service information.

        :param ns_name: namespace name
        :param svc_name: service name
        :return: API response
        """
        api_response: Any
        try:
            api_response = self.k8s_client.read_namespaced_service_status(
                name=svc_name, namespace=ns_name, pretty=True
            )
            self.logger.info("Desc %s: %s", type(api_response), api_response)
        except ApiException as e:
            api_response = None
            self.logger.error("Could not read service status: %s", e)
        return api_response

    def get_services(self, ns_name: str | None, svc_name: str | None) -> dict:
        """
        Get information on kubernetes services.

        :param ns_name: namespace
        :param svc_name: service name
        :return: dict with pod name, IP address and namespace
        """
        svcs = {}
        if svc_name:
            self.logger.info("Read service %s", svc_name)
        else:
            self.logger.info("Read services")
        if ns_name:
            self.logger.info("Use namespace %s", ns_name)
        services = self.k8s_client.list_service_for_all_namespaces(  # type: ignore[union-attr]
            watch=False
        )
        for isvc in services.items:
            svc_nm, svc_ns, svc_ip, svc_port, svc_prot = self.get_service(isvc, ns_name, svc_name)
            if svc_nm is not None:
                svcs[svc_nm] = (svc_ns, svc_ip, svc_port, svc_prot)
        self.logger.info("Found %d services", len(svcs))
        return svcs

    def get_service_addr(
        self, isvc: Any, ns_name: str | None, svc_name: str | None
    ) -> Tuple[str | None, str | None, str | None, str | None, str | None]:
        """
        Get IP address for K8S service.

        :param isvc: K8S service handle
        :param ns_name: namespace
        :param svc_name: service name
        :return: tuple with service name, namespace, IP address, port, protocol
        """
        isvc_ns = isvc.metadata.namespace
        if ns_name is not None:
            if isvc_ns != ns_name:
                return None, None, None, None, None
        isvc_name = isvc.metadata.name
        if svc_name is not None:
            if svc_name != isvc_name:
                return None, None, None, None, None
        self.logger.debug("Service %s:\n%s", isvc_name, isvc)
        try:
            svc_ip = isvc.status.load_balancer.ingress[0].ip
            svc_port = str(isvc.spec.ports[0].port)
            svc_prot = isvc.spec.ports[0].protocol
        except TypeError:
            svc_ip = "---"
            svc_port = ""
            svc_prot = ""
        return isvc_name, isvc_ns, svc_ip, svc_port, svc_prot

    def get_pod_log(self, ns_name: str | None, pod_name: str) -> Any:
        """
        Read pod log file.

        :param ns_name: namespace
        :param pod_name: pod name
        :return: log string
        """
        self.logger.info("Read pod log for %s", pod_name)
        api_response: Any
        try:
            api_response = self.k8s_client.read_namespaced_pod_log(
                name=pod_name, namespace=ns_name
            )
            self.logger.debug("Log: %s", api_response)
        except ApiException as e:
            api_response = None
            self.logger.warning("Could not read pod log: %s", e)
        return api_response

    def get_pod_desc(self, ns_name: str | None, pod_name: str) -> Any:
        """
        Describe pod.

        :param ns_name: namespace
        :param pod_name: pod name
        :return: API response
        """
        self.logger.debug("Describe pod %s in namespace %s", pod_name, ns_name)
        api_response: Any
        try:
            api_response = self.k8s_client.read_namespaced_pod(
                name=pod_name, namespace=ns_name, pretty=True, _preload_content=True
            )
        except ApiException as e:
            api_response = None
            self.logger.warning("Could not read pod %s description: %s", pod_name, e)
        return api_response
