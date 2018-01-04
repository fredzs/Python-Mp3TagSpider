from Entity.Config import Config


class ConfigService(object):
    @staticmethod
    def init():
        ConfigService.read_config("config.txt")

    @staticmethod
    def read_config(config_file_name):
        with open(config_file_name, 'r') as f:
            for line in f:
                line = line.strip('\n')
                key = line[:line.index(' = ')]
                value = line[line.index(' = ') + 3:]
                Config.get_config_field()[key] = value

