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

Install the Synapse Python client before running this script with:

    pip install synapseclient
"""

import argparse
from synapseclient import Synapse, Project


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
    args = parse_arguments()
    syn = Synapse()
    syn.login(args.username, args.password, rememberMe=args.remember)
    entity = syn.get(args.synid, downloadFile=False)
    team = syn.getTeam(args.team)
    syn.setPermissions(entity, team.id, accessType=args.permissions)
    print("Success!")


def parse_arguments() -> argparse.Namespace:
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
    parser.add_argument("--username", help="Synapse username")
    parser.add_argument("--password", help="Synapse password")
    parser.add_argument(
        "--remember", help="Remember Synapse credentials", action="store_true"
    )
    args = parser.parse_args()
    if "NONE" in args.permissions:
        print("NONE was specified, so revoking all permissions")
        args.permissions = []
    return args


if __name__ == "__main__":
    main()
