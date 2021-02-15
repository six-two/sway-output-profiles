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
DEFAUTL_STATE_PATH = "/tmp/sway-output-profiles.txt"

# State format:
# If the last action was set: <current profile>
# If the last action was toggle: <current profile>\n<previous profile>

def read_state(config: dict) -> str:
    file_path = config.get("state_path", DEFAUTL_STATE_PATH)
    with open(file_path, "rb") as f:
        return f.read().decode("utf-8")


def write_state(config: dict, state: str) -> None:
    file_path = config.get("state_path", DEFAUTL_STATE_PATH)
    with open(file_path, "wb") as f:
        f.write(state.encode("utf-8"))


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
            # TODO check for \n in name?
            check_field_type(profile, "commands", type(["list", "of", "strings"]))
        return config
    except Exception:
        print("An internal error occurred while parsing your config file. Please check it for errors!\n")
        traceback.print_exc()
        sys.exit(1)


def wrong_usage():
    print("# =========================== Usage ===================================")
    print("# List all possible profiles:")
    print(f"{sys.argv[0]} list")
    print()
    print("# Show the current profile:")
    print(f"{sys.argv[0]} get")
    print()
    print("# Activate a specific profile:")
    print(f"{sys.argv[0]} set <PROFILE_NAME>")
    print()
    print("# Toggle between two profiles:")
    print(f"{sys.argv[0]} toggle <PROFILE_NAME_1> [PROFILE_NAME_2]")
    print("# This will select PROFILE_NAME_1, unless PROFILE_NAME_1 is already active. In that case PROFILE_NAME_2 will be used.")
    print("# If you do not supply PROFILE_NAME_2, the currently active profile will be used as default value (or the previous, if PROFILE_NAME_1 is currently active).")

    sys.exit(1)


def apply_profile(profile_name: str) -> None:
    for profile in config["profiles"]:
        # Find the selected profile
        if profile["name"] == profile_name:
            for command in profile["commands"]:
                subprocess.call([command], shell=True)
            return

    print(f"Error: Unknown profile '{profile_name}'!\n")
    subcommand_list(config)
    sys.exit(1)


def subcommand_list(config: dict) -> None:
    names = [p.get("name") for p in config["profiles"]]
    print(f"The following {len(names)} profile(s) can be used:")
    for name in sorted(names):
        print(f" - {name}")


def subcommand_get(config: dict) -> None:
    state = read_state(config)
    print(state.split("\n")[0])


def subcommand_set(config: dict, profile_name: str) -> None:
    apply_profile(profile_name)
    write_state(config, profile_name)


def subcommand_toggle(config: dict, profile_1: str, profile_2: str = "") -> None:
    state = read_state(config)
    parsed_state = state.split("\n")
    current = parsed_state[0]

    if profile_1 != current:
        # Apply profile 1
        apply_profile(profile_1)
        write_state(config, f"{profile_1}\n{current}")
    else:
        # If necessary look up profile 2 from state
        if not profile_2 and len(parsed_state) > 1:
            profile_2 = parsed_state[1]

        if profile_2:
            # Apply profile 2
            apply_profile(profile_2)
            write_state(config, f"{profile_2}\n{current}")
        else:
            # Toggling to active profile makes no sense
            # so we just do exactly nothing
            pass



if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        wrong_usage()

    config = read_config(CONFIG_PATH)
    
    subcommand = args[0]
    if subcommand == "list":
        if len(args) == 1:
            subcommand_list(config)
        else:
            wrong_usage()
        subcommand_list(config)
    elif subcommand == "get":
        if len(args) == 1:
            subcommand_get(config)
        else:
            wrong_usage()
    elif subcommand == "set":
        if len(args) == 2:
            subcommand_set(config, args[1])
        else:
            wrong_usage()
    elif subcommand == "toggle":
        if len(args) == 2:
            subcommand_toggle(config, args[1])
        elif len(args) == 3:
            subcommand_toggle(config, args[1], args[2])
        else:
            wrong_usage()
    else:
        wrong_usage()