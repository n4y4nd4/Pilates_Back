from django.test import TestCase

"""
Test suite entry point.
All tests are organized in the tests/ directory.
"""
# Import all test modules
from .tests.test_models import *
from .tests.test_services import *
from .tests.test_api import *
from .tests.test_utils import *
