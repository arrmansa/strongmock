from fnsource import abc
from src import strongpatch
import unittest
from unittest.mock import patch

def newtestabc():
    print("MOCKED")
    return 0

class alltests(unittest.TestCase):

    @patch("fnsource.abc", newtestabc)
    def test_everything_1(self):
        print("INSIDE")
        abc()
        print("CALL_DONE")

    @strongpatch("fnsource.abc", newtestabc)
    def test_everything_1(self):
        print("INSIDE")
        abc()
        print("CALL_DONE")
    
    def test_everything_2(self):
        print("INSIDE_2")
        abc()
        print("CALL_DONE_2")

if __name__ == '__main__':
    unittest.main()