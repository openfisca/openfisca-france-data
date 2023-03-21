"""Configuration file parser."""

import configparser
from pathlib import Path, PurePath
from xdg import BaseDirectory


default_config_files_directory = Path(BaseDirectory.save_config_path('openfisca-france-data'))


class Config(configparser.SafeConfigParser):
    """Custom Config Parser."""

    config_ini = None

    def __init__(self, config_files_directory = default_config_files_directory):
        configparser.SafeConfigParser.__init__(self)
        assert config_files_directory is not None

        config_ini = PurePath.joinpath(config_files_directory, 'config.ini')
        if Path.exists(config_ini):
            self.config_ini = config_ini
        self.read([config_ini])

    def save(self):
        """Save config to home user config for package openfisca-france-data."""
        assert self.config_ini, "configuration file paths are not defined"
        config_file = open(self.config_ini, 'w')
        self.write(config_file)
        config_file.close()


config = Config()
