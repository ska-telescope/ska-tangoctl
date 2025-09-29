"""Print Tango configuration in text format."""

import json
import logging
from typing import Any

# TODO use(d) for debugging
# DELIMS: dict = {
#     "all": " ",
#     "dict_list": "!",
#     "dict_dict": "#",
#     "dict_para": "@",
#     "dict_csv": ";",
#     "dict_int": "*",
#     "dict_float": "%",
#     "dict_str": "$",
#     "list": "|",
#     "str": "+",
# }
DELIMS: dict = {
    "all": " ",
    "dict_list": " ",
    "dict_dict": " ",
    "dict_para": " ",
    "dict_csv": " ",
    "dict_int": " ",
    "dict_float": " ",
    "dict_str": " ",
    "list": " ",
    "str": " ",
}


class TangoJsonReaderTextMixin:
    """Read JSON and print as markdown."""

    outf: Any
    logger: logging.Logger
    tgo_space: str
    devices_dict: dict
    quiet_mode: bool

    def print_txt_small(self) -> None:  # noqa: C901
        """Print text in short form."""

        def print_attributes() -> None:
            i: int
            attrib: Any
            attrib_item: str
            if "attributes" not in devdict:
                self.logger.info("No attributes")
                return

            """Print attribute in short form."""
            print(f"{'attributes':20}", end="", file=self.outf)
            i = 0
            for attrib in devdict["attributes"]:  # type: ignore[call-overload]
                attrib_item = attrib["name"]  # type: ignore[index]
                if not i:
                    print(f" {attrib_item:40}", end="", file=self.outf)
                else:
                    print(
                        f"{' ':20} {attrib_item:40}",
                        end="",
                        file=self.outf,
                    )
                i += 1
                try:
                    print(f"{attrib['data']['value']}", file=self.outf)  # type: ignore[index]
                except KeyError as oerr:
                    self.logger.debug("Could not read attribute %s : %s", attrib, oerr)
                    print("N/A", file=self.outf)

        def print_commands() -> None:
            """Print commands with values."""
            i: int
            cmd: Any
            cmd_item: str
            if "commands" not in devdict:
                self.logger.info("No commands")
                return

            self.logger.debug(
                "Print commands : %s", devdict["commands"]  # type: ignore[call-overload]
            )
            print(f"{'commands':20}", end="", file=self.outf)
            if not devdict["commands"]:  # type: ignore[call-overload]
                print("N/R", file=self.outf)
                return
            i = 0
            for cmd in devdict["commands"]:  # type: ignore[call-overload]
                if "value" in devdict["commands"][cmd]:  # type: ignore[call-overload]
                    if not i:
                        print(f" {cmd:40}", end="", file=self.outf)
                    else:
                        print(f"{' ':20} {cmd:40}", end="", file=self.outf)
                    i += 1
                    cmd_item = devdict["commands"][cmd]["value"]  # type: ignore[call-overload]
                    print(f"{cmd_item}", file=self.outf)
            if not i:
                print("N/R", file=self.outf)

        def print_properties() -> None:
            ti: int
            prop_name: str
            prop_vals: Any
            if "properties" not in devdict:
                self.logger.info("No properties")
                return

            self.logger.debug(
                "Print %d properties", len(devdict["properties"])  # type: ignore[call-overload]
            )
            if not devdict["properties"]:  # type: ignore[call-overload]
                return
            print(f"{'properties':20} ", end="", file=self.outf)
            if not devdict["properties"]:  # type: ignore[call-overload]
                print(file=self.outf)
                return
            ti = 0
            for prop_name in devdict["properties"]:  # type: ignore[call-overload]
                if not ti:
                    print(f"{prop_name:40}", end="", file=self.outf)
                else:
                    print(f"{' ':20} {prop_name:40}", end="", file=self.outf)
                ti += 1
                prop_vals = devdict["properties"][prop_name][  # type: ignore[call-overload]
                    "value"
                ]
                if not prop_vals:
                    print(file=self.outf)
                    continue
                elif type(prop_vals) is list:
                    print(f"{prop_vals[0]}", file=self.outf)
                    for prop_val in prop_vals[1:]:
                        print(f"{' ':60} {prop_val}", file=self.outf)

        devdict: list

        dev_item: str
        self.logger.debug("Print devices %s", self.devices_dict)
        for devdict in self.devices_dict["devices"]:
            self.logger.debug("Print device %s", devdict)
            print(f"{'name':20} {devdict['name']}", file=self.outf)  # type: ignore[call-overload]
            if "version" in devdict:
                dev_item = devdict["version"]  # type: ignore[call-overload]
            else:
                dev_item = "---"
            print(f"{'version':20} {dev_item}", file=self.outf)
            if "versioninfo" in devdict:
                dev_item = devdict["versioninfo"][0]  # type: ignore[call-overload]
                print(f"{'versioninfo':20} {dev_item}", file=self.outf)
            else:
                print(f"{'versioninfo':20} ---", file=self.outf)
            print_attributes()
            print_commands()
            print_properties()
            print(file=self.outf)

    def print_txt_medium(self) -> None:  # noqa: C901
        """Print the thing in medium size."""

        delim_t: str = DELIMS["all"]

        def print_text_stuff(stuff: str) -> None:
            """
            Print attribute, command or property.

            :param stuff: name of the thing
            """

            def print_dict_list(l_tj: int) -> None:
                """
                Print list in dict.

                :param l_tj: item number
                """
                delim: str = DELIMS["dict_list"]
                self.logger.debug(
                    "Print list %d in dict %s : %s (%d)",
                    tj,
                    devkey2,
                    devkeyval2,
                    len(devkeyval2),
                )
                print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                if len(devkeyval2) == 0:
                    print("[]", file=self.outf)
                elif len(devkeyval2) == 1:
                    if type(devkeyval2[0]) is not str:
                        # TODO fix this
                        # if l_tj:
                        #     print(f"{' ':143}{delim}", file=self.outf, end="")
                        print(f"{str(devkeyval2[0])}", file=self.outf)
                    elif "," in devkeyval2[0]:
                        l_keyvals = devkeyval2[0].split(",")
                        l_keyval = l_keyvals[0]
                        print(f"{l_keyval}", file=self.outf)
                        for l_keyval in l_keyvals[1:]:
                            print(f"{' ':102}{delim}{l_keyval}", file=self.outf)
                    else:
                        if l_tj:
                            print(f"{' ':102}{delim}", file=self.outf, end="")
                        print(f"{devkeyval2[0]}", file=self.outf)
                else:
                    n = 0
                    for l_keyval in devkeyval2:
                        if n:
                            print(f"{' ':102}{delim}", file=self.outf, end="")
                        print(f"{l_keyval}", file=self.outf)
                        n += 1

            def print_dict_dict(d_tj: int) -> None:
                """
                Print dict in dict.

                :param d_tj: item number
                """
                delim: str = DELIMS["dict_dict"]
                self.logger.debug(
                    "Print %d/%d dict in dict %s : %s", d_tj, pi, devkey2, devkeyval2
                )
                print(f"{' ':102}{delim}{devkey2:40}", file=self.outf)
                n = 0
                for d_keyval in devkeyval2:
                    if type(devkeyval2[d_keyval]) is dict:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "Print %d/%d dict in dict in dict %s : %s",
                            n,
                            dd_len,
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}", end="", file=self.outf)
                        m = 0
                        for item2 in devkeyval2[d_keyval]:
                            if m:
                                print(f"{' ':143}{delim}{' ':40}{delim}", end="", file=self.outf)
                            print(
                                f"{' ':143}{delim}{' ':40} {item2} {devkeyval2[d_keyval][item2]}",
                                end="",
                                file=self.outf,
                            )
                            m += 1
                    elif type(devkeyval2[d_keyval]) is list:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "Print %d/%d list in dict in dict %s : %s",
                            n,
                            dd_len,
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if dd_len == 0:
                            print(f"{' ':102}{delim}{d_keyval:40}{delim}[]", file=self.outf)
                        elif dd_len == 1:
                            print(
                                f"{' ':102}{delim}{d_keyval:40}{delim}{devkeyval2[d_keyval][0]}",
                                file=self.outf,
                            )
                        else:
                            print(
                                f"{' ':102}{delim}{d_keyval:40}{delim}{devkeyval2[d_keyval][0]}",
                                file=self.outf,
                            )
                            m = 0
                            for d_item in devkeyval2[d_keyval][1:]:
                                print(f"{' ':143}{delim}", end="", file=self.outf)
                                if type(d_item) is dict:
                                    k = 0
                                    for key2 in d_item:
                                        if k:
                                            print(
                                                f"{' ':143}{delim}",
                                                end="",
                                                file=self.outf,
                                            )
                                        print(
                                            f" {key2:32}{delim}{d_item[key2]}",
                                            file=self.outf,
                                        )
                                        k += 1
                                else:
                                    print(f"{delim}{d_item}", file=self.outf)
                                m += 1
                    elif type(devkeyval2[d_keyval]) is not str:
                        self.logger.debug(
                            "Print %d %s in dict in dict %s : %s",
                            n,
                            type(devkeyval2[d_keyval]),
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not n:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        else:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}", end="", file=self.outf)
                        print(f"{devkeyval2[d_keyval]}", file=self.outf)
                    else:
                        self.logger.debug(
                            "Print %d/%d string in dict in dict %s : %s",
                            n,
                            len(devkeyval2[d_keyval]),
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not n:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        else:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}{devkeyval2[d_keyval]}", file=self.outf)
                    n += 1

            def print_dict_para(p_tj: int) -> None:
                """
                Print paragraph in dict.

                :param p_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("Print %d paragraph in dict : %s", p_tj, devkeyval2)
                if not p_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102} {devkey2:40}{delim}", file=self.outf, end="")
                p_keyvals = devkeyval2.split("\n")
                # Remove empty lines
                p_keyvals2 = []
                for p_keyval in p_keyvals:
                    p_keyval2 = p_keyval.strip()
                    if p_keyval2:
                        if len(p_keyval2) > 70:
                            lsp = p_keyval2[0:70].rfind(" ")
                            p_keyvals2.append(p_keyval2[0:lsp])
                            p_keyvals2.append(p_keyval2[lsp + 1 :])
                        else:
                            p_keyvals2.append(" ".join(p_keyval2.split()))
                print(f"{p_keyvals2[0]}", file=self.outf)
                for p_keyval2 in p_keyvals2[1:]:
                    print(f"{' ':102}{delim}{p_keyval2}", file=self.outf)

            def print_dict_csv(c_tj: int) -> None:
                """
                Print CSV string in dict.

                :param c_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("Print %d CSV in dict %s", c_tj, devkeyval2)
                if not c_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                c_keyvals = devkeyval2.split(",")
                c_keyval = c_keyvals[0]
                print(f"{c_keyval}", file=self.outf)
                for c_keyval in c_keyvals[1:]:
                    print(f"{' ':102}{c_keyval}", file=self.outf)

            def print_dict_int(s_tj: int) -> None:
                """
                Print int in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                print(f"{devkeyval2}", file=self.outf)

            def print_dict_float(s_tj: int) -> None:
                """
                Print float in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                print(f"{devkeyval2}", file=self.outf)

            def print_dict_str(s_tj: int) -> None:
                """
                Print string in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["dict_str"]
                self.logger.debug("Print %d string in dict %s : '%s'", s_tj, devkey2, devkeyval2)
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                s_keyvals2 = []
                if len(devkeyval2) > 70:
                    lsp = devkeyval2[0:70].rfind(" ")
                    s_keyvals2.append(devkeyval2[0:lsp])
                    s_keyvals2.append(devkeyval2[lsp + 1 :])
                else:
                    s_keyvals2.append(" ".join(devkeyval2.split()))
                print(f"{s_keyvals2[0]}{delim}", file=self.outf)
                for s_keyval2 in s_keyvals2[1:]:
                    print(f"{' ':102}{delim}{s_keyval2}", file=self.outf)

            def print_list(l_tj: int) -> None:
                """
                Print list.

                :param l_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("*** Print %d list %s : %s", l_tj, devkey, devkeyval)
                if not l_tj:
                    print(f"{devkey:40}{delim}", end="", file=self.outf)
                else:
                    print(f"{' ':102}{delim}{devkey:40}{delim}", end="", file=self.outf)
                if len(devkeyval) == 1:
                    if type(devkeyval[0]) is not str:
                        print(f"{' ':102} {devkeyval[0]}", file=self.outf)
                    elif "," in devkeyval[0]:
                        l_keyvals = devkeyval[0].split(",")
                        l_keyval = l_keyvals[0]
                        print(f"{l_keyval.strip()}", file=self.outf)
                        for l_keyval in l_keyvals[1:]:
                            if "\n" in l_keyval:
                                n = 0
                                for line in l_keyval.split("\n"):
                                    if line:
                                        if n:
                                            print(f"{' ':102}", file=self.outf, end="")
                                        print(f" {line.strip()}", file=self.outf)
                                    n += 1
                            else:
                                print(f"{' ':102} {l_keyval.strip()}", file=self.outf)
                    else:
                        print(f"{' ':102} {devkeyval[0]}", file=self.outf)
                else:
                    print(f"{devkeyval}", file=self.outf)

            def print_str(s_tj: int) -> None:
                """
                Print string value.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("*** Print %d string %s : %s", s_tj, devkey, devkeyval)
                if not s_tj:
                    print(f"{devkey:40}{delim}", end="", file=self.outf)
                else:
                    print(f"{' ':102}{delim}{devkey:40}{delim}", end="", file=self.outf)
                if not devkeyval:
                    print(file=self.outf)
                elif type(devkeyval) is str:
                    if "\n" in devkeyval:
                        s_keyvals = devkeyval.split("\n")
                        # Remove empty lines
                        s_keyvals2 = []
                        for s_keyval in s_keyvals:
                            s_keyval2 = s_keyval.strip()
                            if s_keyval2:
                                if len(s_keyval2) > 70:
                                    lsp = s_keyval2[0:70].rfind(" ")
                                    s_keyvals2.append(s_keyval2[0:lsp])
                                    s_keyvals2.append(s_keyval2[lsp + 1 :])
                                else:
                                    s_keyvals2.append(" ".join(s_keyval2.split()))
                        print(f"{s_keyvals2[0]}", file=self.outf)
                        for s_keyval2 in s_keyvals2[1:]:
                            print(f"{' ':102}{delim}{s_keyval2}", file=self.outf)
                    elif "," in devkeyval:
                        s_keyvals = devkeyval.split(",")
                        s_keyval = s_keyvals[0]
                        print(f"{s_keyval.strip()}", file=self.outf)
                        for s_keyval in s_keyvals[1:]:
                            print(f"{' ':102} {s_keyval.strip()}", file=self.outf)
                    elif len(devkeyval) > 70:
                        s_keyvals2 = []
                        lsp = devkeyval[0:70].rfind(" ")
                        s_keyvals2.append(devkeyval[0:lsp])
                        s_keyvals2.append(devkeyval[lsp + 1 :])
                        print(f"{s_keyvals2[0]}", file=self.outf)
                        for s_keyval2 in s_keyvals2[1:]:
                            print(f"{' ':102} {s_keyval2}", file=self.outf)
                    else:
                        print(f"{devkeyval}", file=self.outf)
                elif type(devkeyval) is list:
                    print(f"{devkeyval[0]}", file=self.outf)
                    for s_keyval2 in devkeyval[1:]:
                        print(f"{' ':102} {s_keyval2}", file=self.outf)
                else:
                    print(f"{devkeyval}", file=self.outf)

            key: str
            ti: int
            tj: int
            devkeys: Any
            devkey: Any
            devkeyval: Any
            devkeyval2: Any

            self.logger.debug("Print %d %s: %s", len(devdict[stuff]), stuff, devdict[stuff])
            if not devdict[stuff]:
                return
            print(f"{stuff:20}{delim_t}", end="", file=self.outf)
            if not devdict[stuff]:
                print(file=self.outf)
                return
            ti = 0
            for item in devdict[stuff]:
                self.logger.debug("* Print %d item : %s", ti, item)
                for key in item:
                    if not ti:
                        try:
                            print(f"{key:40}{delim_t}", end="", file=self.outf)
                        except TypeError:
                            logging.warning("Could not print '%s' (%s)", key, type(key))
                    else:
                        print(f"{' ':20}{delim_t}{key:40}{delim_t}", end="", file=self.outf)
                    ti += 1
                    devkeys = item[key]
                    self.logger.debug("** Print item %s keys : %s", key, devkeys)
                    if type(devkeys) is not dict:
                        print(f"{devkeys}", file=self.outf)
                        continue
                    if not devkeys:
                        print("{}", file=self.outf)
                        continue
                    tj = 0
                    for devkey in devkeys:
                        devkeyval = devkeys[devkey]
                        if type(devkeyval) is dict:
                            pi = 0
                            self.logger.debug("*** Print %d dict %s : %s", tj, devkey, devkeyval)
                            print(f"{' ':61}{delim_t}{devkey:40}{delim_t}", file=self.outf)
                            # Read dictionary value
                            for devkey2 in devkeyval:
                                devkeyval2 = devkeyval[devkey2]
                                if type(devkeyval2) is list:
                                    print(file=self.outf)
                                    print_dict_list(tj)
                                elif type(devkeyval2) is dict:
                                    print(file=self.outf)
                                    print_dict_dict(tj)
                                    pi = tj
                                elif type(devkeyval2) is int:
                                    print_dict_int(tj)
                                elif type(devkeyval2) is float:
                                    print_dict_float(tj)
                                elif "\n" in devkeyval2:
                                    print_dict_para(tj)
                                elif "," in devkeyval2:
                                    print_dict_csv(tj)
                                elif not devkeyval2:
                                    print(file=self.outf)
                                else:
                                    print_dict_str(tj)
                                tj += 1
                        elif type(devkeyval) is list:
                            print_list(tj)
                            tj += 1
                        else:
                            self.logger.debug("Print %d string : %s", tj, devkeyval)
                            print_str(tj)
                            tj += 1

        def print_text_properties() -> None:
            """Print device properties in text format."""
            ti: int
            prop_name: str
            prop_vals: Any

            self.logger.debug(
                "Print %d properties: %s", len(devdict["properties"]), devdict["properties"]
            )
            if not devdict["properties"]:
                return
            print(f"{'properties':20} ", end="", file=self.outf)
            if not devdict["properties"]:
                print(file=self.outf)
                return
            ti = 0
            for propdict in devdict["properties"]:
                prop_name = propdict["name"]
                if not ti:
                    print(f"{prop_name:40} {'value':40} ", end="", file=self.outf)
                else:
                    print(f"{' ':20} {prop_name:40} {'value':40} ", end="", file=self.outf)
                ti += 1
                if "value" in propdict:
                    prop_vals = propdict["value"]
                else:
                    prop_vals = None
                if not prop_vals:
                    print(file=self.outf)
                    continue
                elif type(prop_vals) is list:
                    print(f"{prop_vals[0]}", file=self.outf)
                    for prop_val in prop_vals[1:]:
                        print(f"{' ':102} {prop_val}", file=self.outf)

        def print_text_pod() -> None:
            """Print pod information."""
            self.logger.debug("Print pod :\n%s", json.dumps(devdict, indent=4, default=str))
            if "pod" not in devdict:
                return
            if not devdict["pod"]:
                return
            print(f"{' ':20} {'pod':40} {'name':40} {devdict['pod']['metadata']['name']}")
            print(f"{' ':20} {' ':40} {'api_version':40} {devdict['pod']['api_version']}")
            print(f"{' ':20} {' ':40} {'phase':40} {devdict['pod']['status']['phase']}")
            print(f"{' ':20} {' ':40} {'start_time':40} {devdict['pod']['status']['start_time']}")
            print(f"{' ':20} {' ':40} {'host_ip':40} {devdict['pod']['status']['host_ip']}")
            print(f"{' ':20} {' ':40} {'pod_ip':40} {devdict['pod']['status']['pod_ip']}")
            ports: list = []
            for container in devdict["pod"]["spec"]["containers"]:
                for port in container["ports"]:
                    ports.append(str(port["container_port"]))
            print(f"{' ':20} {' ':40} {'ports':40} {','.join(ports)}")
            if devdict["processes"]["output"]:
                proc = devdict["processes"]["output"][0]
                psef = " ".join((" ".join(proc.split())).split(" ")[7:])
                print(f"{' ':20} {'process':40} {psef}")
                if len(devdict["processes"]["output"]) > 1:
                    for proc in devdict["processes"]["output"][1:]:
                        psef = " ".join((" ".join(proc.split())).split(" ")[7:])
                        print(f"{' ':20} {'process':40} {psef}")

        devdict: dict
        i: int
        j: int
        err_msg: str
        emsg: str
        info_key: str
        self.logger.debug("Print devices %s", self.devices_dict)
        for devdict in self.devices_dict["devices"]:
            self.logger.debug("Print device %s", devdict)
            print(f"{'name':20}{delim_t}{devdict['name']}", file=self.outf)
            print(f"{'version':20}{delim_t}{devdict['version']}", file=self.outf)
            print(f"{'green mode':20}{delim_t}{devdict['green_mode']}", file=self.outf)
            print(f"{'device access':20}{delim_t}{devdict['device_access']}", file=self.outf)
            print(f"{'logging level':20}{delim_t}{devdict['logging_level']}", file=self.outf)
            if "errors" in devdict and len(devdict["errors"]) and not self.quiet_mode:
                print(f"{'errors':20}", file=self.outf, end="")
                i = 0
                for err_msg in devdict["errors"]:
                    if "\n" in err_msg:
                        j = 0
                        for emsg in err_msg.split("\n"):
                            if not i and not j:
                                pass
                            if i and not j:
                                print(f"{' ':20}", file=self.outf, end="")
                            elif j:
                                print(f"{' ':20} ...", file=self.outf, end="")
                            else:
                                pass
                            print(f"{delim_t}{emsg}", file=self.outf)
                            j += 1
                    else:
                        if i:
                            print(f"{' ':20}", file=self.outf, end="")
                        print(f"{delim_t}{err_msg}", file=self.outf)
                    i += 1
            if "info" in devdict:
                i = 0
                for info_key in devdict["info"]:
                    if not i:
                        print(
                            f"{'info':20}{delim_t}{info_key:40}{delim_t}"
                            f"{devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    else:
                        print(
                            f"{' ':20}{delim_t}{info_key:40}{delim_t}{devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    i += 1
            print_text_stuff("attributes")
            print_text_stuff("commands")
            print_text_properties()
            print_text_pod()
            print(file=self.outf)

    def print_txt_large(self) -> None:  # noqa: C901
        """Print the whole thing."""

        delim_t: str = DELIMS["all"]

        def print_text_stuff(stuff: str) -> None:
            """
            Print attribute, command or property.

            :param stuff: name of the thing
            """

            def print_dict_list(l_tj: int) -> None:
                """
                Print list in dict.

                :param l_tj: item number
                """
                delim: str = DELIMS["dict_list"]
                self.logger.debug(
                    "Print list %d in dict %s : %s (%d)",
                    tj,
                    devkey2,
                    devkeyval2,
                    len(devkeyval2),
                )
                print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                if len(devkeyval2) == 0:
                    print("[]", file=self.outf)
                elif len(devkeyval2) == 1:
                    if type(devkeyval2[0]) is not str:
                        # TODO fix this
                        # if l_tj:
                        #     print(f"{' ':143}{delim}", file=self.outf, end="")
                        print(f"{str(devkeyval2[0])}", file=self.outf)
                    elif "," in devkeyval2[0]:
                        l_keyvals = devkeyval2[0].split(",")
                        l_keyval = l_keyvals[0]
                        print(f"{l_keyval}", file=self.outf)
                        for l_keyval in l_keyvals[1:]:
                            print(f"{' ':102}{delim}{l_keyval}", file=self.outf)
                    else:
                        if l_tj:
                            print(f"{' ':102}{delim}", file=self.outf, end="")
                        print(f"{devkeyval2[0]}", file=self.outf)
                else:
                    n = 0
                    for l_keyval in devkeyval2:
                        if n:
                            print(f"{' ':102}{delim}", file=self.outf, end="")
                        print(f"{l_keyval}", file=self.outf)
                        n += 1

            def print_dict_dict(d_tj: int) -> None:
                """
                Print dict in dict.

                :param d_tj: item number
                """
                delim: str = DELIMS["dict_dict"]
                self.logger.debug(
                    "Print %d/%d dict in dict %s : %s", d_tj, pi, devkey2, devkeyval2
                )
                print(f"{' ':102}{delim}{devkey2:40}", file=self.outf)
                n = 0
                for d_keyval in devkeyval2:
                    if type(devkeyval2[d_keyval]) is dict:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "Print %d/%d dict in dict in dict %s : %s",
                            n,
                            dd_len,
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}", end="", file=self.outf)
                        m = 0
                        for item2 in devkeyval2[d_keyval]:
                            if m:
                                print(f"{' ':143}{delim}{' ':40}{delim}", end="", file=self.outf)
                            print(
                                f"{' ':143}{delim}{' ':40} {item2} {devkeyval2[d_keyval][item2]}",
                                end="",
                                file=self.outf,
                            )
                            m += 1
                    elif type(devkeyval2[d_keyval]) is list:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "Print %d/%d list in dict in dict %s : %s",
                            n,
                            dd_len,
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if dd_len == 0:
                            print(f"{' ':102}{delim}{d_keyval:40}{delim}[]", file=self.outf)
                        elif dd_len == 1:
                            print(
                                f"{' ':102}{delim}{d_keyval:40}{delim}{devkeyval2[d_keyval][0]}",
                                file=self.outf,
                            )
                        else:
                            print(
                                f"{' ':102}{delim}{d_keyval:40}{delim}{devkeyval2[d_keyval][0]}",
                                file=self.outf,
                            )
                            m = 0
                            for d_item in devkeyval2[d_keyval][1:]:
                                print(f"{' ':143}{delim}", end="", file=self.outf)
                                if type(d_item) is dict:
                                    k = 0
                                    for key2 in d_item:
                                        if k:
                                            print(
                                                f"{' ':143}{delim}",
                                                end="",
                                                file=self.outf,
                                            )
                                        print(
                                            f" {key2:32}{delim}{d_item[key2]}",
                                            file=self.outf,
                                        )
                                        k += 1
                                else:
                                    print(f"{delim}{d_item}", file=self.outf)
                                m += 1
                    elif type(devkeyval2[d_keyval]) is not str:
                        self.logger.debug(
                            "Print %d %s in dict in dict %s : %s",
                            n,
                            type(devkeyval2[d_keyval]),
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not n:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        else:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}", end="", file=self.outf)
                        print(f"{devkeyval2[d_keyval]}", file=self.outf)
                    else:
                        self.logger.debug(
                            "Print %d/%d string in dict in dict %s : %s",
                            n,
                            len(devkeyval2[d_keyval]),
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not n:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        else:
                            print(f"{' ':143}{delim}", end="", file=self.outf)
                        print(f"{d_keyval:40}{delim}{devkeyval2[d_keyval]}", file=self.outf)
                    n += 1

            def print_dict_para(p_tj: int) -> None:
                """
                Print paragraph in dict.

                :param p_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("Print %d paragraph in dict : %s", p_tj, devkeyval2)
                if not p_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102} {devkey2:40}{delim}", file=self.outf, end="")
                p_keyvals = devkeyval2.split("\n")
                # Remove empty lines
                p_keyvals2 = []
                for p_keyval in p_keyvals:
                    p_keyval2 = p_keyval.strip()
                    if p_keyval2:
                        if len(p_keyval2) > 70:
                            lsp = p_keyval2[0:70].rfind(" ")
                            p_keyvals2.append(p_keyval2[0:lsp])
                            p_keyvals2.append(p_keyval2[lsp + 1 :])
                        else:
                            p_keyvals2.append(" ".join(p_keyval2.split()))
                print(f"{p_keyvals2[0]}", file=self.outf)
                for p_keyval2 in p_keyvals2[1:]:
                    print(f"{' ':102}{delim}{p_keyval2}", file=self.outf)

            def print_dict_csv(c_tj: int) -> None:
                """
                Print CSV string in dict.

                :param c_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("Print %d CSV in dict %s", c_tj, devkeyval2)
                if not c_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                c_keyvals = devkeyval2.split(",")
                c_keyval = c_keyvals[0]
                print(f"{c_keyval}", file=self.outf)
                for c_keyval in c_keyvals[1:]:
                    print(f"{' ':102}{c_keyval}", file=self.outf)

            def print_dict_int(s_tj: int) -> None:
                """
                Print int in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                print(f"{devkeyval2}", file=self.outf)

            def print_dict_float(s_tj: int) -> None:
                """
                Print float in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                print(f"{devkeyval2}", file=self.outf)

            def print_dict_str(s_tj: int) -> None:
                """
                Print string in dict.

                :param s_tj: item number
                """
                delim: str = DELIMS["dict_str"]
                self.logger.debug("Print %d string in dict %s : '%s'", s_tj, devkey2, devkeyval2)
                if not s_tj:
                    print(f"{devkey2:61}{delim}", file=self.outf, end="")
                else:
                    print(f"{' ':102}{delim}{devkey2:40}{delim}", file=self.outf, end="")
                s_keyvals2 = []
                if len(devkeyval2) > 70:
                    lsp = devkeyval2[0:70].rfind(" ")
                    s_keyvals2.append(devkeyval2[0:lsp])
                    s_keyvals2.append(devkeyval2[lsp + 1 :])
                else:
                    s_keyvals2.append(" ".join(devkeyval2.split()))
                print(f"{s_keyvals2[0]}{delim}", file=self.outf)
                for s_keyval2 in s_keyvals2[1:]:
                    print(f"{' ':102}{delim}{s_keyval2}", file=self.outf)

            def print_list(l_tj: int) -> None:
                """
                Print list.

                :param l_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("*** Print %d list %s : %s", l_tj, devkey, devkeyval)
                if not l_tj:
                    print(f"{devkey:40}{delim}", end="", file=self.outf)
                else:
                    print(f"{' ':102}{delim}{devkey:40}{delim}", end="", file=self.outf)
                if len(devkeyval) == 1:
                    if "," in devkeyval[0]:
                        l_keyvals = devkeyval[0].split(",")
                        l_keyval = l_keyvals[0]
                        print(f"{l_keyval.strip()}", file=self.outf)
                        for l_keyval in l_keyvals[1:]:
                            if "\n" in l_keyval:
                                n = 0
                                for line in l_keyval.split("\n"):
                                    if line:
                                        if n:
                                            print(f"{' ':102}", file=self.outf, end="")
                                        print(f" {line.strip()}", file=self.outf)
                                    n += 1
                            else:
                                print(f"{' ':102} {l_keyval.strip()}", file=self.outf)
                    else:
                        print(f"{' ':102} {devkeyval[0]}", file=self.outf)
                else:
                    print(f"{devkeyval}", file=self.outf)

            def print_str(s_tj: int) -> None:
                """
                Print string value.

                :param s_tj: item number
                """
                delim: str = DELIMS["all"]
                self.logger.debug("*** Print %d string %s : %s", s_tj, devkey, devkeyval)
                if not s_tj:
                    print(f"{devkey:40}{delim}", end="", file=self.outf)
                else:
                    print(f"{' ':102}{delim}{devkey:40}{delim}", end="", file=self.outf)
                if not devkeyval:
                    print(file=self.outf)
                elif type(devkeyval) is str:
                    if "\n" in devkeyval:
                        s_keyvals = devkeyval.split("\n")
                        # Remove empty lines
                        s_keyvals2 = []
                        for s_keyval in s_keyvals:
                            s_keyval2 = s_keyval.strip()
                            if s_keyval2:
                                if len(s_keyval2) > 70:
                                    lsp = s_keyval2[0:70].rfind(" ")
                                    s_keyvals2.append(s_keyval2[0:lsp])
                                    s_keyvals2.append(s_keyval2[lsp + 1 :])
                                else:
                                    s_keyvals2.append(" ".join(s_keyval2.split()))
                        print(f"{s_keyvals2[0]}", file=self.outf)
                        for s_keyval2 in s_keyvals2[1:]:
                            print(f"{' ':102}{delim}{s_keyval2}", file=self.outf)
                    elif "," in devkeyval:
                        s_keyvals = devkeyval.split(",")
                        s_keyval = s_keyvals[0]
                        print(f"{s_keyval.strip()}", file=self.outf)
                        for s_keyval in s_keyvals[1:]:
                            print(f"{' ':102} {s_keyval.strip()}", file=self.outf)
                    elif len(devkeyval) > 70:
                        s_keyvals2 = []
                        lsp = devkeyval[0:70].rfind(" ")
                        s_keyvals2.append(devkeyval[0:lsp])
                        s_keyvals2.append(devkeyval[lsp + 1 :])
                        print(f"{s_keyvals2[0]}", file=self.outf)
                        for s_keyval2 in s_keyvals2[1:]:
                            print(f"{' ':102} {s_keyval2}", file=self.outf)
                    else:
                        print(f"{devkeyval}", file=self.outf)
                elif type(devkeyval) is list:
                    print(f"{devkeyval[0]}", file=self.outf)
                    for s_keyval2 in devkeyval[1:]:
                        print(f"{' ':102} {s_keyval2}", file=self.outf)
                else:
                    print(f"{devkeyval}", file=self.outf)

            key: str
            ti: int
            tj: int
            devkeys: Any
            devkey: Any
            devkeyval: Any
            devkeyval2: Any

            self.logger.debug("Print %d %s: %s", len(devdict[stuff]), stuff, devdict[stuff])
            if not devdict[stuff]:
                return
            print(f"{stuff:20}{delim_t}", end="", file=self.outf)
            if not devdict[stuff]:
                print(file=self.outf)
                return
            ti = 0
            for item in devdict[stuff]:
                self.logger.debug("* Print %d item : %s", ti, item)
                for key in item:
                    if not ti:
                        try:
                            print(f"{key:40}{delim_t}", end="", file=self.outf)
                        except TypeError:
                            logging.warning("Could not print '%s' (%s)", key, type(key))
                    else:
                        print(f"{' ':20}{delim_t}{key:40}{delim_t}", end="", file=self.outf)
                    ti += 1
                    devkeys = item[key]
                    self.logger.debug("** Print item %s keys : %s", key, devkeys)
                    if type(devkeys) is not dict:
                        print(f"{devkeys}", file=self.outf)
                        continue
                    if not devkeys:
                        print("{}", file=self.outf)
                        continue
                    tj = 0
                    for devkey in devkeys:
                        devkeyval = devkeys[devkey]
                        if type(devkeyval) is dict:
                            pi = 0
                            self.logger.debug("*** Print %d dict %s : %s", tj, devkey, devkeyval)
                            print(f"{' ':61}{delim_t}{devkey:40}{delim_t}", file=self.outf)
                            # Read dictionary value
                            for devkey2 in devkeyval:
                                devkeyval2 = devkeyval[devkey2]
                                if type(devkeyval2) is list:
                                    print(file=self.outf)
                                    print_dict_list(tj)
                                elif type(devkeyval2) is dict:
                                    print(file=self.outf)
                                    print_dict_dict(tj)
                                    pi = tj
                                elif type(devkeyval2) is int:
                                    print_dict_int(tj)
                                elif type(devkeyval2) is float:
                                    print_dict_float(tj)
                                elif "\n" in devkeyval2:
                                    print_dict_para(tj)
                                elif "," in devkeyval2:
                                    print_dict_csv(tj)
                                elif not devkeyval2:
                                    print(file=self.outf)
                                else:
                                    print_dict_str(tj)
                                tj += 1
                        elif type(devkeyval) is list:
                            print_list(tj)
                            tj += 1
                        else:
                            self.logger.debug("Print %d string : %s", tj, devkeyval)
                            print_str(tj)
                            tj += 1

        def print_text_properties() -> None:
            """Print device properties in text format."""
            ti: int
            prop_name: str
            prop_vals: Any

            self.logger.debug(
                "Print %d properties: %s", len(devdict["properties"]), devdict["properties"]
            )
            if not devdict["properties"]:
                return
            print(f"{'properties':20} ", end="", file=self.outf)
            if not devdict["properties"]:
                print(file=self.outf)
                return
            ti = 0
            for propdict in devdict["properties"]:
                prop_name = propdict["name"]
                if not ti:
                    print(f"{prop_name:40} {'value':40} ", end="", file=self.outf)
                else:
                    print(f"{' ':20} {prop_name:40} {'value':40} ", end="", file=self.outf)
                ti += 1
                if "value" in propdict:
                    prop_vals = propdict["value"]
                else:
                    prop_vals = None
                if not prop_vals:
                    print(file=self.outf)
                    continue
                elif type(prop_vals) is list:
                    print(f"{prop_vals[0]}", file=self.outf)
                    for prop_val in prop_vals[1:]:
                        print(f"{' ':102} {prop_val}", file=self.outf)

        def print_text_pod() -> None:
            """Print pod information."""
            self.logger.debug("Print pod :\n%s", json.dumps(devdict, indent=4, default=str))
            if "pod" not in devdict:
                return
            if not devdict["pod"]:
                return
            print(f"{' ':20} {'pod':40} {'name':40} {devdict['pod']['metadata']['name']}")
            print(f"{' ':20} {' ':40} {'api_version':40} {devdict['pod']['api_version']}")
            print(f"{' ':20} {' ':40} {'phase':40} {devdict['pod']['status']['phase']}")
            print(f"{' ':20} {' ':40} {'start_time':40} {devdict['pod']['status']['start_time']}")
            print(f"{' ':20} {' ':40} {'host_ip':40} {devdict['pod']['status']['host_ip']}")
            print(f"{' ':20} {' ':40} {'pod_ip':40} {devdict['pod']['status']['pod_ip']}")
            ports: list = []
            for container in devdict["pod"]["spec"]["containers"]:
                for port in container["ports"]:
                    ports.append(str(port["container_port"]))
            print(f"{' ':20} {' ':40} {'ports':40} {','.join(ports)}")
            if devdict["processes"]["output"]:
                proc = devdict["processes"]["output"][0]
                psef = " ".join((" ".join(proc.split())).split(" ")[7:])
                print(f"{' ':20} {'process':40} {psef}")
                if len(devdict["processes"]["output"]) > 1:
                    for proc in devdict["processes"]["output"][1:]:
                        psef = " ".join((" ".join(proc.split())).split(" ")[7:])
                        print(f"{' ':20} {'process':40} {psef}")

        devdict: dict
        i: int
        j: int
        err_msg: str
        emsg: str
        info_key: str
        self.logger.debug("Print devices %s", self.devices_dict)
        for devdict in self.devices_dict["devices"]:
            self.logger.debug("Print device %s", devdict)
            print(f"{'name':20}{delim_t}{devdict['name']}", file=self.outf)
            print(f"{'version':20}{delim_t}{devdict['version']}", file=self.outf)
            print(f"{'green mode':20}{delim_t}{devdict['green_mode']}", file=self.outf)
            print(f"{'device access':20}{delim_t}{devdict['device_access']}", file=self.outf)
            print(f"{'logging level':20}{delim_t}{devdict['logging_level']}", file=self.outf)
            if "errors" in devdict and len(devdict["errors"]) and not self.quiet_mode:
                print(f"{'errors':20}", file=self.outf, end="")
                i = 0
                for err_msg in devdict["errors"]:
                    if "\n" in err_msg:
                        j = 0
                        for emsg in err_msg.split("\n"):
                            if not i and not j:
                                pass
                            if i and not j:
                                print(f"{' ':20}", file=self.outf, end="")
                            elif j:
                                print(f"{' ':20} ...", file=self.outf, end="")
                            else:
                                pass
                            print(f"{delim_t}{emsg}", file=self.outf)
                            j += 1
                    else:
                        if i:
                            print(f"{' ':20}", file=self.outf, end="")
                        print(f"{delim_t}{err_msg}", file=self.outf)
                    i += 1
            if "info" in devdict:
                i = 0
                for info_key in devdict["info"]:
                    if not i:
                        print(
                            f"{'info':20}{delim_t}{info_key:40}{delim_t}"
                            f"{devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    else:
                        print(
                            f"{' ':20}{delim_t}{info_key:40}{delim_t}{devdict['info'][info_key]}",
                            file=self.outf,
                        )
                    i += 1
            print_text_stuff("attributes")
            print_text_stuff("commands")
            print_text_properties()
            print_text_pod()
            print(file=self.outf)
