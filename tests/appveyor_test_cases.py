import inspect
import subprocess
import numpy
import time
import sys
import os
import re
import lackey
import pytest


class TestMouseMethods(object):

    def test_movement(self, mouse):
        mouse.move(lackey.Location(10, 10))
        lackey.sleep(0.01)
        assert mouse.getPos().getTuple() == (10, 10)
        mouse.moveSpeed(lackey.Location(100, 200), 0.5)
        assert mouse.getPos().getTuple() == (100, 200)
        lackey.wheel(mouse.getPos(), 0, 3) # Mostly just verifying it doesn't crash

class TestKeyboardMethods(object):

    def test_keys(self, kb):
        kb.keyDown("{SHIFT}")
        kb.keyUp("{CTRL}")
        kb.keyUp("{SHIFT}")
        kb.type("{CTRL}")
        # Really this should check to make sure these keys have all been released, but
        # I'm not sure how to make that work without continuously monitoring the keyboard
        # (which is the usual scenario). Ah well... if your computer is acting weird after
        # you run this test, the SHIFT, CTRL, or ALT keys might not have been released
        # properly.

class TestAppMethods(object):

    @pytest.mark.skipif(not sys.platform.startswith("win"),
                        reason="Tests Windows feature")
    def test_windows_getters(self):
        app = lackey.App("notepad.exe tests\\test_cases.py")
        app2 = lackey.App("notepad.exe tests\\test_cases.py")
        #app.setUsing("test_cases.py")
        app.open()
        app2.open()
        lackey.sleep(1)
        app2.close()
        app.focus()
        assert app.getName() == "notepad.exe"
        assert app.isRunning()
        assert re.search("test_cases(.py)? - Notepad", app.getWindow())
        assert app.getPID() != -1
        region = app.window()
        assert isinstance(region, lackey.Region)
        assert region.getW() > 0
        assert region.getH() > 0
        app.close()

    @pytest.mark.skipif(not sys.platform == "darwin",
                        reason="Tests OSX feature")
    @pytest.mark.skipif("TRAVIS" in os.environ,
                        reason="Skip these tests in travis build environment")
    def test_osx_getters(self):
        a = lackey.App("+open -a TextEdit tests/test_cases.py")
        a2 = lackey.App("open -a TextEdit tests/appveyor_test_cases.py")
        lackey.sleep(1)
        app = lackey.App("test_cases.py")
        app2 = lackey.App("appveyor_test_cases.py")
        #app.setUsing("test_cases.py")
        lackey.sleep(1)
        app2.close()
        app.focus()
        print(app.getPID())
        assert app.isRunning()
        assert app.getName()[-len("TextEdit"):] == "TextEdit"
        #self.assertEqual(app.getWindow(), "test_cases.py") # Doesn't work on `open`-triggered apps
        assert app.getPID() != -1
        region = app.window()
        assert isinstance(region, lackey.Region)
        assert region.getW() > 0
        assert region.getH() > 0
        app.close()

    @pytest.mark.skipif(not sys.platform.startswith("win"),
                        reason="Tests Windows feature")
    def test_windows_launchers(self):
        app = lackey.App("notepad.exe")
        app.setUsing("tests\\test_cases.py")
        app.open()
        lackey.wait(1)
        assert app.getName() == "notepad.exe"
        assert app.isRunning()
        assert re.search("test_cases(.py)? - Notepad", app.getWindow())
        assert app.getPID() != -1
        app.close()
        lackey.wait(0.9)

    @pytest.mark.skipif(not sys.platform == "darwin",
                        reason="Tests OSX feature")
    @pytest.mark.skipif("TRAVIS" in os.environ,
                        reason="Skip these tests in travis build environment")
    def test_osx_launchers(self):
        a = lackey.App("open")
        a.setUsing("-a TextEdit tests/test_cases.py")
        a.open()
        lackey.wait(1)
        app = lackey.App("test_cases.py")
        assert app.isRunning()
        assert app.getName()[-len("TextEdit"):] == "TextEdit"
        #self.assertEqual(app.getWindow(), "test_cases.py")  # Doesn't work on `open`-triggered apps
        assert app.getPID() != -1
        app.close()
        lackey.wait(0.9)


