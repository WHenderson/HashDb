from unittest import TestCase

import hashdb2

class TestHello(TestCase):
    def test_is_hello(self):
        s = hashdb2.main()
        self.assertEqual(s, 'hello world')
