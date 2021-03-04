"""Configuration proxy
"""

import logging
import os
import json
from typing import Any, Dict, List, Optional, Type
import jsonschema
from jsonpath_ng import parse as jsonpath


logger = logging.getLogger(__name__)


class ConfigProxy:
    env_location: str = "CONFIG_PATH"
    config_file_names: List[str] = ["config.json"]
    current_config: Optional["ConfigProxy"] = None

    def __init__(self, config_path: str):
        self.config_path = config_path
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found in {self.config_path}")
        main_dirname = os.path.abspath(os.path.dirname(__file__))
        schema_path = os.path.join(main_dirname, "config.schema.json")
        with open(self.config_path, "r", encoding="utf-8") as fid:
            self.config: dict = json.load(fid)
        if not os.path.exists(schema_path):
            logger.warning("Configuration schema was not found in %s. Continuing without schema.", schema_path)
            self.schema = {}
            return
        with open(schema_path, "r", encoding="utf-8") as fid:
            self.schema = json.load(fid)
        jsonschema.validate(self.config, self.schema)

    def get_value(self, path: str) -> Any:
        expr = jsonpath(path).find(self.config)
        if not expr:
            return None
        if len(expr) == 1:
            return expr[0].value
        else:
            return [e.value for e in expr]

    @classmethod
    def get_config_path(cls) -> str:
        """Config files are sought in following order:
        1. {env_location} environmental variable specifying path to config file
        2. {config_file_names} in current working directory
        """
        if (config_path := os.getenv(cls.env_location, None)) :
            logger.info("Using config file from env %s=%s", cls.env_location, config_path)
            return config_path
        wd = os.path.abspath(os.path.dirname("./"))
        pd = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        paths = [os.path.join(dirname, fname) for dirname in (wd, pd) for fname in cls.config_file_names]
        for config_path in paths:
            logger.info("Searching for config path in %s", config_path)
            if os.path.exists(config_path):
                return config_path
        raise FileNotFoundError(
            (
                "Configuration file was not found in any of the usual locations. "
                f"Please, use env varibale {cls.env_location} instead."
            )
        )

    @classmethod
    def get_config(cls) -> "ConfigProxy":
        if cls.current_config:
            return cls.current_config
        config_path = cls.get_config_path()
        cls.current_config = cls(config_path)
        return cls.current_config

    @classmethod
    def reload(cls) -> "ConfigProxy":
        cls.current_config = None
        return cls.get_config()


class ConfigProperty:
    path: Optional[str]
    env: Optional[str]
    default: Optional[Any] = None

    def __init__(
        self,
        path: Optional[str] = None,
        env: Optional[str] = None,
        default: Optional[Any] = None,
        proxy: Type[ConfigProxy] = ConfigProxy,
    ):
        self.path = path
        self.env = env
        self.default = default
        self.ProxyType = proxy

    def get_value(self) -> Any:
        if self.env and (value := os.getenv(self.env, None)):
            return value
        config = self.ProxyType.get_config()
        if self.path and (value := config.get_value(self.path)):
            return value
        if self.default is not None:
            return self.default
        return None


class StringProperty(ConfigProperty):
    @property
    def value(self) -> Optional[str]:
        return self.get_value()


class IntProperty(ConfigProperty):
    @property
    def value(self) -> Optional[int]:
        return self.get_value()


class ListOfIntsProperty(ConfigProperty):
    @property
    def value(self) -> List[int]:
        return self.get_value()


class ListOfStringsProperty(ConfigProperty):
    @property
    def value(self) -> List[str]:
        return self.get_value()


class ListOfObjectsProperty(ConfigProperty):
    @property
    def value(self) -> List[Dict]:
        return self.get_value()


class ListOfListsProperty(ConfigProperty):
    @property
    def value(self) -> List[List]:
        return self.get_value()
