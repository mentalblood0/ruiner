import re
import dataclasses



@dataclasses.dataclass(frozen = True, kw_only = False)
class Regexp:

	value : re.Pattern[str]

	@classmethod
	def sequence(cls, *sequence: 'Regexp'):
		assert len(sequence) > 1
		result = sequence[0]
		for e in sequence[1:]:
			result += e
		return result

	def match(self, text: str):
		return self.value.fullmatch(text)

	def find(self, text: str):
		return self.value.finditer(text)

	@property
	def optional(self):
		return Regexp(re.compile(f'(?:{self})?'))

	@property
	def degrouped(self):
		return Regexp(
			re.compile(
				re.sub(
					re.compile(r'\(\?P<\w+>([^\)]+)\)'),
					r'\1',
					str(self)
				)
			)
		)

	def __str__(self):
		return self.value.pattern

	def __call__(self, name: str):
		return Regexp(re.compile(f'(?P<{name}>{self.degrouped})'))

	def __add__(self, another: 'Regexp'):
		return Regexp(re.compile(f'{self}{another}'))