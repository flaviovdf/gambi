# -*- coding: utf8 -*-

'''
Gambi is a Python autograder created for Moodle's Virtual
Programming Laboratory (VPL). VPL follows a input output
style (i.e., akin to coding competitions) test cases.
Gambi will automatically create such test cases based on
a Jupyter notebook
'''


from typing import Any
from typing import Self

from pathlib import Path


import builtins
import copy
import json
import io
import pprint
import secrets


def new_print(*args):
    buffer = io.StringIO()
    print(*args, file=buffer)
    return buffer.getvalue()


def random_key(n: int = 6) -> str:
    n = (n * 3) // 4
    return secrets.token_urlsafe(n)


def has_method(o: Any, name: str) -> bool:
    return callable(getattr(o, name, None))


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
        self.repr = 0

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
        self.repr += 1
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
            json.dump(q, questions_file)

        with open(cases, 'w') as cases_file:
            for key in self.order:
                val = to_str(self.test_cases[key])
                print(f'Case = {key}', file=cases_file)
                print('Input =', file=cases_file)
                print(f'Output = {val}', file=cases_file)
        self.repr = 0
        return self

    def _repr_pretty_(self, p: Any, c: bool) -> str:
        if self.order and self.repr:
            for key in self.order[-self.repr:]:
                val = to_str(self.test_cases[key], 50)
                p.text(f'Case = {key}\n')
                p.text('Input =\n')
                p.text(f'Output = {val}\n')
        self.repr = 0


class GambiStudent(object):
    def __init__(self, questions: Path | str):
        if isinstance(questions, str):
            questions = Path(questions)
        if not questions.exists():
            raise IOError(f'{questions} does not exist!')
        self.test_cases = {}
        with open(questions, 'r') as questions_file:
            order_json = json.load(questions_file)
            self.order = order_json['order']
        self.repr = None

    def register_answer(
        self, variable: Any, key: str
    ) -> Self:
        if key in self.test_cases:
            self.repr = f'[‼️] Answer to {key} was overwritten!'
        else:
            self.repr = f'[🤙] Answer to {key} was stored'

        self.test_cases[key] = copy.deepcopy(variable)
        return self

    def _repr_pretty_(self, p: Any, c: bool) -> str:
        if self.repr is not None:
            msg = self.repr
            p.text(f'{msg}\n\n')
            self.repr = None
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
        print = builtins.print
        for key in self.order:
            if key in self.test_cases:
                print(to_str(self.test_cases[key]))
            else:
                print('')
