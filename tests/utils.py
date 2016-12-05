#!/usr/bin/env python
"""
    tests.utils
    ===========

    Some useful utility functions

    parameterise.testcase_method() decorator
    A decorator to create a parameterised test function defined
    by a list of dictionaries.

"""
import inspect
import warnings
from functools import wraps


def get_name_func(func, num, parameters):
    # Helper function
    # set to test_name if exists else name of original function + num with warning !
    test_name = parameters.get('test_name')
    if test_name is not None:
        return test_name
    else:
        warnings.warn("You have not set 'test_name' in the parameters",
                      RuntimeWarning, stacklevel=2)
        base_name = func.__name__
        name_suffix = "_%s" % (num, )
        return base_name + name_suffix


# Based of nose_parameterized: https://github.com/wolever/nose-parameterized
class parameterise(object):
    """ Parameterize a test case::

            class TestInt(object):
                @parameterized.testcase_method([
                    {
                        'test_name': 'test_int_19',
                        'test_description': 'this is an example test',
                        'input': 19,
                        'expected': 19,
                    },
                    {
                        'test_name': 'test_second',
                        ...
                    }
                ])
                def test_int(self, input, expected, base=16):
                    actual = int(input, base=base)
                    assert_equal(actual, expected)

    """

    @classmethod
    def testcase_method(cls, input):
        parameterized_input = cls.get_input(input)

        def parameterized_expand_wrapper(f, instance=None):
            stack = inspect.stack()
            frame = stack[1]
            frame_locals = frame[0].f_locals

            for num, params in enumerate(parameterized_input):
                name = get_name_func(f, num, params)
                doc = params.get('test_description', "")
                test = cls.param_as_standalone_func(params, f, name, doc)
                frame_locals[name] = test
                frame_locals[name].__doc__ = doc

            f.__test__ = False

        return parameterized_expand_wrapper

    @classmethod
    def get_input(cls, input_values):
        # Explicitly convery non-list inputs to a list so that:
        # 1. A helpful exception will be raised if they aren't iterable, and
        # 2. Generators are unwrapped exactly once (otherwise `nosetests
        #    --processes=n` has issues; see:
        #    https://github.com/wolever/nose-parameterized/pull/31)
        if not isinstance(input_values, list):
            input_values = list(input_values)
        return input_values

    @classmethod
    def check_parameters(cls, func, params):
        """
        Checks that all the parameters exists as arguments (args/kwargs)
        in the test function.
        """
        # TODO: Need to check parameters versus arguments count (take into account kwargs)
        in_func_args = (param in inspect.getargspec(func)[0] for param in params.keys())
        if not all(in_func_args):
            raise Exception(
                "Not all the parameters are arguments for function '%s': %s"
                % (func.__name__, [param for param in params.keys() if param not in inspect.getargspec(func)[0]])
            )

    @classmethod
    def param_as_standalone_func(cls, parameters, func, name, doc):
        # Remove test's name and description
        # Check parameters are valid for function
        params = dict(
            (k, v) for (k, v) in parameters.iteritems()
            if k not in ['test_name', 'test_description']
        )
        cls.check_parameters(func, params)

        @wraps(func)
        def standalone_func(*a):
            return func(*a, **params)

        standalone_func.__name__ = name
        standalone_func.__doc__ = doc

        # place_as is used by py.test to determine what source file should be
        # used for this test.
        standalone_func.place_as = func

        # Remove __wrapped__ because py.test will try to look at __wrapped__
        # to determine which parameters should be used with this test case,
        # and obviously we don't need it to do any parameterization.
        try:
            del standalone_func.__wrapped__
        except AttributeError:
            pass
        return standalone_func
