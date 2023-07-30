"""
MIT License

Copyright (c) 2023 Jean-Paul Gavini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import time
import utils
import yaml
from typing import Any
import os
import re
import json
import voluptuous as vol
import mappers
import prompters

TS_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_TIMEOUT = 30


def cls():
    # print("\033[37;44m")
    print("\033[40m", end="")
    print("\033[2J", end="")


def printif(key: str, list: dict) -> None:
    if key in list:
        print(f"{key}: {list[key]}")


def tprint(*args: list) -> None:
    print(time.strftime(TS_FORMAT), *args)


def bip(n: int = 3):
    for i in range(n):
        print("\a")
        # time.sleep(0.1)


def error(s: str) -> None:
    print(f"\033[0;31m[{time.strftime(TS_FORMAT)}][ERROR]___{s}\033[0m")


def fatal(s: str) -> None:
    print(f"\033[1;31m[{time.strftime(TS_FORMAT)}][FATAL]___{s}\033[0m")


def warning(s: str) -> None:
    print(f"\033[0;33m[{time.strftime(TS_FORMAT)}][WARNING]_{s}\033[0m")


def success(s: str) -> None:
    print(f"\033[0;32m[{time.strftime(TS_FORMAT)}][SUCCESS]_{s}\033[0m")


def info(s: str, header=True) -> None:
    if header:
        print(f"\033[0;34m[{time.strftime(TS_FORMAT)}][INFO]____{s}\033[0m")
    else:
        for line in s.split("\n"):
            print(f"\033[1;34m{line}\033[0m")


def head(s: str, header=True) -> None:
    if header:
        print(f"\033[1;34m[{time.strftime(TS_FORMAT)}][INFO]____{s}\033[0m")


def debug(s: str) -> None:
    print(f"\033[0;90m[{time.strftime(TS_FORMAT)}][DEBUG]____{s}\033[0m")


def alert(s: str) -> None:
    print(f"\033[1;35m[{time.strftime(TS_FORMAT)}][ALERT]___{s}\033[0m")


def achievement(s: str) -> None:
    print(f"\033[1;32m[{time.strftime(TS_FORMAT)}][SUCCESS]_{s}\033[0m")


def load_config(config_file_name: str) -> Any:
    ip_address_regex = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    config = None

    def validate_default_target(value):
        if value not in config["targets"]:
            raise vol.Invalid(f"Invalid value '{value}' (not found in targets list)")
        return value

    def validate_envkey(value):
        envkey = os.getenv(value)
        if not envkey:
            raise vol.Invalid(f"Environment variable {value} not set")
        else:
            return value

    def validate_mapper(value):
        # Check if the function name exists in the "mappers" module and is callable
        if hasattr(mappers, value) and callable(getattr(mappers, value)):
            return value
        else:
            raise vol.Invalid(f"Function 'mappers.{value}' not found or not callable")

    def validate_prompter(value):
        # Check if the function name exists in the "prompters" module and is callable
        if hasattr(prompters, value) and callable(getattr(prompters, value)):
            return value
        else:
            raise vol.Invalid(f"Function 'prompters.{value}' not found or not callable")

    def validate_template(value):
        # Check if the template name exists in the config templates list
        if config["templates"].get(value):
            return value
        else:
            raise vol.Invalid(f"Template '{value}' not found in templates list")

    try:
        with open(config_file_name) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except IOError as e:
        utils.error(f"Can't load configuration file: {config_file_name}")
        utils.error(f"Cause : {e}")
        exit(1)

    # Define the config schema

    mapping_schema = vol.Schema(
        {
            vol.Optional("path"): str,
            vol.Optional("in"): vol.All(str, validate_mapper),
            vol.Optional("out"): vol.All(str, validate_mapper),
            vol.Optional("prompter"): vol.All(str, validate_prompter),
            vol.Optional("template"): vol.All(str, validate_template),
            # vol.Optional(str): str,
        }
    )

    schema = vol.Schema(
        {
            vol.Optional("system", default={}): {
                vol.Optional("ssl", default=False): bool,
                vol.Optional("debug", default=False): bool,
                vol.Optional("port", default=8000): int,
                vol.Optional("timeout", default=DEFAULT_TIMEOUT): vol.Any(float, int),
                vol.Optional("masterkey"): str,
            },
            vol.Optional("cerbere", default={}): {
                vol.Optional("max_tries", default=3): int,
                vol.Optional("whitelist", default=[]): [vol.Match(ip_address_regex)],
                vol.Optional("blacklist", default=[]): [vol.Match(ip_address_regex)],
            },
            vol.Required("targets"): {
                vol.Required("default"): vol.All(str, validate_default_target),
                vol.Required(str): {
                    vol.Required("url"): str,
                    vol.Optional("envkey"): vol.All(str, validate_envkey),
                    vol.Optional("key"): str,
                    vol.Optional("preserveMethod", default=False): bool,
                    vol.Required("mapping"): {
                        vol.Required(str): vol.Any(mapping_schema, None)
                    },
                },
            },
            vol.Optional("templates"): {
                vol.Optional(str): {
                    vol.Required("preprompt", default=""): str,
                    vol.Optional("start", default=""): str,
                    vol.Optional("system", default=""): str,
                    vol.Optional("user", default=""): str,
                    vol.Optional("assistant", default=""): str,
                }
            },
        }
    )

    # Validate the config
    try:
        config = schema(config)
        utils.success("Config file successfully read and validated.")
    except vol.MultipleInvalid as e:
        utils.fatal("Config file validation failed:")
        for error in e.errors:
            utils.error(f"- {error}")
        exit(1)

    # Enrich the validated config
    # First, add the master proxy key
    if "masterkey" in config["system"]:
        utils.alert(
            "Master key found in config file. This is a security risk that is not recommended."
        )
        utils.alert(
            "Please consider removing the master key from the config file and use the environment variable MOOLTIPROXY_KEY instead."
        )
        config["masterkey"] = config["system"]["masterkey"]
    else:
        master_key = os.getenv("MOOLTIPROXY_KEY")
        if not master_key:
            utils.fatal("Environment variable MOOLTIPROXY_KEY not set.")
            utils.fatal(
                "For obvious security reasons, you MUST define this variable before running the proxy."
            )
            exit(1)
        else:
            config["masterkey"] = master_key

    # Then populate the key field from the environment based on the envkey field, if any
    for target in config["targets"]:
        if "key" in config["targets"][target]:
            utils.error(
                f"Key found in config file for target {target}. This is a security risk that is not recommended."
            )
            utils.error(
                f"Please consider removing the key from the config file and use the 'envkey' directive instead."
            )

        if "envkey" in config["targets"][target] and (
            not "key" in config["targets"][target]
            or not config["targets"][target]["key"]
        ):
            config["targets"][target]["key"] = os.getenv(
                config["targets"][target]["envkey"]
            )

    # Then instanciate prompts templates at the endpoint level, to avoid having to pass it at runtime
    for targetname in config["targets"]:
        # skip the default target
        if targetname == "default":
            continue
        targetmapping = config["targets"][targetname].get("mapping", {})
        for endpointname in targetmapping:
            endpointconfig = targetmapping[endpointname]
            if endpointconfig and type(endpointconfig) is dict:
                templatename = endpointconfig.get("template", None)
                if templatename:
                    config["targets"][targetname]["mapping"][endpointname][
                        "template"
                    ] = config["templates"][templatename] | {
                        "template_name": templatename
                    }

    return config
