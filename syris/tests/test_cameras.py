import numpy as np
import quantities as q
import syris
import syris.config as cfg
from syris.devices.cameras import Camera, FPSError, is_fps_feasible
from syris.tests import SyrisTest, slow


@slow
class TestCamera(SyrisTest):

    def setUp(self):
        syris.init()
        wavelengths = np.arange(10) * q.nm
        qe = np.ones(len(wavelengths))
        self.camera = Camera(1e-3 * q.um,
                             1.0,
                             10.0,
                             0,
                             10,
                             (64, 64),
                             wavelengths=wavelengths,
                             quantum_efficiencies=qe,
                             exp_time=1 * q.s,
                             fps=1 / q.s)

    def test_constructor(self):
        Camera(1 * q.um, 0.1, 10, 1, 12, None)
        Camera(1 * q.um, 0.1, 10, 1, 12, (64, 64))
        cam = Camera(1 * q.um, 0.1, 10, 1, 12, None, (64, 64),
                     exp_time=1 * q.ms)
        self.assertEqual(cam.fps.simplified, 1000 / q.s)

        cam = Camera(1 * q.um, 0.1, 10, 1, 12, (64, 64),
                     fps=1000 / q.s)
        self.assertEqual(cam.exp_time, 1 * q.ms)

        cam = Camera(1 * q.um, 0.1, 10, 1, 12, (64, 64),
                     exp_time = 0.5 * q.ms, fps=1000 / q.s)

        self.assertRaises(FPSError, Camera, 1 * q.um, 0.1, 10, 1, 12,
                          (64, 64), exp_time = 1.5 * q.ms,
                          fps=1000 / q.s)

        self.assertRaises(FPSError, Camera, 1 * q.um, 0.1, 10, 1, 12,
                          (64, 64), exp_time = 1.0 * q.ms,
                          fps=1500 / q.s)

    def test_is_fps_feasible(self):
        self.assertTrue(is_fps_feasible(1000 / q.s, 1 * q.ms))
        self.assertTrue(is_fps_feasible(1000 / q.s, 0.5 * q.ms))
        self.assertFalse(is_fps_feasible(1000 / q.s, 2 * q.ms))

    def test_fps_setting(self):
        self.camera.fps = 0.5 / q.s

        def _set_fps(fps):
            self.camera.fps = fps

        self.assertRaises(FPSError, _set_fps, 1001 / q.s)

    def test_exp_time_setting(self):
        self.camera.exp_time = 0.5 * q.ms

        def _set_exp_time(exp_time):
            self.camera.exp_time = exp_time

        self.assertRaises(FPSError, _set_exp_time, 1.5 * q.s)

    def test_bpp(self):
        self.assertEqual(self.camera.max_grey_value, 2 ** self.camera.bpp - 1)

    def test_dark(self):
        photons = np.zeros(self.camera.shape, dtype=cfg.PRECISION.np_float)
        res = self.camera.get_image(photons, shot_noise=True, psf=False)

        self.assertNotEqual(np.var(res), 0.0)
        self.assertNotEqual(np.sum(res), 0.0)

    def test_saturation(self):
        photons = np.ones(self.camera.shape, dtype=cfg.PRECISION.np_float) * 10 * \
                self.camera.max_grey_value
        res = self.camera.get_image(photons.astype(np.float32), shot_noise=False, psf=False)

        self.assertEqual(np.var(res), 0)

        diff = np.ones(self.camera.shape) * self.camera.max_grey_value - res
        self.assertEqual(np.sum(diff), 0)
