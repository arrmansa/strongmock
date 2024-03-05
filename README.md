# StrongMock

Ever wanted **Unlimited Power** while patching things ? 

StrongMock is a powerful mocking library for Python that leverages low-level ctypes functionality to provide extensive mocking capabilities. Some care may be needed while using this.

# Functionality/Usage

## Basic 
instead of `unittest.mock.patch` use `strongmock.strongpatch`

## More advanced features

### `strongpatch.equal_basic_objects`
Can make floats / ints / True False and other basic objects equal to each other. \
This customization of the equality behavior of basic objects can be useful when you have to test very very specific edge cases, maybe something governing program flow etc.

### `strongpatch.object`
Same as `patch.object`, but does the same advanced replacement as `strongpatch`

### `strongpatch.multiple`
Same as `patch.multiple`, but does the same advanced replacement as `strongpatch`

# Async

Also works on async functions, with similar stronger patching

# Safety

Some care has been taken to avoid crashes and breakage, but the user does have full control. One word answer - no.

# Working

## strongpatch

This applies when the target of a `strongmock.strongpatch` is a function defined in python with a `__code__` attribute. For other cases (methods in a class, classes, lbrary functions in c, etc.), the behaviour is the same as `unittest.patch`.\
This will patch the `__code__` attribute of the function to call the mock, meaning that references will also have the functionality of mock. \
This can be extremely convenient in some cases.

## strongpatch.equal_basic_objects

We dump the bytes from objsrc to objdst

### huh?

Yes, you can now pass these testcases.

```python
import unittest
from strongmock import strongpatch
class StrongMockDemoTest(unittest.TestCase):
    @strongpatch.equal_basic_objects(True, False)
    def test_true_and_false_are_equal(self):
        self.True != False:
```

# Links
[PyPi](https://pypi.org/project/strongmock) \
[GitHub](https://github.com/arrmansa/strongmock)

# License
StrongMock is licensed under the Unlicense. See the LICENSE file for details.

# Official theme music
When using these methods, it is recommended that you listen to this for better code. \
[Kai's Theme Epic Version (Slowed + BassBoosted)](https://www.youtube.com/watch?v=uMvNQRSKccg)