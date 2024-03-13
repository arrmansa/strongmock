import inspect
import sys
import builtins
import pkgutil
from ctypes import memmove
from functools import wraps, partial
from unittest.mock import DEFAULT, MagicMock, _get_target, _patch, _patch_dict


class memmove_objects:
    """
    A context manager and decorator for doing memmove on 2 objects.
    """

    def __init__(self, objsrc, objdst):
        self.objsrc = objsrc
        self.objdst = objdst
        self.obj_size = objsrc.__sizeof__()
        self.dstobj_byte_storage = bytes([255] * (self.obj_size + 1))
        self.offset = self.dstobj_byte_storage.__sizeof__() - self.obj_size

    def __enter__(self):
        memmove(id(self.dstobj_byte_storage) + self.offset, id(self.objdst), self.obj_size)
        memmove(id(self.objdst), id(self.objsrc), self.obj_size)

    def __exit__(self, *_):
        memmove(id(self.objdst), id(self.dstobj_byte_storage) + self.offset, self.obj_size)

    def __call__(self, fn):
        @wraps(fn)
        def decoratedfn(*_, **__):
            with self:
                return fn(*_, **__)

        return decoratedfn


class mock_imports:
    def __init__(self, module_names, override=True):
        self.module_names = module_names
        self.override = override

    def __enter__(self):
        self.original_import = builtins.__import__
        self.added_names = {}

        def _import(name, *args, **kwargs):
            if any(map(name.startswith, self.module_names)):
                if name not in sys.modules:
                    self.added_names[name] = None
                    sys.modules[name] = MagicMock(spec=None)
                else:
                    if not isinstance(sys.modules[name], MagicMock):
                        self.added_names[name] = sys.modules[name]
                        sys.modules[name] = MagicMock(spec=None)
                    return sys.modules[name]
                return sys.modules[name]
            else:
                return self.original_import(name, *args, **kwargs)

        builtins.__import__ = _import

    def __exit__(self, *_):
        builtins.__import__ = self.original_import
        for name, value in self.added_names.items():
            if value is None:
                del sys.modules[name]
            else:
                sys.modules[name] = value

    def __call__(self, fn):
        @wraps(fn)
        def decoratedfn(*_, **__):
            with self:
                return fn(*_, **__)

        return decoratedfn


def get_definition_requirements(fnsrc):
    argtypes = set(p.kind for p in inspect.signature(fnsrc).parameters.values())
    positional_test = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    keyword_test = (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    position_needed = any(map(argtypes.__contains__, positional_test))
    keyword_needed = any(map(argtypes.__contains__, keyword_test))
    return position_needed, keyword_needed


class _strongpatch(_patch):

    def copy(self):
        patcher = _strongpatch(self.getter, self.attribute, self.new, self.spec, self.create, self.spec_set, self.autospec, self.new_callable, self.kwargs)
        patcher.attribute_name = self.attribute_name
        patcher.additional_patchers = [p.copy() for p in self.additional_patchers]
        return patcher

    def __enter__(self):
        super().__enter__()
        if inspect.isfunction(self.temp_original) and hasattr(self.temp_original, "__code__"):
            replacement = getattr(self.target, self.attribute)
            if callable(replacement):
                self.fn_replacement_data = self.replace_fn_code(replacement, self.temp_original)

    def __exit__(self, *_):
        if hasattr(self, "fn_replacement_data"):
            self.restore_fn_code(self.temp_original, self.fn_replacement_data)
        super().__exit__(*_)

    @staticmethod
    def replace_fn_code(fnsrc, fndest):
        """
        Args:
            fndest (function): a function that will have it's __code__ replaced
            fnsrc (function): a function that will be called instead
        """
        # A non-closure lambda function with __replacementfunc__ kwarg that will be the __code__ donor
        position_needed, keyword_needed = get_definition_requirements(fnsrc)
        if position_needed and keyword_needed:
            l_replacement = lambda *_, __replacementfunc__=fnsrc, **__: __replacementfunc__(*_, **__)
        elif not position_needed and keyword_needed:
            l_replacement = lambda __replacementfunc__=fnsrc, **__: __replacementfunc__(**__)
        elif position_needed and not keyword_needed:
            l_replacement = lambda *_, __replacementfunc__=fnsrc: __replacementfunc__(*_)
        elif not position_needed and not keyword_needed:
            l_replacement = lambda __replacementfunc__=fnsrc: __replacementfunc__()

        # Store original defaults
        original_defaults = fndest.__defaults__, fndest.__kwdefaults__

        # Change fndest
        fndest.__defaults__ = l_replacement.__defaults__
        fndest.__kwdefaults__ = l_replacement.__kwdefaults__

        # Replace the code object with memmove
        memmove_backup = memmove_objects(l_replacement.__code__, fndest.__code__)
        memmove_backup.__enter__()

        return memmove_backup, original_defaults

    @staticmethod
    def restore_fn_code(fndest, fn_replacement_data):
        memmove_backup, original_defaults = fn_replacement_data
        fndest.__defaults__, fndest.__kwdefaults__ = original_defaults
        memmove_backup.__exit__()


class strongpatch:
    def __new__(cls, target, new=DEFAULT, spec=None, create=False, spec_set=None, autospec=None, new_callable=None, **kwargs):
        getter, attribute = _get_target(target)
        return _strongpatch(getter, attribute, new, spec, create, spec_set, autospec, new_callable, kwargs)

    @staticmethod
    def dict(*_, **__):
        _patch_dict(*_, **__)

    @staticmethod
    def object(target, attribute, new=DEFAULT, spec=None, create=False, spec_set=None, autospec=None, new_callable=None, *, unsafe=False, **kwargs):
        if type(target) is str:
            raise TypeError(f"{target!r} must be the actual object to be patched, not a str")
        getter = lambda: target
        return _strongpatch(getter, attribute, new, spec, create, spec_set, autospec, new_callable, kwargs)

    @staticmethod
    def multiple(target, spec=None, create=False, spec_set=None, autospec=None, new_callable=None, **kwargs):
        if type(target) is str:
            getter = partial(pkgutil.resolve_name, target)
        else:
            getter = lambda: target

        if not kwargs:
            raise ValueError("Must supply at least one keyword argument with patch.multiple")
        # need to wrap in a list for python 3, where items is a view
        items = list(kwargs.items())
        attribute, new = items[0]
        patcher = _strongpatch(getter, attribute, new, spec, create, spec_set, autospec, new_callable, {})
        patcher.attribute_name = attribute
        for attribute, new in items[1:]:
            this_patcher = _strongpatch(getter, attribute, new, spec, create, spec_set, autospec, new_callable, {})
            this_patcher.attribute_name = attribute
            patcher.additional_patchers.append(this_patcher)
        return patcher

    @staticmethod
    def stopall():
        for strongpatch in reversed(_strongpatch._active_patches):
            strongpatch.stop()

    @staticmethod
    def equal_basic_objects(objsrc, objdst, skip_check=False):
        if skip_check and (objdst.__sizeof__() < objsrc.__sizeof__()):
            raise RuntimeWarning("objsrc is bigger than objdst. This may cause segfaults")
        return memmove_objects(objsrc, objdst)

    mock_imports = mock_imports
