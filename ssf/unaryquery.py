from slsparser.shapels import SANode, Op
from slsparser.pathls import PANode, POp
from rdflib.namespace import SH, URIRef
from typing import List, Optional

from ssf.sparql_conformance import (
    _build_all_query,
    _build_closed_query,
    _build_countrange_query,
    _build_countrange_test_query,
    _build_countrange_top_query,
    _build_disjoint_id_query,
    _build_disjoint_query,
    _build_equality_id_query,
    _build_equality_query,
    _build_exists_hasvalue_query,
    _build_filter_condition,
    _build_forall_query,
    _build_forall_test_query,
    _build_hasvalue_query,
    _build_join,
    _build_lt_query,
    _build_lte_query,
    _build_maxcount_qualified_query,
    _build_maxcount_test_query,
    _build_maxcount_top_query,
    _build_negate,
    _build_not_disjoint_id_query,
    _build_not_disjoint_query,
    _build_not_equality_id_query,
    _build_not_equality_query,
    _build_test_query,
    _build_union,
    _build_uniquelang_query
)

def to_path(node: PANode) -> str:
    """to sparql path"""
    if node.pop == POp.PROP:
        return '<' + str(node.children[0]) + '>'

    if node.pop == POp.INV:
        return '^(' + to_path(node.children[0]) + ')'

    if node.pop == POp.ALT:
        out = ''
        for child in node.children:
            out += to_path(child) + '|'
        return out[:-1]

    if node.pop == POp.COMP:
        out = ''
        for child in node.children:
            out += to_path(child) + '/'
        return out[:-1]

    if node.pop == POp.KLEENE:
        return '(' + to_path(node.children[0]) + ')*'

    if node.pop == POp.ZEROORONE:
        return '(' + to_path(node.children[0]) + ')+'

    return ''

def to_uq(node: SANode) -> str:
    """to unary query; assumes shape is expanded"""
    if node.op == Op.HASSHAPE:
        raise ValueError('node must be expanded')

    if node.op == Op.TOP:
        return _build_all_query()

    if node.op == Op.AND:
        return _build_join([to_uq(child) for child in node.children])

    if node.op == Op.OR:
        return _build_union([to_uq(child) for child in node.children])

    if node.op == Op.NOT:
        child = node.children[0]
        if child.op == Op.TEST:
            return _build_test_query(child.children, negate=True)
        if child.op == Op.EQ:
            if child.children[0].pop == POp.ID:
                return _build_not_equality_id_query(to_path(child.children[1]))
            return _build_not_equality_query(to_path(child.children[0]),
                                             to_path(child.children[1]))
        if child.op == Op.DISJ:
            if child.children[0].pop == POp.ID:
                return _build_not_disjoint_id_query(to_path(child.children[1]))
            return _build_not_disjoint_query(to_path(child.children[0]),
                                             to_path(child.children[1]))

        return _build_negate(to_uq(node.children[0]))

    if node.op == Op.CLOSED:
        properties = []
        for child in node.children:
            properties.append(to_path(child))
        return _build_closed_query(properties)

    if node.op == Op.DISJ:
        if node.children[0] == POp.ID:
            return _build_disjoint_id_query(to_path(node.children[1]))
        return _build_disjoint_query(to_path(node.children[0]),
                                     to_path(node.children[1]))

    if node.op == Op.EQ:
        if node.children[0].pop == POp.ID:
            return _build_equality_id_query(to_path(node.children[1]))
        return _build_equality_query(to_path(node.children[0]),
                                     to_path(node.children[1]))

    if node.op == Op.FORALL:
        if node.children[1].op == Op.TEST:
            return _build_forall_test_query(to_path(node.children[0]), 
                                            _build_filter_condition(node.children[1].children, var = '?o'))
        return _build_forall_query(to_path(node.children[0]), to_uq(node.children[1]))

    if node.op == Op.COUNTRANGE:
        mincount = int(node.children[0])
        maxcount = None if not node.children[1] else node.children[1]
        path = to_path(node.children[2])
        shape = node.children[3]

        # Optimization
        if mincount == 0:
            if shape.op == Op.TEST:
                return _build_maxcount_test_query(maxcount, path, 
                                                _build_filter_condition(shape.children))
            if shape.op == Op.TOP:
                return _build_maxcount_top_query(maxcount, path)
            return _build_maxcount_qualified_query(maxcount, path, to_uq(shape))

        if mincount == 1 and shape.op == Op.HASVALUE:
            value = shape.children[0]
            str_value = str(value)
            if isinstance(value, URIRef):
                str_value = f'<{str_value}>'
            return _build_exists_hasvalue_query(path, str_value)

        if shape.op == Op.TEST:
            return _build_countrange_test_query(mincount, maxcount, path, 
                                                _build_filter_condition(shape.children, var='?o'))

        if shape.op == Op.TOP:
            return _build_countrange_top_query(mincount, maxcount, path)
        
        return _build_countrange_query(mincount, maxcount, path, to_uq(shape))

    if node.op == Op.LESSTHAN:
        return _build_lt_query(to_path(node.children[0]),
                               to_path(node.children[1]))

    if node.op == Op.LESSTHANEQ:
        return _build_lte_query(to_path(node.children[0]),
                                to_path(node.children[1]))

    if node.op == Op.HASVALUE:
        return _build_hasvalue_query(node.children[0])

    if node.op == Op.UNIQUELANG:
        return _build_uniquelang_query(to_path(node.children[0]))

    if node.op == Op.TEST:
        return _build_test_query(node.children)

    raise ValueError(f'Unknown Op encountered: {node.op}')