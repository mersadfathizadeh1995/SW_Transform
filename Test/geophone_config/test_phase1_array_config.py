"""QC Tests for Phase 1: ArrayConfig Core Data Structure.

Tests the ArrayConfig dataclass implementation against the specification
in Plan/gephone_config/geophone_full_config.md Section 5.1.

Test Categories:
- Channel Selection Modes (Section 4.1)
- Spacing/Position Modes (Section 4.2)  
- Shot Type Handling (Section 4.3)
- Interior Shot Options (Section 4.4)
- Serialization & Factory Functions

Run with: python -m pytest Test/geophone_config/test_phase1_array_config.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'SRC'))

import numpy as np
import pytest
from sw_transform.core.array_config import (
    ArrayConfig, 
    create_default_config, 
    create_first_n_config,
    create_custom_positions_config
)


# =============================================================================
# Section 4.1: Channel Selection Mode Tests
# =============================================================================

class TestChannelSelectionAll:
    """Test 'all' channel selection mode."""
    
    def test_all_24_channels(self):
        """Use all channels from 24-channel file."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='all')
        indices = cfg.get_selected_indices()
        assert len(indices) == 24
        assert list(indices) == list(range(24))
    
    def test_all_48_channels(self):
        """Use all channels from 48-channel file."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='all')
        indices = cfg.get_selected_indices()
        assert len(indices) == 48
        assert list(indices) == list(range(48))


class TestChannelSelectionFirstN:
    """Test 'first_n' channel selection mode.
    
    Spec: 48 channels → use 1-24
    """
    
    def test_first_24_of_48(self):
        """Use first 24 of 48 channels."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='first_n', n_channels_use=24)
        indices = cfg.get_selected_indices()
        assert len(indices) == 24
        assert list(indices) == list(range(24))
    
    def test_first_12_of_24(self):
        """Use first 12 of 24 channels."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='first_n', n_channels_use=12)
        indices = cfg.get_selected_indices()
        assert len(indices) == 12
        assert list(indices) == list(range(12))
    
    def test_first_n_exceeds_available(self):
        """Request more channels than available - should cap."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='first_n', n_channels_use=48)
        indices = cfg.get_selected_indices()
        assert len(indices) == 24  # Capped at file count


class TestChannelSelectionLastN:
    """Test 'last_n' channel selection mode.
    
    Spec: 48 channels → use 25-48
    """
    
    def test_last_24_of_48(self):
        """Use last 24 of 48 channels."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='last_n', n_channels_use=24)
        indices = cfg.get_selected_indices()
        assert len(indices) == 24
        assert list(indices) == list(range(24, 48))
    
    def test_last_12_of_24(self):
        """Use last 12 of 24 channels."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='last_n', n_channels_use=12)
        indices = cfg.get_selected_indices()
        assert len(indices) == 12
        assert list(indices) == list(range(12, 24))
    
    def test_last_n_exceeds_available(self):
        """Request more channels than available - should return all."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='last_n', n_channels_use=48)
        indices = cfg.get_selected_indices()
        assert len(indices) == 24


class TestChannelSelectionRange:
    """Test 'range' channel selection mode.
    
    Spec: 48 channels → use 10-34
    """
    
    def test_range_10_to_34(self):
        """Use channel range [10, 34) from 48-channel file."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='range', 
                         channel_start=10, channel_end=34)
        indices = cfg.get_selected_indices()
        assert len(indices) == 24
        assert list(indices) == list(range(10, 34))
    
    def test_range_clips_to_file_bounds(self):
        """Range should clip to file bounds."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='range',
                         channel_start=10, channel_end=50)
        indices = cfg.get_selected_indices()
        assert len(indices) == 14
        assert indices[-1] == 23
    
    def test_range_start_negative_clips(self):
        """Negative start should clip to 0."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='range',
                         channel_start=-5, channel_end=10)
        indices = cfg.get_selected_indices()
        assert indices[0] == 0
        assert len(indices) == 10


