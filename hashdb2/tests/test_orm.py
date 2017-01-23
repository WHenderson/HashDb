from unittest import TestCase
from hashdb2.orm import create_schema
import sqlite3

class TestORM(TestCase):
    def test_create_schema(self):
        conn = sqlite3.connect(':memory:')
        create_schema(conn)
