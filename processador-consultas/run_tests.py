import unittest
from test_h1u import ColoredTextTestRunner, TestSQLValidator, TestMetadata
from test_h2u import TestRelationalAlgebra
from test_h3u import TestOperatorGraph

def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # HU1
    suite.addTests(loader.loadTestsFromTestCase(TestSQLValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestMetadata))

    # HU2
    suite.addTests(loader.loadTestsFromTestCase(TestRelationalAlgebra))

    # HU3
    suite.addTests(loader.loadTestsFromTestCase(TestOperatorGraph))

    runner = ColoredTextTestRunner(verbosity=0)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    ok = main()
    raise SystemExit(0 if ok else 1)