class TestScreenMethods(object):

    def testScreenInfo(self, screen):
        assert screen.getNumberScreens() > 0
        x, y, w, h = screen.getBounds()
        assert x == 0 # Top left corner of primary screen should be 0,0
        assert y == 0 # Top left corner of primary screen should be 0,0
        assert w > 0 # Primary screen should be wider than 0
        assert h > 0 # Primary screen should be taller than 0

    def testCapture(self, screen):
        tpath = screen.capture()
        assert isinstance(tpath, numpy.ndarray)

class TestLocationMethods(object):

    def test_getters(self, test_loc):
        assert test_loc.getX() == 10
        assert test_loc.getY() == 11
        assert test_loc.getTuple() == (10,11)
        assert str(test_loc) == "(Location object at (10,11))"

    def test_set_location(self, test_loc):
        test_loc.setLocation(3, 5)
        assert test_loc.getX() == 3
        assert test_loc.getY() == 5
        test_loc.setLocation(-3, 1009)
        assert test_loc.getX() == -3
        assert test_loc.getY() == 1009

    def test_offsets(self, test_loc):
        offset = test_loc.offset(3, -5)
        assert offset.getTuple() == (13,6)
        offset = test_loc.above(10)
        assert offset.getTuple() == (10,1)
        offset = test_loc.below(16)
        assert offset.getTuple() == (10,27)
        offset = test_loc.right(5)
        assert offset.getTuple() == (15,11)
        offset = test_loc.left(7)
        assert offset.getTuple() == (3,11)

    def test_screen_methods(self, test_loc):
        outside_loc = lackey.Location(-10, -10)
        assert outside_loc.getScreen() is None # Should be outside all screens and return None
        assert test_loc.getScreen().getID() == 0 # Test location should be on screen 0
        assert outside_loc.getMonitor().getID() == 0 # Outside all screens, should return default monitor (0)
        assert test_loc.getMonitor().getID() == 0 # Outside all screens, should return default monitor (0)
        assert outside_loc.getColor() is None # No color outside all screens, should return None
        assert isinstance(test_loc.getColor(), numpy.ndarray) # No color outside all screens, should return None


class TestPatternMethods(object):
    
    def test_defaults(self, pattern, pattern_path):
        assert pattern.similarity == 0.7
        assert isinstance(pattern.offset, lackey.Location)
        assert pattern.offset.getTuple() == (0,0)
        assert pattern.path[-len(pattern_path):] == pattern_path

    def test_setters(self, pattern, pattern_path):
        test_pattern = pattern.similar(0.5)
        assert test_pattern.similarity == 0.5
        assert test_pattern.path[-len(pattern_path):] == pattern_path
        test_pattern = pattern.exact()
        assert test_pattern.similarity == 1.0
        assert test_pattern.path[-len(pattern_path):] == pattern_path
        test_pattern = pattern.targetOffset(3, 5)
        assert test_pattern.similarity == 0.7
        assert test_pattern.path[-len(pattern_path):] == pattern_path
        assert test_pattern.offset.getTuple() == (3,5)

    def test_getters(self, pattern, pattern_path):
        assert pattern.getFilename()[-len(pattern_path):] == pattern_path
        assert pattern.getTargetOffset().getTuple() == (0,0)
        assert pattern.getSimilar() == 0.7

    def test_constructor(self, pattern, pattern_path):
        cloned_pattern = lackey.Pattern(pattern)
        assert cloned_pattern.isValid()
        pattern_from_image = lackey.Pattern(pattern.getImage())
        assert pattern_from_image.isImagePattern()
        with pytest.raises(TypeError):
            lackey.Pattern(True)
        with pytest.raises(lackey.ImageMissing):
            lackey.Pattern("non_existent_file.png")


