from colorama import *
from datetime import datetime
init()


class Logger():
    _logLevel = 'INFO'
    _logTypes = ['VERBOSE','INFO','WARNING','ERROR','CRITICAL']
    _logColors = {
        'VERBOSE': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED
    }

    @staticmethod
    def log(level, name, message):
        level = level.upper()

        if level not in Logger._logTypes:
            print(Fore.YELLOW + 'Invalid Loglevel')
            print(Style.RESET_ALL)

        print(Logger._logColors[level] + f'[{datetime.now} - {name}] {message}')
        print(Style.RESET_ALL)

    @staticmethod
    def set_log_level(level: str):
        level = level.upper()
        if level in Logger._logTypes:
            Logger._logLevel = level
        else:
            print(Fore.YELLOW + 'Invalid Loglevel')
            print(Style.RESET_ALL)

    @staticmethod
    def verbose(name, message):
        Logger.log('VERBOSE', name, message)

    @staticmethod
    def info(name, message):
        Logger.log('INFO', name, message)

    @staticmethod
    def warn(name, message):
        Logger.log('WARNING', name, message)

    @staticmethod
    def error(name, message):
        Logger.log('ERROR', name, message)

    @staticmethod
    def critical(name, message):
        Logger.log('CRITICAL', name, message)