class TestChannelSelectionCustom:
    """Test 'custom' channel selection mode.
    
    Spec: Use specific indices like [1, 3, 5, 7, 10, 15, 20]
    """
    
    def test_custom_odd_indices(self):
        """Select odd channel indices."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[1, 3, 5, 7, 9, 11])
        indices = cfg.get_selected_indices()
        assert len(indices) == 6
        assert list(indices) == [1, 3, 5, 7, 9, 11]
    
    def test_custom_sparse_selection(self):
        """Select sparse channel set."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[0, 5, 10, 15, 20, 23])
        indices = cfg.get_selected_indices()
        assert len(indices) == 6
        assert list(indices) == [0, 5, 10, 15, 20, 23]
    
    def test_custom_filters_invalid_indices(self):
        """Invalid indices should be filtered out."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[0, 5, 50, -1, 23, 100])
        indices = cfg.get_selected_indices()
        assert len(indices) == 3
        assert list(indices) == [0, 5, 23]
    
    def test_custom_sorted_output(self):
        """Custom indices should be returned sorted."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[20, 5, 15, 0, 10])
        indices = cfg.get_selected_indices()
        assert list(indices) == [0, 5, 10, 15, 20]


# =============================================================================
# Section 4.2: Spacing/Position Mode Tests  
# =============================================================================

class TestUniformSpacing:
    """Test uniform spacing mode.
    
    Spec: dx = 2.0m creates positions [0, 2, 4, 6, ...]
    """
    
    def test_uniform_2m_spacing(self):
        """Standard 2m uniform spacing."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, spacing_mode='uniform')
        positions = cfg.get_positions()
        assert len(positions) == 24
        assert positions[0] == 0.0
        assert positions[-1] == 46.0
        assert np.allclose(np.diff(positions), 2.0)
    
    def test_uniform_1m_spacing(self):
        """1m uniform spacing."""
        cfg = ArrayConfig(n_channels_file=12, dx=1.0, spacing_mode='uniform')
        positions = cfg.get_positions()
        assert len(positions) == 12
        assert positions[-1] == 11.0
    
    def test_uniform_with_channel_selection(self):
        """Uniform spacing with first_n selection."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='first_n',
                         n_channels_use=24, dx=2.0, spacing_mode='uniform')
        positions = cfg.get_positions()
        assert len(positions) == 24
        assert positions[0] == 0.0
        assert positions[-1] == 46.0
    
    def test_uniform_last_n_positions(self):
        """Uniform spacing with last_n selection."""
        cfg = ArrayConfig(n_channels_file=48, channel_mode='last_n',
                         n_channels_use=24, dx=2.0, spacing_mode='uniform')
        positions = cfg.get_positions()
        assert len(positions) == 24
        assert positions[0] == 48.0  # Channel 24 at 48m
        assert positions[-1] == 94.0  # Channel 47 at 94m


