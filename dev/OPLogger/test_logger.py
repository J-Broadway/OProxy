# Test script for OPLogger
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from OPLogger import Logger

# Mock the parent object for testing
class MockParent:
    def __init__(self):
        self.Name = 'OProxy'

# Create logger instance
logger = Logger(MockParent())

print("=== OPLogger Test ===")

# Run the test
logger.flush()
logger('hello world', process='Test')
logger('hello world', process='Test')
logger('hello world', process='Different')

print("=== Test completed ===")
