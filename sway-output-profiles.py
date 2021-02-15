#!/usr/bin/env python3

from typing import Dict
import os
import subprocess
import sys
import traceback
# External libraries
import yaml

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# Configure me here
CONFIG_PATH = os.path.join(SCRIPT_DIR, "profiles.yaml")


def check_field_type(obj: dict, field_name: str, expected_type: type) -> None:
    field = obj.get(field_name)
    if field:
        if type(field) != expected_type:
            raise Exception(f"Invalid field type for '{field_name}': Expected {expected_type} but got {type(field)}. Raw data: {obj}")
    else:
        raise Exception(f"Missing field: '{field_name}'. Raw data: {obj}")
    

def read_config(path: str) -> Dict:
    with open(path, "rb") as f:
        file_text = f.read().decode("utf-8")
    try:
        config = yaml.safe_load(file_text)
        # Do some checks on the config. They are far from exhaustive
        check_field_type(config, "profiles", type([{"list": "of objects"}]))
        profiles = config.get("profiles")
        for profile in profiles:
            check_field_type(profile, "name", type("string"))
            check_field_type(profile, "commands", type(["list", "of", "strings"]))
        return config
    except Exception:
        print("An internal error occurred while parsing your config file. Please check it for errors!\n")
        traceback.print_exc()
        sys.exit(1)


def wrong_usage():
    print("# To set the profile to a specific value, use this command:")
    print(f"{sys.argv[0]} set <PROFILE_NAME>")
    print()
    print("# To toggle between two profiles, use this command:")
    print(f"{sys.argv[0]} toggle <PROFILE_NAME_1> [PROFILE_NAME_2]")
    print("# This will select PROFILE_NAME_1, unless PROFILE_NAME_1 is already active. In that case PROFILE_NAME_2 will be used.")
    print("# If you do not supply PROFILE_NAME_2, the currently active profile will be used as default value (or the previous, if PROFILE_NAME_1 is currently active).")
    print()
    print("# To list all possible profiles use this command:")
    print(f"{sys.argv[0]} list")

    sys.exit(1)


def subcommand_list(config: dict) -> None:
    names = [p.get("name") for p in config["profiles"]]
    print(f"The following {len(names)} profile(s) can be used:")
    for name in sorted(names):
        print(f" - {name}")


def subcommand_set(config: dict, profile_name: str) -> None:
    for profile in config["profiles"]:
        # Find the selected profile
        if profile["name"] == profile_name:
            for command in profile["commands"]:
                subprocess.call([command], shell=True)
            # TODO write name to file

    print(f"Error: Unknown profile '{profile_name}'!\n")
    subcommand_list(config)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        wrong_usage()

    config = read_config(CONFIG_PATH)
    
    subcommand = args[0]
    if subcommand == "list":
        subcommand_list(config)
    elif subcommand == "set":
        if len(args) == 2:
            subcommand_set(config, args[1])
        else:
            wrong_usage()