class TestCustomPositions:
    """Test custom positions mode.
    
    Spec: [0, 2, 4, 6, 10, 15, 20, 30] for non-uniform arrays
    Reference: MATLAB UofA_MASWMultiProcessVibroseisNonUniform.m line 41
    """
    
    def test_nonuniform_positions_from_matlab(self):
        """Test non-uniform positions matching MATLAB reference."""
        # From MATLAB: spacing=[0;2;4;6;8;10;14;18;22;26;30;35;40;45;50;55;60;65;70;75;80;85;90;95]
        matlab_positions = [0, 2, 4, 6, 8, 10, 14, 18, 22, 26, 30, 35, 40, 45, 
                           50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
        cfg = ArrayConfig(
            n_channels_file=24, 
            spacing_mode='custom',
            custom_positions=matlab_positions, 
            channel_mode='all'
        )
        positions = cfg.get_positions()
        assert len(positions) == 24
        assert np.allclose(positions, matlab_positions)
    
    def test_custom_variable_spacing(self):
        """Test variable spacing pattern."""
        custom = [0, 2, 4, 6, 10, 16, 24]
        cfg = ArrayConfig(n_channels_file=7, spacing_mode='custom',
                         custom_positions=custom, channel_mode='all')
        positions = cfg.get_positions()
        assert list(positions) == custom
    
    def test_custom_positions_min_spacing(self):
        """Test min spacing calculation for aliasing."""
        cfg = ArrayConfig(n_channels_file=6, spacing_mode='custom',
                         custom_positions=[0, 2, 4, 6, 10, 16])
        min_sp = cfg.get_min_spacing()
        assert min_sp == 2.0  # Minimum diff is 2m


class TestArrayLengthCalculation:
    """Test array length calculations."""
    
    def test_uniform_array_length(self):
        """Array length for uniform spacing."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0)
        assert cfg.get_array_length() == 46.0
    
    def test_custom_array_length(self):
        """Array length for custom positions."""
        cfg = ArrayConfig(n_channels_file=5, spacing_mode='custom',
                         custom_positions=[0, 5, 15, 30, 50])
        assert cfg.get_array_length() == 50.0
    
    def test_single_channel_length(self):
        """Single channel should have zero length."""
        cfg = ArrayConfig(n_channels_file=1, dx=2.0)
        assert cfg.get_array_length() == 0.0


# =============================================================================
# Section 4.3: Shot Type Handling Tests
# =============================================================================

class TestShotClassificationExterior:
    """Test exterior shot classification.
    
    Spec:
    - exterior_left: Source before first geophone
    - exterior_right: Source after last geophone
    """
    
    def test_exterior_left_negative_offset(self):
        """Source at -10m is exterior left."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=-10.0)
        assert cfg.classify_shot() == 'exterior_left'
        assert not cfg.needs_reverse()
    
    def test_exterior_left_far(self):
        """Source at -50m is still exterior left."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=-50.0)
        assert cfg.classify_shot() == 'exterior_left'
    
    def test_exterior_right_beyond_array(self):
        """Source beyond array end is exterior right."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=56.0)
        assert cfg.classify_shot() == 'exterior_right'
        assert cfg.needs_reverse()
    
    def test_exterior_right_far(self):
        """Source at 100m is exterior right (array ends at 46m)."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=100.0)
        assert cfg.classify_shot() == 'exterior_right'


class TestShotClassificationEdge:
    """Test edge shot classification.
    
    Spec:
    - edge_left: Source at first geophone
    - edge_right: Source at last geophone  
    """
    
    def test_edge_left_at_zero(self):
        """Source at 0m (first geophone) is edge left."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=0.0)
        assert cfg.classify_shot() == 'edge_left'
        assert not cfg.needs_reverse()
    
    def test_edge_left_within_tolerance(self):
        """Source near first geophone (within 1% of dx) is edge left."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=0.01)
        assert cfg.classify_shot() == 'edge_left'
    
    def test_edge_right_at_end(self):
        """Source at 46m (last geophone) is edge right."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=46.0)
        assert cfg.classify_shot() == 'edge_right'
        assert cfg.needs_reverse()
    
    def test_edge_right_within_tolerance(self):
        """Source near last geophone (within 1% of dx) is edge right."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=45.99)
        assert cfg.classify_shot() == 'edge_right'


class TestShotClassificationInterior:
    """Test interior shot classification.
    
    Spec: Source within array bounds
    """
    
    def test_interior_middle(self):
        """Source at middle of array is interior."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=22.0)
        assert cfg.classify_shot() == 'interior'
    
    def test_interior_near_start(self):
        """Source at 5m is interior (not edge)."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=5.0)
        assert cfg.classify_shot() == 'interior'
    
    def test_interior_near_end(self):
        """Source at 40m is interior (not edge)."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=40.0)
        assert cfg.classify_shot() == 'interior'


# =============================================================================
# Section 4.4: Interior Shot Options Tests
# =============================================================================

class TestInteriorShotSplit:
    """Test interior shot splitting into virtual shots.
    
    Spec:
    - Left side only: Geophones left of source (reversed)
    - Right side only: Geophones right of source (normal)
    - Both sides: Two virtual shots
    """
    
    def test_split_both_sides(self):
        """Split interior shot into both virtual shots."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=22.0,
                         interior_side='both')
        configs = cfg.split_interior_shot()
        assert len(configs) == 2
    
    def test_split_left_only(self):
        """Split interior shot - left side only."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=22.0,
                         interior_side='left')
        configs = cfg.split_interior_shot()
        assert len(configs) == 1
        # Left side positions should all be < source position
        left_pos = configs[0].get_positions()
        assert all(p < 22.0 for p in left_pos)
    
    def test_split_right_only(self):
        """Split interior shot - right side only."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=22.0,
                         interior_side='right')
        configs = cfg.split_interior_shot()
        assert len(configs) == 1
        # Right side positions should all be > source position
        right_pos = configs[0].get_positions()
        assert all(p > 22.0 for p in right_pos)
    
    def test_exterior_shot_no_split(self):
        """Exterior shot should not split - returns self."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=-10.0)
        configs = cfg.split_interior_shot()
        assert len(configs) == 1
        assert configs[0] is cfg
    
    def test_split_respects_min_channels(self):
        """Split should require minimum 6 channels per side."""
        # Source at 4m: only 2 channels on left (0m, 2m)
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=4.0,
                         interior_side='both')
        configs = cfg.split_interior_shot()
        # Should only have right side (left has < 6 channels)
        assert len(configs) == 1
    
    def test_split_left_reversed_order(self):
        """Left virtual shot should have reversed channel order."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=22.0,
                         interior_side='left')
        configs = cfg.split_interior_shot()
        left_cfg = configs[0]
        # Positions should be in descending order (reversed for wave direction)
        positions = left_cfg.custom_positions
        assert positions[0] > positions[-1], "Left side should be reversed"


# =============================================================================
# Data Extraction Tests
# =============================================================================

class TestDataExtraction:
    """Test get_effective_data() method."""
    
    def test_extract_all_channels(self):
        """Extract all channels from data."""
        data = np.arange(1000 * 24).reshape(1000, 24)
        cfg = ArrayConfig(n_channels_file=24, channel_mode='all')
        extracted = cfg.get_effective_data(data)
        assert extracted.shape == (1000, 24)
        assert np.array_equal(extracted, data)
    
    def test_extract_first_n(self):
        """Extract first N channels."""
        data = np.arange(1000 * 48).reshape(1000, 48)
        cfg = ArrayConfig(n_channels_file=48, channel_mode='first_n', n_channels_use=24)
        extracted = cfg.get_effective_data(data)
        assert extracted.shape == (1000, 24)
        assert np.array_equal(extracted, data[:, :24])
    
    def test_extract_last_n(self):
        """Extract last N channels."""
        data = np.arange(1000 * 48).reshape(1000, 48)
        cfg = ArrayConfig(n_channels_file=48, channel_mode='last_n', n_channels_use=24)
        extracted = cfg.get_effective_data(data)
        assert extracted.shape == (1000, 24)
        assert np.array_equal(extracted, data[:, 24:48])
    
    def test_extract_custom(self):
        """Extract custom channel set."""
        data = np.arange(1000 * 24).reshape(1000, 24)
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[0, 5, 10, 15, 20])
        extracted = cfg.get_effective_data(data)
        assert extracted.shape == (1000, 5)
        assert np.array_equal(extracted[:, 0], data[:, 0])
        assert np.array_equal(extracted[:, 2], data[:, 10])
    
    def test_extract_1d_array(self):
        """Extract from 1D array (single time sample)."""
        data = np.arange(24)
        cfg = ArrayConfig(n_channels_file=24, channel_mode='first_n', n_channels_use=12)
        extracted = cfg.get_effective_data(data)
        assert extracted.shape == (12,)


# =============================================================================
# Serialization Tests
# =============================================================================

class TestSerialization:
    """Test to_dict() and from_dict() methods."""
    
    def test_to_dict_default(self):
        """Test default config to dict."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0)
        d = cfg.to_dict()
        assert d['n_channels_file'] == 24
        assert d['dx'] == 2.0
        assert d['channel_mode'] == 'all'
        assert d['spacing_mode'] == 'uniform'
    
    def test_from_dict_basic(self):
        """Test creating config from dict."""
        d = {
            'n_channels_file': 48,
            'dx_file': 2.0,
            'channel_mode': 'first_n',
            'n_channels_use': 24,
            'channel_start': 0,
            'channel_end': 24,
            'channel_indices': [],
            'spacing_mode': 'uniform',
            'dx': 2.0,
            'custom_positions': [],
            'source_position': -10.0,
            'interior_side': 'both'
        }
        cfg = ArrayConfig.from_dict(d)
        assert cfg.n_channels_file == 48
        assert cfg.channel_mode == 'first_n'
    
    def test_roundtrip_all_fields(self):
        """Test dict roundtrip preserves all values."""
        cfg1 = ArrayConfig(
            n_channels_file=36,
            dx_file=1.5,
            channel_mode='range',
            n_channels_use=24,
            channel_start=5,
            channel_end=25,
            channel_indices=[],
            spacing_mode='custom',
            dx=1.5,
            custom_positions=[0, 2, 4, 8, 12, 18],
            source_position=-5.0,
            interior_side='left'
        )
        cfg2 = ArrayConfig.from_dict(cfg1.to_dict())
        
        assert cfg1.n_channels_file == cfg2.n_channels_file
        assert cfg1.dx == cfg2.dx
        assert cfg1.channel_mode == cfg2.channel_mode
        assert cfg1.channel_start == cfg2.channel_start
        assert cfg1.spacing_mode == cfg2.spacing_mode
        assert cfg1.interior_side == cfg2.interior_side


