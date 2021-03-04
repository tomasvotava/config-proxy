# config-proxy

This is a Python module that enables you to setup paths for both json configuration and configuration from env variables.

It automatically looks into environmental variables and either uses its value, or looks it up in json configuration file or falls back to default.

## Install

Either clone from this repository or use `pip` / `poetry` like so:

### Via `pip`

```console
pip install config-proxy
```

### Using `poetry`

```console
poetry add config-proxy
```

## Usage

### Basic usage

If your configuration file is either called `config.json` and is expected in the current working directory or its location is set using `CONFIG_PATH` environmental variable, the usage is fairly easy:

#### `config.json`

```json
{
  "database": {
    "host": "mydbhost.databases.com"
  }
}
```

#### `main.py`

```python
from config_proxy import StringProperty

database_host = StringProperty(path="database.host", env="DATABASE_HOST", default="localhost")

print(database_host.value)
```

```bash
$ python main.py
mydbhost.databases.com

$ DATABASE_HOST="overridden.database.com" python main.py
overridden.database.com
```

### Advanced usage

If you want to specify configuration file path and customize env variable that stores the path, you have to extend the `ConfigProxy` class and overload attributes you wish to change.

#### `my-special-config.json`

```json
{
    "database": {
        "host": "mydbhost.databases.com"
    }
}
```

#### `custom.py`

```python
from config_proxy import ConfigProxy as _ConfigProxy, StringProperty

class ConfigProxy(_ConfigProxy):
    env_location = "ENV_VARIABLE_THAT_CONTAINS_MY_CONFIG_PATH"
    config_file_names = ["my-special-config.json"]

```

**Please note**, that `StringProperty` now does not know it should use your subclass instead, do not forget to specify it when creating the property:

```python
database_host = StringProperty(path="database.host", env="DATABASE_HOST", default="localhost", proxy=ConfigProxy)

print(database_host.value)
```

If you want to specify a custom config file, you can use:

```bash
$ ENV_VARIABLE_THAT_CONTAINS_MY_CONFIG_PATH="/actual/path/to/my/config.json" python custom.py
mydbhost.databases.com
```
