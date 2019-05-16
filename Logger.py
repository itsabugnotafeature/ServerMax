class LogLevel:
    HALT = 0
    ERROR = 1 << 0
    WARNING = 1 << 1
    NOTICE = 1 << 2
    PLAIN = 1 << 3

_level = LogLevel.WARNING
_default_level = _level

def log(message, level=None):
    message = repr(message)

    if level is None:
        level = default_level

    if level <= _level:
        if level == LogLevel.HALT:
            raise RuntimeError(message)
        elif level == LogLevel.ERROR:
            print(f"\033[38;5;1mERROR: {message}\033[0m")
        elif level == LogLevel.WARNING:
            print(f"\033[38;5;208mWARNING: {message}\033[0m")
        elif level == LogLevel.NOTICE:
            print(f"\033[38;5;226mNOTICE: {message}\033[0m")
        elif level == LogLevel.PLAIN:
            print(f"\033[0m{message}\033[0m")
        else:
            log(f"Invalid logging level: {repr(level)}", LogLevel.HALT)

def set_log_level(new_level):
    _level = new_level

def set_default_level(level):
    default_level = level