# =============================================================================
# Factory Function Tests
# =============================================================================

class TestFactoryFunctions:
    """Test factory helper functions."""
    
    def test_create_default_config(self):
        """Test create_default_config()."""
        cfg = create_default_config(24, 2.0, -10.0)
        assert cfg.n_channels_file == 24
        assert cfg.dx == 2.0
        assert cfg.source_position == -10.0
        assert cfg.channel_mode == 'all'
        assert cfg.get_n_selected() == 24
    
    def test_create_default_config_positive_offset(self):
        """Test default config with positive offset (exterior right)."""
        cfg = create_default_config(24, 2.0, 10.0)
        # Array length = 23 * 2 = 46m, source at 46 + 10 = 56m
        assert cfg.source_position == 56.0
        assert cfg.classify_shot() == 'exterior_right'
    
    def test_create_first_n_config(self):
        """Test create_first_n_config()."""
        cfg = create_first_n_config(48, 24, 2.0, -10.0)
        assert cfg.n_channels_file == 48
        assert cfg.channel_mode == 'first_n'
        assert cfg.n_channels_use == 24
        assert cfg.get_n_selected() == 24
    
    def test_create_custom_positions_config(self):
        """Test create_custom_positions_config()."""
        positions = [0, 2, 4, 6, 10, 14, 20, 28]
        cfg = create_custom_positions_config(8, positions, -5.0)
        assert cfg.spacing_mode == 'custom'
        assert cfg.source_position == -5.0
        assert np.allclose(cfg.get_positions(), positions)


