import unittest
from core.emotion_model import EmotionModel
from core.models import EmotionCoordinate


class TestEmotionModel(unittest.TestCase):
    def setUp(self):
        self.model = EmotionModel()

    def test_praise_classification(self):
        # Major-like chroma vector (e.g. C Major energy high on C=0, E=4, G=7)
        c_major_chroma = [1.0, 0.1, 0.1, 0.1, 0.9, 0.1, 0.1, 0.8, 0.1, 0.1, 0.1, 0.1]

        # Fast tempo 130 BPM, high RMS, bright centroid
        emotion = self.model.evaluate_frame(
            rms_norm=0.85,
            centroid_norm=0.80,
            chroma_12=c_major_chroma,
            tempo_bpm=130.0,
            onset_norm=0.75,
            mfcc_norm=0.70
        )

        self.assertGreater(emotion.valence, 0.0)
        self.assertGreater(emotion.arousal, 0.0)
        self.assertEqual(emotion.quadrant, "Q1_PRAISE_HIGH")

    def test_worship_ambient_classification(self):
        # Minor-like chroma vector (e.g. A Minor energy high on A=9, C=0, E=4)
        a_minor_chroma = [0.8, 0.1, 0.1, 0.1, 0.7, 0.1, 0.1, 0.1, 0.1, 1.0, 0.1, 0.1]

        # Slow tempo 65 BPM, low RMS, darker centroid
        emotion = self.model.evaluate_frame(
            rms_norm=0.25,
            centroid_norm=0.20,
            chroma_12=a_minor_chroma,
            tempo_bpm=65.0,
            onset_norm=0.10,
            mfcc_norm=0.30
        )

        self.assertLess(emotion.arousal, 0.0)
        self.assertIn(emotion.quadrant, ["Q3_DEEP_WORSHIP", "Q4_PEACE_INTIMACY"])


if __name__ == "__main__":
    unittest.main()
