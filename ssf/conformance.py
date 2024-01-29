import rdflib
from typing import Optional

from slsparser.shapels import parse
from slsparser.utilities import expand_shape
from ssf.unaryquery import to_uq

def conforms(data_graph: rdflib.Graph, shapes_graph: rdflib.Graph):
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
from slsparser.shapels import Op

def optimize_conformance(node: SANode) -> Optional[SANode]:
    '''
    This function optimizes the sanode for logical equivalence in the
    sense that trivally true subshapes, as well as redundand subshapes,
    are handled. 
    GOALS:
        - We should try to minimize the use of TOP 
        - We should try to minimize the use of COUNTRANGE 0 X
        - We should try to minimize the use of EQ/DISJ
    RULES:
        - replace NEG TOP with BOT
        - replace AND with BOT with BOT
        - remove TOP from AND, if empty, replace with TOP
        - remove identical shapes from AND/OR
        - if AND/OR of one shape, replace with shape
        - replace OR with TOP with TOP
        - replace NOT NOT SANODE with SANODE
        - replace FORALL E TOP with TOP
        - replace countrange "n > 1" None HASVALUE with BOT
    '''

    new_children = []
    for child in node.children:
        if isinstance(child, SANode):
            new_child = optimize_conformance(child)
            if new_child:
                new_children.append(new_child)
        else:
            new_children.append(child)

    node.children = new_children

    if node.op == Op.NOT and node.children[0] == Op.TOP:
        return SANode(Op.BOT, [])
    
    if node.op == Op.NOT and node.children[0] == Op.BOT:
        return SANode(Op.TOP, [])
    
    if node.op == Op.AND and any(map(lambda c: c.op == Op.BOT, node.children)):
        return SANode(Op.BOT, [])
    
    if node.op == Op.OR and any(map(lambda c: c.op == Op.TOP, node.children)):
        return SANode(Op.TOP, [])
    
    if node.op == Op.AND and any(map(lambda c: c.op == Op.TOP, node.children)):
        node.children = list(filter(lambda c: c.op != Op.TOP, node.children))
        if len(node.children) == 1:
            return node.children[1]
        elif len(node.children) == 0:
            return SANode(Op.TOP, [])
        return node
        
    if node.op == Op.OR and any(map(lambda c: c.op == Op.BOT, node.children)):
        node.children = list(filter(lambda c: c.op != Op.BOT, node.children))
        if len(node.children) == 1:
            return node.children[1]
        elif len(node.children) == 0:
            return SANode(Op.BOT, [])
        return node
    
    if node.op == Op.NOT:
        numnot = _count_not_depth(node)
        child = _get_first_shape_from_not(node)
        if numnot % 2 == 0:
            return child
        return SANode(Op.NOT, child)
    
    if node.op == Op.FORALL and node.children[1].op == Op.TOP:
        return SANode(Op.TOP, [])
    
    return node
    

def _count_not_depth(node: SANode) -> int:
    if node.op != Op.NOT:
        return 0
    return _count_not_depth(node.child[0]) + 1


def _get_first_shape_from_not(node: SANode) -> SANode:
    if node.op != Op.NOT:
        return node
    return _get_first_shape_from_not(node.child[0])