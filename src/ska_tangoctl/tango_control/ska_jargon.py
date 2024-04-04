"""Short list of jargon encountered."""

GLOSSARY: dict = {
    "cbf": "Correlator Beam Former",
    "csp": "Central Signal Processor",
    "ds": "Device Server",
    "elt": "Element",
    "fs": "Frequency Slice",
    "fsp": "Frequency Slice Processor",
    "lmc": "Local Monitor and Control",
    "lru": "Line Replaceable Unit",
    "odt": "Observation Design Tool",
    "oet": "Observation Execution Tool",
    "oso": "Observatory Science Operations",
    "pdm": "UNKNOWN PDM",
    "pht": "Proposal Handling Tool",
    "pst": "Pulsar timing",
    "pss": "Pulsar Search",
    "ptt": "Project Tracking Tool",
    "scv": "UNKNOWN SCV",
    "sdp": "Science Data Processing",
    "spf": "Single Pixel Feed",
    "spfc": "Single Pixel Feed Controller",
    "spfrx": "Single Pixel Feed Receiver",
    "tm": "Telescope Manager",
    "tmc": "Telescope Monitor and Control",
    "vcc": "Very Coarse Channelizer",
}


def print_jargon() -> None:
    """Print known jargon."""
    for tla in GLOSSARY:
        print(f"{tla.upper():6} : {GLOSSARY[tla]}")


def get_ska_jargon(abbrev: str) -> str:
    """
    Look up an acronym.

    :param abbrev: multi letter acronym
    :return: meaning of acronym
    """
    try:
        rv = f"{GLOSSARY[abbrev.lower()]} ({abbrev.upper()})"
    except KeyError:
        rv = f"UNDEFINED ({abbrev.upper()})"
    return rv


def find_jargon(inp: str) -> str:
    """
    Look for jargon inside a string.

    :param inp: string that potentially contains jargon
    :return: fully expanded acronyms
    """
    rv = ""
    for key in GLOSSARY:
        if key in inp:
            if rv:
                rv += f", {GLOSSARY[key]} ({key.upper()})"
            else:
                rv = f"{GLOSSARY[key]} ({key.upper()})"
        else:
            key2 = f"{key[0].upper}{key[1:]}"
            if key2 in inp:
                if rv:
                    rv += f", {GLOSSARY[key]} ({key.upper()})"
                else:
                    rv = f"{GLOSSARY[key]} ({key.upper()})"
    return rv
