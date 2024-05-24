from configparser import ConfigParser

class Utils:
    @staticmethod
    def read_config(filename, section):
        parser = ConfigParser()
        parser.read(filename)

        settings = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                settings[param[0]] = param[1]
        else:
            raise Exception(f'Section {section} not found in the {filename} file')

        return settings
