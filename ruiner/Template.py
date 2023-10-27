import re
import typing
import functools
import dataclasses



@dataclasses.dataclass(frozen = True, kw_only = False)
class Pattern:

	value : str

	expression = re.compile('.*')

	def __post_init__(self):
		if not self.expression.fullmatch(self.value):
			raise ValueError(f'Expression {self.expression} does not match value {self.value}')

	@classmethod
	@property
	def pattern(cls):
		return cls.degrouped

	@classmethod
	@property
	def named(cls):
		return f'(?P<{cls.__name__}>{cls.degrouped})'

	@classmethod
	@property
	def optional(cls):
		return f'(?:{cls.degrouped})?'

	@classmethod
	@property
	def degrouped(cls):
		return re.sub(
			re.compile(r'\(\?P<\w+>([^\)]+)\)'),
			r'\1',
			cls.expression.pattern
		)

	@functools.cached_property
	def groups(self):
		if (match := self.expression.fullmatch(self.value)) is None:
			raise ValueError
		if not (result := match.groupdict()):
			raise ValueError
		return result

	@functools.cached_property
	def specified(self):
		return self

	@classmethod
	@functools.lru_cache
	def extracted(cls, source: 'Pattern'):
		return [
			cls(source.value[m.start():m.end()])
			for m in cls.expression.finditer(source.value)
		]

	@classmethod
	@functools.lru_cache
	def highlighted(cls, source: 'Pattern'):
		result: list[Other | cls] = []
		last = None
		for m in cls.expression.finditer(source.value):
			if (
				last is None and
				m.start() > (last_end := 0)
			) or (
				last is not None and
				m.start() > (last_end := last.end())
			):
				result.append(Other(source.value[last_end:m.start()]))
			last = m
			result.append(cls(source.value[m.start():m.end()]).specified)
		if last is None:
			result.append(Other(source.value))
		else:
			if (last_end := last.end()) != len(source.value):
				result.append(Other(source.value[last_end:]))
		return result


class Name(Pattern):
	expression = re.compile('\\w+')

class Spaces(Pattern):
	expression = re.compile(' *')

class Open(Pattern):
	expression = re.compile('<!--')

class Close(Pattern):
	expression = re.compile('-->')

class Delimiter(Pattern):
	expression = re.compile('\n')

class Other(Pattern):

	expression = re.compile('.+')

	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template']):
		return self.value


class Operator(Pattern):

	expression = re.compile(f'\\({Name.named}\\)')

	@functools.cached_property
	def name(self):
		return self.groups['Name']


class Optional(Operator):
	expression = re.compile(r'\(optional\)')


class Expression(Pattern):

	class Type(Operator):

		class Parameter(Operator):
			expression = re.compile(r'\(param\)')

		class Reference(Operator):
			expression = re.compile(r'\(ref\)')

	expression = re.compile(Open.pattern + Spaces.pattern + Optional.optional + Type.pattern + Name.named + Spaces.pattern + Close.pattern)

	@functools.cached_property
	def name(self):
		return Name(self.groups['Name'])

	@functools.cached_property
	def specified(self):
		for C in (Parameter, Reference):
			try:
				return C(self.value)
			except ValueError:
				continue
		raise ValueError

class Parameter(Expression):

	expression = re.compile(Open.pattern + Spaces.pattern + Optional.optional + Expression.Type.Parameter.pattern + Name.named + Spaces.pattern + Close.pattern)

	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template']):
		match (result := parameters[self.name.value]):
			case str():
				yield result
			case list():
				for r in result:
					match r:
						case str():
							yield r
						case _:
							raise ValueError
			case _:
				raise ValueError

class Reference(Expression):

	expression = re.compile(Open.pattern + Spaces.pattern + Optional.optional + Expression.Type.Reference.pattern + Name.named + Spaces.pattern + Close.pattern)

	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template'], left: str = '', right: str = '') -> typing.Generator[str, typing.Any, typing.Any]:
		match (inner := parameters[self.name.value]):
			case str():
				raise ValueError
			case list():
				for p in inner:
					match p:
						case str():
							raise ValueError
						case _:
							yield templates[self.name.value].rendered(p, templates, left, right)
			case _:
				yield templates[self.name.value].rendered(inner, templates)


class Line(Pattern):

	class OneReference(Pattern):

		expression = re.compile(Other.optional + Reference.pattern + Other.optional)

		def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template'], left: str = '', right: str = ''):

			highlighted = Expression.highlighted(self)

			match highlighted[0]:
				case Other():
					_left = highlighted[0].rendered(parameters, templates)
					r = 1
				case _:
					_left = ''
					r = 0
			match highlighted[-1]:
				case Other():
					_right = highlighted[-1].rendered(parameters, templates)
				case _:
					_right = ''

			return Delimiter.expression.pattern.join(
				_left + _e + _right
				for _e in highlighted[r].rendered(parameters, templates, left + _left, _right + right)
			)

	@functools.cached_property
	def specified(self):
		try:
			return Line.OneReference(self.value)
		except ValueError:
			return self

	@functools.cache
	def _rendered(self, inner: tuple[str]):
		result = ''
		current = iter(inner)
		for _e in Expression.highlighted(self):
			match (e := _e.specified):
				case Other():
					result += e.value
				case Parameter() | Reference():
					result += next(current)
		return result

	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template'], left: str = '', right: str = ''):
		match len(extracted := Expression.extracted(self)):
			case 0:
				return left + self.value + right
			case _:
				return Delimiter.expression.pattern.join([
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

	expression = re.compile('(?:.*\n)*(?:.*)?')

	@functools.cached_property
	def lines(self):
		return [
			Line(l).specified
			for l in self.value.split(Delimiter.expression.pattern)
		]

	def rendered(self, parameters: 'Template.Parameters', templates: dict[str, 'Template'] = {}, left: str = '', right: str = ''):
		return Delimiter.expression.pattern.join([
			l.rendered(parameters, templates, left, right)
			for l in self.lines
		])