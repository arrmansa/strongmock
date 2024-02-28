from ctypes import memmove
from functools import wraps
import pkgutil
import inspect
from unittest.mock import _patch, _patch_dict, DEFAULT, _get_target, partial

def _memmove_replacement(objsrc, objdst):
    # Replace the code object with memset
    obj_size = objsrc.__sizeof__()
    dstobj_byte_storage = bytes([255] * (obj_size + 1))
    offset = dstobj_byte_storage.__sizeof__() - obj_size  # 33
    memmove(id(dstobj_byte_storage) + offset, id(objdst), obj_size)
    memmove(id(objdst), id(objsrc), obj_size)
    return obj_size, dstobj_byte_storage

def _memmove_unreplacement(objsize, dst_byte_storage, objdst):
    offset = dst_byte_storage.__sizeof__() - objsize
    memmove(id(objdst), id(dst_byte_storage) + offset, objsize)


def get_definition_requirements(fnsrc):
    argtypes = set(p.kind for p in inspect.signature(fnsrc).parameters.values())
    if any(map(argtypes.__contains__, (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.POSITIONAL_OR_KEYWORD))):
        position_needed = True
    else:
        position_needed = False
    if any(map(argtypes.__contains__, (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD, inspect.Parameter.POSITIONAL_OR_KEYWORD))):
        keyword_needed = True
    else:
        keyword_needed = False
    return position_needed, keyword_needed

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

    attribute_name = None
    _active_patches = []

    def copy(self):
        patcher = _strongpatch(
            self.getter, self.attribute, self.new, self.spec,
            self.create, self.spec_set,
            self.autospec, self.new_callable, self.kwargs,
        )
        patcher.attribute_name = self.attribute_name
        patcher.additional_patchers = [p.copy() for p in self.additional_patchers]
        return patcher

    def __enter__(self):
        super().__enter__()
        if inspect.isfunction(self.temp_original) and hasattr(self.temp_original, "__code__"):
            replacement = getattr(self.target, self.attribute)
            if callable(replacement):
                self.replace_fn_code(replacement, self.temp_original)

    def __exit__(self, *_):
        self.restore_fn_code(self.temp_original)
        super().__exit__(*_)

    def replace_fn_code(self, fnsrc, fndest):
        """
        self.strong_mock_level indicates forcefulness of changes made
        Args:
            fndest (function): a function that will have it's __code__ replaced
            fnsrc (function): a function that will be called instead
        """
        self.strong_mock_level = True

        # A non-closure lambda function with __replacementfunc__ kwarg that will be the __code__ donor
        position_needed, keyword_needed = get_definition_requirements(fnsrc)
        self.lambda_store = [lambda *_, __replacementfunc__=fnsrc, **__: __replacementfunc__(*_, **__)]
        if position_needed and keyword_needed:
            self.lambda_store = [lambda *_, __replacementfunc__=fnsrc, **__: __replacementfunc__(*_, **__)]
        elif not position_needed and keyword_needed:
            self.lambda_store = [lambda __replacementfunc__=fnsrc, **__: __replacementfunc__(**__)]
        elif position_needed and not keyword_needed:
            self.lambda_store = [lambda *_, __replacementfunc__=fnsrc: __replacementfunc__(*_)]
        elif not position_needed and not keyword_needed:
            self.lambda_store = [lambda __replacementfunc__=fnsrc: __replacementfunc__()]
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

        # Replace the code object with memmove
        self.memmove_backup = _memmove_replacement(l_replacement.__code__, fndest.__code__)

    def restore_fn_code(self, fndest):
        if hasattr(self, "strong_mock_level") and self.strong_mock_level:
            if self.original__self__ is not None:
                setattr(fndest, "__self__", self.original__self__)
            fndest.__defaults__ = self.original__defaults__
            fndest.__kwdefaults__ = self.original__kwdefaults__
            _memmove_unreplacement(*self.memmove_backup, fndest.__code__)

def _strongpatch_object(
        target, attribute, new=DEFAULT, spec=None,
        create=False, spec_set=None, autospec=None,
        new_callable=None, *, unsafe=False, **kwargs,
    ):
    if type(target) is str:
        raise TypeError(
            f"{target!r} must be the actual object to be patched, not a str"
        )
    getter = lambda: target
    return _strongpatch(
        getter, attribute, new, spec, create,
        spec_set, autospec, new_callable, kwargs
    )

def _strongpatch_multiple(target, spec=None, create=False, spec_set=None,
                    autospec=None, new_callable=None, **kwargs):
    if type(target) is str:
        getter = partial(pkgutil.resolve_name, target)
    else:
        getter = lambda: target

    if not kwargs:
        raise ValueError(
            'Must supply at least one keyword argument with patch.multiple'
        )
    # need to wrap in a list for python 3, where items is a view
    items = list(kwargs.items())
    attribute, new = items[0]
    patcher = _strongpatch(
        getter, attribute, new, spec, create, spec_set,
        autospec, new_callable, {}
    )
    patcher.attribute_name = attribute
    for attribute, new in items[1:]:
        this_patcher = _strongpatch(
            getter, attribute, new, spec, create, spec_set,
            autospec, new_callable, {}
        )
        this_patcher.attribute_name = attribute
        patcher.additional_patchers.append(this_patcher)
    return patcher

def _strongpatch_stopall():
    """Stop all active patches. LIFO to unroll nested patches."""
    for patch in reversed(_strongpatch._active_patches):
        patch.stop()

def _strongpatch_equal_basic_objects(objsrc, objdst):
    if objdst.__sizeof__() < objsrc.__sizeof__():
        raise RuntimeWarning("objsrc is bigger than objdst. This may cause segfaults")
    def decorator(fn):
        @wraps(fn)
        def wrappedfn(*_, **__):
            memmove_backup = _memmove_replacement(objsrc, objdst)
            errlist = []
            try:
                output = fn(*_, **__)
                return output
            except:
                raise
            finally:
                _memmove_unreplacement(*memmove_backup, objdst)
        return wrappedfn
    return decorator

strongpatch.object = _strongpatch_object
strongpatch.dict = _patch_dict
strongpatch.multiple = _strongpatch_multiple
strongpatch.stopall = _strongpatch_stopall
strongpatch.TEST_PREFIX = 'test'
strongpatch.equal_basic_objects = _strongpatch_equal_basic_objects
