![tests](https://github.com/MentalBlood/ruiner/actions/workflows/python-package.yml/badge.svg)

# 🔫 ruiner

Pure Python object oriented implementation of template language originally presented in [drunk snail](https://github.com/mentalblood/drunk_snail)

## Why this language?

* Easy syntax
* Separates logic and data

## Why better then drunk snail?

* Small codebase
* Secure by design
* Flexible object model

## Example

Row:
```html
<tr>
    <td><!-- (param)cell --></td>
</tr>
```
Table:
```html
<table>
    <!-- (ref)Row -->
</table>
```
Arguments:
```python
{
    "Row": [
        {
            "cell": [
                "1",
                "2"
            ]
        },
        {
            "cell": [
                "3",
                "4"
            ]
        }
    ]
}
```
Result:
```html
<table>
    <tr>
        <td>1</td>
        <td>2</td>
    </tr>
    <tr>
        <td>3</td>
        <td>4</td>
    </tr>
</table>
```

## Installation

```bash
pip install git+https://github.com/MentalBlood/ruiner
```

## Usage

```python
import ruiner

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
```

## Testing/Benchmarking

Using [pytest](https://pypi.org/project/pytest/) and [pytest-benchmark](https://github.com/ionelmc/pytest-benchmark):

```bash
pip install --upgrade git+https://github.com/MentalBlood/ruiner
git clone https://github.com/MentalBlood/ruiner
cd ruiner
pytest
```
