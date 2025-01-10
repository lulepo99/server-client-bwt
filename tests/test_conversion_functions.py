import unittest
from conversion_functions import burrows_wheeler_conversion, revert_burrows_wheeler


# Testing is perfomed considering valid inputs only, as input validation is handled by the client
class TestConversionFunctions(unittest.TestCase):

    def test_burrows_wheeler_conversion(self):
        self.assertEqual(burrows_wheeler_conversion("ACGTACGTACGTACGTACGT"), "TTTTT$AAAAACCCCCGGGGG")

    def test_revert_burrows_wheeler(self):
        self.assertEqual(revert_burrows_wheeler("TTTTT$AAAAACCCCCGGGGG"), "ACGTACGTACGTACGTACGT")


if __name__ == "__main__":
    unittest.main()
