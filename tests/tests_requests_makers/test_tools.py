from src.core.requests_makers.tools import prepare_params


def test_prepare_params():
    a = {'test': 1, '2': 'test'}
    ans = prepare_params(a)
    assert ans['test'] == a['test']
    assert ans['2'] == a['2']


def test_prepare_params_bool():
    a = {'test': 1, 'bool': True, 'test2': False}
    ans = prepare_params(a)
    assert ans['test'] == 1
    assert ans['bool'] == 'true'
    assert ans['test2'] == 'false'
