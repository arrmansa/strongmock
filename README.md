# StrongMock

Ever wanted **Unlimited Power** while patching things ? 

StrongMock is a powerful mocking library for Python that leverages low-level ctypes functionality to provide extensive mocking capabilities. Some care may be needed while using this.

# Functionality/Usage

## Basic 

1. Instead of `from unittest.mock import patch` use `from strongmock import strongpatch`. 
2. `strongpatch` is an alias for `patch` in the module, meaning `from strongmock import patch` can also be used.
3. Full compatibility - all methods and classes present in `unittest.mock` are present in `strongmock`.
4. `isinstance` compatibility - limited to `Mock`, `MagicMock` and `AsyncMock`.

## More features

### `strongpatch.equal_basic_objects`
Can make floats / ints / True False and other basic objects equal to each other. \
This customization of the equality behavior of basic objects can be useful when you have to test very very specific edge cases, maybe something governing program flow etc. Can also be used as a context manager.

### `strongpatch.mock_imports`
Replaces imports with Magicmock, takes in a tuple of strings, optional parameter override which decides if we override existing imports as well (True by default). Can also be used as a context manager.

# Async

Also works on async functions, with similar stronger patching

# Safety

Some care has been taken to avoid crashes and breakage, but the user does have full control. One word answer - no.
## Note - we have 100% Coverage, all Testcases passing

# Working and usage

## strongpatch

This applies when the target of a `strongmock.strongpatch` is a function defined in python with a `__code__` attribute. For other cases (methods in a class, classes, lbrary functions in c, etc.), the behaviour is the same as `unittest.patch`.\
This will patch the `__code__` attribute of the function to call the mock, meaning that references will also have the functionality of mock. \
This can be extremely convenient in some cases.

## strongpatch.mock_imports

We can pass testcases that need imports inside them

```python
class TestImportPatch(unittest.TestCase):
    @strongpatch.mock_imports(("somelib_abcd",))
    def test_import_somelib_abcd(self):
        import somelib_abcd
        self.assertIsInstance(somelib_abcd.somefn(), MagicMock)
```

## strongpatch.equal_basic_objects

We dump the bytes from objsrc to objdst, meaning we can do basically do `True = False` or `1 = 2` (not `==` as in comparison but `=` as in assignment)

### huh?

Yes, you can now pass these testcases.

```python
import unittest
from strongmock import strongpatch
class StrongMockDemoTest(unittest.TestCase):
    @strongpatch.equal_basic_objects(False, True)
    def test_truefalse_patch_0(self):
        if True != False:
            raise RuntimeError("TRUEFALSE PATCH FAILED")
```

# Links
[PyPi](https://pypi.org/project/strongmock) \
[GitHub](https://github.com/arrmansa/strongmock)

# License
StrongMock is licensed under the Unlicense. See the LICENSE file for details.

# Official theme music
When using these methods, it is recommended that you listen to this for better code. \
[Kai's Theme Epic Version (Slowed + BassBoosted)](https://www.youtube.com/watch?v=uMvNQRSKccg)