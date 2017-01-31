from unittest import TestCase
from hashdb2.orm import create, create_schema

class TestORM(TestCase):
    def test_create_schema(self):
        engine = create(None)
        create_schema(engine)
