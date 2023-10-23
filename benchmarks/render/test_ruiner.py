import pytest
import ruiner
import pathlib

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


@pytest.mark.benchmark(group='render')
def test_drunk_snail(benchmark, table: ruiner.Template, parameters: ruiner.Template.Parameters, templates: dict[str, ruiner.Template]):
	benchmark(lambda: table.rendered(parameters, templates))