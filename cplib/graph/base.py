#!/usr/bin/env python3

"""Base type definitions for graph algorithms.

This module defines common types used throughout the graph package
to provide type safety and clarity in graph algorithm implementations.
"""

from typing import NewType


Node = NewType('Node', int)
"""Node identifier type.

Represents a vertex in a graph. Internally stored as an integer
but provides type safety to distinguish from other integer values.

Examples:
    >>> node1 = Node(0)
    >>> node2 = Node(1)
    >>> # Type checker will ensure nodes are used correctly
"""

Edge = NewType('Edge', tuple[Node, Node])
"""Edge type representing a connection between two nodes.

An edge is defined as a tuple of two Node objects representing
the endpoints of the edge. For directed graphs, the order matters
(first node is source, second is target).

Examples:
    >>> edge = Edge((Node(0), Node(1)))
    >>> source, target = edge
"""

EdgeNum = NewType('EdgeNum', int)
"""Edge number/identifier type.

Used to uniquely identify edges in a graph, particularly useful
for algorithms that need to reference specific edges by index.

Examples:
    >>> edge_id = EdgeNum(0)
    >>> # First edge in the edge list
"""

Weight = NewType('Weight', int)
"""Edge weight type.

Represents the weight or cost associated with an edge in weighted graphs.
Internally an integer but provides type safety for weight calculations.

Examples:
    >>> weight = Weight(10)
    >>> total_cost = Weight(weight + Weight(5))  # Weight(15)
"""

Capacity = NewType('Capacity', int)
"""Edge capacity type.

Represents the maximum flow that an edge can carry in flow networks.

Examples:
    >>> capacity = Capacity(100)
    >>> # Edge can carry up to 100 units of flow
"""

Cost = NewType('Cost', int)
"""Edge cost type.

Represents the cost associated with using an edge in flow networks.

Examples:
    >>> cost = Cost(5)
    >>> # Using this edge incurs a cost of 5 units
"""
