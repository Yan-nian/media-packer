"""Media Packer - A torrent creation tool for TV shows and movies"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__all__ = ["__version__"]