"""Tests for Phase 2: SourceConfigPanel.

Tests the new SourceConfigPanel component with embedded file table.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'SRC')))


class TestSourceConfigPanelImport(unittest.TestCase):
    """Test that SourceConfigPanel can be imported."""
    
    def test_import_source_config_panel(self):
        """SourceConfigPanel should be importable from components."""
        from sw_transform.gui.components import SourceConfigPanel
        self.assertIsNotNone(SourceConfigPanel)


class TestSourceConfigPanelBasic(unittest.TestCase):
    """Test basic SourceConfigPanel functionality."""
    
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
        """SourceConfigPanel should be creatable."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        self.assertIsNotNone(panel)
        panel.destroy()
    
    def test_panel_has_source_title(self):
        """Panel should have 'Source Configuration' title."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        title_text = panel.title_label.cget("text")
        self.assertEqual(title_text, "Source Configuration")
        panel.destroy()
    
    def test_default_mode_is_standard(self):
        """Default mode should be 'standard'."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        self.assertEqual(panel.mode_var.get(), "standard")
        panel.destroy()
    
    def test_default_interior_side_is_both(self):
        """Default interior side should be 'both'."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        self.assertEqual(panel.interior_side_var.get(), "both")
        panel.destroy()
    
    def test_update_files(self):
        """update_files() should populate file data."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        
        file_info = {
            'file1': {'path': '/path/file1.dat', 'offset': '+10', 'type': 'seg2', 'reverse': False},
            'file2': {'path': '/path/file2.dat', 'offset': '-5', 'type': 'seg2', 'reverse': False},
        }
        panel.update_files(file_info)
        
        positions = panel.get_source_positions()
        self.assertEqual(len(positions), 2)
        self.assertAlmostEqual(positions['file1'], 10.0)
        self.assertAlmostEqual(positions['file2'], -5.0)
        panel.destroy()
    
    def test_get_source_positions_empty(self):
        """get_source_positions() should return empty dict when no files."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        positions = panel.get_source_positions()
        self.assertEqual(positions, {})
        panel.destroy()
    
    def test_is_custom_mode(self):
        """is_custom_mode() should reflect mode setting."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        
        panel.mode_var.set("standard")
        self.assertFalse(panel.is_custom_mode())
        
        panel.mode_var.set("custom")
        self.assertTrue(panel.is_custom_mode())
        panel.destroy()
    
    def test_set_mode(self):
        """set_mode() should change mode."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        
        panel.set_mode("custom")
        self.assertEqual(panel.mode_var.get(), "custom")
        
        panel.set_mode("standard")
        self.assertEqual(panel.mode_var.get(), "standard")
        panel.destroy()
    
    def test_force_custom_mode(self):
        """force_custom_mode() should set custom mode."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        
        panel.mode_var.set("standard")
        panel.force_custom_mode()
        self.assertEqual(panel.mode_var.get(), "custom")
        panel.destroy()
    
    def test_clear(self):
        """clear() should remove all file data."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        
        file_info = {'file1': {'path': '/path/file1.dat', 'offset': '+10', 'type': 'seg2', 'reverse': False}}
        panel.update_files(file_info)
        self.assertEqual(len(panel.get_source_positions()), 1)
        
        panel.clear()
        self.assertEqual(len(panel.get_source_positions()), 0)
        panel.destroy()
    
    def test_update_receiver_positions(self):
        """update_receiver_positions() should update shot types."""
        from sw_transform.gui.components import SourceConfigPanel
        panel = SourceConfigPanel(self.root)
        
        file_info = {
            'file1': {'path': '/path/file1.dat', 'offset': '-10', 'type': 'seg2', 'reverse': False},
        }
        panel.update_files(file_info)
        panel.update_receiver_positions([0, 2, 4, 6, 8, 10])
        
        # Source at -10 should be exterior_left
        self.assertEqual(panel._file_data['file1']['shot_type'], 'exterior_left')
        panel.destroy()


class TestSimpleMASWGUISourceConfigIntegration(unittest.TestCase):
    """Test SourceConfigPanel integration in SimpleMASWGUI."""
    
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
    
    def test_gui_has_source_config(self):
        """SimpleMASWGUI should have source_config attribute."""
        from sw_transform.gui.simple_app import SimpleMASWGUI
        app = SimpleMASWGUI(self.root)
        self.assertIsNotNone(app.source_config)
    
    def test_source_config_type(self):
        """source_config should be SourceConfigPanel instance."""
        from sw_transform.gui.simple_app import SimpleMASWGUI
        from sw_transform.gui.components import SourceConfigPanel
        app = SimpleMASWGUI(self.root)
        self.assertIsInstance(app.source_config, SourceConfigPanel)
    
    def test_gui_has_both_configs(self):
        """SimpleMASWGUI should have both receiver_config and source_config."""
        from sw_transform.gui.simple_app import SimpleMASWGUI
        app = SimpleMASWGUI(self.root)
        self.assertIsNotNone(app.receiver_config)
        self.assertIsNotNone(app.source_config)


if __name__ == '__main__':
    unittest.main(verbosity=2)
