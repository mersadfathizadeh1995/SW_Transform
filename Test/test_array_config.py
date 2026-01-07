"""Unit tests for ArrayConfig dataclass.

Tests all channel selection modes, position calculations, shot classification,
and interior shot splitting functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'SRC'))

import numpy as np
import pytest
from sw_transform.core.array_config import (
    ArrayConfig, 
    create_default_config, 
    create_first_n_config,
    create_custom_positions_config
)


class TestChannelSelection:
    """Test channel selection modes."""
    
    def test_all_channels(self):
        """Test 'all' mode returns all channels."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='all')
        indices = cfg.get_selected_indices()
        assert len(indices) == 24
        assert np.array_equal(indices, np.arange(24))
    
    def test_first_n_channels(self):
        """Test 'first_n' mode returns first N channels."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='first_n', n_channels_use=24)
        indices = cfg.get_selected_indices()
        assert len(indices) == 24
        assert np.array_equal(indices, np.arange(24))
    
    def test_first_n_exceeds_file(self):
        """Test 'first_n' when N > file channels."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='first_n', n_channels_use=48)
        indices = cfg.get_selected_indices()
        assert len(indices) == 24
    
    def test_last_n_channels(self):
        """Test 'last_n' mode returns last N channels."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='last_n', n_channels_use=24)
        indices = cfg.get_selected_indices()
        assert len(indices) == 24
        assert np.array_equal(indices, np.arange(24, 48))
    
    def test_range_channels(self):
        """Test 'range' mode returns channel range."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='range', 
                         channel_start=10, channel_end=30)
        indices = cfg.get_selected_indices()
        assert len(indices) == 20
        assert np.array_equal(indices, np.arange(10, 30))
    
    def test_range_clipped(self):
        """Test 'range' mode clips to file bounds."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='range',
                         channel_start=10, channel_end=50)
        indices = cfg.get_selected_indices()
        assert len(indices) == 14
        assert indices[-1] == 23
    
    def test_custom_channels(self):
        """Test 'custom' mode with specific indices."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[0, 2, 4, 6, 8, 10])
        indices = cfg.get_selected_indices()
        assert len(indices) == 6
        assert np.array_equal(indices, [0, 2, 4, 6, 8, 10])
    
    def test_custom_filters_invalid(self):
        """Test 'custom' mode filters out invalid indices."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[0, 5, 50, -1, 23])
        indices = cfg.get_selected_indices()
        assert len(indices) == 3
        assert np.array_equal(indices, [0, 5, 23])


class TestPositions:
    """Test position calculations."""
    
    def test_uniform_positions(self):
        """Test uniform spacing positions."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, spacing_mode='uniform')
        positions = cfg.get_positions()
        assert len(positions) == 24
        assert positions[0] == 0.0
        assert positions[-1] == 46.0
        assert np.allclose(np.diff(positions), 2.0)
    
    def test_custom_positions(self):
        """Test custom positions array."""
        custom = [0, 2, 4, 6, 10, 14, 18, 22, 26, 30]
        cfg = ArrayConfig(n_channels_file=10, spacing_mode='custom',
                         custom_positions=custom, channel_mode='all')
        positions = cfg.get_positions()
        assert len(positions) == 10
        assert np.array_equal(positions, custom)
    
    def test_uniform_with_first_n(self):
        """Test uniform positions with first_n selection."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='first_n',
                         n_channels_use=24, dx=2.0, spacing_mode='uniform')
        positions = cfg.get_positions()
        assert len(positions) == 24
        assert positions[0] == 0.0
        assert positions[-1] == 46.0
    
    def test_uniform_with_last_n(self):
        """Test uniform positions with last_n selection."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='last_n',
                         n_channels_use=24, dx=2.0, spacing_mode='uniform')
        positions = cfg.get_positions()
        assert len(positions) == 24
        assert positions[0] == 48.0
        assert positions[-1] == 94.0
    
    def test_get_array_length(self):
        """Test array length calculation."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0)
        length = cfg.get_array_length()
        assert length == 46.0
    
    def test_get_min_spacing_uniform(self):
        """Test minimum spacing for uniform array."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0)
        min_sp = cfg.get_min_spacing()
        assert min_sp == 2.0
    
    def test_get_min_spacing_nonuniform(self):
        """Test minimum spacing for non-uniform array."""
        cfg = ArrayConfig(n_channels_file=6, spacing_mode='custom',
                         custom_positions=[0, 2, 4, 6, 10, 16])
        min_sp = cfg.get_min_spacing()
        assert min_sp == 2.0


