"""Display tree of servers."""

import collections
import fnmatch
import functools
from typing import Any

from ska_tangoctl.tango_control.tango_database import (
    _server_host_str,
    _server_str,
    get_db,
    get_db_info,
)


def _device_class_str(dev: Any) -> str:
    """
    Get string for device class.

    :param dev: Tango device
    :return: information string
    """
    klass = dev if isinstance(dev, str) else dev.klass
    return klass


def _device_str(dev: Any) -> str:
    """
    Get string for device.

    :param dev: Tango device
    :return: information string
    """
    dev = dev if isinstance(dev, str) else dev.name
    return dev


def _alias_str(dev: Any) -> str:
    """
    Get string for device alias.

    :param dev: Tango device
    :return: information string
    """
    dev = dev if isinstance(dev, str) else dev.alias
    dev = "---" if dev is None else dev
    return dev


def _device_exported_str(dev: Any) -> str:
    """
    Get string for device export status.

    :param dev: Tango device
    :return: information string
    """
    text = "Exported" if dev.exported else "Not. Exp."
    return text


def fnmatch_any(name: str, patterns: Any, case_insensitive: bool = False) -> Any:
    """
    Check if name matches any of those in the list of patterns.

    :param name: input
    :param patterns: match this
    :param case_insensitive: uppercase or lowercase
    :return: matches
    """
    if not patterns:
        return True
    if isinstance(patterns, str):
        patterns = (patterns,)
    if case_insensitive:
        name = name.lower()
        patterns = [p.lower() for p in patterns]
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def iter_devices(
    device: Any = None,
    server: Any = None,
    klass: Any = None,
    host: Any = None,
    include_dserver: bool = True,
    reverse: bool = False,
    db: Any = None,
) -> Any:
    """
    Iterate over devices.

    :param device: device name
    :param server: server name
    :param klass: device class
    :param host: hostname
    :param include_dserver: include devices that start with 'dserver' or 'sys'
    :param db: database handle
    :return: list of devices
    """
    db = get_db(db)
    db_info = get_db_info(db=db)

    devs, servers = db_info.devices, db_info.servers
    devices = (devs[dname] for dname in sorted(devs, reverse=reverse))
    if not include_dserver:
        # devices = (d for d in devices if d.klass != "DServer")
        devices = (
            d for d in devices if d.name[0:3].lower() != "sys" and d.name[0:7].lower() != "dserver"
        )
    devices = (
        d
        for d in devices
        if fnmatch_any(d.name, device, case_insensitive=True)
        or (d.alias and fnmatch_any(d.alias, device, case_insensitive=True))
    )
    devices = (d for d in devices if fnmatch_any(d.klass, klass))
    devices = (d for d in devices if fnmatch_any(d.server, server))
    devices = (d for d in devices if fnmatch_any(servers[d.server], host, case_insensitive=True))
    return devices


def device_tree(
    device: Any = None,
    server: Any = None,
    klass: Any = None,
    host: Any = None,
    include_dserver: Any = True,
    reverse: bool = False,
    verbose: Any = False,
) -> None:
    """
    Show a tree of devices.

    :param device: device name
    :param server: server name
    :param klass: device class
    :param host: hostname
    :param include_dserver: include devices that start with 'dserver' or 'sys'
    :param verbose: detailed output
    """
    verbose_template = "{:30} {:30} {:35} {:40} {:40} {}"
    db = None
    db_info = get_db_info(db=db)

    import treelib  # type: ignore[import-untyped]

    tree = treelib.Tree()
    db_node = tree.create_node(db_info.name)
    all_servers = db_info.servers
    devices = iter_devices(
        device=device,
        klass=klass,
        server=server,
        host=host,
        include_dserver=include_dserver,
        reverse=reverse,
        db=db,
    )
    domains: Any = collections.defaultdict(functools.partial(collections.defaultdict, dict))
    for dev in devices:
        d, f, m = dev.name.split("/")
        domains[d.lower()][f.lower()][m.lower()] = dev
    for domain in sorted(domains, reverse=reverse):
        d_node = tree.create_node(_device_str(domain), parent=db_node)
        families = domains[domain]
        for family in sorted(families, reverse=reverse):
            f_node = tree.create_node(_device_str(family), parent=d_node)
            members = families[family]
            for member in sorted(members, reverse=reverse):
                if verbose:
                    dev = members[member]
                    srv = all_servers[dev.server]
                    text = verbose_template.format(
                        _device_str(member),
                        _alias_str(dev),
                        _device_class_str(dev),
                        _server_str(srv),
                        _server_host_str(srv),
                        _device_exported_str(dev),
                    )
                else:
                    text = member
                tree.create_node(text, parent=f_node)
    print(str(tree))
