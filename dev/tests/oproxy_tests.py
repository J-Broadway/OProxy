import test_functions as tf 
opr = parent.src.OProxy
log = tf.log


''' Notes for LLM
	Please do not edit unless explicitly asked
'''
# Make sure ops have correct names
if t := op('changed1'):
	t.name = 'op1'
	
if t := op('changed2'):
	t.name = 'op2'
	
if t := op('changed3'):
	t.name = 'op3'
	
# Clear storage first
tf.init()
opr._clear()
mvs = ['op1','op2','op3']

# _add tests
opr._add('items', mvs) # Create OProxyContainer Item

# Verify storage after add
tf.current_storage('Line 61: Storage after _add')

# Hardcoded expected storage (normalized for comparison - OP objects become placeholders)
expected = {
  "OProxies": {
    "children": {
      "items": {
        "children": {},
        "ops": {
          "op1": {"path": "/project1/myProject/op1", "op": "<OP_OBJECT>", "extensions": {}},
          "op2": {"path": "/project1/myProject/op2", "op": "<OP_OBJECT>", "extensions": {}},
          "op3": {"path": "/project1/myProject/op3", "op": "<OP_OBJECT>", "extensions": {}}
        },
        "extensions": {}
      }
    },
    "extensions": {}
  }
}
tf.passed(expected, 'storage', 'Checking if storage matches expected')

# test accessibility
for i in opr.items:
	log(f'Accessibility Test: {i.name}', status='test', process='access')

# test individual acces like so
log(f'Accessibility Test by [0] {opr.items[0].name}', status='test', process='access')
log(f'Accessibility Test by [1] {opr.items[1].name}', status='test', process='access')
log(f'Accessibility Test by [2] {opr.items[2].name}', status='test', process='access')

# Testing Nested structure
tf.info('Testing Nested structure')
opr.items._add('nest', mvs)
opr.items._add('second_nest', mvs)
tf.current_storage('Storage after _add nested')

# Set expected storage
expected = {
  "OProxies": {
    "children": {
      "items": {
        "children": {
          "nest": {
            "children": {},
            "ops": {
              "op1": {
                "path": "/project1/myProject/op1",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op2": {
                "path": "/project1/myProject/op2",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op3": {
                "path": "/project1/myProject/op3",
                "op": "<OP_OBJECT>",
                "extensions": {}
              }
            },
            "extensions": {}
          },
          "second_nest": {
            "children": {},
            "ops": {
              "op1": {
                "path": "/project1/myProject/op1",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op2": {
                "path": "/project1/myProject/op2",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op3": {
                "path": "/project1/myProject/op3",
                "op": "<OP_OBJECT>",
                "extensions": {}
              }
            },
            "extensions": {}
          }
        },
        "ops": {
          "op1": {
            "path": "/project1/myProject/op1",
            "op": "<OP_OBJECT>",
            "extensions": {}
          },
          "op2": {
            "path": "/project1/myProject/op2",
            "op": "<OP_OBJECT>",
            "extensions": {}
          },
          "op3": {
            "path": "/project1/myProject/op3",
            "op": "<OP_OBJECT>",
            "extensions": {}
          }
        },
        "extensions": {}
      }
    },
    "extensions": {}
  }
}

tf.passed(expected, 'storage', 'Checking if nested storage matches expected')

# Validation tests
tf.info('Begin testing name validation')

# Test invalid container names
invalid_names = [
    'test space',      # space
    'test-space',      # hyphen
    'test.space',      # dot
    '123test',         # starts with digit
    'test@name',       # special character
    'class',           # Python keyword
    'def',             # Python keyword
    '',                # empty string
    'test name',       # multiple spaces
    'for',             # Python keyword
    'if',              # Python keyword
]

for invalid_name in invalid_names:
    try:
        opr._add(invalid_name, mvs)
        log(f"ERROR: Should have failed for invalid name '{invalid_name}'", status='error', process='validation_test')
        raise Exception(f"Validation failed - allowed invalid name '{invalid_name}'")
    except ValueError as e:
        log(f"SUCCESS: Correctly rejected invalid name '{invalid_name}': {e}", status='test', process='validation_test')
    except Exception as e:
        log(f"UNEXPECTED ERROR for '{invalid_name}': {e}", status='error', process='validation_test')
        raise

# Test valid container names
valid_names = [
    'test_container',
    'TestContainer',
    'test123',
    '_private',
    'a',
    'my_long_container_name_with_underscores'
]

for valid_name in valid_names:
    try:
        # Clean up any existing container first
        if valid_name in opr._children:
            opr._remove(valid_name)

        opr._add(valid_name, ['op1'])
        log(f"SUCCESS: Correctly accepted valid name '{valid_name}'", status='test', process='validation_test')

        # Clean up
        opr._remove(valid_name)
    except Exception as e:
        log(f"ERROR: Failed to accept valid name '{valid_name}': {e}", status='error', process='validation_test')
        raise

# Test invalid extension names
invalid_ext_names = [
    'test space',
    'test-space',
    '123test',
    'class',
    'def',
    'for',
    ''
]

