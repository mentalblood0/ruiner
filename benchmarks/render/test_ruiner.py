import typing

import pytest
from pytest_benchmark import fixture

import ruiner


@pytest.fixture()
def table_width():
    return 100


@pytest.fixture()
def table_height():
    return 100


@pytest.fixture()
def cell_value(table_width: int) -> typing.Callable[[int, int], str]:
    return lambda x, y: str(x + y * table_width)


@pytest.fixture()
def row():
    return ruiner.Template("<tr>\n" "    <td><!-- (param)cell --></td>\n" "</tr>")


@pytest.fixture()
def table():
    return ruiner.Template("<table>\n" "    <!-- (ref)Row -->\n" "</table>")


@pytest.fixture()
def parameters(
    table_width: int, table_height: int, cell_value: typing.Callable[[int, int], str]
) -> ruiner.TemplateParameters:
    return {"Row": [{"cell": [cell_value(x, y) for x in range(table_width)]} for y in range(table_height)]}


@pytest.fixture()
def templates(row: ruiner.Template):
    return {"Row": row}


def test_drunk_snail(
    benchmark: fixture.BenchmarkFixture,
    table: ruiner.Template,
    parameters: ruiner.TemplateParameters,
    templates: typing.Dict[str, ruiner.Template],
):
    def test():
        return table.rendered(parameters, templates)

    first = test()
    assert len(first) == 220806
    benchmark(test)
    assert first == test()
