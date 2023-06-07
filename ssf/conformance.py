import rdflib
from typing import Optional

from slsparser.shapels import parse
from slsparser.utilities import expand_shape
from unaryquery import to_uq


def conforms(data_graph: rdflib.Graph, shapes_graph: rdflib.graph):
    not_conforms = []
    conforms = []

    schema = parse(shapes_graph)
    shape_defs = schema[0]
    target_defs = schema[1]
    # Reminder: a schema consists out of two dicts
    # Both dicts: IRI (shape name) -> SANode
    # In the first dict, the range is the shape definitions
    # In the second dict, the range is the target definitions if present

    for shape_name in list(shape_defs):
        if shape_name not in list(target_defs):
            continue  # if there is no target definition, skip
        expanded = expand_shape(shape_defs, shape_defs[shape_name])
        shapedef_uq = to_uq(expanded)
        targetdef_uq = to_uq(target_defs[shape_name])

        rhs = _result_to_set(data_graph.query(shapedef_uq))
        lhs = _result_to_set(data_graph.query(targetdef_uq))

        if not lhs.issubset(rhs):
            not_conforms.append(lhs.difference(rhs))
        else:
            conforms.append(lhs)

    return conforms, not_conforms


def _result_to_set(result: rdflib.query.Result) -> set:
    out = set()
    for row in result:
        out.add(row.v)  # v is the SELECT variable
    return out


# Often shapes are written in such a way that it contains redundancies
# "redundancies" are relative to the usage of the shapes. For example:
# in shape fragments "forall p.top" gives us all triples with predicate
# p. However, this shape is trivially satisfied by every node. So it is
# logically equivalent to "true" or "top". The shape fragment for "top"
# is empty. This is a well known property of provenance methods. They 
# rely on the syntax of the expression and not the logical truth 
# semantics. So, we need to be careful. Every application needs to decide
# for themselves how to optimize shapes. In our case, this means that 
# we need different optimizers for the generation of conformance queries
# and for the shape fragment queries.

from slsparser.shapels import SANode

def optimize_conformance(node: SANode) -> Optional[SANode]:
    '''
    This function optimizes the sanode for logical equivalence in the
    sense that trivally true subshapes, as well as redundand subshapes.
    are handled. 
    GOALS:
        - We should try to minimize the use of TOP 
        - We should try to minimize the use of COUNTRANGE 0 X
        - We should try to minimize the use of EQ/DISJ
    RULES:
        - replace NEG TOP with BOT
        - replace FORALL E BOT with BOT
        - replace AND with BOT with BOT
        - remove TOP from AND, if empty, replace with TOP
        - remove identical shapes from AND/OR
        - if AND/OR of one shape, replace with shape
        - replace OR with TOP with TOP
        - replace NOT NOT SANODE with SANODE
        - replace FORALL E TOP with TOP
        - replace countrange "n > 1" None HASVALUE with BOT
    '''
    pass