class TestRegionMethods(object):

    def test_constructor(self, screen):
        assert isinstance(lackey.Region(screen), lackey.Region)
        assert isinstance(lackey.Region((0, 0, 5, 5)), lackey.Region)
        assert isinstance(lackey.Region(0, 0), lackey.Region)
        assert isinstance(lackey.Region(0, 0, 10, 10, 3), lackey.Region)
        with pytest.raises(TypeError):
            lackey.Region("foobar")
        with pytest.raises(TypeError):
            lackey.Region()
        assert isinstance(lackey.Region.create(lackey.Location(0,0), 5, 5), lackey.Region)
        assert isinstance(lackey.Region.create(
            lackey.Location(0, 0), 
            lackey.Region.CREATE_X_DIRECTION_RIGHT,
            lackey.Region.CREATE_Y_DIRECTION_BOTTOM,
            10,
            10
        ), lackey.Region)
        assert isinstance(lackey.Region.create(
            lackey.Location(10, 10),
            lackey.Region.CREATE_X_DIRECTION_LEFT,
            lackey.Region.CREATE_Y_DIRECTION_TOP,
            10,
            10
        ), lackey.Region)

    def test_changers(self, screen):
        # setLocation
        assert screen.getTopLeft() == lackey.Location(0, 0)
        assert screen.setLocation(lackey.Location(10, 10)).getTopLeft() == lackey.Location(10, 10)
        with pytest.raises(ValueError):
            screen.setLocation(None)
        # setROI
        screen.setROI((5, 5, 10, 10))
        new_region = lackey.Screen(0)
        new_region.morphTo(screen)
        with pytest.raises(TypeError):
            new_region.morphTo("werdz")
        assert screen.getTopLeft() == new_region.getTopLeft()
        assert screen.getTopRight() == new_region.getTopRight()
        assert screen.getBottomLeft() == new_region.getBottomLeft()
        assert screen.getBottomRight() == new_region.getBottomRight()
        with pytest.raises(TypeError):
            new_region.setROI("hammersauce")
        with pytest.raises(TypeError):
            new_region.setROI()
        new_region.add(5, 5, 5, 5)
        assert new_region.getTopLeft() == lackey.Location(0, 0)
        # copyTo - only guaranteed one screen, so just make sure it doesn't crash
        new_region.copyTo(0)
        new_region.copyTo(lackey.Screen(0))

    def test_info(self, screen):
        assert not screen.contains(lackey.Location(-5, -5))
        new_region = lackey.Region(-10, -10, 5, 5)
        assert not screen.contains(new_region)
        with pytest.raises(TypeError):
            screen.contains("werdz")
        screen.hover()
        assert screen.containsMouse()


    def test_validity_methods(self, screen):
        assert screen.isRegionValid()
        clipped = screen.clipRegionToScreen()
        assert clipped is not None
        assert clipped.getX() == screen.getX()
        assert clipped.getY() == screen.getY()
        assert clipped.getW() == screen.getW()
        assert clipped.getH() == screen.getH()

    def test_around_methods(self, screen):
        center_region = screen.get(lackey.Region.MID_BIG)
        below_region = center_region.below()
        assert below_region.isRegionValid()
        below_region = center_region.below(10)
        assert below_region.isRegionValid()
        above_region = center_region.above()
        assert above_region.isRegionValid()
        above_region = center_region.above(10)
        assert above_region.isRegionValid()
        right_region = center_region.right()
        assert right_region.isRegionValid()
        right_region = center_region.right(10)
        assert right_region.isRegionValid()
        left_region = center_region.left()
        assert left_region.isRegionValid()
        left_region = center_region.left(10)
        assert left_region.isRegionValid()
        nearby_region = center_region.nearby(10)
        assert nearby_region.isRegionValid()
        grow_region = center_region.grow(10, 5)
        assert grow_region.isRegionValid()
        grow_region = center_region.grow(10)
        assert grow_region.isRegionValid()
        inside_region = center_region.inside()
        assert inside_region.isRegionValid()
        offset_region = center_region.offset(lackey.Location(10, 10))
        assert offset_region.isRegionValid()
        with pytest.raises(ValueError):
            offset_region = left_region.offset(-1000, -1000)

    def test_highlighter(self, screen):
        center_region = screen.get(lackey.Region.MID_BIG)
        center_region.highlight()
        center_region.highlight(2, "blue")
        center_region.highlight(True, 0)
        print("Doing stuff...")
        time.sleep(1)
        center_region.highlight(False)

    def test_settings(self, screen):
        screen.setAutoWaitTimeout(10)
        assert screen.getAutoWaitTimeout() == 10.0
        screen.setWaitScanRate(2)
        assert screen.getWaitScanRate() == 2.0


