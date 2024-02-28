# StrongMock
StrongMock is a powerful mocking library for Python that leverages low-level ctypes functionality to provide extensive mocking capabilities. Some care may be needed while using this.

# Functionality
This will patch the `__code__` attribute of a function with your new function, meaning that references will also have the functionality of mock. This can occasionally be extremely convenient.

# Usage
instead of `unittest.mock.patch` use `strongmock.strongpatch`