class TestShotClassification:
    """Test shot type classification."""
    
    def test_exterior_left(self):
        """Test exterior left shot classification."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=-10.0)
        assert cfg.classify_shot() == 'exterior_left'
        assert not cfg.needs_reverse()
    
    def test_exterior_right(self):
        """Test exterior right shot classification."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=56.0)
        assert cfg.classify_shot() == 'exterior_right'
        assert cfg.needs_reverse()
    
    def test_edge_left(self):
        """Test edge left shot classification."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=0.0)
        assert cfg.classify_shot() == 'edge_left'
        assert not cfg.needs_reverse()
    
    def test_edge_right(self):
        """Test edge right shot classification."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=46.0)
        assert cfg.classify_shot() == 'edge_right'
        assert cfg.needs_reverse()
    
    def test_interior(self):
        """Test interior shot classification."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=20.0)
        assert cfg.classify_shot() == 'interior'


class TestInteriorShotSplit:
    """Test interior shot splitting."""
    
    def test_split_both_sides(self):
        """Test splitting interior shot into both sides."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=22.0,
                         interior_side='both')
        configs = cfg.split_interior_shot()
        assert len(configs) == 2
    
    def test_split_left_only(self):
        """Test splitting interior shot - left side only."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=22.0,
                         interior_side='left')
        configs = cfg.split_interior_shot()
        assert len(configs) == 1
        left_pos = configs[0].get_positions()
        assert all(p < 22.0 for p in left_pos)
    
    def test_split_right_only(self):
        """Test splitting interior shot - right side only."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=22.0,
                         interior_side='right')
        configs = cfg.split_interior_shot()
        assert len(configs) == 1
        right_pos = configs[0].get_positions()
        assert all(p > 22.0 for p in right_pos)
    
    def test_exterior_no_split(self):
        """Test exterior shot returns self."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=-10.0)
        configs = cfg.split_interior_shot()
        assert len(configs) == 1
        assert configs[0] is cfg
    
    def test_split_min_channels(self):
        """Test split respects minimum channel count."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=4.0,
                         interior_side='both')
        configs = cfg.split_interior_shot()
        assert len(configs) == 1


class TestDataExtraction:
    """Test data extraction with selected channels."""
    
    def test_extract_all(self):
        """Test extracting all channels."""
        data = np.random.rand(1000, 24)
        cfg = ArrayConfig(n_channels_file=24, channel_mode='all')
        extracted = cfg.get_effective_data(data)
        assert extracted.shape == (1000, 24)
    
    def test_extract_first_n(self):
        """Test extracting first N channels."""
        data = np.random.rand(1000, 48)
        cfg = ArrayConfig(n_channels_file=48, channel_mode='first_n', n_channels_use=24)
        extracted = cfg.get_effective_data(data)
        assert extracted.shape == (1000, 24)
        assert np.array_equal(extracted, data[:, :24])
    
    def test_extract_custom(self):
        """Test extracting custom channels."""
        data = np.random.rand(1000, 24)
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[0, 5, 10, 15, 20])
        extracted = cfg.get_effective_data(data)
        assert extracted.shape == (1000, 5)


class TestSerialization:
    """Test serialization to/from dict."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=-10.0)
        d = cfg.to_dict()
        assert d['n_channels_file'] == 24
        assert d['dx'] == 2.0
        assert d['source_position'] == -10.0
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {'n_channels_file': 48, 'dx': 3.0, 'channel_mode': 'first_n',
             'n_channels_use': 24, 'source_position': -15.0, 'dx_file': 3.0,
             'channel_start': 0, 'channel_end': 24, 'channel_indices': [],
             'spacing_mode': 'uniform', 'custom_positions': [],
             'interior_side': 'both'}
        cfg = ArrayConfig.from_dict(d)
        assert cfg.n_channels_file == 48
        assert cfg.dx == 3.0
        assert cfg.channel_mode == 'first_n'
    
    def test_roundtrip(self):
        """Test dict roundtrip preserves values."""
        cfg1 = ArrayConfig(n_channels_file=36, dx=1.5, channel_mode='range',
                          channel_start=5, channel_end=25, source_position=-5.0)
        cfg2 = ArrayConfig.from_dict(cfg1.to_dict())
        assert cfg1.n_channels_file == cfg2.n_channels_file
        assert cfg1.dx == cfg2.dx
        assert cfg1.channel_mode == cfg2.channel_mode
        assert cfg1.channel_start == cfg2.channel_start


class TestFactoryFunctions:
    """Test factory functions."""
    
    def test_create_default_config(self):
        """Test default config creation."""
        cfg = create_default_config(24, 2.0, -10.0)
        assert cfg.n_channels_file == 24
        assert cfg.dx == 2.0
        assert cfg.source_position == -10.0
        assert cfg.get_n_selected() == 24
    
    def test_create_default_config_positive_offset(self):
        """Test default config with positive offset."""
        cfg = create_default_config(24, 2.0, 10.0)
        assert cfg.source_position == 56.0
    
    def test_create_first_n_config(self):
        """Test first_n config creation."""
        cfg = create_first_n_config(48, 24, 2.0, -10.0)
        assert cfg.n_channels_file == 48
        assert cfg.get_n_selected() == 24
        assert cfg.channel_mode == 'first_n'
    
    def test_create_custom_positions_config(self):
        """Test custom positions config creation."""
        positions = [0, 2, 4, 6, 10, 14, 20, 28]
        cfg = create_custom_positions_config(8, positions, -5.0)
        assert cfg.spacing_mode == 'custom'
        assert np.array_equal(cfg.get_positions(), positions)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
