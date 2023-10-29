import pytest
import ruiner
import typing
import pathlib
from pytest_benchmark import fixture

from ..common import *



@pytest.fixture
def row(directory: pathlib.Path):
	return ruiner.Template((directory / 'Row.xml').read_text())


@pytest.fixture
def table(directory: pathlib.Path):
	return ruiner.Template((directory / 'Table.xml').read_text())


@pytest.fixture
def parameters(table_width: int, table_height: int, cell_value: typing.Callable[[int, int], str]) -> ruiner.Template.Parameters:
	return {
		"Row": [
			{
				"cell": [
					cell_value(x, y)
					for x in range(table_width)
				]
			}
			for y in range(table_height)
		]
	}


@pytest.fixture
def templates(row: ruiner.Template):
	return {'Row': row}


def test_drunk_snail(benchmark: typing.Callable[[type[pytest.FixtureRequest]], fixture.BenchmarkFixture], table: ruiner.Template, parameters: ruiner.Template.Parameters, templates: dict[str, ruiner.Template]):
	f = lambda: table.rendered(parameters, templates)
	first = f()
	assert len(first) == 220806
	benchmark(f)
	assert first == f()