@pytest.mark.usefixtures("screen")
class TestObserverEventMethods(object):
    def setup_method(self, method):
        self.generic_event = lackey.ObserveEvent(screen, event_type="GENERIC")
        self.appear_event = lackey.ObserveEvent(screen, event_type="APPEAR")
        self.vanish_event = lackey.ObserveEvent(screen, event_type="VANISH")
        self.change_event = lackey.ObserveEvent(screen, event_type="CHANGE")

    def test_validators(self):
        assert self.generic_event.isGeneric()
        assert not self.generic_event.isAppear()
        assert self.appear_event.isAppear()
        assert not self.appear_event.isVanish()
        assert self.vanish_event.isVanish()
        assert not self.vanish_event.isChange()
        assert self.change_event.isChange()
        assert not self.change_event.isGeneric()

    def test_getters(self):
        assert self.generic_event.getRegion() == screen
        with pytest.raises(TypeError) as context:
            self.generic_event.getImage()
        with pytest.raises(TypeError) as context:
            self.generic_event.getMatch()
        with pytest.raises(TypeError) as context:
            self.generic_event.getChanges()

class TestInterfaces(object):
    """ This class tests Sikuli interface compatibility on a surface level.
    Makes sure the class has the correct methods, and that the methods have the
    expected number of arguments.
    """
    def test_app_interface(self):
        """ Checking App class interface methods """
        ## Class methods
        has_method(lackey.App, "pause", 2)
        has_method(lackey.App, "open", 2)
        has_method(lackey.App, "focus", 2)
        has_method(lackey.App, "close", 2)
        has_method(lackey.App, "focusedWindow", 1)

        ## Instance methods
        app = lackey.App()
        has_method(app, "__init__", 2)
        has_method(app, "isRunning", 2)
        has_method(app, "hasWindow", 1)
        has_method(app, "getWindow", 1)
        has_method(app, "getPID", 1)
        has_method(app, "getName", 1)
        has_method(app, "setUsing", 2)
        has_method(app, "open", 2)
        has_method(app, "focus", 1)
        has_method(app, "close", 1)
        has_method(app, "window", 2)

    def test_region_interface(self):
        """ Checking Region class interface methods """
        has_method(lackey.Region, "__init__", 1) # uses *args
        has_method(lackey.Region, "setX", 2)
        has_method(lackey.Region, "setY", 2)
        has_method(lackey.Region, "setW", 2)
        has_method(lackey.Region, "setH", 2)
        has_method(lackey.Region, "moveTo", 2)
        has_method(lackey.Region, "setROI", 1)   # uses *args
        has_method(lackey.Region, "setRect", 1)  # uses *args
        has_method(lackey.Region, "morphTo", 2)
        has_method(lackey.Region, "getX", 1)
        has_method(lackey.Region, "getY", 1)
        has_method(lackey.Region, "getW", 1)
        has_method(lackey.Region, "getH", 1)
        has_method(lackey.Region, "getTopLeft", 1)
        has_method(lackey.Region, "getTopRight", 1)
        has_method(lackey.Region, "getBottomLeft", 1)
        has_method(lackey.Region, "getBottomRight", 1)
        has_method(lackey.Region, "getScreen", 1)
        has_method(lackey.Region, "getLastMatch", 1)
        has_method(lackey.Region, "getLastMatches", 1)
        has_method(lackey.Region, "getTime", 1)
        has_method(lackey.Region, "isRegionValid", 1)
        has_method(lackey.Region, "setAutoWaitTimeout", 2)
        has_method(lackey.Region, "getAutoWaitTimeout", 1)
        has_method(lackey.Region, "setWaitScanRate", 2)
        has_method(lackey.Region, "getWaitScanRate", 1)
        has_method(lackey.Region, "get", 2)
        has_method(lackey.Region, "getRow", 3)
        has_method(lackey.Region, "getCol", 3)
        has_method(lackey.Region, "setRows", 2)
        has_method(lackey.Region, "setCols", 2)
        has_method(lackey.Region, "setRaster", 3)
        has_method(lackey.Region, "getCell", 3)
        has_method(lackey.Region, "isRasterValid", 1)
        has_method(lackey.Region, "getRows", 1)
        has_method(lackey.Region, "getCols", 1)
        has_method(lackey.Region, "getRowH", 1)
        has_method(lackey.Region, "getColW", 1)
        has_method(lackey.Region, "offset", 3)
        has_method(lackey.Region, "inside", 1)
        has_method(lackey.Region, "grow", 3)
        has_method(lackey.Region, "nearby", 2)
        has_method(lackey.Region, "above", 2)
        has_method(lackey.Region, "below", 2)
        has_method(lackey.Region, "left", 2)
        has_method(lackey.Region, "right", 2)
        has_method(lackey.Region, "find", 2)
        has_method(lackey.Region, "findAll", 2)
        has_method(lackey.Region, "wait", 3)
        has_method(lackey.Region, "waitVanish", 3)
        has_method(lackey.Region, "exists", 3)
        has_method(lackey.Region, "click", 3)
        has_method(lackey.Region, "doubleClick", 3)
        has_method(lackey.Region, "rightClick", 3)
        has_method(lackey.Region, "highlight", 1) # Uses *args
        has_method(lackey.Region, "hover", 2)
        has_method(lackey.Region, "dragDrop", 4)
        has_method(lackey.Region, "drag", 2)
        has_method(lackey.Region, "dropAt", 3)
        has_method(lackey.Region, "type", 1) 		# Uses *args
        has_method(lackey.Region, "paste", 1)		# Uses *args
        has_method(lackey.Region, "text", 1)
        has_method(lackey.Region, "mouseDown", 2)
        has_method(lackey.Region, "mouseUp", 2)
        has_method(lackey.Region, "mouseMove", 3)
        has_method(lackey.Region, "wheel", 1)     # Uses *args
        has_method(lackey.Region, "keyDown", 2)
        has_method(lackey.Region, "keyUp", 2)
        # Event Handler Methods
        has_method(lackey.Region, "onAppear", 3)
        has_method(lackey.Region, "onVanish", 3)
        has_method(lackey.Region, "onChange", 3)
        has_method(lackey.Region, "isChanged", 3)
        has_method(lackey.Region, "observe", 2)
        has_method(lackey.Region, "observeInBackground", 2)
        has_method(lackey.Region, "stopObserver", 1)
        has_method(lackey.Region, "hasObserver", 1)
        has_method(lackey.Region, "isObserving", 1)
        has_method(lackey.Region, "hasEvents", 1)
        has_method(lackey.Region, "getEvents", 1)
        has_method(lackey.Region, "getEvent", 2)
        has_method(lackey.Region, "setInactive", 2)
        has_method(lackey.Region, "setActive", 2)
        # FindFailed event methods
        has_method(lackey.Region, "setFindFailedResponse", 2)
        has_method(lackey.Region, "setFindFailedHandler", 2)
        has_method(lackey.Region, "getFindFailedResponse", 1)
        has_method(lackey.Region, "setThrowException", 2)
        has_method(lackey.Region, "getThrowException", 1)
        has_method(lackey.Region, "_raiseFindFailed", 2)
        has_method(lackey.Region, "_findFailedPrompt", 2)

    def test_pattern_interface(self):
        """ Checking App class interface methods """
        has_method(lackey.Pattern, "__init__", 2)
        has_method(lackey.Pattern, "similar", 2)
        has_method(lackey.Pattern, "exact", 1)
        has_method(lackey.Pattern, "targetOffset", 3)
        has_method(lackey.Pattern, "getFilename", 1)
        has_method(lackey.Pattern, "getTargetOffset", 1)

    def test_match_interface(self):
        """ Checking Match class interface methods """
        has_method(lackey.Match, "getScore", 1)
        has_method(lackey.Match, "getTarget", 1)

    def test_location_interface(self):
        """ Checking Location class interface methods """
        has_method(lackey.Location, "__init__", 3)
        has_method(lackey.Location, "getX", 1)
        has_method(lackey.Location, "getY", 1)
        has_method(lackey.Location, "setLocation", 3)
        has_method(lackey.Location, "offset", 3)
        has_method(lackey.Location, "above", 2)
        has_method(lackey.Location, "below", 2)
        has_method(lackey.Location, "left", 2)
        has_method(lackey.Location, "right", 2)

    def test_screen_interface(self):
        """ Checking Screen class interface methods """
        has_method(lackey.Screen, "__init__", 2)
        has_method(lackey.Screen, "getNumberScreens", 1)
        has_method(lackey.Screen, "getBounds", 1)
        has_method(lackey.Screen, "capture", 1) 			# Uses *args
        has_method(lackey.Screen, "selectRegion", 2)

    def test_platform_manager_interface(self):
        """ Checking Platform Manager interface methods """

        ## Screen methods
        has_method(lackey.PlatformManager, "getBitmapFromRect", 5)
        has_method(lackey.PlatformManager, "getScreenBounds", 2)
        has_method(lackey.PlatformManager, "getScreenDetails", 1)
        has_method(lackey.PlatformManager, "isPointVisible", 3)

        ## Clipboard methods
        has_method(lackey.PlatformManager, "osCopy", 1)
        has_method(lackey.PlatformManager, "osPaste", 1)

        ## Window methods
        has_method(lackey.PlatformManager, "getWindowByTitle", 3)
        has_method(lackey.PlatformManager, "getWindowByPID", 3)
        has_method(lackey.PlatformManager, "getWindowRect", 2)
        has_method(lackey.PlatformManager, "focusWindow", 2)
        has_method(lackey.PlatformManager, "getWindowTitle", 2)
        has_method(lackey.PlatformManager, "getWindowPID", 2)
        has_method(lackey.PlatformManager, "getForegroundWindow", 1)

        ## Process methods
        has_method(lackey.PlatformManager, "isPIDValid", 2)
        has_method(lackey.PlatformManager, "killProcess", 2)
        has_method(lackey.PlatformManager, "getProcessName", 2)


