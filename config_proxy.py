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
    """Proxy to your configuration. It loads json file,
    checks it against json schema (if found) and provides
    an easy way of accessing json keys using JSON path.

    If you need to change any of the class' settings,
    you should create a subclass.

    E.g. here we change environmental variable that contains
    our config file path to `PATH_TO_CONFIG` and default name
    of the configuration file to `settings.json`:

    ```python
    from config_proxy import ConfigProxy as _ConfigProxy

    class ConfigProxy(_ConfigProxy):
        env_location = "PATH_TO_CONFIG"
        config_file_names = ["settings.json"]
    ```

    If you create a subclass, do not forget to actually pass
    it to all of your properties:

    ```python
    property = StringProperty(..., proxy=MyConfigProxySubclass)
    ```
    """

    env_location: str = "CONFIG_PATH"
    config_file_names: List[str] = ["config.json"]
    current_config: Optional["ConfigProxy"] = None
    strict: bool = True

    def __init__(self, config_path: Optional[str]):
        """Class constructor. You are not supposed to actually create
        an instance of this class, instead you should use *Property classes
        or use `get_config` static method.

        Arguments:
            config_path {str} -- An actual path to json configuration file

        Raises:
            FileNotFoundError: Specified configuration file was not found.
        """
        self.config_path = config_path
        if self.config_path is None:
            if not self.strict:
                self.config = {}
                self.schema = {}
                return
            raise FileNotFoundError("Config file was not found")
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

    def get_value(self, path: str, use_list: Optional[bool] = None) -> Any:
        """Return value from json config file using JSON path.

        Arguments:
            path {str} -- A JSON path valid string.
        """
        expr = jsonpath(path).find(self.config)
        if not expr:
            return [] if use_list else None
        if use_list:
            return [e.value for e in expr]
        elif use_list == False:
            return expr[0].value
        # Guess whether to return list or not by default
        if len(expr) == 1:
            return expr[0].value
        else:
            return [e.value for e in expr]

    @classmethod
    def get_config_path(cls) -> str:
        """Config files are sought in following order:

        1. `env_location` environmental variable specifying path to config file

        2. `config_file_names` in current working directory
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
        """Creates an instance of `ConfigProxy`, while actually searching for
        the correct config file. If this method already was called, existing
        configuration is returned.
        """
        if cls.current_config:
            return cls.current_config
        try:
            config_path = cls.get_config_path()
        except FileNotFoundError as error:
            if cls.strict:
                raise error
            config_path = None
        cls.current_config = cls(config_path)
        return cls.current_config

    @classmethod
    def reload(cls) -> "ConfigProxy":
        """Same as `get_config` but ensures that the configuration file is
        read again if it already was opened before.
        """
        cls.current_config = None
        return cls.get_config()


class ConfigProperty:
    """A base class for access properties of the configuration
    file (and / or environmental variables).

    Various subclasses are provided in order to make the most use of
    Python's typehinting and making your IDE actually autocomplete
    your config values' types. If you do not need this functionality,
    you are free to use this base class instead of actual subclasses.

    Example:


    ### Config file

    ```json
    {
        "database": {
            "host": "mydb.host.com",
            "port": 1234
        }
    }
    ```

    ### Python file

    ```python
    from config_proxy import ConfigProperty, StringProperty, IntProperty

    # Here we get autocomplete because we know the result will be `str` and `int` respectively:
    host = StringProperty("database.host", "DB_HOST", "localhost")
    port = IntProperty("database.port", "DB_PORT", 5432)

    # Here we have no autocomplete because we used base class instead of typed subclasses:
    password = ConfigProperty("database.password", "DB_PASSWORD")
    ```
    """

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

    def get_value(self, use_list: Optional[bool] = None, forced: Optional[bool] = None) -> Any:
        if self.env and (value := os.getenv(self.env, None)):
            return value
        config = self.ProxyType.get_config()
        if self.path and (value := config.get_value(self.path, use_list=use_list)):
            return value
        if self.default is not None:
            return self.default
        if forced:
            raise ValueError(f"Property {self.env} / {self.path} has no value")
        return [] if use_list else None

    @property
    def value(self) -> Optional[str]:
        """Returns value found either in env, config file or default"""
        return self.get_value()

    @property
    def fvalue(self) -> str:
        """Returns value. If the value is not present in either env or config file, ValueError is raised."""
        return self.get_value(forced=True)


class StringProperty(ConfigProperty):
    """See `ConfigProperty` for more."""

    @property
    def value(self) -> Optional[str]:
        return self.get_value(use_list=False)

    @property
    def fvalue(self) -> str:
        return self.get_value(use_list=False, forced=True)


class IntProperty(ConfigProperty):
    """See `ConfigProperty` for more."""

    @property
    def value(self) -> Optional[int]:
        return self.get_value(use_list=False)

    @property
    def fvalue(self) -> int:
        return self.get_value(use_list=False, forced=True)


class ListOfIntsProperty(ConfigProperty):
    """See `ConfigProperty` for more."""

    @property
    def value(self) -> List[int]:
        return self.get_value(use_list=True)


class ListOfStringsProperty(ConfigProperty):
    """See `ConfigProperty` for more."""

    @property
    def value(self) -> List[str]:
        return self.get_value(use_list=True)


class ListOfObjectsProperty(ConfigProperty):
    """See `ConfigProperty` for more."""

    @property
    def value(self) -> List[Dict]:
        return self.get_value(use_list=True)


class ListOfListsProperty(ConfigProperty):
    """See `ConfigProperty` for more."""

    @property
    def value(self) -> List[List]:
        return self.get_value(use_list=True)
