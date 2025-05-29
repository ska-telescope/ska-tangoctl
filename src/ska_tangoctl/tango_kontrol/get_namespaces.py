"""Read Kubernetes namespaces."""

import logging
import re
import urllib3  # type: ignore[import]
from kubernetes import client, config  # type: ignore[import]


def get_namespaces_list(logger: logging.Logger, kube_namespace: str | None) -> list:
    """
    Get a list of Kubernetes namespaces.

    :param kube_namespace: K8S namespace regex
    :return: list of namespaces
    """
    ns_list: list = []
    k8s_client = client.CoreV1Api()
    try:
        namespaces: list = k8s_client.list_namespace(_request_timeout=(1, 5))
    except client.exceptions.ApiException:
        logger.error("Could not read Kubernetes namespaces")
        return ns_list
    except TimeoutError:
        logger.error("Timemout error")
        return ns_list
    except urllib3.exceptions.ConnectTimeoutError:
        logger.error("Timemout while reading Kubernetes namespaces")
        return ns_list
    except urllib3.exceptions.MaxRetryError:
        logger.error("Max retries while reading Kubernetes namespaces")
        return ns_list
    if kube_namespace is not None:
        pat = re.compile(kube_namespace)
        for namespace in namespaces.items:  # type: ignore[attr-defined]
            ns_name = namespace.metadata.name
            if re.fullmatch(pat, ns_name):
                logger.info("Found namespace: %s", ns_name)
                ns_list.append(ns_name)
            else:
                logger.debug("Skip namespace: %s", ns_name)
    else:
        for namespace in namespaces.items:  # type: ignore[attr-defined]
            ns_name = namespace.metadata.name
            logger.debug("Namespace: %s", ns_name)
            ns_list.append(ns_name)
    return ns_list