# =============================================================================
# Edge Cases and Validation Tests  
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_custom_indices(self):
        """Custom mode with empty indices list."""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[])
        indices = cfg.get_selected_indices()
        assert len(indices) == 0
    
    def test_single_channel_file(self):
        """Single channel file."""
        cfg = ArrayConfig(n_channels_file=1, dx=2.0)
        assert cfg.get_n_selected() == 1
        assert cfg.get_array_length() == 0.0
    
    def test_zero_spacing(self):
        """Zero spacing edge case."""
        cfg = ArrayConfig(n_channels_file=24, dx=0.0)
        positions = cfg.get_positions()
        assert all(p == 0.0 for p in positions)
    
    def test_repr_output(self):
        """Test __repr__ produces valid string."""
        cfg = ArrayConfig(n_channels_file=24, dx=2.0, source_position=-10.0)
        r = repr(cfg)
        assert 'ArrayConfig' in r
        assert '24/24' in r
        assert 'exterior_left' in r


# =============================================================================
# Spec Compliance Tests (Section 7 Test Cases)
# =============================================================================

class TestSpecCompliance:
    """Tests from Plan Section 7.1 - Channel Selection Tests."""
    
    def test_spec_use_all_24(self):
        """Spec: Use all 24 channels → Indices [0-23]"""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='all')
        indices = cfg.get_selected_indices()
        assert np.array_equal(indices, np.arange(24))
    
    def test_spec_first_12_of_24(self):
        """Spec: First 12 of 24 → Indices [0-11]"""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='first_n', n_channels_use=12)
        indices = cfg.get_selected_indices()
        assert np.array_equal(indices, np.arange(12))
    
    def test_spec_last_12_of_24(self):
        """Spec: Last 12 of 24 → Indices [12-23]"""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='last_n', n_channels_use=12)
        indices = cfg.get_selected_indices()
        assert np.array_equal(indices, np.arange(12, 24))
    
    def test_spec_range_5_15(self):
        """Spec: Range 5-15 → Indices [5-14]"""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='range',
                         channel_start=5, channel_end=15)
        indices = cfg.get_selected_indices()
        assert np.array_equal(indices, np.arange(5, 15))
    
    def test_spec_custom(self):
        """Spec: Custom [0,2,4,6,8] → Indices [0,2,4,6,8]"""
        cfg = ArrayConfig(n_channels_file=24, channel_mode='custom',
                         channel_indices=[0, 2, 4, 6, 8])
        indices = cfg.get_selected_indices()
        assert np.array_equal(indices, [0, 2, 4, 6, 8])


