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
Synapse structure. The most useful sheets are included alonside this
script as CSV files.

    https://docs.google.com/spreadsheets/d/1kUKrAZA16o6J0wNKJPQ6Heh8V9gXKhtuAmRQjBsPHvs

Each sheet in the above Google Sheet has a corresponding page in the
following LucidChart document where the graph is visualized:

    https://lucid.app/invitations/accept/706d589b-9027-4249-945e-5f728fda468d

At a high level, this script will accomplish the following steps:

    (1) Load the given Synapse schema into a graph representation.

    (2) Order the "instance nodes" based on the appropriate sequence
        of events that need to happen on Synapse, namely:

            Project > Folder > Fileview > Team > ACL > Permissions

        This order will be extracted from the dependency graph
        formed by the 'Requires' edges using topological sorting.
        For instance, a folder should require a project, or
        permissions should require a project, a team, and an ACL.

    (3) TBD.

This script assembles elements drawn from the following files in the
schematic repository (commit 2b2a29d8):

    - examples/csv_to_schemaorg.py
    - schematic/schemas/examples/explorer_usage.py
    - schematic/schemas/explorer.py
"""

import os
import argparse
from tempfile import mkstemp

from yaml import dump
import pandas as pd
import networkx as nx

from schematic.schemas.explorer import SchemaExplorer
from schematic.schemas.generator import SchemaGenerator
from schematic.utils.csv_utils import create_nx_schema_objects
from schematic.utils.viz_utils import visualize


def main():
    args = parse_arguments()
    schema = load_schema(args.csv_schema)
    generator = generate_generator(schema)
    dependency_graph = get_dependency_subgraph(generator)
    # visualize_graph(dependency_graph, args.output_graph)
    dependency_order = get_dependency_order(dependency_graph, args.root_node)
    generate_template(schema, dependency_order)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=IMPLEMENTATION_DETAILS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("csv_schema")
    parser.add_argument("--output_graph")
    parser.add_argument("--root_node", default="SynapseStructure")
    args = parser.parse_args()
    return args


def load_schema(csv_filepath):
    schema = SchemaExplorer()
    classes = pd.read_csv(csv_filepath)
    schema = create_nx_schema_objects(classes, schema)
    return schema


def generate_generator(schema):
    generator = SchemaGenerator(schema_explorer=schema)
    return generator


def get_dependency_subgraph(generator):
    schema_nx = generator.se.get_nx_schema()
    dependency_graph = generator.get_subgraph_by_edge_type(
        schema_nx, "requiresDependency"
    )
    return dependency_graph


def get_dependencies(dependency_graph, node):
    dependencies = nx.descendants(dependency_graph, node)
    return dependencies


def visualize_graph(graph, output_file):
    # Skip if no output file is given
    if output_file is None:
        return
    # Get format from file extension
    file_root, file_ext = os.path.splitext(output_file)
    viz_format = file_ext[1:]  # Remove period
    print(
        f"Using '{viz_format}' as GraphViz visualization format. List of "
        "available formats: https://www.graphviz.org/doc/info/output.html"
    )
    # Generate and render GraphViz DiGraph object
    edges = list(graph.edges)
    digraph = visualize(edges)
    digraph.format = viz_format
    digraph.render(file_root)


def sort_graph_nodes(graph):
    sorted_nodes = nx.topological_sort(graph)
    return sorted_nodes


def get_dependency_order(dependency_graph, root_node):
    structure_nodes = get_dependencies(dependency_graph, root_node)
    sorted_nodes = sort_graph_nodes(dependency_graph)
    dependencies_first = reversed(list(sorted_nodes))
    isin_structure = lambda x: x in structure_nodes
    dependencies_first = filter(isin_structure, dependencies_first)
    return dependencies_first


def get_class_attributes(schema, node):
    parent = schema.explore_class(node)["subClassOf"][0]
    properties = schema.explore_class(parent)["properties"][0]["properties"]
    return properties


def generate_template(schema, nodes):
    contents = dict()
    for node in nodes:
        node_attributes = get_class_attributes(schema, node)
        contents[node] = node_attributes
    print(contents)


if __name__ == "__main__":
    main()
