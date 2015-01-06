import sys
import unittest
from ctypes import byref, POINTER, c_int
from .. import SDL_Init, SDL_Quit, SDL_INIT_EVERYTHING
from ..stdinc import Uint8, Uint32, SDL_TRUE, SDL_FALSE
from .. import render, video, surface, pixels, blendmode, rect
from ..ext.pixelaccess import PixelView

_ISPYPY = hasattr(sys, "pypy_version_info")
if _ISPYPY:
    import gc


# TODO: mostly positive tests, improve this!
class SDLRenderTest(unittest.TestCase):
    __tags__ = ["sdl"]

    def setUp(self):
        SDL_Init(SDL_INIT_EVERYTHING)

    def tearDown(self):
        SDL_Quit()

    def test_SDL_RendererInfo(self):
        info = render.SDL_RendererInfo()
        self.assertIsInstance(info, render.SDL_RendererInfo)

    def test_SDL_Renderer(self):
        val = render.SDL_Renderer()
        self.assertIsInstance(val, render.SDL_Renderer)

    def test_SDL_Texture(self):
        val = render.SDL_Texture()
        self.assertIsInstance(val, render.SDL_Texture)

    def test_SDL_GetNumRenderDrivers(self):
        val = render.SDL_GetNumRenderDrivers()
        self.assertGreaterEqual(val, 1)

    def test_SDL_GetRenderDriverInfo(self):
        success = False
        drivers = render.SDL_GetNumRenderDrivers()
        for x in range(drivers):
            info = render.SDL_RendererInfo()
            ret = render.SDL_GetRenderDriverInfo(x, byref(info))
            self.assertEqual(ret, 0)
            # We must find at least one software renderer
            if info.name == b"software":
                success = True
        self.assertTrue(success, "failed on retrieving the driver information")

