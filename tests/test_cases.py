import inspect
import subprocess
import unittest
import time
import sys
import os
#sys.path.insert(0, os.path.abspath('..'))
import lackey
import numpy

from .appveyor_test_cases import *
import pytest

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str

@pytest.mark.skipif(not sys.platform.startswith("win"),
                    reason="Uses Windows feature")
class TestKeyboardMethods(object):

    @pytest.fixture(autouse=True)
    def notepad(self):
        self.app = lackey.App("notepad.exe")
        self.app.open()
        time.sleep(1)
        yield
        self.app.close()

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

    def test_parsed_special_codes(self, kb):
        OUTPUTS = {
            # Special codes should output the text below.
            # Multiple special codes should be parsed correctly.
            # False special codes should be typed out normally.
            "{SPACE}": " ",
            "{TAB}": "\t",
            "{SPACE}{SPACE}": "  ",
            "{TAB}{TAB}": "\t\t",
            "{ENTER}{ENTER}": "\r\n\r\n",
            "{TEST}": "{TEST}",
            "{TEST}{TEST}": "{TEST}{TEST}"
        }

        def type_and_check_equals(typed, expected):
            kb.type(typed)
            time.sleep(0.2)
            lackey.type("a", lackey.Key.CTRL)
            lackey.type("c", lackey.Key.CTRL)

            assert lackey.getClipboard() == expected

        for code in OUTPUTS:
            type_and_check_equals(code, OUTPUTS[code])


class TestComplexFeatures(unittest.TestCase):
    def setUp(self):
        lackey.addImagePath(os.path.dirname(__file__))
        lackey.Screen(0).hover()
        lackey.Screen(0).click()

    def testImporter(self):
        """ Tries to import the test_cases project file 
        (ignores FindFailed exception thrown by project) """
        try:
            sys.path.append(os.path.join(os.getcwd(), "tests"))
            import test_import
        except lackey.FindFailed:
            pass

    def testTypeCopyPaste(self):
        """ Also tests the log file """
        lackey.Debug.setLogFile("logfile.txt")
        r = lackey.Screen(0)
        if sys.platform.startswith("win"):
            app = lackey.App("notepad.exe").open()
            time.sleep(1)
            r.type("This is a Test")
            r.type("a", lackey.Key.CTRL) # Select all
            r.type("c", lackey.Key.CTRL) # Copy
            assert r.getClipboard() == "This is a Test"
            r.type("{DELETE}") # Clear the selected text
            r.paste("This, on the other hand, is a {SHIFT}broken {SHIFT}record.") # Paste should ignore special characters and insert the string as is
            r.type("a", lackey.Key.CTRL) # Select all
            r.type("c", lackey.Key.CTRL) # Copy
            assert r.getClipboard() == "This, on the other hand, is a {SHIFT}broken {SHIFT}record."
        elif sys.platform == "darwin":
            app = lackey.App("+open -e")
            lackey.sleep(2)
            #r.debugPreview()
            r.wait(lackey.Pattern("preview_open_2.png"))
            r.click(lackey.Pattern("preview_open_2.png"))
            lackey.type("n", lackey.KeyModifier.CMD)
            time.sleep(1)
            app = lackey.App("Untitled")
            r.type("This is a Test")
            r.type("a", lackey.KeyModifier.CMD) # Select all
            r.type("c", lackey.KeyModifier.CMD) # Copy
            assert r.getClipboard() == "This is a Test"
            r.type("{DELETE}") # Clear the selected text
            r.paste("This, on the other hand, is a {SHIFT}broken {SHIFT}record.") # Paste should ignore special characters and insert the string as is
            r.type("a", lackey.KeyModifier.CMD) # Select all
            r.type("c", lackey.KeyModifier.CMD) # Copy
            assert r.getClipboard() == "This, on the other hand, is a {SHIFT}broken {SHIFT}record."
        else:
            raise NotImplementedError("Platforms supported include: Windows, OS X")

        app.close()

        lackey.Debug.setLogFile(None)

        assert os.path.exists("logfile.txt")

    def testOpenApp(self):
        """ This looks for the specified Notepad icon on the desktop.

        This test will probably fail if you don't have the same setup I do.
        """
        def test_observer(appear_event):
            assert(appear_event.isAppear())
            img = appear_event.getImage()
            region = appear_event.getRegion()
            region.TestFlag = True
            region.stopObserver()
        r = lackey.Screen(0)
        if sys.platform.startswith("win"):
            r.doubleClick("notepad.png")
        elif sys.platform == "darwin":
            r.doubleClick("textedit.png")
            r.wait("preview_open_2.png")
            r.type("n", lackey.KeyModifier.CMD)
        time.sleep(2)
        r.type("This is a test")
        if sys.platform.startswith("win"):
            r.onAppear(lackey.Pattern("test_text.png").similar(0.6), test_observer)
        elif sys.platform == "darwin":
            r.onAppear(lackey.Pattern("mac_test_text.png").similar(0.6), test_observer)
        r.observe(30)
        assert r.TestFlag
        assert r.getTime() > 0
        if sys.platform.startswith("win"):
            r.rightClick(r.getLastMatch())
            r.click("select_all.png")
            r.type("c", lackey.Key.CTRL) # Copy
        elif sys.platform == "darwin":
            r.type("a", lackey.KeyModifier.CMD)
            r.type("c", lackey.KeyModifier.CMD)
        assert r.getClipboard() == "This is a test"
        r.type("{DELETE}")
        if sys.platform.startswith("win"):
            r.type("{F4}", lackey.Key.ALT)
        elif sys.platform == "darwin":
            r.type("w", lackey.KeyModifier.CMD)
            r.click(lackey.Pattern("textedit_save_2.png").targetOffset(-86, 25))
            lackey.sleep(0.5)
            r.type("q", lackey.KeyModifier.CMD)

    def testDragDrop(self):
        """ This relies on two specific icons on the desktop.

        This test will probably fail if you don't have the same setup I do.
        """
        r = lackey.Screen(0)
        if sys.platform.startswith("win"):
            r.dragDrop("test_file_txt.png", "notepad.png")
            assert r.exists("test_file_txt.png")
            r.type("{F4}", lackey.Key.ALT)
        elif sys.platform == "darwin":
            r.dragDrop("test_file_rtf.png", "textedit.png")
            assert r.exists("test_file_rtf.png")
            r.type("w", lackey.KeyModifier.CMD)
            r.type("q", lackey.KeyModifier.CMD)

    def testFindFailed(self):
        """ Sets up a region (which should not have the target icon) """

        r = lackey.Screen(0).get(lackey.Region.NORTH_EAST)
        with pytest.raises(lackey.FindFailed) as context:
            r.find("notepad.png")
        r.setFindFailedResponse(r.SKIP)
        try:
            r.find("notepad.png")
        except lackey.FindFailed:
            self.fail("Incorrectly threw FindFailed exception; should have skipped")

@pytest.mark.skip(reason="Requires user intervention")
class TestRasterMethods(object):

    def testRaster(self, screen):
        # This should preview the specified sections of the primary screen.
        screen.debugPreview("Full screen")
        screen.get(lackey.Region.NORTH).debugPreview("Top half")
        screen.get(lackey.Region.SOUTH).debugPreview("Bottom half")
        screen.get(lackey.Region.NORTH_WEST).debugPreview("Upper right corner")
        screen.get(522).debugPreview("Center (small)")
        screen.get(lackey.Region.MID_BIG).debugPreview("Center (half)")

if __name__ == '__main__':
    unittest.main()
