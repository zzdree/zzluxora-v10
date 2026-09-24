import unittest
from core.color_engine import ColorEngine


class TestColorEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ColorEngine()

    def test_hsv_to_rgb(self):
        # Pure Red: H=0, S=1, V=1
        r, g, b = self.engine.hsv_to_rgb(0, 1.0, 1.0)
        self.assertEqual((r, g, b), (255, 0, 0))

        # Pure Green: H=120, S=1, V=1
        r, g, b = self.engine.hsv_to_rgb(120, 1.0, 1.0)
        self.assertEqual((r, g, b), (0, 255, 0))

        # Pure Blue: H=240, S=1, V=1
        r, g, b = self.engine.hsv_to_rgb(240, 1.0, 1.0)
        self.assertEqual((r, g, b), (0, 0, 255))

    def test_physical_rgbw_decomposition(self):
        # Case 1: Pure saturated color (e.g. Red 255, 0, 0) -> W should be 0
        rgbw = self.engine.rgb_to_physical_rgbw(255, 0, 0)
        self.assertEqual(rgbw.red, 255)
        self.assertEqual(rgbw.green, 0)
        self.assertEqual(rgbw.blue, 0)
        self.assertEqual(rgbw.white, 0)

        # Case 2: Pure White (255, 255, 255) -> R,G,B should be 0, W should be 255
        rgbw = self.engine.rgb_to_physical_rgbw(255, 255, 255)
        self.assertEqual(rgbw.red, 0)
        self.assertEqual(rgbw.green, 0)
        self.assertEqual(rgbw.blue, 0)
        self.assertEqual(rgbw.white, 255)

        # Case 3: Pastel Pink (255, 100, 100) -> W=100, R=155, G=0, B=0
        rgbw = self.engine.rgb_to_physical_rgbw(255, 100, 100)
        self.assertEqual(rgbw.white, 100)
        self.assertEqual(rgbw.red, 155)
        self.assertEqual(rgbw.green, 0)
        self.assertEqual(rgbw.blue, 0)


if __name__ == "__main__":
    unittest.main()
