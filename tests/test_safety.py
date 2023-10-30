import pytest
import ruiner


def test_nonexistent_param():
    assert ruiner.Template(
        'lalala<!-- (param)p -->lololo'
    ).rendered({}) == 'lalalalololo'


def test_nonexistent_ref():
    with pytest.raises(KeyError):
        ruiner.Template('<!-- (ref)something -->').rendered({})


def test_nonexistent_ref_deep():
    with pytest.raises(KeyError):
        ruiner.Template('<!-- (ref)test_nonexistent_ref_2 -->').rendered(
            parameters={},
            templates={
                'test_nonexistent_ref_2': ruiner.Template('<!-- (ref)no -->')
            }
        )


def test_recursion():
    with pytest.raises(RecursionError):
        ruiner.Template('<!-- (ref)test_recursion -->').rendered(
            parameters={},
            templates={
                'test_recursion': ruiner.Template(
                    '<!-- (ref)test_recursion -->'
                )
            }
        )


def test_recursion_deep():
    templates = {
        'test_recursion_deep_1': ruiner.Template(
            '<!-- (ref)test_recursion_deep_2 -->'
        ),
        'test_recursion_deep_2': ruiner.Template(
            '<!-- (ref)test_recursion_deep_1 -->'
        ),
    }
    with pytest.raises(RecursionError):
        ruiner.Template('<!-- (ref)test_recursion_deep_1 -->').rendered(
            parameters={},
            templates=templates
        )
    with pytest.raises(RecursionError):
        ruiner.Template('<!-- (ref)test_recursion_deep_2 -->').rendered(
            parameters={},
            templates=templates
        )
