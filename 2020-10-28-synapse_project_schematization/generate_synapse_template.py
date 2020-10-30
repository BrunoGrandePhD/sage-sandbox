#!/usr/bin/env python3

"""
generate_synapse_template.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script is a proof of concept to demonstrate that a schema graph
can be used to generate a Synapse template. A Synapse template is
defined as a set of files that describe the structure of one of more
Synapse projects, including their contents (e.g. Folders, Tables) and
associated permissions (e.g. using Teams). Some of these files may be
user-configurable to provide values to attributes like entity names.
"""

IMPLEMENTATION_DETAILS = """
Implementation Details
~~~~~~~~~~~~~~~~~~~~~~

For now, the schema graph is generated from a CSV file that lists:

    (1) The general types of Synapse entities (e.g. project, team).
        In object-oriented programming, these would be the classes.
        Once loaded in the graph, these will be referred to as
        "class nodes".

    (2) The specific versions of these Synapse entities required by
        the application at hand. In object-oriented programming,
        these would be the class instances. Once loaded in the graph,
        these will be referred to as "instance nodes". The `Parent`
        column refers to the class being instantiated.

The following Google Sheet describes a simplified version of the HTAN
Synapse structure. A copy of this table is included as a CSV file in
this repository (i.e. htan_synapse_schema.csv).

    https://docs.google.com/spreadsheets/d/1kUKrAZA16o6J0wNKJPQ6Heh8V9gXKhtuAmRQjBsPHvs

At a high level, this script will accomplish the following steps:

    (1) Load the given Synapse schema into a graph representation.

    (2) Order the "instance nodes" based on the appropriate sequence
        of events that need to happen on Synapse. This will involve
        obtaining the child nodes for the "class nodes" in the
        following order:

            Project > Folder > Fileview > Team > ACL > Permissions

    (3) TBD.

This script assembles elements drawn from the following files in the
schematic repository (commit 2b2a29d8):

    - examples/csv_to_schemaorg.py
    - schematic/schemas/examples/explorer_usage.py
"""

import os
import argparse

import pandas as pd

from schematic.schemas.explorer import SchemaExplorer
from schematic.utils.csv_utils import create_schema_classes


def main():
    args = parse_arguments()
    schema = load_schema(args.csv_schema)
    if args.output_graph is not None:
        visualize_graph(schema, args.output_graph)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=IMPLEMENTATION_DETAILS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("csv_schema")
    parser.add_argument("--output_graph")
    args = parser.parse_args()
    return args


def load_schema(csv_filepath):
    schema = SchemaExplorer()
    classes = pd.read_csv(csv_filepath)
    schema = create_schema_classes(classes, schema)
    return schema


def visualize_graph(schema, output_file):
    # Get format from file extension
    file_root, file_ext = os.path.splitext(output_file)
    viz_format = file_ext[1:]  # Remove period
    print(
        f"Using {viz_format} as GraphViz visualization format. Ensure that "
        "it is supported: https://www.graphviz.org/doc/info/output.html"
    )
    # Generate and render GraphViz DiGraph object
    gv_digraph = schema.sub_schema_graph("Synapse", "down")
    gv_digraph.format = viz_format
    gv_digraph.render(file_root)


if __name__ == "__main__":
    main()
