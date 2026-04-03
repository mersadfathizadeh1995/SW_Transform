"""Default values for MASW 2D GUI components.

Copied from masw2d_tab.py lines 67-85 (_DEFAULTS dict).
"""

# MASW 2D Default values (used for reset)
MASW2D_DEFAULTS = {
    # Transform settings
    'grid_n': '4000',
    'vspace': 'log',
    'tol': '0.01',
    'power_threshold': '0.1',
    'vibrosis': False,
    'cylindrical': False,
    
    # Preprocessing settings
    'start_time': '0.0',
    'end_time': '1.0',
    'downsample': True,
    'down_factor': '16',
    'numf': '4000',
    
    # Image export settings
    'plot_max_vel': 'auto',
    'plot_max_freq': 'auto',
    'cmap': 'jet',
    'dpi': '150',
    'fig_width': '8',
    'fig_height': '6',
    'contour_levels': '30',
    'plot_style': 'contourf',
    
    # Array defaults
    'n_channels': '24',
    'dx': '2.0',
    'source_type': 'hammer',
    'slide_step': '1',
    
    # Processing defaults
    'method': 'ps',
    'freq_min': '0',
    'freq_max': '100',
    'vel_min': '0',
    'vel_max': '4000',
}