class TestConvenienceFunctions(object):
    def test_function_defs(self):
        has_method(lackey, "sleep", 1)
        has_method(lackey, "exit", 1)
        has_method(lackey, "setShowActions", 1)
        has_method(lackey, "getBundlePath", 0)
        has_method(lackey, "getBundleFolder", 0)
        has_method(lackey, "setBundlePath", 1)
        has_method(lackey, "getImagePath", 0)
        has_method(lackey, "addImagePath", 1)
        has_method(lackey, "addHTTPImagePath", 1)
        has_method(lackey, "getParentPath", 0)
        has_method(lackey, "getParentFolder", 0)
        has_method(lackey, "makePath", 0) # Uses *args
        has_method(lackey, "makeFolder", 0) # Uses *args
        has_method(lackey, "unzip", 2)
        has_method(lackey, "popat", 0) # Uses *args
        has_method(lackey, "popup", 2)
        has_method(lackey, "popError", 2)
        has_method(lackey, "popAsk", 2)
        has_method(lackey, "input", 4)
        has_method(lackey, "inputText", 5)
        has_method(lackey, "select", 4)
        has_method(lackey, "popFile", 1)

    def test_renamed_builtin_functions(self):
        assert lackey.exit_ == sys.exit
        assert lackey.input_ == input
        assert lackey.type_ == type


def has_method(cls, mthd, args=0):
    """ Custom test to make sure a class has the specified method
    (and that it takes `args` parameters) """
    assert callable(getattr(cls, mthd, None))
    if args > 0:
        assert len(inspect.getargspec(getattr(cls, mthd))[0]) == args
