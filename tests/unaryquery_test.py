from pytest import mark
from rdflib import Graph, Namespace
from rdflib.namespace import RDF
from rdflib import Literal

from slsparser.shapels import parse
from slsparser.utilities import expand_shape
from ssf.unaryquery import to_uq

EX = Namespace('http://example.org/')

@mark.parametrize('shape_file, expected_nodes', [
    ('datatype.sh.ttl', [EX.node3]),
    ('languagein.sh.ttl', [EX.node1, EX.node2]),
    ('lengthrange.sh.ttl', [Literal('belgium',lang='en'), Literal('Belgie',lang='nl'), Literal('Luxemburg',lang='nl')]),
    ('lessthan.sh.ttl', [EX.node5]),
    ('lessthaneq.sh.ttl', [EX.node5, EX.node6]),
    ('nodekind.sh.ttl', [EX.node1, EX.node2, EX.node3, EX.node4, EX.node5, EX.node6]),
    ('numericrange.sh.ttl', [Literal(34)]),
    ('pattern.sh.ttl', [Literal('belgium',lang='en'), Literal('Belgie',lang='nl')]),
    ('uniquelang.sh.ttl', [EX.node1])
])
def test_unary_query_tests(shape_file, expected_nodes):
    _unary_query_helper('uq_tests_testfiles', shape_file, expected_nodes)


@mark.parametrize('shape_file, expected_nodes', [
    ('closed.sh.ttl', [EX.user1]),
    ('colleague_friend.sh.ttl', [EX.user1, EX.manager2]),
    #('knows_ceo.sh.ttl', [EX.user2]), # rdflib bug, appears to not be able to do the join of two subqueries
    ('manager_vacation.sh.ttl', [EX.manager1, EX.manager2, EX.manager3]),
    ('name_givenname.sh.ttl', [EX.manager1, EX.manager2]),
    ('phone_not_email.sh.ttl', [EX.user1]),
    ('user_managed.sh.ttl', [EX.user1])
])
def test_unary_query_structural(shape_file, expected_nodes):
    _unary_query_helper('uq_user_manager_testfiles', shape_file, expected_nodes)


def _unary_query_helper(folder, shape_file, expected_nodes):
    shapesgraph = Graph()
    shapesgraph.parse(f'./tests/{folder}/{shape_file}')

    schema = parse(shapesgraph)
    testshape = schema[0][EX.testshape]
    expanded_testshape = expand_shape(schema[0], testshape)
    unaryquery = to_uq(expanded_testshape)

    datagraph = Graph()
    datagraph.parse(f'./tests/{folder}/data.ttl')

    query_results = datagraph.query(unaryquery)
    resultset = set()
    for row in query_results:
        resultset.add(row[0])

    assert resultset == set(expected_nodes)

def test_simple_query():
    datagraph = Graph()
    datagraph.parse(f'./tests/uq_user_manager_testfiles/data.ttl')

    unaryquery = 'SELECT ?v { { SELECT ?v ?o WHERE { ?v <http://example.org/knows>  ?o } } . { SELECT (?v AS ?o) WHERE { SELECT ?v WHERE { ?v <http://example.org/CEO-of> <http://example.org/MyCompany> } } } }'

    query_results = datagraph.query(unaryquery)
    resultset = set()
    for row in query_results:
        resultset.add(row[0])

    assert resultset == set()

def test_personshape():
    _unary_query_helper('uq_other_testfiles', 'personshape.ttl', [])