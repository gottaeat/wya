import logging


class ANSIColors:
    RES = "\033[0;39m"

    LBLK = "\033[0;30m"
    LRED = "\033[0;31m"
    LGRN = "\033[0;32m"
    LYEL = "\033[0;33m"
    LBLU = "\033[0;34m"
    LMGN = "\033[0;35m"
    LCYN = "\033[0;36m"
    LWHI = "\033[0;37m"

    BBLK = "\033[1;30m"
    BRED = "\033[1;31m"
    BGRN = "\033[1;32m"
    BYEL = "\033[1;33m"
    BBLU = "\033[1;34m"
    BMGN = "\033[1;35m"
    BCYN = "\033[1;36m"
    BWHI = "\033[1;37m"

    def __init__(self):
        pass


c = ANSIColors()


class WYAFormatter(logging.Formatter):
    _FORMATS = {
        logging.NOTSET: c.LCYN,
        logging.DEBUG: c.BWHI,
        logging.INFO: c.BBLU,
        logging.WARNING: c.LGRN,
        logging.ERROR: c.LRED,
        logging.CRITICAL: c.LRED,
    }

    def format(self, record):
        _fmt = f"{c.BBLK}[{c.BWHI}%(name)s{c.BBLK}]"
        _fmt += f"[{self._FORMATS.get(record.levelno)}"
        _fmt += f"%(levelname)-.1s{c.BBLK}]{c.RES} %(message)s"

        return logging.Formatter(fmt=_fmt, datefmt="%H:%M:%S", validate=True).format(
            record
        )


def set_root_logger(debug=False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = WYAFormatter()

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
