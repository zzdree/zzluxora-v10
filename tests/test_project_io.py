import os
import tempfile
import unittest
from core.project_io import ProjectIO


class TestProjectIO(unittest.TestCase):
    def test_default_project_creation(self):
        proj = ProjectIO.create_default_project("My Service Sunday")
        self.assertEqual(proj["app"], "ZZLUXORA")
        self.assertEqual(proj["version"], ProjectIO.VERSION)
        self.assertEqual(proj["project_name"], "My Service Sunday")
        self.assertEqual(len(proj["patches"]), 2)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test_proj.zlx")
            original_data = ProjectIO.create_default_project("Test Church Event")
            original_data["target_ip"] = "192.168.4.1"

            save_ok = ProjectIO.save_project(original_data, file_path)
            self.assertTrue(save_ok)
            self.assertTrue(os.path.exists(file_path))

            loaded_data = ProjectIO.load_project(file_path)
            self.assertIsNotNone(loaded_data)
            self.assertEqual(loaded_data["project_name"], "Test Church Event")
            self.assertEqual(loaded_data["target_ip"], "192.168.4.1")


if __name__ == "__main__":
    unittest.main()
