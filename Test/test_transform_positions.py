"""Unit tests for transform position array support.

Tests all 4 transforms (PS, FK, FDBF, SS) with both uniform scalar dx
and non-uniform position arrays.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'SRC'))

import numpy as np
import pytest
from sw_transform.processing.ps import phase_shift_transform
from sw_transform.processing.fk import fk_transform
from sw_transform.processing.fdbf import fdbf_transform
from sw_transform.processing.ss import slant_stack_transform


def create_synthetic_data(n_samples=1024, n_channels=24, dt=0.001, velocity=200.0, freq=30.0):
    """Create synthetic surface wave data for testing."""
    t = np.arange(n_samples) * dt
    data = np.zeros((n_samples, n_channels))
    for i in range(n_channels):
        offset = i * 2.0
        delay = offset / velocity
        data[:, i] = np.sin(2 * np.pi * freq * (t - delay)) * np.exp(-((t - delay - 0.1)**2) / 0.01)
    return data


class TestUniformSpacing:
    """Test transforms with uniform scalar dx."""
    
    @pytest.fixture
    def synthetic_data(self):
        return create_synthetic_data()
    
    def test_ps_uniform(self, synthetic_data):
        """Test PS transform with scalar dx."""
        f, v, p = phase_shift_transform(synthetic_data, 0.001, 2.0, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_fk_uniform(self, synthetic_data):
        """Test FK transform with scalar dx."""
        f, v, p = fk_transform(synthetic_data, 0.001, 2.0, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_fdbf_uniform(self, synthetic_data):
        """Test FDBF transform with scalar dx."""
        f, v, p = fdbf_transform(synthetic_data, 0.001, 2.0, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_ss_uniform(self, synthetic_data):
        """Test SS transform with scalar dx."""
        f, v, p = slant_stack_transform(synthetic_data, 0.001, 2.0, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))


class TestNonUniformSpacing:
    """Test transforms with position arrays."""
    
    @pytest.fixture
    def synthetic_data(self):
        return create_synthetic_data()
    
    @pytest.fixture
    def uniform_positions(self):
        """Uniform positions as array (should match scalar dx=2)."""
        return np.arange(24) * 2.0
    
    @pytest.fixture
    def nonuniform_positions(self):
        """Non-uniform positions (varying spacing)."""
        return np.array([0, 2, 4, 6, 8, 10, 14, 18, 22, 26, 30, 35, 
                        40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95], dtype=float)
    
    def test_ps_uniform_array(self, synthetic_data, uniform_positions):
        """Test PS transform with uniform positions array."""
        f, v, p = phase_shift_transform(synthetic_data, 0.001, uniform_positions, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_fk_uniform_array(self, synthetic_data, uniform_positions):
        """Test FK transform with uniform positions array."""
        f, v, p = fk_transform(synthetic_data, 0.001, uniform_positions, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_fdbf_uniform_array(self, synthetic_data, uniform_positions):
        """Test FDBF transform with uniform positions array."""
        f, v, p = fdbf_transform(synthetic_data, 0.001, uniform_positions, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_ss_uniform_array(self, synthetic_data, uniform_positions):
        """Test SS transform with uniform positions array."""
        f, v, p = slant_stack_transform(synthetic_data, 0.001, uniform_positions, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_ps_nonuniform(self, synthetic_data, nonuniform_positions):
        """Test PS transform with non-uniform positions."""
        f, v, p = phase_shift_transform(synthetic_data, 0.001, nonuniform_positions, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_fk_nonuniform(self, synthetic_data, nonuniform_positions):
        """Test FK transform with non-uniform positions."""
        f, v, p = fk_transform(synthetic_data, 0.001, nonuniform_positions, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_fdbf_nonuniform(self, synthetic_data, nonuniform_positions):
        """Test FDBF transform with non-uniform positions."""
        f, v, p = fdbf_transform(synthetic_data, 0.001, nonuniform_positions, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))
    
    def test_ss_nonuniform(self, synthetic_data, nonuniform_positions):
        """Test SS transform with non-uniform positions."""
        f, v, p = slant_stack_transform(synthetic_data, 0.001, nonuniform_positions, fmin=5, fmax=80)
        assert p.shape[0] > 0
        assert p.shape[1] > 0
        assert not np.any(np.isnan(p))


class TestScalarVsArrayConsistency:
    """Test that scalar dx and equivalent array give same results."""
    
    @pytest.fixture
    def synthetic_data(self):
        return create_synthetic_data()
    
    def test_ps_consistency(self, synthetic_data):
        """PS: scalar dx=2 should match array [0,2,4,...]."""
        f1, v1, p1 = phase_shift_transform(synthetic_data, 0.001, 2.0, fmin=5, fmax=80)
        positions = np.arange(24) * 2.0
        f2, v2, p2 = phase_shift_transform(synthetic_data, 0.001, positions, fmin=5, fmax=80)
        assert np.allclose(p1, p2, rtol=1e-10)
    
    def test_fk_consistency(self, synthetic_data):
        """FK: scalar dx=2 should match array [0,2,4,...]."""
        f1, v1, p1 = fk_transform(synthetic_data, 0.001, 2.0, fmin=5, fmax=80)
        positions = np.arange(24) * 2.0
        f2, v2, p2 = fk_transform(synthetic_data, 0.001, positions, fmin=5, fmax=80)
        assert np.allclose(p1, p2, rtol=1e-10)
    
    def test_fdbf_consistency(self, synthetic_data):
        """FDBF: scalar dx=2 should match array [0,2,4,...]."""
        f1, v1, p1 = fdbf_transform(synthetic_data, 0.001, 2.0, fmin=5, fmax=80)
        positions = np.arange(24) * 2.0
        f2, v2, p2 = fdbf_transform(synthetic_data, 0.001, positions, fmin=5, fmax=80)
        assert np.allclose(p1, p2, rtol=1e-10)
    
    def test_ss_consistency(self, synthetic_data):
        """SS: scalar dx=2 should match array [0,2,4,...]."""
        f1, v1, p1 = slant_stack_transform(synthetic_data, 0.001, 2.0, fmin=5, fmax=80)
        positions = np.arange(24) * 2.0
        f2, v2, p2 = slant_stack_transform(synthetic_data, 0.001, positions, fmin=5, fmax=80)
        assert np.allclose(p1, p2, rtol=1e-10)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
