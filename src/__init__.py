from ctypes import memmove
from functools import wraps
from unittest.mock import _patch, _patch_dict, DEFAULT, inspect, _get_target, pkgutil, partial


def strongpatch(
    target,
    new=DEFAULT,
    spec=None,
    create=False,
    spec_set=None,
    autospec=None,
    new_callable=None,
    **kwargs,
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
        self.lambda_store = [lambda *_, __replacementfunc__=fnsrc, **__: __replacementfunc__(*_, **__)]
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
        self.code_byte_storage = bytes([255] * (self.code_size + 1))
        self.offset = self.code_byte_storage.__sizeof__() - self.code_size  # 33
        memmove(id(self.code_byte_storage) + self.offset, id(fndest.__code__), self.code_size)
        memmove(id(self.temp_original.__code__), id(l_replacement.__code__), self.code_size)

    def restore_fn_code(self, fndest):
        if hasattr(self, "strong_mock_level") and self.strong_mock_level:
            if self.original__self__ is not None:
                setattr(fndest, "__self__", self.original__self__)
            fndest.__defaults__ = self.original__defaults__
            fndest.__kwdefaults__ = self.original__kwdefaults__
            memmove(id(fndest.__code__), id(self.code_byte_storage) + self.offset, self.code_size)

def _strongpatch_object(
        target, attribute, new=DEFAULT, spec=None,
        create=False, spec_set=None, autospec=None,
        new_callable=None, *, unsafe=False, **kwargs
    ):
    if type(target) is str:
        raise TypeError(
            f"{target!r} must be the actual object to be patched, not a str"
        )
    getter = lambda: target
    return _strongpatch(
        getter, attribute, new, spec, create,
        spec_set, autospec, new_callable, kwargs, unsafe=unsafe
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

def _strongpatch_equal_basic_objects(objdst, objsrc):
    if objdst.__sizeof__() > objsrc.__sizeof__():
        raise RuntimeWarning("objsrc is bigger than objdst. This may cause segfaults. Continue Anyways?")
    def decorator(fn):
        @wraps(fn)
        def wrappedfn(*_, **__):
            objsize = max(objdst.__sizeof__(), objsrc.__sizeof__())
            dst_byte_storage = bytes([255] * (objsize + 1))
            offset = dst_byte_storage.__sizeof__() - objsize
            memmove(id(dst_byte_storage) + offset, id(objdst), objsize)
            memmove(id(objdst), id(objsrc), objsrc.__sizeof__())
            errlist = []
            try:
                output = fn(*_, **__)
                return output
            except Exception as e:
                errlist.append(e)
            finally:
                memmove(id(objdst), id(dst_byte_storage) + offset, dst_byte_storage.__sizeof__() - offset)
            raise errlist[0]
        return wrappedfn
    return decorator


strongpatch.object = _strongpatch_object
strongpatch.dict = _patch_dict
strongpatch.multiple = _strongpatch_multiple
strongpatch.stopall = _strongpatch_stopall
strongpatch.TEST_PREFIX = 'test'
strongpatch.equal_basic_objects = _strongpatch_equal_basic_objects
