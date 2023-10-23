import pytest

from drunk_snail_python import addTemplate, removeTemplate, render

from .common import render_lambda, param_values



def test_nonexistent_template():
	with pytest.raises(KeyError):
		render('name', {})


def test_nonexistent_param():
	assert render_lambda('lalala<!-- (param)p -->lololo', {}) == b'lalalalololo\n'


def test_nonexistent_ref():
	with pytest.raises(KeyError):
		render_lambda('<!-- (ref)something -->')


def test_nonexistent_ref_deep():

	addTemplate('test_nonexistent_ref_1', '<!-- (ref)test_nonexistent_ref_2 -->')
	addTemplate('test_nonexistent_ref_2', '<!-- (ref)no -->')
	with pytest.raises(KeyError):
		render('test_nonexistent_ref_1', {})


def test_buf_overflow():
	assert render_lambda(' ' * 1024)


def test_other_overflow(param_values):

	for name in param_values[:1]:
		addTemplate(f'test_other_deep_inject_{name.decode()}', name)

	for i, name in enumerate(param_values[1:]):
		addTemplate(
			f'test_other_deep_inject_{name.decode()}',
			f'{name.decode()}<!-- (ref)test_other_deep_inject_{param_values[i].decode()} -->{name.decode()}'
		)

	assert render(
		f'test_other_deep_inject_{param_values[-1].decode()}',
		{}
	) == f"{b''.join(reversed(param_values))[:-1].decode()}{b''.join(param_values).decode()}\n".encode('utf8')


def test_name_overflow(value=b'param'):
	name = 'a' * 512
	assert render_lambda(f'<!-- (param){name} -->', {name: value}) == f'{value.decode()}\n'.encode('utf8')


def test_value_overflow():
	value = b'a' * 512
	assert render_lambda(f'<!-- (param)name -->', {'name': value}) == f'{value.decode()}\n'.encode('utf8')


def test_stack_overflow(param_values):

	for name in param_values[:1]:
		addTemplate(f'o{name.decode()}', '')

	for i, name in enumerate(param_values[1:]):
		addTemplate(
			f'o{name.decode()}',
			f'<!-- (ref)o{param_values[i].decode()} -->'
		)

	assert render(f'o{param_values[-1].decode()}', {}) == b''


def test_cyrillic_source():
	assert render_lambda('ляляля') == 'ляляля\n'.encode('utf8')


def test_cyrillic_name():
	addTemplate('ляляля', 'lalala')
	assert render('ляляля', {}) == b'lalala\n'


def test_nonbytes():
	for template, params in (
		('<!-- (param)x -->',                  {'x': 1}),
		('<!-- (param)x -->',                  {'x': [1]}),
		('<!-- (param)x --><!-- (param)y -->', {'x': b'1', 'y': 1})
	):
		with pytest.raises(Exception):
			render_lambda(template, params)


def test_recursion():
	addTemplate('test_recursion', '<!-- (ref)test_recursion -->')
	with pytest.raises(Exception):
		render('test_recursion', {}, True)


def test_recursion_deep():
	addTemplate('test_recursion_deep_1', '<!-- (ref)test_recursion_2 -->')
	addTemplate('test_recursion_deep_2', '<!-- (ref)test_recursion_1 -->')
	with pytest.raises(Exception):
		render('test_recursion_deep_1', {}, True)
	with pytest.raises(Exception):
		render('test_recursion_deep_2', {}, True)


def test_different_lengths_empty_line():
	for l in range(1, 10 ** 4):
		text = b' ' * l + b'\n'
		assert render_lambda(text) == text


def test_different_lengths_param_name():
	addTemplate('l', '<!-- (param)p -->')
	for l in range(1, 10 ** 4):
		name = 'n' * l
		assert render_lambda(f'<!-- (param){name} -->', {name: b' '}) == b' \n'


def test_different_lengths_param_value():
	addTemplate('l', '<!-- (param)p -->')
	params = {'p': None}
	for l in range(1, 10 ** 4):
		params['p'] = b' ' * l
		assert render('l', params) == params['p'] + b'\n'


@pytest.mark.parametrize(
	('name', 'text'),
	(
		(1, b''),
		(1.0, b''),
		([], b''),
		({}, b''),
		('name', 1),
		('name', 1.0),
		('name', []),
		('name', {})
	)
)
def test_bad_arguments(name, text):
	with pytest.raises(TypeError):
		addTemplate({}, b'')