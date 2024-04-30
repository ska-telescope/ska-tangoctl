"""Display tree of servers."""

import collections
import fnmatch
import functools
import time
from typing import Any

import tango
import tango.gevent

Device = functools.lru_cache(maxsize=1024)(tango.gevent.DeviceProxy)
ServerInfo = collections.namedtuple("ServerInfo", ("name", "type", "instance", "host", "devices"))
DeviceInfo = collections.namedtuple("DeviceInfo", ("name", "server", "klass", "alias", "exported"))
DatabaseInfo = collections.namedtuple(
    "DatabaseInfo", ("name", "host", "port", "servers", "devices", "aliases")
)


def _server_str(server: Any) -> str:
    """
    Get string for server.

    :param server: Tango device server
    :return: information string
    """
    server = server if isinstance(server, str) else server.name
    return server


def _server_host_str(server: Any) -> str:
    """
    Get string for server host.

    :param server: Tango device server
    :return: information string
    """
    host = server if isinstance(server, str) else server.host
    host = "---" if host == "nada" else host
    return host


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


def get_db_name(db: Any) -> str:
    """
    Get database name.

    :param db: database handle
    :return: database name
    """
    return "{}:{}".format(db.get_db_host(), db.get_db_port())


def _get_server_devices(server_id: Any, db: Any = None) -> Any:
    """
    Get database name.

    :param server_id: database server ID
    :param db: database handle
    :return: database device list
    """
    db = get_db(db)
    class_list = db.get_device_class_list(server_id)
    return {
        name: DeviceInfo(name, server_id, klass, alias=None, exported=None)
        for name, klass in zip(class_list[::2], class_list[1::2])
    }


def _build_db_standard(db: Any = None) -> DatabaseInfo:
    """
    Build database string.

    :param db: database handle
    :return: database information
    """
    db = get_db(db)
    all_servers, all_devices = {}, {}
    for server_id in db.get_server_list():
        server_type, server_instance = server_id.split("/", 1)
        devices = _get_server_devices(server_id, db=db)
        all_devices.update(devices)
        device_names = list(devices)
        server = ServerInfo(server_id, server_type, server_instance, None, device_names)
        all_servers[server_id] = server
    host, port = db.get_db_host(), db.get_db_port_num()
    name = "{}:{}".format(host, port)
    return DatabaseInfo(
        servers=all_servers,
        devices=all_devices,
        host=host,
        port=port,
        aliases={},
        name=name,
    )


def _build_db_quick(db_dev: Any) -> DatabaseInfo:
    """
    Build database string.

    :param db_dev: database device
    :return: database information
    """
    all_servers: dict = {}
    all_devices: dict = {}
    query = "SELECT name, alias, exported, host, server, class FROM device"
    r = db_dev.DbMySqlSelect(query)
    row_nb, column_nb = r[0][-2:]
    data = r[1]
    assert row_nb == len(data) // column_nb
    all_servers, all_devices, aliases = {}, {}, {}
    for row in range(row_nb):
        idx = row * column_nb
        cells = data[idx : idx + column_nb]
        dev_name, dev_alias, exported, host, server_id, klass = cells
        # handle garbage:
        if not server_id or server_id.count("/") != 1:
            continue
        if not dev_name or dev_name.count("/") != 2:
            continue
        if not dev_alias:
            dev_alias = None
        else:
            aliases[dev_alias] = dev_name
        device = DeviceInfo(dev_name, server_id, klass, dev_alias, bool(int(exported)))
        server = all_servers.get(server_id)
        if server is None:
            server_type, server_instance = server_id.split("/", 1)
            server = ServerInfo(server_id, server_type, server_instance, host, [])
            all_servers[server_id] = server
        server.devices.append(dev_name)
        all_devices[dev_name.lower()] = device
    db = db_dev.get_device_db()
    host, port = db.get_db_host(), db.get_db_port_num()
    name = "{}:{}".format(host, port)
    return DatabaseInfo(
        servers=all_servers,
        devices=all_devices,
        aliases=aliases,
        host=host,
        port=port,
        name=name,
    )


def _build_db(db: Any = None) -> DatabaseInfo:
    """
    Build database string.

    :param db: database handle
    :return: database string
    """
    db = get_db(db)
    db_dev_name = "{}/{}".format(get_db_name(db), db.dev_name())
    db_dev = Device(db_dev_name)
    if hasattr(db_dev, "DbMySqlSelect"):
        return _build_db_quick(db_dev)
    else:
        return _build_db_standard(db=db)


def timed_lru_cache(seconds: int, maxsize: int = 128, typed: bool = False) -> Any:
    """
    Implement timed LRU cache.

    :param seconds: number of seconds
    :param maxsize: maximum size
    :param typed: check type
    :return: magic thing
    """

    def _wrapper(func: Any) -> Any:
        func = functools.lru_cache(maxsize=maxsize, typed=False)(func)
        func._created = time.monotonic()
        func._expired = lambda: time.monotonic() >= (func._created + seconds)

        @functools.wraps(func)
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            if func._expired():
                func.cache_clear()
                func._created = time.monotonic()
            return func(*args, **kwargs)

        _wrapped.cache_info = func.cache_info  # type: ignore[attr-defined]
        _wrapped.cache_clear = func.cache_clear  # type: ignore[attr-defined]
        return _wrapped

    return _wrapper


def Database(db_name: Any = None) -> Any:
    """
    Get database handle.

    :param db_name: database name
    :return: database handle
    """
    if db_name is None:
        db = tango.Database()
    else:
        if ":" in db_name:
            host, port = db_name.rsplit(":", 10000)
            port = int(port)
        else:
            host, port = db_name, 10000
        db = tango.Database(host, port)

    def build_database() -> Any:
        """
        Build database thing.

        :return: the thing
        """
        return _build_db(db)

    db.get_db_info = timed_lru_cache(10)(build_database)
    return db


def get_db(db: Any = None) -> Any:
    """
    Get database handle.

    :param db: database handle
    :return: database handle
    """
    if db is None or isinstance(db, str):
        return Database(db)
    return db


def get_db_info(db: Any = None) -> Any:
    """
    Get database information.

    :param db: database handle
    :return: information string
    """
    return get_db(db).get_db_info()


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
    exclude_dserver: bool = True,
    db: Any = None,
) -> Any:
    """
    Iterate over devices.

    :param device: device name
    :param server: server name
    :param klass: device class
    :param host: hostname
    :param exclude_dserver: exclude device that start with 'dserver'
    :param db: database handle
    :return: list of devices
    """
    db = get_db(db)
    db_info = get_db_info(db=db)

    devs, servers = db_info.devices, db_info.servers
    devices = (devs[dname] for dname in sorted(devs))
    if exclude_dserver:
        devices = (d for d in devices if d.klass != "DServer")
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
    exclude_dserver: Any = True,
    verbose: Any = False,
) -> None:
    """
    Show a tree of devices.

    :param device: device name
    :param server: server name
    :param klass: device class
    :param host: hostname
    :param exclude_dserver: exclude device that start with 'dserver'
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
        exclude_dserver=exclude_dserver,
        db=db,
    )
    domains: Any = collections.defaultdict(functools.partial(collections.defaultdict, dict))
    for dev in devices:
        d, f, m = dev.name.split("/")
        domains[d.lower()][f.lower()][m.lower()] = dev
    for domain in sorted(domains):
        d_node = tree.create_node(_device_str(domain), parent=db_node)
        families = domains[domain]
        for family in sorted(families):
            f_node = tree.create_node(_device_str(family), parent=d_node)
            members = families[family]
            for member in sorted(members):
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
