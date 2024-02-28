import inspect
from ctypes import memmove
from unittest.mock import DEFAULT, _get_target, _patch


def strongpatch(
        target, new=DEFAULT, spec=None, create=False,
        spec_set=None, autospec=None, new_callable=None, **kwargs,
    ):

    getter, attribute = _get_target(target)
    return _strongpatch(
        getter, attribute, new, spec, create,
        spec_set, autospec, new_callable, kwargs,
    )

class _strongpatch(_patch):

    def copy(self):
        patcher = _strongpatch(
            self.getter, self.attribute, self.new, self.spec,
            self.create, self.spec_set,
            self.autospec, self.new_callable, self.kwargs,
        )
        patcher.attribute_name = self.attribute_name
        patcher.additional_patchers = [
            p.copy() for p in self.additional_patchers
        ]
        return patcher

    def __enter__(self):
        super().__enter__()
        if inspect.isfunction(self.temp_original) and hasattr(self.temp_original, "__code__"):
            replacement = getattr(self.target, self.attribute)
            if callable(replacement):
                self.replace_fn_code(self.temp_original, replacement)

    def __exit__(self, *_):
        self.restore_fn_code(self.temp_original)
        super().__exit__(*_)

    def replace_fn_code(self, fndest, fnsrc):
        """
        self.strong_mock_level indicates forcefulness of changes made
        Args:
            fndest (function): a function that will have it's __code__ replaced
            fnsrc (function): a function that will be called instead
        """
        self.strong_mock_level = True
        # A non-closure lambda function with __replacementfunc__ kwarg that will be the __code__ donor
        self.lambda_store = [lambda *_, __replacementfunc__=fnsrc, **__ : __replacementfunc__(*_, **__)]
        l_replacement = self.lambda_store[0]

        # Store original defaults
        self.original__self__ = getattr(fndest, "__self__", None)
        self.original__defaults__ = fndest.__defaults__
        self.original__kwdefaults__ = fndest.__kwdefaults__

        # Change fndest
        if hasattr(fndest, "__self__"):
            delattr(fndest, "__self__")
        fndest.__defaults__ = l_replacement.__defaults__
        fndest.__kwdefaults__ = l_replacement.__kwdefaults__

        # Replace the code object with memset
        self.code_size = max(fndest.__code__.__sizeof__(), l_replacement.__code__.__sizeof__())
        self.code_byte_storage = bytes([255]*(self.code_size+1))
        self.offset = self.code_byte_storage.__sizeof__() - self.code_size # 33
        memmove(id(self.code_byte_storage) + self.offset, id(fndest.__code__), self.code_size)
        memmove(id(self.temp_original.__code__), id(l_replacement.__code__), self.code_size)

    def restore_fn_code(self, fndest):
        if hasattr(self, "strong_mock_level") and self.strong_mock_level:
            if self.original__self__ is not None:
                setattr(fndest, "__self__", self.original__self__)
            fndest.__defaults__ = self.original__defaults__
            fndest.__kwdefaults__ = self.original__kwdefaults__
            memmove(id(fndest.__code__), id(self.code_byte_storage) + self.offset, self.code_size)
