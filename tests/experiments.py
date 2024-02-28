# noqa: T201, ERA001
# Used rescources
# https://stackoverflow.com/questions/54602320/correctly-replace-a-functions-code-object
# https://docs.python.org/3/reference/datamodel.html#the-standard-type-hierarchy
# https://github.com/arrmansa/modify-tuples-strings-inplace-python/blob/main/final_functions.py
# https://docs.python.org/3/library/inspect.html
# coverage run --source=src -m unittest discover --v


class methodstest:
    @staticmethod
    def a():
        pass

    @classmethod
    def b(cls):
        pass

    def c(self):
        pass


print(methodstest.b.__self__, methodstest().c.__self__)


def dog():
    return "woof"


def cat():
    return "meow"


def do_stuff(seq):
    t1 = sum(seq)
    seq2 = [e + t1 for e in seq]
    t2 = sum(seq2)
    return t1 + t2


def pair(animal):
    def ret():
        return animal() + animal()

    return ret


cats = pair(cat)

print(dog())  # woof
print(cat())  # meow
print(cats())  # meowmeow
print(do_stuff([1, 2, 3]))  # 30

do_stuff.__code__ = dog.__code__
print(do_stuff())  # woof

print(cats.__code__.co_freevars, dog.__code__.co_freevars)  # ('animal',)
# dog.__code__ = cats.__code__.replace(co_freevars=dog.__code__.co_freevars)

print(dog.__code__.__sizeof__(), dog.__code__.replace(co_code=cats.__code__.co_code).__sizeof__(), cats.__code__.__sizeof__())
print(id(dog.__code__.co_freevars), id(dog.__code__))


from ctypes import memmove

catsnew = lambda *_, __replacementfunc__=cats, **__: __replacementfunc__()  # noqa: E731

catsnew()
print("A" * 10)
# memmove(id(dog.__code__), id(dog.__code__.replace(co_freevars=dog.__code__.co_freevars)), 176)
offset = 0
print(dog.__kwdefaults__, catsnew.__kwdefaults__)

code_size = dog.__code__.__sizeof__()
code_byte_storage = bytes([255] * (code_size + 1))
offset = code_byte_storage.__sizeof__() - code_size  # 33
origkwdefaults = dog.__kwdefaults__
memmove(id(code_byte_storage) + offset, id(dog.__code__), code_size)
memmove(id(dog.__code__), id(catsnew.__code__), catsnew.__code__.__sizeof__())
dog.__kwdefaults__ = catsnew.__kwdefaults__
print("MEMMOVE_DONE")
print(dog())  # meowmeow
memmove(id(dog.__code__), id(code_byte_storage) + offset, code_size)
dog.__kwdefaults__ = origkwdefaults
print(dog())  # woof
print(code_byte_storage)
