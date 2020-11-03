#!/usr/bin/env python3

"""
assign_permissions.py
~~~~~~~~~~~~~~~~~~~~~
This script assigns the specified permissions to the given team for
a given Synapse entity, which is typically a project or folder. The
entity is assumed to already exist. If you provide a team name, use
quotes if the name contains spaces. These commands are equivalent:

    python assign_permissions.py syn22916037 "Bruno - Test Team" READ CREATE
    python assign_permissions.py syn22916037 3415192 READ CREATE

If you wanted to revoke all permissions, the command would look like:

    python assign_permissions.py syn22916037 3415192 NONE

While command-line arguments are offered to provide your Synapse
credentials, the preferred method for authentication is to create
the '.synapseConfig' file in your home directory as per:

    https://python-docs.synapse.org/build/html/Credentials.html

This script required Python version 3.6 or later. You must also
install the Synapse Python client using:

    pip install synapseclient
"""

import json
import argparse
from synapseclient import Synapse, Project


VERBOSE = False
PERMISSIONS = (
    "CREATE",
    "READ",
    "UPDATE",
    "DELETE",
    "CHANGE_PERMISSIONS",
    "DOWNLOAD",
    "NONE",
)


def main():
    # Parse command-line arguments
    args = parse_arguments()
    # Set up Synapse
    syn = Synapse()
    syn.login(args.username, args.password, rememberMe=args.remember)
    # Retrieve Synapse entity (e.g., project, folder)
    entity = syn.get(args.synid, downloadFile=False)
    log("Entity", entity)
    # Retrieve team
    team = syn.getTeam(args.team)  # TODO: Handle users with try-catch
    log("Team", team)
    # Assign specified permissions for given entity and team
    permissions = syn.setPermissions(entity, team.id, accessType=args.permissions)
    log("Permissions", permissions)
    # Celebrate
    print("Success!")


def parse_arguments() -> argparse.Namespace:

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("synid", help="ID of Synapse entity (synXXXXXXXX)")
    parser.add_argument("team", help="Name or integer ID of Synapse team")
    parser.add_argument(
        "permissions",
        nargs="+",
        choices=PERMISSIONS,
        metavar="PERMISSION",
        help="List of permissions or NONE",
    )
    parser.add_argument("--username", "-u", help="Synapse username")
    parser.add_argument("--password", "-p", help="Synapse password")
    parser.add_argument(
        "--remember", "-r", help="Remember Synapse credentials", action="store_true"
    )
    parser.add_argument(
        "--verbose", "-v", help="Display more information", action="store_true"
    )
    args = parser.parse_args()

    # Process arguments
    if "NONE" in args.permissions:
        print("NONE was specified, so revoking all permissions")
        args.permissions = []

    global VERBOSE
    VERBOSE = args.verbose

    return args


def log(name, obj):
    # Skip if not verbose
    if not VERBOSE:
        return
    # Convert to dictionary (if possible) to leverage json.dumps()
    if getattr(obj, "__dict__", None) is not None:
        obj = vars(obj)
    # Format object as string based on type
    if isinstance(obj, dict):
        obj = json.dumps(obj, indent=4, sort_keys=True)
    else:
        obj = str(obj)
    # Print object string
    print(f"{name}: {obj}", end="\n\n")


if __name__ == "__main__":
    main()
