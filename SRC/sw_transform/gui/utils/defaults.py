"""Default values for the MASW GUI application.

Copied from simple_app.py lines 103-131 (_DEFAULTS dict) and lines 82-88 (input variables).
"""

# Transform settings defaults
TRANSFORM_DEFAULTS = {
    'grid_fk': '4000',
    'tol_fk': '0',
    'grid_ps': '1200',
    'vspace_ps': 'log',
    'tol_ps': '0',
    'vibrosis': False,
    'cylindrical': False,
}

# Preprocessing defaults
PREPROCESS_DEFAULTS = {
    'downsample': True,
    'down_factor': '16',
    'numf': '4000',
    'start_time': '0.0',
    'end_time': '1.0',
}

# Peak picking defaults
PEAK_DEFAULTS = {
    'power_threshold': '0.1',
}

# Plot/export defaults
PLOT_DEFAULTS = {
    'auto_vel_limits': True,
    'auto_freq_limits': True,
    'plot_min_vel': '0',
    'plot_max_vel': '2000',
    'plot_min_freq': '0',
    'plot_max_freq': '100',
    'freq_tick_spacing': 'auto',
    'vel_tick_spacing': 'auto',
    'cmap': 'jet',
    'dpi': '200',
    'export_spectra': True,
}

# Processing limits defaults (from lines 82-88)
LIMITS_DEFAULTS = {
    'vmin': '0',
    'vmax': '5000',
    'fmin': '0',
    'fmax': '100',
    'time_start': '0.0',
    'time_end': '1.0',
}

# Vibrosis array config
VIBROSIS_DEFAULTS = {
    'dx': '2.0',  # Sensor spacing (m) for .mat files
}

# Combined defaults dict (for backwards compatibility with _DEFAULTS)
DEFAULTS = {
    # Transform
    'grid_fk': TRANSFORM_DEFAULTS['grid_fk'],
    'tol_fk': TRANSFORM_DEFAULTS['tol_fk'],
    'grid_ps': TRANSFORM_DEFAULTS['grid_ps'],
    'vspace_ps': TRANSFORM_DEFAULTS['vspace_ps'],
    'tol_ps': TRANSFORM_DEFAULTS['tol_ps'],
    'vibrosis': TRANSFORM_DEFAULTS['vibrosis'],
    'cylindrical': TRANSFORM_DEFAULTS['cylindrical'],
    # Preprocessing
    'downsample': PREPROCESS_DEFAULTS['downsample'],
    'down_factor': PREPROCESS_DEFAULTS['down_factor'],
    'numf': PREPROCESS_DEFAULTS['numf'],
    # Peak
    'power_threshold': PEAK_DEFAULTS['power_threshold'],
    # Plot
    'auto_vel_limits': PLOT_DEFAULTS['auto_vel_limits'],
    'auto_freq_limits': PLOT_DEFAULTS['auto_freq_limits'],
    'plot_min_vel': PLOT_DEFAULTS['plot_min_vel'],
    'plot_max_vel': PLOT_DEFAULTS['plot_max_vel'],
    'plot_min_freq': PLOT_DEFAULTS['plot_min_freq'],
    'plot_max_freq': PLOT_DEFAULTS['plot_max_freq'],
    'freq_tick_spacing': PLOT_DEFAULTS['freq_tick_spacing'],
    'vel_tick_spacing': PLOT_DEFAULTS['vel_tick_spacing'],
    'cmap': PLOT_DEFAULTS['cmap'],
    'dpi': PLOT_DEFAULTS['dpi'],
    'export_spectra': PLOT_DEFAULTS['export_spectra'],
    # Vibrosis
    'dx': VIBROSIS_DEFAULTS['dx'],
}
