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

Current Challenges
~~~~~~~~~~~~~~~~~~

(1) One of the main tasks for this script is determining the order
    in which the Synapse entities need to be created. Topological
    sorting of a dependency graph is the simplest approach to
    addressing this problem. If I understand correctly, schematic
    organizes attributes as nodes in a graph connected by different
    edge types (e.g. Requires, Properties). To minimize complexity,
    the dependency graph for sorting should be generated using only
    one of the edge types. I propose 'Requires' because it makes
    the most sense for a dependency graph. However, the current
    version of the schema doesn't obey the above creation order.

(2) In the current version of the schema, the 'Requires' attributes
    seem to serve two purposes:

        - To establish the order in which entities should be made.
        - To implicitly set the value of attribute properties.

    For example, the "admin fileview" requires the two center
    projects, which implicitly defines the "scope" property, but
    the admin project should also be a requirement for the
    dependency graph to work. Instead, the fileview is listed as
    a requirement for the admin project. This inconsistency
    makes it impossible to use the 'Requires' graph for sorting.
    On the other hand, including all dependencies in the
    'Requires' field then prevents implicit property definition.
    This latter issue isn't worrisome though because a system
    would be needed to figure out which property was being
    implicitly defined (e.g. "scope" in the above example).

(3) In the current of the schema, some elements are repeated per
    instance and others are not. For example, the center-specific
    projects and teams are repeated, whereas the folders are not.
    I propose that the graph is kept as simple as possible, and
    the properties for different instances (like the name) can be
    defined in another user-configurable YAML file. I envision
    something like this if a node is only meant to exist once:

        ProjectAdmin:
          name: HTAN DCC
        TeamAdmin:
          name: HTAN DCC Team
        AclAdmin:
          access: admin
        AclCenter:
          access: edit
        PermissionsAdmin:
          entity: ProjectAdmin
          acl: AclAdmin
          team: TeamAdmin
        FolderDataTypeX:
          name: Data Type X
        FolderDataTypeY:
          name: Data Type Y

    On the other hand, a node that is meant to exist as multiple
    versions could be defined like this:

        ProjectCenter:
          - name: Center A Data
          - name: Center B Data
          - name: Center C Data
        TeamCenter:
          - name: Center A Team
            members: [bgrande, mnikolov]
          - name: Center B Team
            members: [xengie.doan, thomas.yu]
          - name: Center C Team
            members: [jaeddy, aacebedo]
        PermissionsCenter:
          - entity: Center A Data
            acl: AclCenter
            team: Center A Team
          - entity: Center B Data
            acl: AclCenter
            team: Center B Team
          - entity: Center C Data
            acl: AclCenter
            team: Center C Team

    In the above example, you can see that the entities with
    multiple versions each have three definitions. It seems
    feasible to incorporate logic that these lists are meant
    to be navigated in parallel (à la zip() in Python).

(4) One open question is how to reference other entities being
    created. In the above example, each PermissionsCenter needs
    to reference an entity, an ACL, and a team. The ACL is less
    problematic because it refers to a top-level key. However,
    how should one refer to entities and teams? As placeholders,
    the above example uses the names, but should there be a
    dedicated 'id' key to avoid ambiguity?
"""

import os
import argparse

import pandas as pd
import networkx as nx

from schematic.schemas.explorer import SchemaExplorer
from schematic.schemas.generator import SchemaGenerator
from schematic.utils.csv_utils import create_schema_classes
from schematic.utils.viz_utils import visualize


def main():
    args = parse_arguments()
    graph = load_dependency_graph(args.csv_schema)
    visualize_graph(graph, args.output_graph)
    dependencies = get_dependency_order(graph)
    print(dependencies)


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


def load_dependency_graph(csv_filepath):
    schema = SchemaExplorer()
    classes = pd.read_csv(csv_filepath)
    schema = create_schema_classes(classes, schema)
    schema_nx = schema.get_nx_schema()
    dependency_graph = SchemaGenerator.get_subgraph_by_edge_type(
        schema_nx, schema_nx, "requiresDependency"
    )
    return dependency_graph


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
    return list(sorted_nodes)


def get_dependency_order(graph):
    sorted_nodes = sort_graph_nodes(graph)
    dependencies_first = reversed(sorted_nodes)
    return list(dependencies_first)


if __name__ == "__main__":
    main()
