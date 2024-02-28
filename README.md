# StrongMock
StrongMock is a powerful mocking library for Python that leverages low-level ctypes functionality to provide extensive mocking capabilities. Some care may be needed while using this.

# Functionality
This applies when the target of a `strongmock.strongpatch` is a function defined in python with a `__code__` attribute. For other cases (methods in a class, classes, lbrary functions in c, etc.), the behaviour is the same as `unittest.patch`.\
This will patch the `__code__` attribute of the function to call the mock, meaning that references will also have the functionality of mock. \
This can be extremely convenient in some cases.

# Usage
instead of `unittest.mock.patch` use `strongmock.strongpatch`

# Links
[PyPi](https://pypi.org/project/strongmock) \
[GitHub](https://github.com/arrmansa/strongmock)

# License
StrongMock is licensed under the Unlicense. See the LICENSE file for details.
