# config-proxy

This is a Python module that enables you to setup paths for both json configuration and configuration from env variables.

Readme is TBD...

## Usage

```python
from config_proxy import ConfigProxy as _ConfigProxy, StringProperty

class ConfigProxy(_ConfigProxy):
    env_location = "MY_ENV_WHERE_CONFIG_PATH_WILL_BE_STORED
    config_file_names = ["config.json", "configuration.json", "settings.json", "my-cool-app.json"]

database_host = ConfigProxy.StringProperty(path="database.host", env="DATABASE_HOST", default="localhost")

print(database_host)

# If there is an environmental variable `DATABASE_HOST`, then its value is returned
# If there is a config.json / configuration.json / etc... and it contains {"database": {"host": "<your host>"}}, `<your host>` value is returned
# If neither exists, default `localhost` is returned
```

Please notice that `StringProperty` is a class, thus the CamelCase.
