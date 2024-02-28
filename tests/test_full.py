import unittest
from unittest.mock import MagicMock, patch

import tests.fnsource as fnsource
from src import strongpatch
from tests.fnsource import generic, pair, pairgeneric, plain, asyncplain


def plainmock():
    return "MOCKED"

async def asyncplainmock():
    return "MOCKED"

def genericmock(a, *args, b="d", c="c", **kwargs):
    return a + "MOCKED" + b + c + str((args, kwargs))


pairgenericmock = pair(genericmock)



class TestBasic(unittest.TestCase):

    @patch("tests.fnsource.plain", plainmock)
    def test_plain_0_mockfail(self):
        self.assertEqual(plain(), "ORIGINAL")

    @strongpatch("tests.fnsource.plain", plainmock)
    def test_plain_1_mockwork(self):
        self.assertEqual(plain(), "MOCKED")

    @strongpatch("tests.fnsource.plain")
    def test_plain_2_mockwork(self, _):
        self.assertIsInstance(plain(), MagicMock)

    @strongpatch.object(fnsource, "plain")
    def test_plain_3_mockobjectwork(self, _):
        self.assertIsInstance(plain(), MagicMock)

    def test_plain_4_after(self):
        self.assertEqual(plain(), "ORIGINAL")

class TestBasicObjectPatching(unittest.TestCase):

    @strongpatch.equal_basic_objects(100.0, 101.0)
    def test_float_patch_0(self):
        if 100.0 != 101.0:
            raise RuntimeError("FLOAT PATCH FAILED")

    def test_float_patch_1_after(self):
        if 100.0 == 101.0:
            raise RuntimeError("FLOAT PATCH REMOVAL FAILED")

    @strongpatch.equal_basic_objects(False, True)
    def test_truefalse_patch_0(self):
        if True != False:
            raise RuntimeError("TRUEFALSE PATCH FAILED")

    def test_truefalse_patch_1_after(self):
        if True == False:
            raise RuntimeError("TRUEFALSE PATCH REMOVAL FAILED")

    @strongpatch.equal_basic_objects(37838, 2673229)
    def test_int_patch_0(self):
        if 37838 != 2673229:
            raise RuntimeError("INT PATCH FAILED")

    def test_int_patch_1_after(self):
        if 37838 == 2673229:
            raise RuntimeError("INT PATCH REMOVAL FAILED")


class TestArgsKwargs(unittest.TestCase):

    def test_generic_0_before(self):
        self.assertEqual(generic("a"), "aORIGINALb((), {})")
        self.assertEqual(generic("a", b="c"), "aORIGINALc((), {})")
        self.assertEqual(generic("a", "x", b="c", y="z"), "aORIGINALc(('x',), {'y': 'z'})")

    @strongpatch("tests.fnsource.generic", lambda: "MOCKED")
    def test_generic_1_0_mocked(self):
        self.assertEqual(generic(), "MOCKED")

    @strongpatch("tests.fnsource.generic", lambda a="a": a + "MOCKED")
    def test_generic_1_1_mocked(self):
        self.assertEqual(generic(), "aMOCKED")
        self.assertEqual(generic(a="b"), "bMOCKED")

    @strongpatch("tests.fnsource.generic", genericmock)
    def test_generic_1_2_mocked(self):
        self.assertEqual(generic("a"), "aMOCKEDdc((), {})")
        self.assertEqual(generic("a", b="c"), "aMOCKEDcc((), {})")
        self.assertEqual(generic("a", "x", b="e", y="z"), "aMOCKEDec(('x',), {'y': 'z'})")

    def test_generic_2_after(self):
        self.assertEqual(generic("a"), "aORIGINALb((), {})")
        self.assertEqual(generic("a", b="c"), "aORIGINALc((), {})")
        self.assertEqual(generic("a", "x", b="c", y="z"), "aORIGINALc(('x',), {'y': 'z'})")


class TestClosurePair(unittest.TestCase):

    def test_generic_0_before(self):
        self.assertEqual(pairgeneric("a"), "aORIGINALb((), {})" * 2)
        self.assertEqual(pairgeneric("a", b="c"), "aORIGINALc((), {})" * 2)
        self.assertEqual(pairgeneric("a", "x", b="c", y="z"), "aORIGINALc(('x',), {'y': 'z'})" * 2)

    @strongpatch("tests.fnsource.pairgeneric", lambda: "MOCKED")
    def test_generic_1_0_mocked(self):
        self.assertEqual(pairgeneric(), "MOCKED")

    @strongpatch("tests.fnsource.pairgeneric", lambda a="a": a + "MOCKED")
    def test_generic_1_1_mocked(self):
        self.assertEqual(pairgeneric(), "aMOCKED")
        self.assertEqual(pairgeneric(a="b"), "bMOCKED")

    @strongpatch("tests.fnsource.pairgeneric", genericmock)
    def test_generic_1_2_mocked(self):
        self.assertEqual(pairgeneric("a"), "aMOCKEDdc((), {})")
        self.assertEqual(pairgeneric("a", b="c"), "aMOCKEDcc((), {})")
        self.assertEqual(pairgeneric("a", "x", b="e", y="z"), "aMOCKEDec(('x',), {'y': 'z'})")

    def test_generic_2_after(self):
        self.assertEqual(pairgeneric("a"), "aORIGINALb((), {})" * 2)
        self.assertEqual(pairgeneric("a", b="c"), "aORIGINALc((), {})" * 2)
        self.assertEqual(pairgeneric("a", "x", b="c", y="z"), "aORIGINALc(('x',), {'y': 'z'})" * 2)


class TestAsyncPlain(unittest.IsolatedAsyncioTestCase):

    async def test_async_plain_0_before(self):
        self.assertEqual(await asyncplain(), "ORIGINAL")

    @patch("tests.fnsource.asyncplain", asyncplainmock)
    async def test_async_plain_1_normal(self):
        self.assertEqual(await asyncplain(), "ORIGINAL")
    
    @strongpatch("tests.fnsource.asyncplain", asyncplainmock)
    async def test_async_plain_2_strong(self):
        self.assertEqual(await asyncplain(), "MOCKED")

    async def test_async_plain_4_after(self):
        self.assertEqual(await asyncplain(), "ORIGINAL")


if __name__ == "__main__":
    unittest.main()