for invalid_name in invalid_ext_names:
    try:
        opr._extend(invalid_name, func='hello', dat='extensions_for_tests')
        log(f"ERROR: Should have failed for invalid extension name '{invalid_name}'", status='error', process='validation_test')
        raise Exception(f"Validation failed - allowed invalid extension name '{invalid_name}'")
    except ValueError as e:
        log(f"SUCCESS: Correctly rejected invalid extension name '{invalid_name}': {e}", status='test', process='validation_test')
    except Exception as e:
        log(f"UNEXPECTED ERROR for extension '{invalid_name}': {e}", status='error', process='validation_test')
        raise

tf.info('Name validation tests completed')

tf.info('Begin testing _remove() functionality')

tf.current_storage('Current storage before _remove')

opr.items._remove('op1')
opr.items._remove('op3')

tf.current_storage('Current storage after removal of op1 and op3')
expected = {
  "OProxies": {
    "children": {
      "items": {
        "children": {
          "nest": {
            "children": {},
            "ops": {
              "op1": {
                "path": "/project1/myProject/op1",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op2": {
                "path": "/project1/myProject/op2",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op3": {
                "path": "/project1/myProject/op3",
                "op": "<OP_OBJECT>",
                "extensions": {}
              }
            },
            "extensions": {}
          },
          "second_nest": {
            "children": {},
            "ops": {
              "op1": {
                "path": "/project1/myProject/op1",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op2": {
                "path": "/project1/myProject/op2",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op3": {
                "path": "/project1/myProject/op3",
                "op": "<OP_OBJECT>",
                "extensions": {}
              }
            },
            "extensions": {}
          }
        },
        "ops": {
          "op2": {
            "path": "/project1/myProject/op2",
            "op": "<OP_OBJECT>",
            "extensions": {}
          }
        },
        "extensions": {}
      }
    },
    "extensions": {}
  }
}

tf.passed(expected, 'storage', 'Checking if _remove() functionality works as expected')

tf.info('Going to add another container and test _remove() functionality')
opr.items.nest._add('ANOTHER_NEST', mvs)
tf.current_storage("Current storage after adding 'ANOTHER_NEST' container")
expected = {
  "OProxies": {
    "children": {
      "items": {
        "children": {
          "nest": {
            "children": {
              "ANOTHER_NEST": {
                "children": {},
                "ops": {
                  "op1": {
                    "path": "/project1/myProject/op1",
                    "op": "<OP_OBJECT>",
                    "extensions": {}
                  },
                  "op2": {
                    "path": "/project1/myProject/op2",
                    "op": "<OP_OBJECT>",
                    "extensions": {}
                  },
                  "op3": {
                    "path": "/project1/myProject/op3",
                    "op": "<OP_OBJECT>",
                    "extensions": {}
                  }
                },
                "extensions": {}
              }
            },
            "ops": {
              "op1": {
                "path": "/project1/myProject/op1",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op2": {
                "path": "/project1/myProject/op2",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op3": {
                "path": "/project1/myProject/op3",
                "op": "<OP_OBJECT>",
                "extensions": {}
              }
            },
            "extensions": {}
          },
          "second_nest": {
            "children": {},
            "ops": {
              "op1": {
                "path": "/project1/myProject/op1",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op2": {
                "path": "/project1/myProject/op2",
                "op": "<OP_OBJECT>",
                "extensions": {}
              },
              "op3": {
                "path": "/project1/myProject/op3",
                "op": "<OP_OBJECT>",
                "extensions": {}
              }
            },
            "extensions": {}
          }
        },
        "ops": {
          "op2": {
            "path": "/project1/myProject/op2",
            "op": "<OP_OBJECT>",
            "extensions": {}
          }
        },
        "extensions": {}
      }
    },
    "extensions": {}
  }
}

tf.passed(expected, 'storage', 'Checking above test')
tf.info('Gonna remove an entire branch')
opr.items._remove()
tf.current_storage('Current storage after removing entire branch')
expected = {
  "OProxies": {
    "children": {},
    "extensions": {}
  }
}
tf.passed(expected, 'storage', 'Checking above test')
tf.info('Add container and try to remove individual leaves like this opr.items("op1")._remove()')
opr._add('items', mvs)
tf.current_storage('Current storage after adding "items" container for OProxyLeaf testing')
opr.items('op1')._remove()
opr.items('op2')._remove()
tf.current_storage('Current storage after removing OProxyLeafs')
expected = {
  "OProxies": {
    "children": {
      "items": {
        "children": {},
        "ops": {
          "op3": {"path": "/project1/myProject/op3", "op": "<OP_OBJECT>", "extensions": {}}
        },
        "extensions": {}
      }
    },
    "extensions": {}
  }
}
tf.passed(expected, 'storage', 'Checking above test')

tf.info('Clearing storage!')
#opr._clear(flush_logger=False)
tf.log('==========TESTS COMPLETED==========', status='test', process='complete')
print('Remind me to add more _remove() tests when extensions are implemented')


