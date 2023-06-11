"""
ProteinArea
A package to calculate time-series protein area profile of MD data.
"""

# Add imports here
from .ProteinArea import canvas

# Handle versioneer
from ._version import get_versions
versions = get_versions()
__version__ = versions['version']
__git_revision__ = versions['full-revisionid']
del get_versions, versions
