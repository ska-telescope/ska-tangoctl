"""Display progress bar in a terminal."""

import sys
from typing import Any, TextIO


def progress_bar(
    iterable: list | dict,
    show: bool,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 100,
    fill: str = "*",
    print_end: str = "\r",
    outf: TextIO = sys.stderr,
) -> Any:
    r"""
    Call this in a loop to create a terminal progress bar.

    :param iterable: Required - iterable object (Iterable)
    :param show: print the actual thing
    :param prefix: prefix string
    :param suffix: suffix string
    :param decimals: positive number of decimals in percent complete
    :param length: character length of bar
    :param fill: fill character for bar
    :param print_end: end character (e.g. "\r", "\r\n")
    :param outf: output file handle, stdout or stderr
    :yields: the next one in line
    """

    def print_progress_bar(iteration: Any) -> None:
        """
        Progress bar printing function.

        :param iteration: the thing
        """
        percent: str
        filled_length: int
        bar: str

        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + "-" * (length - filled_length)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=print_end, file=outf)

    total: int
    i: Any
    item: Any

    if show:
        total = len(iterable)
        # Do not divide by zero
        if total == 0:
            total = 1
        # Initialize
        print_progress_bar(0)
        # Update progress bar
        for i, item in enumerate(iterable):
            yield item
            print_progress_bar(i + 1)
        # Erase line when done
        outf.write("\033[K")
        outf.flush()
    else:
        # Nothing to see here
        for i, item in enumerate(iterable):
            yield item
