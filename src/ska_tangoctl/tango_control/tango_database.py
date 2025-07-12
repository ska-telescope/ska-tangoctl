"""Set up Tango databse connection."""

import collections
import functools
import logging
import os
import socket
import time
from typing import Any, List

import tango
import tango.gevent

Device = functools.lru_cache(maxsize=1024)(tango.gevent.DeviceProxy)
DeviceInfo = collections.namedtuple("DeviceInfo", ("name", "server", "klass", "alias", "exported"))
DatabaseInfo = collections.namedtuple(
    "DatabaseInfo", ("name", "host", "port", "servers", "devices", "aliases")
)
ServerInfo = collections.namedtuple("ServerInfo", ("name", "type", "instance", "host", "devices"))


class TangoHostInfo:
    """Read address of Tango database host."""

    logger: logging.Logger

    def __init__(
        self,
        logger: logging.Logger,
        tango_host: str | None,
        tango_fqdn: str,
        tango_port: int,
        ns_name: str | None,
        use_fqdn: bool,
    ):
        """
        Do the thing.

        :param logger: logging handle
        :param tango_host: Tango database host and port
        :param tango_fqdn: Tango database host in FQDN format
        :param tango_port: Tango database port
        :param ns_name: K8S namespace
        :param use_fqdn: use FQDN for host name (otherwise IP address)
        """
        self.logger = logger
        self.tango_fqdn: str
        self.tango_port: int
        self.tango_ip: str | None
        self.tango_host: str | None
        self.ns_name: str | None

        if tango_host is not None:
            self.tango_fqdn = tango_host.split(":")[0]
            self.tango_port = int(tango_host.split(":")[1])
            self.tango_host = tango_host
        else:
            self.tango_fqdn = tango_fqdn
            self.tango_port = tango_port
            # Read the true host name, a list of aliases, and a list of IP addresses, for a host
            try:
                tango_addr = socket.gethostbyname_ex(tango_fqdn)
                self.tango_ip = tango_addr[2][0]
                if use_fqdn:
                    self.tango_host = f"{self.tango_fqdn}:{tango_port}"
                else:
                    self.tango_host = f"{self.tango_ip}:{tango_port}"
            except socket.gaierror:  # as e:
                self.tango_ip = None
                self.tango_host = None
        self.ns_name = ns_name

    def __repr__(self) -> str:
        """
        Print the thing.

        :return: the thing to be printed
        """
        return str(self.tango_host)

    def check_tango(self) -> tuple[str, list[str], list[str]]:
        """
        Check Tango host address.

        :return: error condition
        """
        tango_addr: tuple[str, list[str], list[str]]
        self.logger.info("Check Tango host %s:%d", self.tango_fqdn, self.tango_port)
        try:
            tango_addr = socket.gethostbyname_ex(self.tango_fqdn)
        except socket.gaierror as e:
            self.logger.error("Could not read address %s : %s" % (self.tango_fqdn, e))
            return ("", [], [])
        return tango_addr


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


def get_db_name(db: Any) -> str:
    """
    Get database name.

    :param db: database handle
    :return: database name
    """
    return "{}:{}".format(db.get_db_host(), db.get_db_port())


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
    all_servers: dict
    all_devices: dict
    aliases: dict

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


def timed_lru_cache(seconds: int, maxsize: int = 128) -> Any:
    """
    Implement timed LRU cache.

    :param seconds: number of seconds
    :param maxsize: maximum size
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


def get_tango_hosts(  # noqa: C901
    logger: logging.Logger,
    tango_host: str | None,
    kube_namespace: str | None,
    databaseds_name: str | None,
    cluster_domain: str | None,
    databaseds_port: int,
    use_fqdn: bool,
    namespaces_list: list,
) -> list:
    """
    Compile a list of Tango hosts.

    :param logger: logging handle
    :param tango_host: Tango host
    :param kube_namespace: K8S namespace
    :param databaseds_name: Tango host prefix
    :param cluster_domain: Tango host domain name
    :param databaseds_port: Tango host port number
    :param use_fqdn: use IP address instead of FQDN
    :param namespaces_list: namespaces
    :return: list of hosts
    """
    tango_fqdn: str
    thost: TangoHostInfo
    tango_hosts: List[TangoHostInfo] = []
    logger.info("Get hosts for namespace %s or host %s", kube_namespace, tango_host)

    if namespaces_list:
        logger.debug("Read namespaces %s", namespaces_list)
        for kube_namespace in namespaces_list:
            tango_fqdn = f"{databaseds_name}.{kube_namespace}.{cluster_domain}"
            thost = TangoHostInfo(
                logger, None, tango_fqdn, databaseds_port, kube_namespace, use_fqdn
            )
            if thost.tango_host is not None:
                logger.info("Add host for namespace %s : %s", kube_namespace, thost)
                tango_hosts.append(thost)
            else:
                logger.error("Could not reach Tango host %s", tango_fqdn)
    elif tango_host is not None:
        logger.debug("Use Tango host %s", tango_host)
        thost = TangoHostInfo(logger, tango_host, "", 0, None, use_fqdn)
        logger.info("Set host to %s", thost)
        tango_hosts.append(thost)
    elif kube_namespace is None:
        kube_namespace = os.getenv("KUBE_NAMESPACE")
        if kube_namespace is None:
            logger.warning(
                "No Kubernetes namespace or Tango database server specified,"
                " TANGO_HOST and KUBE_NAMESPACE not set"
            )
            return tango_hosts
        logger.debug("Use namespace %s from environment", kube_namespace)
        tango_fqdn = f"{databaseds_name}.{kube_namespace}.{cluster_domain}"
        thost = TangoHostInfo(logger, None, tango_fqdn, databaseds_port, kube_namespace, use_fqdn)
        if thost.tango_host is not None:
            logger.info("Set host for namespace %s to %s", kube_namespace, thost)
            tango_hosts.append(thost)
        else:
            logger.error("Could not reach Tango host %s", thost)
    elif "," in kube_namespace:
        kube_namespaces: list[str] = kube_namespace.split(",")
        logger.debug("Use namespaces %s", kube_namespaces)
        for kube_namespace in kube_namespaces:
            tango_fqdn = f"{databaseds_name}.{kube_namespace}.{cluster_domain}"
            thost = TangoHostInfo(
                logger, None, tango_fqdn, databaseds_port, kube_namespace, use_fqdn
            )
            if thost.tango_host is not None:
                logger.info("List host for namespace %s : %s", kube_namespace, thost)
                tango_hosts.append(thost)
            else:
                logger.info("No host for namespace %s", kube_namespace)
    elif kube_namespace is not None:
        logger.debug("Use namespace %s", kube_namespace)
        tango_fqdn = f"{databaseds_name}.{kube_namespace}.{cluster_domain}"
        thost = TangoHostInfo(logger, None, tango_fqdn, databaseds_port, kube_namespace, use_fqdn)
        if thost.tango_host is not None:
            logger.info("Set host for namespace %s to %s", kube_namespace, thost)
            tango_hosts.append(thost)
        else:
            logger.info("No host for namespace %s", kube_namespace)
    else:
        logger.warning("Not enough info supplied")
    return tango_hosts
