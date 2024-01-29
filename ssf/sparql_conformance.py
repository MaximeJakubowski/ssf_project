from typing import List, Optional

from rdflib import SH

## GENERAL

def _build_query(body: str) -> str:
    return f'SELECT ?v WHERE {{ {body} }}'

## TOP

def _build_all_query() -> str:
    return _build_query('{ ?v ?_a ?_b. } UNION { ?_c ?_d ?v }')

## AND

def _build_join(queries: List[str]) -> str:
    out = ''
    for query in queries:
        out += f'{{ {query} }} . '
    return _build_query(out[:-2])

## OR

def _build_union(queries: List[str]) -> str:
    out = ''
    for query in queries:
        out += f'{{ {query} }} UNION '
    return _build_query(out[:-6])

## NOT

def _build_negate(shape: str) -> str:
    return _build_query(f'{{ {_build_all_query()} }} MINUS {{ {shape} }}')

## CLOSED

def _build_closed_query(properties: List[str]) -> str:
    propstr = ''
    for prop in properties:
        propstr += prop + ', '
    return _build_negate(f'?v ?p ?o FILTER (?p NOT IN ( {propstr[:-2]} ))')

## DISJOINT

def _build_disjoint_query(path1: str, path2: str) -> str:
    '''N_G minus v {p1} o . v {p2} o'''
    return _build_negate(_build_not_disjoint_query(path1, path2))

def _build_not_disjoint_query(path1: str, path2: str) -> str:
    return _build_query(f'''
    ?v {path1} ?o .
    ?v {path2} ?o
    ''')

def _build_disjoint_id_query(path: str) -> str:
    return _build_negate(_build_not_disjoint_id_query(path))

def _build_not_disjoint_id_query(path: str) -> str:
    return _build_query(f'?v {path} ?v')

## EQUALITY

def _build_equality_query(path1: str, path2: str) -> str:
    return _build_negate(_build_not_equality_query(path1, path2))

def _build_not_equality_query(path1: str, path2: str) -> str:
    return _build_query(f'''
    {{
      ?v {path1} ?o 
      FILTER NOT EXISTS {{ ?v {path2} ?o }}
    }} UNION {{
      ?v {path2} ?o 
      FILTER NOT EXISTS {{ ?v {path1} ?o }}
    }}
    ''')

def _build_equality_id_query(path: str) -> str:
    return _build_query(f'?v :p ?v . ?v :p ?o') + \
    ' GROUP BY ?v HAVING (COUNT(?o) = 1) '


def _build_not_equality_id_query(path: str) -> str:
    return _build_negate(_build_equality_id_query(path))

## FORALL

def _build_forall_query(path: str, shape: str) -> str:
    return _build_negate(
        _build_query(f'''
        ?v {path} ?o.
        {{
          SELECT (?v AS ?o)
          WHERE {{ {_build_negate(shape)} }}
        }}'''))


def _build_forall_test_query(path: str, filter_condition: str):
    # Note: neg_filter_condition must be the negation of the 
    # original filter condition 
    return _build_negate(
        _build_query(f' ?v {path} ?o FILTER ( !({filter_condition}) ) '))

## COUNTRANGE

def _countrange_group_condition(mincount: int, maxcount: Optional[int]):
    # if mincount == 0: # then we cannot do countrange this way
    #     raise ValueError('Cannot build countrange: maxcount')
    if mincount == 1 and maxcount is None: # then it must only exist
        return ''
    if mincount == maxcount:
        return f' GROUP BY ?v HAVING ( COUNT(?o) = {str(mincount)} )'
    return f' GROUP BY ?v HAVING ( COUNT(?o) >= {str(mincount)} ' + \
           f'{ f"&& COUNT(?o) <= {str(maxcount)} )" if maxcount else ")" }'


def _build_countrange_query(mincount: int, maxcount: Optional[int], 
                            path: str, shape: str) -> str:
    return _build_query(f'?v {path} ?o . ' + \
                        f'{{ SELECT (?v AS ?o) WHERE {{ {shape} }} }}') + \
        _countrange_group_condition(mincount, maxcount)


def _build_countrange_top_query(mincount: int, maxcount: Optional[int], 
                                path: str) -> str:
    return _build_query(f'?v {path} ?o') + \
        _countrange_group_condition(mincount, maxcount)
        

def _build_countrange_test_query(mincount: int, maxcount: Optional[int],
                                 path: str, filter_condition: str) -> str:
    return _build_query(f'?v {path} ?o FILTER ({filter_condition})') + \
        _countrange_group_condition(mincount, maxcount)


def _build_exists_hasvalue_query(path: str, value: str) -> str:
    return _build_query(f'?v {path} {value}')


def _build_maxcount_qualified_query(num: int, path: str, shape: str) -> str:
    return _build_negate(
        _build_query(f'''
?v {path} ?o .
{{ SELECT (?v AS ?o) WHERE {{ {shape} }} }}
''') + f' GROUP BY ?v HAVING (COUNT(?o) > {str(num)} )')


