import re
import typing
import functools
import dataclasses

from .Regexp import Regexp



@dataclasses.dataclass(frozen = True, kw_only = False)
class Pattern:

	value : str

	expression = Regexp(re.compile('.*'))

	def __post_init__(self):
		if not self.expression.match(self.value):
			raise ValueError(f'Expression "{self.expression}" does not match value "{self.value}"')

	@functools.cached_property
	def groups(self):
		assert (match := self.expression.match(self.value)) is not None
		return match.groupdict()

	@classmethod
	@functools.lru_cache
	def extracted(cls, source: 'Pattern'):
		return [
			cls(source.value[m.start():m.end()])
			for m in cls.expression.find(source.value)
		]

	@classmethod
	@functools.lru_cache
	def highlighted(cls, source: 'Pattern'):
		result: list[Other | cls] = []
		last = None
		for m in cls.expression.find(source.value):
			if (
				last is None and
				m.start() > (last_end := 0)
			) or (
				last is not None and
				m.start() > (last_end := last.end())
			):
				result.append(Other(source.value[last_end:m.start()]))
			last = m
			result.append(cls(source.value[m.start():m.end()]))
		if last is None:
			result.append(Other(source.value))
		else:
			if (last_end := last.end()) != len(source.value):
				result.append(Other(source.value[last_end:]))
		return result

	def __getitem__(self, name: str):
		return self.groups[name]

	def __contains__(self, name: str):
		return name in self.groups and self.groups[name] is not None


class Name(Pattern):
	expression = Regexp(re.compile('\\w+'))

class Spaces(Pattern):
	expression = Regexp(re.compile(' *'))

class Open(Pattern):
	expression = Regexp(re.compile('<!--'))

class Close(Pattern):
	expression = Regexp(re.compile('-->'))

class Delimiter(Pattern):
	expression = Regexp(re.compile('\n'))

class Other(Pattern):
	@property
	def rendered(self):
		return self.value


class Operator(Pattern):
	expression = Regexp(re.compile(f'\\({Name.expression}\\)'))

class Optional(Operator):
	expression = Regexp(re.compile(r'\(optional\)'))



class Expression(Pattern):

	class Type(Operator):
		class Parameter(Operator):
			expression = Regexp(re.compile(r'\(param\)'))
		class Reference(Operator):
			expression = Regexp(re.compile(r'\(ref\)'))

	expression = Regexp.sequence(
		Open.expression,
		Spaces.expression,
		Optional.expression('optional').optional,
		Type.expression.degrouped,
		Name.expression('name'),
		Spaces.expression,
		Close.expression
	)

	@functools.cached_property
	def name(self):
		return Name(self['name'])

	@property
	def optional(self):
		return 'optional' in self

	@functools.cached_property
	def specified(self):
		for C in (Parameter, Reference):
			try:
				return C(self.value)
			except ValueError:
				continue
		raise ValueError

class Parameter(Expression):
	expression = Regexp.sequence(
		Open.expression,
		Spaces.expression,
		Optional.expression('optional').optional,
		Expression.Type.Parameter.expression,
		Name.expression('name'),
		Spaces.expression,
		Close.expression
	)
	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template']):
		try:
			match (result := parameters[self.name.value]):
				case list():
					for r in result:
						assert isinstance(r, str)
						yield str(r)
				case str():
					yield result
				case _:
					raise ValueError
		except KeyError:
			if not self.optional:
				yield ''

class Reference(Expression):
	expression = Regexp.sequence(
		Open.expression,
		Spaces.expression,
		Optional.expression('optional').optional,
		Expression.Type.Reference.expression,
		Name.expression('name'),
		Spaces.expression,
		Close.expression
	)
	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template'], left: str = '', right: str = '') -> typing.Generator[str, typing.Any, typing.Any]:

		if self.optional:
			if self.name.value not in parameters:
				return ['']
			elif self.name.value not in templates:
				raise KeyError

		match (
			inner := (
				parameters[self.name.value]
				if self.name.value in parameters
				else Template.Parameters({})
			)
		):
			case str():
				raise ValueError
			case list():
				for p in inner:
					assert not isinstance(p, str)
					yield templates[self.name.value].rendered(p, templates, left, right)
			case _:
				yield templates[self.name.value].rendered(inner, templates, left, right)


class Line(Pattern):

	class OneReference(Pattern):

		expression = Regexp.sequence(
			Other.expression.optional('left'),
			Reference.expression('reference'),
			Other.expression.optional('right')
		)

		@functools.cached_property
		def left(self):
			return Other(self['left']).rendered

		@functools.cached_property
		def reference(self):
			return Reference(self['reference'])

		@functools.cached_property
		def right(self):
			return Other(self['right']).rendered

		def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template'], left: str = '', right: str = ''):
			return str(Delimiter.expression).join(
				self.reference.rendered(parameters, templates, left + self.left, self.right + right)
			)

	@functools.cached_property
	def specified(self):
		try:
			return Line.OneReference(self.value)
		except ValueError:
			return self

	def _rendered(self, inner: tuple[str]):
		current = iter(inner)
		return ''.join(
			e.value
			if isinstance(e, Other)
			else next(current)
			for e in Expression.highlighted(self)
		)

	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template'], left: str = '', right: str = ''):
		if not len(extracted := Expression.extracted(self)):
			return left + self.value + right
		else:
			return str(Delimiter.expression).join([
				left + self._rendered(inner) + right
				for inner in zip(
					*[
						p.specified.rendered(parameters, templates)
						for p in extracted
					]
				)
			])


class Template(Pattern):

	Parameters = dict[str, typing.Union[str, list[str], 'Parameters', list['Parameters']]]

	expression = Regexp(re.compile('(?:.*\n)*(?:.*)?'))

	@functools.cached_property
	def lines(self):
		return [
			Line(l).specified
			for l in self.value.split(str(Delimiter.expression))
		]

	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template'] = {}, left: str = '', right: str = ''):
		return str(Delimiter.expression).join([
			l.rendered(parameters, templates, left, right)
			for l in self.lines
		])