"""Read and display Kubernetes and Tango stuff."""

__all__ = [
    "TangoControl",
]

from ska_tangoctl.tango_kontrol.tango_kontrol import (
    TangoControl,
)
from ska_tangoctl.tango_kontrol.tangoktl_config import read_tangoktl_config
