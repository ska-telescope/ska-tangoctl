"""Print Tango configuration in HTML format."""

import json
import logging
from typing import Any

from xml.sax.saxutils import escape


class TangoJsonReaderXmlMixin:
    """Read JSON and print as markdown or text."""

    outf: Any
    logger: logging.Logger
    tgo_space: str
    devices_dict: dict
    quiet_mode: bool

    def print_xml_large(self) -> None:  # noqa: C901
        """Print the whole thing."""

        def print_xml_stuff(stuff: str) -> None:
            """
            Print attribute, command or property.

            :param stuff: name of the thing
            """

            def print_dict_list() -> None:
                """
                Print list in dict.
                """
                self.logger.debug(
                    "** Print list in dict %s : %s (%d)", devkey2, devkeyval2, len(devkeyval2),
                )
                if self.logger.getEffectiveLevel() == logging.DEBUG:
                    print(f"{'\t'*5}\t<!-- {devkeyval2} -->")
                if len(devkeyval2) == 0:
                    print(f'{"\t"*6}<{devkey2} type="list"></{devkey2}>', file=self.outf)
                elif len(devkeyval2) == 1:
                    print(f'{"\t"*6}<{devkey2} type="list">{devkeyval2[0]}</{devkey2}>', file=self.outf)
                else:
                    print(f'{"\t"*6}<{devkey2} type="list">', file=self.outf)
                    for l_keyval in devkeyval2:
                        print(f"{l_keyval}", file=self.outf)
                    print(f"{'\t'*6}</{devkey2}>", file=self.outf)

            def print_dict_dict() -> None:
                """
                Print dict in dict.
                """
                self.logger.debug("** Print dict in dict %s : %s", devkey2, devkeyval2)
                print(f'{"\t"*6}<{devkey2} type="dict">', file=self.outf)
                for d_keyval in devkeyval2:
                    if type(devkeyval2[d_keyval]) is dict:
                        print(f'{"\t"*7}<{d_keyval}>', file=self.outf)
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "*** Print dict in dict in dict %s : %s",
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        for item2 in devkeyval2[d_keyval]:
                            print(
                                f"{'\t'*8}<{item2}>{devkeyval2[d_keyval][item2]}</{item2}>",
                                file=self.outf,
                            )
                        print(f"{'\t'*7}</{d_keyval}>", file=self.outf)
                    elif type(devkeyval2[d_keyval]) is list:
                        dd_len = len(devkeyval2[d_keyval])
                        self.logger.debug(
                            "*** Print list in dict in dict %s : %s",
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        if not dd_len:
                            print(f'{"\t"*7}<{d_keyval}/>', file=self.outf)
                        else:
                            print(f'{"\t"*7}<{d_keyval}>', file=self.outf)
                            for d_item in devkeyval2[d_keyval]:
                                print(f"{d_item}", file=self.outf)
                            print(f"{'\t'*7}</{d_keyval}>", file=self.outf)
                    else:
                        self.logger.debug(
                            "*** Print string in dict in dict %s : %s",
                            d_keyval,
                            devkeyval2[d_keyval],
                        )
                        print(f'{"\t"*7}<{d_keyval}>', file=self.outf, end="")
                        print(f"{devkeyval2[d_keyval]}", file=self.outf, end="")
                        print(f"</{d_keyval}>", file=self.outf)
                print(f"{'\t'*6}</{devkey2}>", file=self.outf)

            def print_dict_para() -> None:
                """
                Print paragraph in dict.

                """
                self.logger.debug("** Print paragraph in dict : %s", devkeyval2)
                print(f"{'\t'*7}<{devkey2}>", file=self.outf, end="")
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
                    print(f" {p_keyval2}", file=self.outf)
                print(f"{'\t'*7}</{devkey2}>", file=self.outf)

            def print_dict_csv() -> None:
                """
                Print CSV string in dict.
                """
                self.logger.debug("** Print CSV in dict %s", devkeyval2)
                print(f"{'\t'*7}<{devkey2}>", file=self.outf)
                c_keyvals = devkeyval2.split(",")
                c_keyval = c_keyvals[0]
                print(f"{c_keyval}", file=self.outf)
                for c_keyval in c_keyvals[1:]:
                    print(f" {c_keyval}", file=self.outf)
                print(f"{'\t'*7}</{devkey2}>", file=self.outf)

            def print_list() -> None:
                """
                Print list.
                """
                self.logger.debug("** Print list %s : %s", devkey, devkeyval)
                if len(devkeyval) == 0:
                    print(f"{'\t'*5}<{devkey}/>", file=self.outf)
                elif len(devkeyval) == 1:
                    print(f"{'\t'*5}<{devkey}>", file=self.outf)
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
                        print(f"{devkeyval[0]}", file=self.outf)
                    print(f"{'\t'*5}</{devkey}>", file=self.outf)
                else:
                    print(f"{'\t'*5}<{devkey}>", file=self.outf)
                    tag = devkey[0:-1]
                    n = 0
                    for dkv in devkeyval:
                        print(f'{'\t'*6}<{tag} value="{n}">{dkv}</{tag}>', file=self.outf)
                        n += 1
                    print(f"{'\t'*5}</{devkey}>", file=self.outf)

            def print_str() -> None:
                """
                Print string value.
                """
                self.logger.debug("** Print string %s : %s", devkey, devkeyval)
                print(f"{' ':102}{devkey:40}", end="", file=self.outf)
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
                            print(f"{' ':102}{s_keyval2}", file=self.outf)
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
            devkeys: Any
            devkey: Any
            devkeyval: Any
            devkeyval2: Any

            tag1 = f"{stuff[0].upper()}{stuff[1:]}"
            tag2 = tag1[0:-1]

            # self.logger.debug("Print %d %s: %s", len(devdict[stuff]), stuff, devdict[stuff])
            if not devdict[stuff]:
                return
            # print(f"{stuff:20}", end="", file=self.outf)
            # if not devdict[stuff]:
            #     print(file=self.outf)
            #     return
            print(f'{'\t'*2}<{tag1}>', file=self.outf)
            for item in devdict[stuff]:
                print(f'{'\t'*3}<{tag2}>', file=self.outf)
                self.logger.debug("* Print item : %s", item)
                if self.logger.getEffectiveLevel() == logging.DEBUG:
                    print(f'{'\t'*4}<!--\n{json.dumps(item, indent=4)}\n-->', file=self.outf)
                for key in item:
                    devkeys = item[key]
                    self.logger.debug("** Print item %s keys : %s", key, devkeys)
                    if type(devkeys) is not dict:
                        print(f"{'\t'*4}<{key}>{devkeys}</{key}>", file=self.outf)
                        continue
                    if not devkeys:
                        print(f"{'\t'*4}<{key}></{key}>", file=self.outf)
                        continue
                    print(f"{'\t'*4}<{key}>", file=self.outf)
                    for devkey in devkeys:
                        devkeyval = devkeys[devkey]
                        self.logger.info(
                            "Print key %s : %s (%s)", devkey, devkeyval, type(devkeyval).__name__
                        )
                        if type(devkeyval) is dict:
                            print(f'{"\t"*5}<{devkey} type="dict">', file=self.outf)
                            self.logger.debug("*** Print dict %s : %s", devkey, devkeyval)
                            # Read dictionary value
                            for devkey2 in devkeyval:
                                devkeyval2 = devkeyval[devkey2]
                                if type(devkeyval2) is list:
                                    print_dict_list()
                                elif type(devkeyval2) is dict:
                                    # print(f'{"\t"*6}<{devkey2} type="dict">')
                                    if self.logger.getEffectiveLevel() == logging.DEBUG:
                                        print(f"{'\t'*5}\t<!--\n{json.dumps(devkeyval2, indent=4)}\n-->")
                                    print_dict_dict()
                                    # print(f"{'\t'*6}</{devkey2}>")
                                elif type(devkeyval2) is int:
                                    print(f"{'\t'*6}\t<{devkey2}>{devkeyval2}</{devkey2}>")
                                elif type(devkeyval2) is float:
                                    print(f"{'\t'*6}\t<{devkey2}>{devkeyval2}</{devkey2}>")
                                elif "\n" in devkeyval2:
                                    print(f'{"\t"*6}<{devkey2} type="para">')
                                    if self.logger.getEffectiveLevel() == logging.DEBUG:
                                        print(f"{'\t'*6}\t<!-- {devkeyval2} -->")
                                    print_dict_para()
                                    print(f"{'\t'*6}</{devkey2}>")
                                elif "," in devkeyval2:
                                    print(f'{"\t"*6}<{devkey2} type="csv">')
                                    if self.logger.getEffectiveLevel() == logging.DEBUG:
                                        print(f"{'\t'*6}\t<!-- {devkeyval2} -->")
                                    print_dict_csv()
                                    print(f"{'\t'*6}</{devkey2}>")
                                elif not devkeyval2:
                                    print(f"{'\t'*6}<{devkey2}/>")
                                    pass
                                else:
                                    print(f"{'\t'*6}<{devkey2}>{devkeyval2}</{devkey2}>")
                            print(f"{'\t'*5}</{devkey}>", file=self.outf)
                        elif type(devkeyval) is list:
                            # print(f"{'\t'*5}<{devkey} type=\"list\">", file=self.outf)
                            print_list()
                            # print(f"{'\t'*5}</{devkey}>", file=self.outf)
                        elif type(devkeyval) is str:
                            dkv = escape(devkeyval).replace("\u2018", "&apos;").replace(
                                "\u2019", "&apos;"
                            )
                            self.logger.debug("Print string : %s", repr(dkv))
                            if "\n" in devkeyval:
                                print(
                                    f'{"\t" * 5}<{devkey} type="str">'
                                    f'<![CDATA[{dkv}>]]></{devkey}>',
                                    file=self.outf,
                                )
                            else:
                                print(
                                    f'{"\t" * 5}<{escape(devkey)} type="str">{devkeyval}</{devkey}>',
                                    file=self.outf,
                                )
                        else:
                            self.logger.debug("*** Print string : %s", devkeyval)
                            print(f"{'\t' * 5}<{devkey} type=\"{type(devkeyval).__name__}\">{devkeyval}</{devkey}>", file=self.outf)
                    print(f"{'\t'*4}</{key}>", file=self.outf)
                print(f'{'\t'*3}</{tag2}>', file=self.outf)
            print(f'{'\t'*2}</{stuff[0].upper()}{stuff[1:]}>', file=self.outf)

        def print_pogo_xml_attributes() -> None:
            """Print device attributes in xml format."""
            for item in devdict["attributes"]:
                self.logger.debug("Print attribute :\n%s", json.dumps(item, indent=4))
                data_format = f'{item["config"]["data_format"][0]}{item["config"]["data_format"][1:].lower()}'
                print(
                    f'{"\t"*2}<attributes name="{item["name"]}" attType="{data_format}"'
                    f' rwType="{item["config"]["writable"]}"'
                    f' displayLevel="{item["config"]["disp_level"]}"'
                    f' polledPeriod="{item["poll_period"]}"'
                    f' maxX="{item["config"]["max_dim_x"]}"'
                    f' maxY="{item["config"]["max_dim_y"]}"'
                    '>',
                    file=self.outf
                )
                print(
                    f'{"\t"*3}<dataType xsi:type="pogoDsl:{item["config"]["data_type"]}"/>',
                    file=self.outf
                )
                # description=item["config"]["description"].split("\n")[0].strip()
                desc_str = ""
                for description in item["config"]["description"].split("\n"):
                    desc_str = description.strip()
                    if desc_str:
                        break
                print(
                    f'{"\t"*3}<properties description="{desc_str}"'
                    f' label="" unit=""'
                    f' standardUnit="{item["config"]["standard_unit"]}"'
                    f' displayUnit="{item["config"]["display_unit"]}"'
                    f' format="{item["config"]["format"]}"'
                    f' maxValue=""'
                    f' minValue=""'
                    f' maxAlarm="{item["config"]["alarms"]["max_alarm"]}"'
                    f' minAlarm="{item["config"]["alarms"]["min_alarm"]}"'
                    f' maxWarning="{item["config"]["alarms"]["max_warning"]}"'
                    f' minWarning="{item["config"]["alarms"]["min_warning"]}"'
                    f' deltaTime="{item["config"]["alarms"]["delta_t"]}"'
                    f' deltaValue="{item["config"]["alarms"]["delta_val"]}"'
                    '>',
                    file=self.outf
                )
                if "enum_labels" in item["config"]:
                    for enum_label in item["config"]["enum_labels"]:
                        print(f'{"\t"*3}<enumLabels>{enum_label}</enumLabels>', file=self.outf)
                print(f'{"\t"*2}<attributes>', file=self.outf)

        def print_pogo_xml_commands() -> None:
            """Print device commands in xml format."""
            for item in devdict["commands"]:
                self.logger.debug("Print command :\n%s", json.dumps(item, indent=4))
                print(
                    f'{"\t"*2}<commands name="{item["name"]}" description=""'
                    f' displayLevel="{item["config"]["disp_level"]}"'
                    '>',
                    file=self.outf
                )
                print(f'{"\t"*3}<argin description="{item["config"]["in_type_desc"]}">', file=self.outf)
                print(f'{"\t"*4}<type xsi:type="pogoDsl:{item["config"]["in_type"].split(".")[-1]}"/>', file=self.outf)
                print(f'{"\t"*3}</argin>', file=self.outf)
                print(f'{"\t"*3}<argout description="{item["config"]["out_type_desc"]}">', file=self.outf)
                print(f'{"\t"*4}<type xsi:type="pogoDsl:{item["config"]["out_type"].split(".")[-1]}"/>', file=self.outf)
                print(f'{"\t"*3}</argout>', file=self.outf)
                print(f'{"\t"*2}</commands>', file=self.outf)

        def print_xml_properties() -> None:
            """Print device properties in xml format."""
            ti: int
            prop_name: str
            prop_vals: Any

            self.logger.debug(
                "** Print %d properties: %s", len(devdict["properties"]), devdict["properties"]
            )
            if not devdict["properties"]:
                return
            print(f"{'\t'*2}<Properties>", file=self.outf)
            if not devdict["properties"]:
                print(f"{'\t'*2}</Properties>", file=self.outf)
                return
            for propdict in devdict["properties"]:
                self.logger.debug("Print property :\n%s", json.dumps(propdict, indent=4))
                print(f"{'\t'*3}<Property>", file=self.outf)
                prop_name = propdict["name"]
                print(f"{'\t'*4}<name>{prop_name}</name>", file=self.outf)
                if "value" in propdict:
                    prop_vals = propdict["value"]
                else:
                    prop_vals = None
                if not prop_vals:
                    print(f"{'\t'*4}<value/>")
                elif type(prop_vals) is list:
                    print(f"{'\t'*4}<value>", file=self.outf, end="")
                    print(f"{prop_vals[0]}", file=self.outf, end="")
                    for prop_val in prop_vals[1:]:
                        print(f",{prop_val.strip()}", file=self.outf, end="")
                    print(f"</value>", file=self.outf)
                print(f"{'\t'*3}</Property>", file=self.outf)
            print(f"{'\t'*2}</Properties>", file=self.outf)

        def print_xml_pod() -> None:
            """Print pod information."""
            self.logger.debug("** Print pod :\n%s", json.dumps(devdict, indent=4, default=str))
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
        # self.logger.debug("* Print devices %s", self.devices_dict)
        print('<?xml version="1.0" encoding="ASCII"?>', file=self.outf)
        print(
            '<pogoDsl:PogoSystem xmi:version="2.0" xmlns:xmi="http://www.omg.org/XMI"'
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            ' xmlns:pogoDsl="http://www.esrf.fr/tango/pogo/PogoDsl">',
            file=self.outf
        )
        for devdict in self.devices_dict["devices"]:
            cls_name = devdict["info"]["dev_class"]
            print(f'\t<classes name="{cls_name}" pogoRevision="9.8">', file=self.outf)
            # self.logger.debug("Print device %s", devdict)
            print(
                f'{"\t"*2}<description'
                f' description="Tango device {devdict["name"]}'
                f' version {devdict["version"]}" license="GPL" copyright="">',
                file=self.outf
            )
            print(f"{'\t'*2}</description>", file=self.outf)
            print(f"{'\t'*2}<Name>{devdict['name']}</Name>", file=self.outf)
            print(f"{'\t'*2}<Version>{devdict['version']}</Version>", file=self.outf)
            print(f"{'\t'*2}<GreenMode>{devdict['green_mode']}</GreenMode>", file=self.outf)
            print(f"{'\t'*2}<DeviceAccess>{devdict['device_access']}</DeviceAccess>", file=self.outf)
            print(f"{'\t'*2}<LoggingLevel>{devdict['logging_level']}</LoggingLevel>", file=self.outf)
            if "errors" in devdict and len(devdict["errors"]) and not self.quiet_mode:
                print(f"{'\t'*2}<Errors>", file=self.outf)
                for err_msg in devdict["errors"]:
                    print(f"{'\t'*3}<Error>{err_msg}</Error>", file=self.outf)
                print(f"{'\t'*2}</Errors>", file=self.outf)
            if "info" in devdict:
                print(f"{'\t'*2}<Info>", file=self.outf)
                for info_key in devdict["info"]:
                    print(
                        f"{'\t'*3}<{info_key}>"
                        f"{devdict['info'][info_key]}"
                        f"</{info_key}>",
                        file=self.outf,
                    )
                print(f"{'\t'*2}</Info>", file=self.outf)
            print_xml_stuff("attributes")
            print_xml_stuff("commands")
            print_xml_properties()
            print_xml_pod()
            print_pogo_xml_attributes()
            print_pogo_xml_commands()
            print('\t</classes>', file=self.outf)

        print('</pogoDsl:PogoSystem>', file=self.outf)

        print(file=self.outf)
