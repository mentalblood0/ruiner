<h1 align="center">🔫 ruiner</h1>

<h3 align="center">safe and clean template engine</h3>

<p align="center">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://www.python.org"><img alt="Python version: >=3.7" src="https://img.shields.io/badge/Python-3.7%20|%203.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12-blue"></a>
</p>

Pure Python object oriented implementation of template language originally presented in [drunk snail](https://codeberg.org/mentalblood/drunk_snail)

## Why this language?

- Easy syntax
- Separates logic and data

## Why better then drunk snail?

- Small codebase
- Secure by design
- Flexible object model

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
pip install --upgrade git+https://codeberg.com/mentalblood/ruiner
git clone https://codeber.org/mentalblood/ruiner
cd ruiner
pytest
```
