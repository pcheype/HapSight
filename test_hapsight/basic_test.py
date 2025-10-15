import numpy as np

from hapsight.my_module import typed_function


def test_typed_function():
    assert not typed_function(np.zeros(10), "")
