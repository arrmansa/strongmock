import inspect
from ctypes import memmove
from unittest.mock import DEFAULT, _get_target, _patch

def strongpatch(
        target, new=DEFAULT, spec=None, create=False,
        spec_set=None, autospec=None, new_callable=None, **kwargs
    ):

    getter, attribute = _get_target(target)
    return _strongpatch(
        getter, attribute, new, spec, create,
        spec_set, autospec, new_callable, kwargs
    )

class _strongpatch(_patch):

    def copy(self):
        patcher = _strongpatch(
            self.getter, self.attribute, self.new, self.spec,
            self.create, self.spec_set,
            self.autospec, self.new_callable, self.kwargs
        )
        patcher.attribute_name = self.attribute_name
        patcher.additional_patchers = [
            p.copy() for p in self.additional_patchers
        ]
        return patcher

    def __enter__(self):
        super().__enter__()
        self.strong_mock_level = 0
        if inspect.isfunction(self.temp_original) and hasattr(self.temp_original, "__code__"):
            replacement = getattr(self.target, self.attribute)
            if hasattr(replacement, "__code__"):
                pass
            elif hasattr(replacement, '__call__'):
                if not hasattr(replacement.__call__, "__code__"):
                    return 
                replacement = replacement.__call__
            else:
                return
            # TRY LEVEL 1 MOCK
            try:
                raise NotImplementedError("Not sure if this works")
                self.code_backup = self.temp_original.__code__
                self.temp_original.__code__ = replacement.__code__
                self.strong_mock_level = 1
                return
            except:
                self.strong_mock_level = 0
            assert self.temp_original.__kwdefaults__ is None or '__replacementfunc__' not in self.temp_original.__kwdefaults__
            self.original__kwdefaults__ = self.temp_original.__kwdefaults__
            self.lambda_store = [lambda *_, __replacementfunc__=replacement, **__ : __replacementfunc__(*_, **__)]
            l_replacement = self.lambda_store[0]
            self.temp_original.__kwdefaults__ = l_replacement.__kwdefaults__ if self.original__kwdefaults__ is None else {**self.original__kwdefaults__, **l_replacement.__kwdefaults__ }
            self.code_size = max(self.temp_original.__code__.__sizeof__(), l_replacement.__code__.__sizeof__())
            self.code_byte_storage = bytes([255]*(self.code_size+1))
            self.offset = self.code_byte_storage.__sizeof__() - self.code_size # 33
            memmove(id(self.code_byte_storage) + self.offset, id(self.temp_original.__code__), self.code_size)
            memmove(id(self.temp_original.__code__), id(l_replacement.__code__), self.code_size)
            self.strong_mock_level = 2
            
    def __exit__(self, *_):
        if self.strong_mock_level == 0:
            pass
        elif self.strong_mock_level == 1:
            self.temp_original.__code__ = self.code_backup
        elif self.strong_mock_level == 2:
            self.temp_original.__kwdefaults__ = self.original__kwdefaults__
            memmove(id(self.temp_original.__code__), id(self.code_byte_storage) + self.offset, self.code_size)
        super().__exit__(*_)