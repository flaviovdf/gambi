# -*- coding: utf8 -*-

'''
Gambi is a Python autograder created for Moodle's Virtual
Programming Laboratory (VPL). VPL follows a input output
style (i.e., akin to coding competitions) test cases.

Gambi will automatically create such test cases based on
a Jupyter notebook. Gambi also provides tools to mark
notebook cells for deletion and/or as read-only.

This is a single file module that does not require anything
besides the standard python library.

VPL performs grading based on the standard output. Thus,
we need to capture the print function to work correctly.
Thus, **Gambi is a HACK** In order to use it correctly,
even the print function will be overwritten. Use it wisely.
'''


from typing import Any
from typing import Self

from pathlib import Path


import builtins
import copy
import json
import pprint
import secrets
import sys


_FREEZE = {
    'metadata': {
        'trusted': True,
        'editable': False,
        'deletable': False
    }
}

_DELETE = {'delete': True}


class _PrintCellAttribute(object):
    def __init__(self, attr: dict):
        self.attr = attr

    def _repr_pretty_(self, p: Any, c: bool) -> str:
        p.text('[gambi]')

    def _repr_json_(self) -> dict:
        return self.attr


def new_print(*args, **kwargs):
    if 'file' in kwargs:
        if kwargs['file'] == sys.stdout:
            raise AttributeError('Cannot print to std.out!')
        print(*args, **kwargs)
    else:
        print(*args, **kwargs, file=sys.stderr)


def original_print(*args, **kwargs):
    return builtins.print(*args, **kwargs)


def random_key(n: int = 6) -> str:
    n = (n * 3) // 4
    return secrets.token_urlsafe(n)


def has_method(o: Any, name: str) -> bool:
    return callable(getattr(o, name, None))


def freeze_cell():
    return _PrintCellAttribute(_FREEZE)


def delete_cell():
    return _PrintCellAttribute(_DELETE)


def to_str(o: Any, max_n: int = None) -> str:
    to_pretty = True
    # pandas objects become strings
    if has_method(o, 'to_csv'):
        value = o.to_csv()
        to_pretty = False
    # numpy/torch/jax arrays and tensors become
    # lists
    elif has_method(o, 'flatten'):
        value = [x for x in o.flatten()]
    # numbers are ok
    elif isinstance(o, (int, float, bool)):
        value = o

    # now pretty print
    if to_pretty:
        txt = pprint.pformat(value)
    else:
        txt = value
    if max_n is not None:
        if len(txt) >= max_n:
            txt = txt[:max_n] + '...'
    return txt


class GambiTeacher(object):

    def __init__(self):
        self.test_cases = {}
        self.order = []
        self.types = []
        self.repr_history = 0

    def create_test_case(
        self, variable: Any, key: str = None
    ) -> Self:
        if key is None:
            key = random_key()
            while key in self.test_cases:
                key = random_key()
        if key in self.test_cases:
            raise KeyError(
                f'Test case {key} already exists'
            )
        self.test_cases[key] = copy.deepcopy(variable)
        self.order.append(key)
        self.types.append(
            str(type(variable)).split("'")[1]
        )
        self.repr_history += 1
        return self

    def create_vpl(
        self, questions: Path | str,
        cases: Path | str,
    ) -> Self:
        if isinstance(questions, str):
            questions = Path(questions)
        if isinstance(cases, str):
            cases = Path(cases)

        with open(questions, 'w') as questions_file:
            q = {}
            q['order'] = self.order
            q['types'] = {}
            for key, type_ in zip(self.order, self.types):
                q['types'][key] = type_
            json.dump(q, questions_file)

        with open(cases, 'w') as cases_file:
            for key in self.order:
                val = to_str(self.test_cases[key])
                print(f'Case = {key}', file=cases_file)
                print('Input =', file=cases_file)
                print(f'Output = {val}', file=cases_file)
        self.repr_history = 0
        return self

    def _repr_pretty_(self, p: Any, c: bool) -> str:
        if self.repr_history > 0:
            n = self.repr_history
            p.text(f'[🤙] Created {n} new test case(s)\n')
        else:
            n = len(self.test_cases)
            p.text(f'[🤙] There are {n} tests case(s)\n')

        if self.order:
            p.text('[🤙] They are as follows\n')
            cases = self.order[-self.repr_history:]
            for key, type_ in zip(self.order, self.types):
                val = to_str(self.test_cases[key], 50)
                p.text(f'[🤙] {key} expects {type_}.\n')
                p.text('[🤙] Summary in VPL:\n')
                p.text(f'Case = {key}\n')
                p.text('Input =\n')
                p.text(f'Output = {val}\n\n')
        self.repr_history = 0


