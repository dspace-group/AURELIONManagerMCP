"""Structured request schemas shared by the AURELION Manager tools, one module per resource.

Models that changed between AURELION Manager versions carry a ``V<major>_<minor>``
suffix naming the version that introduced them; newer versions subclass older ones.
Tools expose the newest models to the LLM.
"""
