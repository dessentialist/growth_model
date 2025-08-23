"""UI package for the FFF Growth System Streamlit application.

Having this file ensures `ui` is treated as a proper Python package in
all execution contexts (Streamlit, pytest, CLI), avoiding import errors
when `ui.*` modules are referenced from within `ui/app.py`.
"""
