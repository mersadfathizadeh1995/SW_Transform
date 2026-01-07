"""Tests for Phase 1: ReceiverConfigPanel.

Tests the renamed ReceiverConfigPanel component and backward compatibility.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'SRC')))


class TestReceiverConfigPanelImport(unittest.TestCase):
    """Test that ReceiverConfigPanel can be imported."""
    
    def test_import_receiver_config_panel(self):
        """ReceiverConfigPanel should be importable from components."""
        from sw_transform.gui.components import ReceiverConfigPanel
        self.assertIsNotNone(ReceiverConfigPanel)
    
    def test_import_array_config_panel_still_works(self):
        """ArrayConfigPanel should still be importable for backward compatibility."""
        from sw_transform.gui.components import ArrayConfigPanel
        self.assertIsNotNone(ArrayConfigPanel)
    
    def test_both_panels_are_different_classes(self):
        """ReceiverConfigPanel and ArrayConfigPanel should be different classes."""
        from sw_transform.gui.components import ReceiverConfigPanel, ArrayConfigPanel
        self.assertIsNot(ReceiverConfigPanel, ArrayConfigPanel)


class TestReceiverConfigPanelBasic(unittest.TestCase):
    """Test basic ReceiverConfigPanel functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up tkinter root for all tests."""
        import tkinter as tk
        cls.root = tk.Tk()
        cls.root.withdraw()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up tkinter root."""
        cls.root.destroy()
    
    def test_create_panel(self):
        """ReceiverConfigPanel should be creatable."""
        from sw_transform.gui.components import ReceiverConfigPanel
        panel = ReceiverConfigPanel(self.root)
        self.assertIsNotNone(panel)
        panel.destroy()
    
    def test_panel_has_receiver_title(self):
        """Panel should have 'Receiver Configuration' title."""
        from sw_transform.gui.components import ReceiverConfigPanel
        panel = ReceiverConfigPanel(self.root)
        title_text = panel.title_label.cget("text")
        self.assertEqual(title_text, "Receiver Configuration")
        panel.destroy()
    
    def test_panel_has_no_source_section(self):
        """ReceiverConfigPanel should NOT have source position section."""
        from sw_transform.gui.components import ReceiverConfigPanel
        panel = ReceiverConfigPanel(self.root)
        # Check that source_position_var doesn't exist
        self.assertFalse(hasattr(panel, 'source_position_var'))
        panel.destroy()
    
    def test_get_config_returns_array_config(self):
        """get_config() should return ArrayConfig object."""
        from sw_transform.gui.components import ReceiverConfigPanel
        from sw_transform.core.array_config import ArrayConfig
        panel = ReceiverConfigPanel(self.root)
        config = panel.get_config()
        self.assertIsInstance(config, ArrayConfig)
        panel.destroy()
    
    def test_get_config_default_source_position(self):
        """get_config() should return default source_position=-10.0."""
        from sw_transform.gui.components import ReceiverConfigPanel
        panel = ReceiverConfigPanel(self.root)
        config = panel.get_config()
        self.assertEqual(config.source_position, -10.0)
        panel.destroy()
    
    def test_is_custom_mode_all_channels(self):
        """is_custom_mode() should return False for 'all' mode."""
        from sw_transform.gui.components import ReceiverConfigPanel
        panel = ReceiverConfigPanel(self.root)
        panel.channel_mode_var.set('all')
        self.assertFalse(panel.is_custom_mode())
        panel.destroy()
    
    def test_is_custom_mode_first_n(self):
        """is_custom_mode() should return True for 'first_n' mode."""
        from sw_transform.gui.components import ReceiverConfigPanel
        panel = ReceiverConfigPanel(self.root)
        panel.channel_mode_var.set('first_n')
        self.assertTrue(panel.is_custom_mode())
        panel.destroy()
    
    def test_set_file_info(self):
        """set_file_info() should update channel and spacing values."""
        from sw_transform.gui.components import ReceiverConfigPanel
        panel = ReceiverConfigPanel(self.root)
        panel.set_file_info(48, 2.5)
        self.assertEqual(panel.n_channels_file_var.get(), "48")
        self.assertEqual(panel.dx_file_var.get(), "2.50")
        panel.destroy()


class TestSimpleMASWGUIIntegration(unittest.TestCase):
    """Test ReceiverConfigPanel integration in SimpleMASWGUI."""
    
    @classmethod
    def setUpClass(cls):
        """Set up tkinter root for all tests."""
        import tkinter as tk
        cls.root = tk.Tk()
        cls.root.withdraw()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up tkinter root."""
        cls.root.destroy()
    
    def test_gui_has_receiver_config(self):
        """SimpleMASWGUI should have receiver_config attribute."""
        from sw_transform.gui.simple_app import SimpleMASWGUI
        app = SimpleMASWGUI(self.root)
        self.assertIsNotNone(app.receiver_config)
    
    def test_gui_array_config_is_alias(self):
        """SimpleMASWGUI.array_config should be alias to receiver_config."""
        from sw_transform.gui.simple_app import SimpleMASWGUI
        app = SimpleMASWGUI(self.root)
        self.assertIs(app.array_config, app.receiver_config)
    
    def test_receiver_config_type(self):
        """receiver_config should be ReceiverConfigPanel instance."""
        from sw_transform.gui.simple_app import SimpleMASWGUI
        from sw_transform.gui.components import ReceiverConfigPanel
        app = SimpleMASWGUI(self.root)
        self.assertIsInstance(app.receiver_config, ReceiverConfigPanel)


if __name__ == '__main__':
    unittest.main(verbosity=2)