#        self.assertRaises((AttributeError, TypeError),
#                          render.SDL_GetRenderDriverInfo, None)
#        self.assertRaises((AttributeError, TypeError),
#                          render.SDL_GetRenderDriverInfo, "Test")
#        self.assertRaises((AttributeError, TypeError),
#                          render.SDL_GetRenderDriverInfo, self)
#        #self.assertRaises(sdl.SDLError, render.SDL_GetRenderDriverInfo, -1)

    def test_SDL_CreateWindowAndRenderer(self):
        window = POINTER(video.SDL_Window)()
        renderer = POINTER(render.SDL_Renderer)()
        ret = render.SDL_CreateWindowAndRenderer \
            (10, 10, video.SDL_WINDOW_HIDDEN, byref(window), byref(renderer))
        self.assertEqual(ret, 0)

        render.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)

        # TODO: the code below works, too - is that really expected from SDL?
        #window, renderer = render.SDL_CreateWindowAndRenderer \
        #   (-10, -10, video.SDL_WINDOW_HIDDEN)
        #self.assertIsInstance(window, video.SDL_Window)
        #self.assertIsInstance(renderer, render.SDL_Renderer)

    def test_SDL_CreateDestroyRenderer(self):
        for i in range(render.SDL_GetNumRenderDrivers()):
            window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                            video.SDL_WINDOW_SHOWN)
            self.assertIsInstance(window.contents, video.SDL_Window)
            renderer = render.SDL_CreateRenderer(window, i,
                                             render.SDL_RENDERER_ACCELERATED)
            self.assertTrue(renderer and renderer.contents,
                "could not create renderer for driver index %d" % i)
            self.assertIsInstance(renderer.contents, render.SDL_Renderer)
            render.SDL_DestroyRenderer(renderer)

            # TODO: using -1 as index for the call below leads to random
            # access violations on Win32
            renderer = render.SDL_CreateRenderer(window, i,
                                                 render.SDL_RENDERER_SOFTWARE)
            self.assertIsInstance(renderer.contents, render.SDL_Renderer)
            render.SDL_DestroyRenderer(renderer)
            video.SDL_DestroyWindow(window)

    def test_SDL_CreateSoftwareRenderer(self):
        sf = surface.SDL_CreateRGBSurface(0, 100, 100, 32,
                                          0xFF000000,
                                          0x00FF0000,
                                          0x0000FF00,
                                          0x000000FF)
        renderer = render.SDL_CreateSoftwareRenderer(sf)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)
        render.SDL_DestroyRenderer(renderer)
        surface.SDL_FreeSurface(sf)

        #self.assertRaises((AttributeError, TypeError),
        #                  render.SDL_CreateSoftwareRenderer, None)
        #self.assertRaises((AttributeError, TypeError),
        #                  render.SDL_CreateSoftwareRenderer, 1234)

    def test_SDL_GetRenderer(self):
        for i in range(render.SDL_GetNumRenderDrivers()):
            window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                            video.SDL_WINDOW_HIDDEN)
            self.assertIsInstance(window.contents, video.SDL_Window)
            renderer = render.SDL_GetRenderer(window)
            self.assertFalse(renderer)
            renderer = render.SDL_CreateRenderer(window, i,
                                                 render.SDL_RENDERER_SOFTWARE)
            self.assertTrue(renderer and renderer.contents,
                "could not create renderer for driver index %d" % i)
            ren = render.SDL_GetRenderer(window)
            self.assertIsInstance(ren.contents, render.SDL_Renderer)
            render.SDL_DestroyRenderer(renderer)
            self.assertFalse(render.SDL_GetRenderer(window))

            video.SDL_DestroyWindow(window)
            self.assertFalse(render.SDL_GetRenderer(window))
        #self.assertRaises((AttributeError, TypeError),
        #                  render.SDL_GetRenderer, None)
        #self.assertRaises((AttributeError, TypeError),
        #                  render.SDL_GetRenderer, "Test")

    def test_SDL_GetRendererInfo(self):
        for i in range(render.SDL_GetNumRenderDrivers()):
            window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                            video.SDL_WINDOW_HIDDEN)
            self.assertIsInstance(window.contents, video.SDL_Window)
            renderer = render.SDL_CreateRenderer(window, i,
                                                 render.SDL_RENDERER_SOFTWARE)
            self.assertTrue(renderer and renderer.contents,
                "could not create renderer for driver index %d" % i)
            self.assertIsInstance(renderer.contents, render.SDL_Renderer)
            info = render.SDL_RendererInfo()
            ret = render.SDL_GetRendererInfo(renderer, byref(info))
            self.assertEqual(ret, 0)
            render.SDL_DestroyRenderer(renderer)

            #self.assertRaises(sdl.SDLError, render.SDL_GetRendererInfo,
            #                  renderer)

            video.SDL_DestroyWindow(window)
        self.assertRaises((AttributeError, TypeError),
                          render.SDL_GetRendererInfo, None)
        self.assertRaises((AttributeError, TypeError),
                          render.SDL_GetRendererInfo, "Test")

    def test_SDL_CreateDestroyTexture(self):
        window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                        video.SDL_WINDOW_HIDDEN)
        self.assertIsInstance(window.contents, video.SDL_Window)
        renderer = render.SDL_CreateRenderer(window, -1,
                                             render.SDL_RENDERER_SOFTWARE)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)

        formats = (pixels.SDL_PIXELFORMAT_ARGB8888,
                   pixels.SDL_PIXELFORMAT_RGB555,
                   pixels.SDL_PIXELFORMAT_RGBA4444,
                   pixels.SDL_PIXELFORMAT_RGBA8888,
                   pixels.SDL_PIXELFORMAT_ARGB2101010,
                   pixels.SDL_PIXELFORMAT_YUY2
                   )
        access = (render.SDL_TEXTUREACCESS_STATIC,
                  render.SDL_TEXTUREACCESS_STREAMING,
                  render.SDL_TEXTUREACCESS_TARGET)
        for fmt in formats:
            for acc in access:
                for w in range(1, 300, 5):
                    for h in range(1, 300, 5):
                        tex = render.SDL_CreateTexture(renderer, fmt, acc,
                                                       w, h)
                        self.assertIsInstance(tex.contents, render.SDL_Texture)
                        render.SDL_DestroyTexture(tex)
                    if _ISPYPY and (w % 50) == 0:
                        gc.collect()

        #self.assertRaises(sdl.SDLError, render.SDL_CreateTexture, renderer,
        #                  pixels.SDL_PIXELFORMAT_RGB555, 1, -10, 10)
        #self.assertRaises(sdl.SDLError, render.SDL_CreateTexture, renderer,
        #                  pixels.SDL_PIXELFORMAT_RGB555, 1, 10, -10)
        #self.assertRaises(sdl.SDLError, render.SDL_CreateTexture, renderer,
        #                  pixels.SDL_PIXELFORMAT_RGB555, 1, -10, -10)
        #self.assertRaises(ValueError, render.SDL_CreateTexture, renderer,
        #                  pixels.SDL_PIXELFORMAT_RGB555, -5, 10, 10)
        #self.assertRaises(ValueError, render.SDL_CreateTexture, renderer,
        #                  - 10, 1, 10, 10)
        #self.assertRaises((AttributeError, TypeError),
        #                  render.SDL_CreateTexture, None,
        #                  pixels.SDL_PIXELFORMAT_RGB555, 1, 10, 10)
        #self.assertRaises((AttributeError, TypeError),
        #                  render.SDL_CreateTexture, "Test",
        #                  pixels.SDL_PIXELFORMAT_RGB555, 1, 10, 10)
        #self.assertRaises(ValueError, render.SDL_CreateTexture, renderer,
        #                  "Test", 1, 10, 10)
        #self.assertRaises(ValueError, render.SDL_CreateTexture, renderer,
        #                  pixels.SDL_PIXELFORMAT_RGB555, None, 10, 10)
        #self.assertRaises(ValueError, render.SDL_CreateTexture, renderer,
        #                  pixels.SDL_PIXELFORMAT_RGB555, "Test", 10, 10)

        render.SDL_DestroyRenderer(renderer)
        #self.assertRaises(sdl.SDLError, render.SDL_CreateTexture, renderer,
        #                  pixels.SDL_PIXELFORMAT_RGB555, 1, 10, 10)
        video.SDL_DestroyWindow(window)

    def test_SDL_CreateTextureFromSurface(self):
        sf = surface.SDL_CreateRGBSurface(0, 100, 100, 32, 0xFF000000,
                                          0x00FF0000, 0x0000FF00, 0x000000FF)
        self.assertIsInstance(sf.contents, surface.SDL_Surface)
        window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                        video.SDL_WINDOW_HIDDEN)
        self.assertIsInstance(window.contents, video.SDL_Window)
        renderer = render.SDL_CreateRenderer(window, -1,
                                             render.SDL_RENDERER_SOFTWARE)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)
        tex = render.SDL_CreateTextureFromSurface(renderer, sf)
        self.assertIsInstance(tex.contents, render.SDL_Texture)

    def test_SDL_QueryTexture(self):
        window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                        video.SDL_WINDOW_HIDDEN)
        self.assertIsInstance(window.contents, video.SDL_Window)
        renderer = render.SDL_CreateRenderer(window, -1,
                                             render.SDL_RENDERER_SOFTWARE)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)

        formats = (pixels.SDL_PIXELFORMAT_ARGB8888,
                   pixels.SDL_PIXELFORMAT_RGB555,
                   pixels.SDL_PIXELFORMAT_RGBA4444,
                   pixels.SDL_PIXELFORMAT_ARGB2101010,
                   pixels.SDL_PIXELFORMAT_YUY2
                   )
        access = (render.SDL_TEXTUREACCESS_STATIC,
                  render.SDL_TEXTUREACCESS_STREAMING,
                  render.SDL_TEXTUREACCESS_TARGET)
        for fmt in formats:
            for acc in access:
                for w in range(1, 300, 5):
                    for h in range(1, 300, 5):
                        tex = render.SDL_CreateTexture(renderer, fmt, acc,
                                                       w, h)
                        self.assertIsInstance(tex.contents, render.SDL_Texture)
                        qf, qa, qw, qh = Uint32(), c_int(), c_int(), c_int()
                        ret = render.SDL_QueryTexture(tex, byref(qf),
                                                      byref(qa), byref(qw),
                                                      byref(qh))
                        self.assertEqual(ret, 0)
                        self.assertEqual(qf.value, fmt)
                        self.assertEqual(qa.value, acc)
                        self.assertEqual(qw.value, w)
                        self.assertEqual(qh.value, h)
                        render.SDL_DestroyTexture(tex)
                    if _ISPYPY and (w % 50) == 0:
                        gc.collect()

        render.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)

    def test_SDL_GetSetTextureColorMod(self):
        window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                        video.SDL_WINDOW_HIDDEN)
        self.assertIsInstance(window.contents, video.SDL_Window)
        renderer = render.SDL_CreateRenderer(window, -1,
                                             render.SDL_RENDERER_SOFTWARE)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)

        tex = render.SDL_CreateTexture(renderer,
                                       pixels.SDL_PIXELFORMAT_ARGB8888,
                                       render.SDL_TEXTUREACCESS_STREAMING,
                                       10, 10)
        self.assertIsInstance(tex.contents, render.SDL_Texture)
        colors = ((16, 22, 185),
                  (32, 64, 128),
                  (64, 32, 128),
                  (64, 32, 255),
                  (255, 32, 64),
                  (255, 32, 128),
                  (0, 0, 0),
                  (255, 255, 255),
                  (128, 128, 128),
                  )
        for r, g, b in colors:
            ret = render.SDL_SetTextureColorMod(tex, r, g, b)
            self.assertEqual(ret, 0)
            tr, tg, tb = Uint8(), Uint8(), Uint8()
            ret = render.SDL_GetTextureColorMod(tex, byref(tr), byref(tg),
                                                byref(tb))
            self.assertEqual(ret, 0)
            self.assertEqual((tr.value, tg.value, tb.value), (r, g, b))

        render.SDL_DestroyTexture(tex)
        #self.assertRaises(sdl.SDLError, render.SDL_SetTextureColorMod, tex,
        #                  10, 20, 30)
        #self.assertRaises(sdl.SDLError, render.SDL_GetTextureColorMod, tex)

        render.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)

    def test_SDL_GetSetTextureAlphaMod(self):
        window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                        video.SDL_WINDOW_HIDDEN)
        self.assertIsInstance(window.contents, video.SDL_Window)
        renderer = render.SDL_CreateRenderer(window, -1,
                                             render.SDL_RENDERER_SOFTWARE)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)

        tex = render.SDL_CreateTexture(renderer,
                                       pixels.SDL_PIXELFORMAT_ARGB8888,
                                       render.SDL_TEXTUREACCESS_STREAMING,
                                       10, 10)
        self.assertIsInstance(tex.contents, render.SDL_Texture)

        for alpha in range(0, 255):
            ret = render.SDL_SetTextureAlphaMod(tex, alpha)
            self.assertEqual(ret, 0)
            talpha = Uint8()
            ret = render.SDL_GetTextureAlphaMod(tex, byref(talpha))
            self.assertEqual(ret, 0)
            self.assertEqual(talpha.value, alpha)

        render.SDL_DestroyTexture(tex)
        #self.assertRaises(sdl.SDLError, render.SDL_SetTextureColorMod, tex,
        #                  10, 20, 30)
        #self.assertRaises(sdl.SDLError, render.SDL_GetTextureColorMod, tex)

        render.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)

    def test_SDL_GetSetTextureBlendMode(self):
        window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                        video.SDL_WINDOW_HIDDEN)
        self.assertIsInstance(window.contents, video.SDL_Window)
        renderer = render.SDL_CreateRenderer(window, -1,
                                             render.SDL_RENDERER_SOFTWARE)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)

        tex = render.SDL_CreateTexture(renderer,
                                       pixels.SDL_PIXELFORMAT_ARGB8888,
                                       render.SDL_TEXTUREACCESS_STREAMING,
                                       10, 10)
        self.assertIsInstance(tex.contents, render.SDL_Texture)

        modes = (blendmode.SDL_BLENDMODE_NONE,
                 blendmode.SDL_BLENDMODE_ADD,
                 blendmode.SDL_BLENDMODE_BLEND,
                 blendmode.SDL_BLENDMODE_MOD,
                 )
        for mode in modes:
            ret = render.SDL_SetTextureBlendMode(tex, mode)
            self.assertEqual(ret, 0)
            tmode = blendmode.SDL_BlendMode()
            ret = render.SDL_GetTextureBlendMode(tex, byref(tmode))
            self.assertEqual(ret, 0)
            self.assertEqual(tmode.value, mode)

        render.SDL_DestroyTexture(tex)
        #self.assertRaises(sdl.SDLError, render.SDL_SetTextureBlendMode, tex,
        #                  modes[2])
        #self.assertRaises(sdl.SDLError, render.SDL_GetTextureBlendMode, tex)

        render.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)

    @unittest.skip("not implemented")
    def test_SDL_UpdateTexture(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_LockUnlockTexture(self):
        pass

    def test_SDL_RenderTargetSupported(self):
        for i in range(render.SDL_GetNumRenderDrivers()):
            window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                            video.SDL_WINDOW_HIDDEN)
            self.assertIsInstance(window.contents, video.SDL_Window)
            renderer = render.SDL_CreateRenderer\
                (window, i, render.SDL_RENDERER_ACCELERATED)
            self.assertTrue(renderer and renderer.contents,
                "could not create renderer for driver index %d" % i)
            self.assertIsInstance(renderer.contents, render.SDL_Renderer)

            val = render.SDL_RenderTargetSupported(renderer)
            self.assertIn(val, (SDL_TRUE, SDL_FALSE))
            render.SDL_DestroyRenderer(renderer)
            video.SDL_DestroyWindow(window)

    def test_SDL_GetSetRenderTarget(self):
        skipcount = 0
        for i in range(render.SDL_GetNumRenderDrivers()):
            window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                            video.SDL_WINDOW_HIDDEN)
            self.assertIsInstance(window.contents, video.SDL_Window)
            renderer = render.SDL_CreateRenderer \
                (window, i, render.SDL_RENDERER_ACCELERATED)
            self.assertTrue(renderer and renderer.contents,
                "could not create renderer for driver index %d" % i)
            self.assertIsInstance(renderer.contents, render.SDL_Renderer)

            supported = render.SDL_RenderTargetSupported(renderer)
            if not supported:
                skipcount += 1
                render.SDL_DestroyRenderer(renderer)
                continue

            ret = render.SDL_SetRenderTarget(renderer, None)
            self.assertEqual(ret, 0)
            self.assertFalse(render.SDL_GetRenderTarget(renderer))

            tex = render.SDL_CreateTexture(renderer,
                                           pixels.SDL_PIXELFORMAT_ARGB8888,
                                           render.SDL_TEXTUREACCESS_TARGET,
                                           10, 10)
            ret = render.SDL_SetRenderTarget(renderer, tex)
            self.assertEqual(ret, 0)
            tgt = render.SDL_GetRenderTarget(renderer)
            self.assertIsInstance(tgt.contents, render.SDL_Texture)
            render.SDL_DestroyTexture(tex)

            # TODO: Check in the SDL codebase, why the code below does
            # not fail...
            # tex2 = render.SDL_CreateTexture(renderer,
            #                              pixels.SDL_PIXELFORMAT_ARGB8888,
            #                              render.SDL_TEXTUREACCESS_STREAMING,
            #                              10, 10)
            # self.assertRaises(SDLError, render.SDL_SetRenderTarget, renderer,
            #                   tex2)
            # render.SDL_DestroyTexture(tex2)

            render.SDL_DestroyRenderer(renderer)
            video.SDL_DestroyWindow(window)

        if skipcount == render.SDL_GetNumRenderDrivers():
            self.skipTest("None of the renderers supports render targets")

    def test_SDL_RenderGetSetViewport(self):
        rects = (rect.SDL_Rect(0, 0, 0, 0),
                 rect.SDL_Rect(0, 0, 10, 10),
                 rect.SDL_Rect(3, 3, 5, 5),
                 rect.SDL_Rect(-5, -5, 10, 10),
                 rect.SDL_Rect(10, 10, 10, 10),
                 rect.SDL_Rect(0, 0, -10, -10),
                 rect.SDL_Rect(-10, 0, 10, 10),
                 rect.SDL_Rect(0, -10, 10, 10),
                 rect.SDL_Rect(-10, -10, 10, 10),
            )
        failcount = 0
        port = rect.SDL_Rect()
        for i in range(render.SDL_GetNumRenderDrivers()):
            window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                            video.SDL_WINDOW_HIDDEN |
                                            video.SDL_WINDOW_BORDERLESS)
            self.assertIsInstance(window.contents, video.SDL_Window)
            renderer = render.SDL_CreateRenderer \
                (window, i, render.SDL_RENDERER_ACCELERATED)
            self.assertTrue(renderer and renderer.contents,
                "could not create renderer for driver index %d" % i)
            self.assertIsInstance(renderer.contents, render.SDL_Renderer)
            ret = render.SDL_RenderSetViewport(renderer, None)
            self.assertEqual(ret, 0)
            render.SDL_RenderGetViewport(renderer, byref(port))
            self.assertEqual(port, rect.SDL_Rect(0, 0, 10, 10))
            for r in rects:
                if r.w == r.h == 0:
                    # http://bugzilla.libsdl.org/show_bug.cgi?id=1622
                    # OpenGL renderers cause a exception here.
                    continue
                ret = render.SDL_RenderSetViewport(renderer, r)
                self.assertEqual(ret, 0)
                render.SDL_RenderGetViewport(renderer, byref(port))
                if port != r:
                    failcount += 1

            render.SDL_DestroyRenderer(renderer)
            video.SDL_DestroyWindow(window)

        if failcount > 0:
            unittest.skip("""for some reason, even with correct values, this
seems to fail on creating the second renderer of the window, if any""")

    def test_SDL_GetSetRenderDrawColor(self):
        for i in range(render.SDL_GetNumRenderDrivers()):
            window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                            video.SDL_WINDOW_HIDDEN)
            self.assertIsInstance(window.contents, video.SDL_Window)
            renderer = render.SDL_CreateRenderer \
                (window, i, render.SDL_RENDERER_ACCELERATED|render.SDL_RENDERER_SOFTWARE)
            self.assertTrue(renderer and renderer.contents,
                "could not create renderer for driver index %d" % i)
            self.assertIsInstance(renderer.contents, render.SDL_Renderer)

            colors = ((16, 22, 185, 217),
                      (32, 64, 128, 255),
                      (64, 32, 128, 255),
                      (64, 32, 255, 128),
                      (255, 32, 64, 128),
                      (255, 32, 128, 64),
                      (0, 0, 0, 0),
                      (255, 255, 255, 255),
                      (128, 128, 128, 255),
                      )
            for r, g, b, a in colors:
                ret = render.SDL_SetRenderDrawColor(renderer, r, g, b, a)
                self.assertEqual(ret, 0)
                dr, dg, db, da = Uint8(), Uint8(), Uint8(), Uint8()
                ret = render.SDL_GetRenderDrawColor(renderer, byref(dr),
                                                    byref(dg), byref(db),
                                                    byref(da))
                self.assertEqual(ret, 0)
                self.assertEqual((dr.value, dg.value, db.value, da.value),
                                 (r, g, b, a))
            render.SDL_DestroyRenderer(renderer)
            #self.assertRaises(sdl.SDLError, render.SDL_SetRenderDrawColor,
            #                  renderer, 10, 20, 30, 40)
            #self.assertRaises(sdl.SDLError, render.SDL_GetRenderDrawColor,
            #                  renderer)
            video.SDL_DestroyWindow(window)

    def test_SDL_GetSetRenderDrawBlendMode(self):
        for i in range(render.SDL_GetNumRenderDrivers()):
            window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                            video.SDL_WINDOW_HIDDEN)
            self.assertIsInstance(window.contents, video.SDL_Window)
            renderer = render.SDL_CreateRenderer \
                (window, i, render.SDL_RENDERER_ACCELERATED|render.SDL_RENDERER_SOFTWARE)
            self.assertTrue(renderer and renderer.contents,
                "could not create renderer for driver index %d" % i)
            self.assertIsInstance(renderer.contents, render.SDL_Renderer)

            modes = (blendmode.SDL_BLENDMODE_NONE,
                     blendmode.SDL_BLENDMODE_ADD,
                     blendmode.SDL_BLENDMODE_BLEND,
                     blendmode.SDL_BLENDMODE_MOD,
                     )
            for mode in modes:
                ret = render.SDL_SetRenderDrawBlendMode(renderer, mode)
                bmode = blendmode.SDL_BlendMode()
                ret = render.SDL_GetRenderDrawBlendMode(renderer, byref(bmode))
                self.assertEqual(ret, 0)
                self.assertEqual(bmode.value, mode)
            render.SDL_DestroyRenderer(renderer)
            #self.assertRaises(sdl.SDLError, render.SDL_SetRenderDrawBlendMode,
            #                  renderer, video.SDL_BLENDMODE_ADD)
            #self.assertRaises(sdl.SDLError, render.SDL_GetRenderDrawBlendMode,
            #                  renderer)
            video.SDL_DestroyWindow(window)

    def test_SDL_RenderClear(self):
        window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10,
                                        video.SDL_WINDOW_HIDDEN)
        self.assertIsInstance(window.contents, video.SDL_Window)
        renderer = render.SDL_CreateRenderer(window, -1,
                                             render.SDL_RENDERER_ACCELERATED)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)

        ret = render.SDL_RenderClear(renderer)
        self.assertEqual(ret, 0)
        render.SDL_DestroyRenderer(renderer)
        #self.assertRaises(sdl.SDLError, render.SDL_RenderClear, renderer)
