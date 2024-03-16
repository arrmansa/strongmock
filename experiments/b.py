from a import a as _source_a
from copy import deepcopy

a = deepcopy(_source_a)

print(a.f.__globals__)

print(id(a.f), id(_source_a.f))
print(id(a.f.__globals__), id(_source_a.f.__globals__))
print(a.f.__dict__)
print(a.f)

print(a.f.__globals__)
#a.f.__globals__ = _source_a.f.__globals__.copy()
object.__setattr__(a.f, "__globals__", _source_a.f.__globals__.copy())
a.f.__globals__["a"] = a

print(a.f())