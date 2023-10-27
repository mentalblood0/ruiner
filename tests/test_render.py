import pytest
import ruiner



@pytest.fixture
def param_name():
	return 'x'


@pytest.fixture
def param_value():
	return 'lalala'


@pytest.fixture
def params_one(param_name: str, param_value: str):
	return {param_name: param_value}


@pytest.fixture
def params_list(param_name: str, param_values: list[str]):
	return {param_name: param_values}


def test_basic(param_name: str, param_value: str, params_one: ruiner.Template.Parameters):
	assert ruiner.Template(f'<!-- (param){param_name} -->').rendered(params_one) == f'{param_value}'
	assert ruiner.Template(f'<!-- (param){param_name} -->\n').rendered(params_one) == f'{param_value}\n'
	assert ruiner.Template(f'{param_value}').rendered({}) == f'{param_value}'


def test_empty_template():
	assert ruiner.Template('').rendered({}) == ''


def test_ref():

	greeting = ruiner.Template('Hello, <!-- (param)name -->!\n<!-- (ref)addition -->!\n')
	addition = ruiner.Template('Nice to <!-- (param)action --> you')

	assert greeting.rendered(
		{
			'name': 'username',
			'addition': {
				'action': 'eat'
			}
		},
		{'addition': addition}
	) == 'Hello, username!\nNice to eat you!\n'
	result = greeting.rendered(
		{
			'name': 'username',
			'addition': [{
				'action': 'meet'
			}, {
				'action': 'eat'
			}, {
				'action': 'split'
			}]
		},
		{'addition': addition}
	)
	assert result == 'Hello, username!\nNice to meet you!\nNice to eat you!\nNice to split you!\n'


# def test_consicutive_lines(number: int = 2):

# 	for i in range(number):
# 		addTemplate(f'test_consicutive_lines_{i}', str(i))

# 	ruiner.Template(
# 		''.join(
# 			f'    <!-- (ref)test_consicutive_lines_{i} -->\n'
# 			for i in range(number)
# 		),
# 		{}
# 	) == ''.join(
# 		f'    {i}\n'
# 		for i in range(number)
# 	)


def test_optional_param():
	assert ruiner.Template('<!-- (optional)(param)a -->').rendered({}) == ''


def test_optional_ref():
	templates = {
		'test_optional_ref_1': ruiner.Template('lalala')
	}
	assert ruiner.Template('<!-- (optional)(ref)test_optional_ref_1 -->').rendered(
		{},
		templates
	) == ''
	assert ruiner.Template(
		'<!-- (optional)(ref)test_optional_ref_1 -->'
	).rendered(
		{
			'test_optional_ref_1': [None]
		},
		templates
	) == 'lalala'


def test_table():
	assert ruiner.Template(
		'<table>\n'
		'	<!-- (ref)Row -->\n'
		'</table>',
	).rendered(
		parameters = {
			'Row': [
				{'cell': ['1.1', '2.1', '3.1']},
				{'cell': ['1.2', '2.2', '3.2']},
				{'cell': ['1.3', '2.3', '3.3']}
			]
		},
		templates = {
			'Row': ruiner.Template(
				'<tr>\n'
				'	<td><!-- (param)cell --></td>\n'
				'</tr>'
			)
		}
	) == (
		'<table>\n'
		'	<tr>\n'
		'		<td>1.1</td>\n'
		'		<td>2.1</td>\n'
		'		<td>3.1</td>\n'
		'	</tr>\n'
		'	<tr>\n'
		'		<td>1.2</td>\n'
		'		<td>2.2</td>\n'
		'		<td>3.2</td>\n'
		'	</tr>\n'
		'	<tr>\n'
		'		<td>1.3</td>\n'
		'		<td>2.3</td>\n'
		'		<td>3.3</td>\n'
		'	</tr>\n'
		'</table>'
	)


def test_multiple_params():
	assert ruiner.Template(
		'before<!-- (param)a -->between1<!-- (param)b -->between2<!-- (param)c -->after'
	).rendered(
		 {
			'a': '<a>',
			'b': '<b>',
			'c': '<c>'
		 }
	) == 'before<a>between1<b>between2<c>after'


def test_multiple_params_followed_by_empty_line():
	assert ruiner.Template(
		'Rendering <!-- (param)size -->x<!-- (param)size --> table (mean of <!-- (param)experiments_number --> experiments)\n\n',
	).rendered(
		{
			'size':               '10',
			'experiments_number': '1000'
		}
	) == 'Rendering 10x10 table (mean of 1000 experiments)\n\n'