def _build_maxcount_top_query(num: int, path: str) -> str:
    return _build_negate(
        _build_query(f'?v {path} ?o') + \
            f' GROUP BY ?v HAVING (COUNT(?o) > {str(num)} )')


def _build_maxcount_test_query(num: int, path: str, 
                               filter_condition: str) -> str:
    return _build_negate(
        _build_query(f'?v {path} ?o FILTER ({filter_condition})') + \
            f' GROUP BY ?v HAVING (COUNT(?o) > {str(num)} )')


## LESSTHAN

def _build_lt_query(path: str, prop: str) -> str:
    return _build_query(f'?v {path} ?e ' + 
        f'FILTER NOT EXISTS {{ ?v {prop} ?p FILTER ( ?e >= ?p )}}')

## LESSTHANEQ

def _build_lte_query(path: str, prop: str) -> str:
    return _build_query(f'?v {path} ?e' + 
        f'FILTER NOT EXISTS {{ ?v {prop} ?p FILTER ( ?e > ?p )}}')

## HASVALUE

def _build_hasvalue_query(value: str) -> str:
    return _build_query(f'BIND ( <{str(value)}> AS ?v )')

## UNIQUELANG

def _build_uniquelang_query(path: str) -> str:
    return _build_negate(
        _build_query(f'''
        SELECT ?v
        WHERE {{
            ?v {path} ?o1 .
            ?v {path} ?o2 
            FILTER ( ?o1 != ?o2 && lang(?o1) = lang(?o2) && lang(?o1) != "" )
        }}
        '''))

## TEST

def _build_test_query(parameters: List, negate: bool=False) -> str:
    return _build_query(
        f'{{ {_build_all_query()} }} FILTER ({_build_filter_condition(parameters, negate=negate)})')

def _build_filter_condition(parameters: List, negate: bool=False, var: str='?v') -> str:
    neg = '!' if negate else ''

    test_type = parameters[0]

    if test_type == SH['PatternConstraintComponent']:
        fmt_flags = ''
        pattern_flags = parameters[2]
        for flag in pattern_flags:
            fmt_flags += str(flag)
        return f'{neg}regex({var}, "{str(parameters[1])}", "{fmt_flags}")'

    if test_type == SH['DatatypeConstraintComponent']:
        return f'{neg}(datatype({var}) = <{str(parameters[1])}>)'
    
    if test_type == SH['NodeKindConstraintComponent']:
        if parameters[1] == SH.IRI:
            return f'{neg}isIRI({var})'
        if parameters[1] == SH.Literal:
            return f'{neg}isLiteral({var})'
        if parameters[1] == SH.BlankNode:
            return f'{neg}isBlank({var})'
        if parameters[1] == SH.BlankNodeOrIRI:
            return f'{neg}(isIRI({var}) || isBlank({var}))'
        if parameters[1] == SH.BlankNodeOrLiteral:
            return f'{neg}(isBlank({var}) || isLiteral({var}))'
        if parameters[1] == SH.IRIOrLiteral:
            return f'{neg}(isIRI({var}) || isLiteral({var}))'

    if test_type == 'numeric_range':
        out = ''
        for i in range(1, len(parameters)-1, 2):
            range_type = parameters[i]
            range_value = parameters[i+1]
            if range_type == SH['MinExclusiveConstraintComponent']:
                out += f'&& {neg}( {var} > {str(range_value)} )'
            if range_type == SH['MaxExclusiveConstraintComponent']:
                out += f'&& {neg}( {var} < {str(range_value)} )'
            if range_type == SH['MinInclusiveConstraintComponent']:
                out += f'&& {neg}( {var} >= {str(range_value)} )'
            if range_type == SH['MaxInclusiveConstraintComponent']:
                out += f'&& {neg}( {var} <= {str(range_value)} )'
        return f'{out[3:]}' # no &&
    
    if test_type == 'length_range':
        out = ''
        for i in range(1, len(parameters)-1, 2):
            range_type = parameters[i]
            range_value = parameters[i+1]
            if range_type == SH['MinLengthConstraintComponent']:
                out += f'&& {neg}( strlen({var}) >= {str(range_value)} )'
            if range_type == SH['MaxLengthConstraintComponent']:
                out += f'&& {neg}( strlen({var}) <= {str(range_value)} )'
        return f'{out[3:]}' # no &&
    
    if test_type == SH['LanguageInConstraintComponent']:
        languages = parameters[1]
        return f'( lang({var}) {"NOT" if neg else ""} IN {_as_sparql_strlist(languages)})'

    return ''

def _as_sparql_strlist(l: List) -> str:
    out = '('
    for elem in l:
        out += f' "{str(elem)}",'
    return out[:-1 ] + ' )'