class TestSpecNonUniformSpacing:
    """Tests from Plan Section 7.2 - Non-Uniform Spacing Tests."""
    
    def test_spec_uniform_2m_aliasing(self):
        """Spec: Uniform 2m → k_alias = π/2"""
        cfg = ArrayConfig(n_channels_file=6, dx=2.0, spacing_mode='uniform')
        min_sp = cfg.get_min_spacing()
        k_alias = np.pi / min_sp
        assert np.isclose(k_alias, np.pi / 2)
    
    def test_spec_nonuniform_aliasing(self):
        """Spec: Non-uniform [0,2,4,8,14,22] → min diff = 2m"""
        cfg = ArrayConfig(n_channels_file=6, spacing_mode='custom',
                         custom_positions=[0, 2, 4, 8, 14, 22])
        min_sp = cfg.get_min_spacing()
        assert min_sp == 2.0
    
    def test_spec_variable_aliasing(self):
        """Spec: Variable [0,1,2,4,8,16] → min diff = 1m"""
        cfg = ArrayConfig(n_channels_file=6, spacing_mode='custom',
                         custom_positions=[0, 1, 2, 4, 8, 16])
        min_sp = cfg.get_min_spacing()
        assert min_sp == 1.0


class TestSpecInteriorShot:
    """Tests from Plan Section 7.3 - Interior Shot Tests."""
    
    def test_spec_source_at_10m(self):
        """Spec: Source at 10m in [0-22m] array → splits"""
        cfg = ArrayConfig(n_channels_file=12, dx=2.0, source_position=10.0,
                         interior_side='both')
        assert cfg.classify_shot() == 'interior'
        configs = cfg.split_interior_shot()
        # Should have both sides (enough channels on each)
        assert len(configs) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
