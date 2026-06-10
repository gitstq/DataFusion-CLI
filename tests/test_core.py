"""
Unit tests for DataFusion core engine
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datafusion.core import DataFusionEngine, DataSource


class TestDataFusionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = DataFusionEngine()

    def test_add_source(self):
        data = [{"id": "1", "name": "Test"}]
        source = DataSource("test", "json", data)
        self.engine.add_source(source)
        self.assertEqual(len(self.engine.sources), 1)
        self.assertIn("test", self.engine.sources)

    def test_schema_inference(self):
        data = [
            {"id": "1", "name": "Alice", "age": 30, "active": True},
            {"id": "2", "name": "Bob", "age": 25, "active": False}
        ]
        source = DataSource("users", "json", data)
        schema = source.get_schema()
        self.assertEqual(schema["id"], "str")
        self.assertEqual(schema["name"], "str")
        self.assertEqual(schema["age"], "int")
        self.assertEqual(schema["active"], "bool")

    def test_conflict_detection(self):
        data_a = [{"id": "1", "name": "Alice", "age": 30}]
        data_b = [{"id": "1", "name": "Alice", "age": 31}]
        self.engine.add_source(DataSource("src_a", "json", data_a))
        self.engine.add_source(DataSource("src_b", "json", data_b))

        conflicts = self.engine.detect_conflicts("id")
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["key"], "1")

    def test_fuse_merge(self):
        data_a = [{"id": "1", "name": "Alice", "city": "Beijing"}]
        data_b = [{"id": "1", "name": "Alice", "email": "alice@test.com"}]
        self.engine.add_source(DataSource("src_a", "json", data_a))
        self.engine.add_source(DataSource("src_b", "json", data_b))

        fused = self.engine.fuse("id", conflict_strategy="merge")
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0]["city"], "Beijing")
        self.assertEqual(fused[0]["email"], "alice@test.com")

    def test_find_relations(self):
        data = [
            {"id": "1", "name": "Alice", "dept": "Engineering"},
            {"id": "2", "name": "Bob", "dept": "Engineering"},
            {"id": "3", "name": "Charlie", "dept": "Product"}
        ]
        self.engine.add_source(DataSource("employees", "json", data))
        self.engine.fuse("id")

        relations = self.engine.find_relations("id", ["dept"])
        self.assertIn("dept:Engineering", relations)
        self.assertEqual(len(relations["dept:Engineering"]), 2)

    def test_statistics(self):
        data_a = [{"id": "1", "name": "Alice"}]
        data_b = [{"id": "2", "name": "Bob"}]
        self.engine.add_source(DataSource("src_a", "json", data_a))
        self.engine.add_source(DataSource("src_b", "json", data_b))
        self.engine.fuse("id")

        stats = self.engine.compute_statistics()
        self.assertEqual(stats["total_sources"], 2)
        self.assertEqual(stats["total_records_fused"], 2)


class TestDataSource(unittest.TestCase):

    def test_record_count(self):
        data = [{"id": "1"}, {"id": "2"}]
        source = DataSource("test", "json", data)
        self.assertEqual(source.record_count, 2)

    def test_metadata(self):
        data = [{"id": "1"}]
        source = DataSource("test", "json", data, {"file": "test.json"})
        self.assertEqual(source.metadata["file"], "test.json")


if __name__ == '__main__':
    unittest.main()