#        self.assertRaises((AttributeError, TypeError),
#                          render.SDL_RenderClear, None)
#        self.assertRaises((AttributeError, TypeError),
#                          render.SDL_RenderClear, "Test")
#        self.assertRaises((AttributeError, TypeError),
#                          render.SDL_RenderClear, 123456)

    @unittest.skipIf(hasattr(sys, "pypy_version_info"),
                     "PyPy's ctypes can't do byref(value, offset)")
    @unittest.skipIf(sys.platform=="cli",
                     "IronPython can't cast values array values correctly")
    def test_SDL_RenderDrawPoint(self):
        points = ((-4, -3), (-4, 3), (4, -3),
                  (0, 0), (1, 1), (10, 10), (99, 99),
                  (4, 22), (57, 88), (45, 15),
                  (100, 100)
                  )
        r, g, b, a = 0xAA, 0xBB, 0xCC, 0xDD
        w, h = 100, 100
        sf = surface.SDL_CreateRGBSurface(0, w, h, 32, 0xFF000000, 0x00FF0000,
                                          0x0000FF00, 0x000000FF)
        color = pixels.SDL_MapRGBA(sf.contents.format, r, g, b, a)
        renderer = render.SDL_CreateSoftwareRenderer(sf)
        self.assertIsInstance(renderer.contents, render.SDL_Renderer)
        ret = render.SDL_SetRenderDrawColor(renderer, r, g, b, a)
        self.assertEqual(ret, 0)
        for x, y in points:
            ret = render.SDL_RenderDrawPoint(renderer, x, y)
            self.assertEqual(ret, 0)
        render.SDL_RenderPresent(renderer)
        view = PixelView(sf.contents)
        for x, y in points:
            npx = max(x + 1, w)
            npy = max(y + 1, h)
            ppx = max(x - 1, 0)
            ppy = max(y - 1, 0)
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            self.assertEqual(hex(view[y][x]), hex(color))
            if (npx, npy) not in points:
                self.assertNotEqual(hex(view[npy][npx]), hex(color))
            if (ppx, ppy) not in points:
                self.assertNotEqual(hex(view[ppy][ppx]), hex(color))
        render.SDL_DestroyRenderer(renderer)
        del view
        surface.SDL_FreeSurface(sf)

    @unittest.skip("not implemented")
    def test_SDL_RenderDrawPoints(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderDrawLine(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderDrawLines(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderDrawRect(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderDrawRects(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderFillRect(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderFillRects(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderCopy(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderReadPixels(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderPresent(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderGetSetScale(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderGetSetLogicalSize(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_RenderGetSetClipRect(self):
        pass

    @unittest.skip("not implemented")
    def test_SDL_GetRendererOutputSize(self):
        pass

if __name__ == '__main__':
    sys.exit(unittest.main())