class GambiStudent(object):
    def __init__(self, questions: Path | str):
        if isinstance(questions, str):
            questions = Path(questions)
        if not questions.exists():
            raise IOError(f'{questions} does not exist!')
        self.test_cases = {}
        with open(questions, 'r') as questions_file:
            qjson = json.load(questions_file)
            self.order = qjson['order']
            self.types = qjson['types']
        self.repr_messages = []

    def register_answer(
        self, variable: Any, key: str
    ) -> Self:
        if key not in self.order:
            raise KeyError(f'{key} is not a question!')
        if key in self.test_cases:
            msg = f'[‼️] Answer to {key} was overwritten!'
        else:
            msg = f'[🤙] Answer to {key} was stored'

        self.test_cases[key] = copy.deepcopy(variable)
        self.repr_messages.append(msg)
        return self

    def _repr_pretty_(self, p: Any, c: bool) -> str:
        if self.repr_messages:
            for msg in self.repr_messages:
                p.text(f'{msg}\n\n')
            self.repr_messages = []
        nq = len(self.order)
        na = len(self.test_cases)
        p.text(f'This activity has {nq} questions.\n')
        p.text(f'You have provided {na} answers.\n')
        if nq - na == 0:
            p.text('[🤙 🤙 🤙] Good to submit!\n')
        else:
            missing = []
            for key in self.order:
                if key not in self.test_cases:
                    missing.append(key)
            p.text(f'[‼️ ‼️ ‼️] Missing: {missing}\n')

    def evaluate(self):
        for key in self.order:
            if key in self.test_cases:
                builtins.print(
                    to_str(self.test_cases[key])
                )
            else:
                builtins.print('[‼️ ‼️ ‼️] No Answer!')


def convert_notebook(notebook: dict) -> dict:
    new_notebook = copy.deepcopy(notebook)
    cells = notebook['cells']
    new_cells = []
    for cell in cells:
        new_cell = copy.deepcopy(cell)
        if (
            'cell_type' not in cell or
            'outputs' not in cell or
            cell['cell_type'] != 'code'
        ):
            new_cells.append(new_cell)
        else:
            output = new_cell['outputs']
            if (
                not output or
                'data' not in output[0]
            ):
                new_cells.append(new_cell)
            else:
                data = output[0]['data']
                if (
                    'text/plain' in data and
                    data['text/plain'] == ['[gambi]'] and
                    'application/json' in data
                ):
                    info = data['application/json']
                    if info == _DELETE:
                        continue
                    if info == _FREEZE:
                        key = 'metadata'
                        new_cell[key] = info[key]
                new_cell['outputs'] = []
                new_cells.append(new_cell)
    new_notebook['cells'] = new_cells
    return new_notebook


if __name__ == '__main__':
    import sys

    program = sys.argv[0]
    err = sys.stderr

    if len(sys.argv) == 1:
        builtins.print(
            f'Usage {program} jupyter-notebook-path',
            file=err
        )
        sys.exit(1)

    notebook_path = Path(sys.argv[1])
    if not notebook_path.exists():
        builtins.print(
            f'{notebook_path} does not exist!',
            file=err
        )
        sys.exit(1)

    if notebook_path.is_dir():
        builtins.print(
            f'{notebook_path} is a directory!',
            file=err
        )
        sys.exit(1)

    if (
        not notebook_path.suffix or
        notebook_path.suffix != '.ipynb'
    ):
        builtins.print(
            f'{notebook_path} not a notebook file!',
            file=err
        )
        sys.exit(1)

    with open(notebook_path) as json_file:
        notebook = json.load(json_file)
        builtins.print(convert_notebook(notebook))
