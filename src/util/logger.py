import datetime
import os

colors = {
    'VERB': ['\x1b[34m', '\x1b[0m'],
    'INFO': ['\x1b[32m', '\x1b[0m'],
    'WARN': ['\x1b[33m', '\x1b[0m'],
    'ERR': ['\x1b[31m', '\x1b[0m'],
    'CRIT': ['\x1b[31m', '\x1b[0m']
}

class Log():
    log_group = 'UNKNOWN'
    log_level = 'INFO'

    # fallback to old method
    def __init__(self, *args):
        Log._log(*args)

    @staticmethod
    def _log(name, level, message, show_time = True):
        level_types = ['VERB', 'INFO', 'WARN', 'ERR', 'CRIT']

        if level not in level_types:
            print('Invalid error logging level, please use one of the following:', level_types)
            return

        if level_types.index(level) < level_types.index(Log.log_level):
            return

        log = ''
        color = ('', '')

        if show_time:
            currentDate = datetime.datetime.now()
            log = f'[{currentDate.strftime("%H:%M:%S")}] '

            color = colors[level]

        print(f'{log}{color[0]}[{name:<5s}/{level:>5s}]{color[1]} {message}')

        with open(f'./logs/{Log.log_group}/{level.lower()}_{currentDate.strftime("%Y-%m-%d")}.log', 'a') as f:
            f.write(f'{log}[{name}/{level}] {message}\n')

    @staticmethod
    def verbose(name, message, show_time = True):
        Log._log(name, 'VERB', message, show_time)

    @staticmethod
    def info(name, message, show_time = True):
        Log._log(name, 'INFO', message, show_time)

    @staticmethod
    def warning(name, message, show_time = True):
        Log._log(name, 'WARN', message, show_time)

    @staticmethod
    def error(name, message, show_time = True):
        Log._log(name, 'ERR', message, show_time)

    @staticmethod
    def critical(name, message, show_time = True):
        Log._log(name, 'CRIT', message, show_time)

    @staticmethod
    def set_log_group(name):
        Log.log_group = name

        try:
            os.mkdir(f'./logs/{name}/')
        except FileExistsError:
            pass
