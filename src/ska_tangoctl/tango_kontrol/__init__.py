"""Read and display Kubernetes and Tango stuff."""

__all__ = [
    "TangoControlKubernetes",
    "read_tangoktl_config",
    "get_namespaces_dict",
    "get_namespaces_list",
    "show_namespaces",
]

from ska_tangoctl.tango_kontrol.tango_kontrol import (
    TangoControlKubernetes,
    get_namespaces_dict,
    get_namespaces_list,
    show_namespaces,
)
from ska_tangoctl.tango_kontrol.tangoktl_config import read_tangoktl_config
