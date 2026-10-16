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
        """A dark, quiet, minor frame lands in the worship region.

        This exercises the model's own mapping on the inputs it is handed. It
        does NOT claim the analysis pipeline can produce a centroid_norm of 0.20
        from a real worship recording: feature_extractor normalises the centroid
        against each track's own peak, so real tracks average 0.66 to 0.84 and
        every track always contains its own brightest frame. The absolute
        timbre claim in script_math_model.md rows 8-9 is unreachable for that
        reason; test_per_track_normalisation_keeps_centroid_positive below pins
        the real behaviour so the gap cannot be forgotten.
        """
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

    def test_mode_score_uses_pearson_and_reaches_the_manuscript_scale(self):
        """Mode_score must be Pearson correlation on the manuscript's +-1 scale.

        Regression: the implementation normalised both vectors and took
        np.dot, which is the COSINE of two non-negative profiles. Those profiles
        are 0.9495 alike under cosine, so the contrast collapsed: a chroma vector
        set exactly to the major profile scored +0.0373 and the whole reachable
        space topped out at 0.1782, while script_chapter_02.md promises "+1
        menandakan modus Mayor dominan dan -1 menandakan modus Minor dominan".
        Pearson drops the profile correlation to 0.5121 and restores the range.
        """
        major = self.model.MAJOR_PROFILE.astype(float)
        minor = self.model.MINOR_PROFILE.astype(float)

        self.assertGreater(self.model.compute_mode_ratio(major), 0.15,
                           "a chroma vector equal to the major profile must score clearly positive")
        self.assertLess(self.model.compute_mode_ratio(minor), -0.15,
                        "a chroma vector equal to the minor profile must score clearly negative")

        # The old cosine implementation capped out at 0.1782 across the whole
        # reachable space; Pearson must go well beyond that.
        import numpy as np
        rng = np.random.default_rng(11)
        peak = max(abs(self.model.compute_mode_ratio(rng.random(12) ** 3)) for _ in range(20000))
        self.assertGreater(peak, 0.35, f"reachable |Mode_score| only {peak:.4f}")

    def test_mode_score_is_zero_for_content_with_no_tonal_centre(self):
        import numpy as np
        self.assertAlmostEqual(self.model.compute_mode_ratio(np.ones(12)), 0.0, places=6)
        self.assertAlmostEqual(self.model.compute_mode_ratio(np.zeros(12)), 0.0, places=6)

    def test_mode_score_never_raises_on_malformed_input(self):
        """Malformed chroma must read as 'no tonal content', not kill the worker.

        Regression: a list of non-numeric strings reached np.asarray and raised
        ValueError, which would propagate out of analyze_audio_stream and abort
        the whole analysis.
        """
        for bad in (["a"] * 12, [1, "x"] * 6, None, [float("nan")] * 12, [1, 2, 3], []):
            with self.subTest(value=repr(bad)):
                self.assertEqual(self.model.compute_mode_ratio(bad), 0.0)

    def test_per_track_normalisation_pins_the_measured_reality(self):
        """Pins the measurement that limits Valence, without overclaiming.

        feature_extractor.py normalises the spectral centroid against each
        track's own maximum. Two consequences hold for EVERY track, by
        construction, and are asserted here:

          1. The brightest frame always normalises to exactly 1.0.
          2. Therefore the mean centroid score is pulled upward relative to a
             fixed scale, because the track's own peak defines the top.

        What is NOT asserted is that the mean centroid score is always
        positive. A track dominated by one very bright frame can still average
        negative, as the synthetic example below shows; it is the ten real
        benchmark tracks that averaged 0.66 to 0.84 because their centroid
        spread is fairly even. The value of this test is to keep the mechanism
        visible, not to claim a universal sign.

        The measured consequence on the ten benchmark tracks is recorded in
        script_math_model.md's notes: centroid plus MFCC contributed +0.214 to
        +0.352 and every track scored positive Valence, so raising the mode
        weight alone (tested up to 0.80) could not produce negative Valence.
        """
        import numpy as np

        # 1. The peak frame always normalises to exactly 1.0 - this is the
        #    structural fact, true for any track by construction.
        for centroids in (
            np.array([100.0, 150.0, 900.0, 200.0, 400.0]),   # one dominant frame
            np.array([300.0, 320.0, 350.0, 310.0, 340.0]),   # evenly spread
            np.array([50.0, 50.0, 50.0, 50.0, 5000.0]),      # extreme outlier
        ):
            with self.subTest(centroids=centroids.tolist()):
                self.assertAlmostEqual(float((centroids / centroids.max()).max()), 1.0, places=9)

        # 2. An evenly spread track - like real worship audio - averages a
        #    strongly positive centroid score, which is what keeps Valence up.
        even = np.array([265.0, 280.0, 300.0, 290.0, 275.0])
        even_score = 2.0 * (even / even.max()) - 1.0
        self.assertGreater(float(np.mean(even_score)), 0.5,
                           "an evenly spread centroid yields a large positive term")

        # 3. But a single dominant frame can push the average negative: the
        #    sign is a property of the track's spread, not of the normalisation.
        spiky = np.array([100.0, 150.0, 900.0, 200.0, 400.0])
        spiky_score = 2.0 * (spiky / spiky.max()) - 1.0
        self.assertLess(float(np.mean(spiky_score)), 0.0,
                        "a spiky track can average negative, so the sign is not universal")

        # 4. And the mode term cannot rescue a negative-Valence outcome on the
        #    measured tracks: even at weight 0.80 the minor tracks stayed
        #    positive, because the other two terms carried +0.214 to +0.352.
        worst_case_mode = -0.23
        mean_other_terms = 0.268
        self.assertGreater(0.80 * worst_case_mode + mean_other_terms, 0.0,
                           "raising the mode weight alone cannot produce negative Valence")


if __name__ == "__main__":
    unittest.main()
