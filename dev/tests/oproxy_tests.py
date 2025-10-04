import json

opr = parent.src.OProxy
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

def info(msg):
	print(f'\n{msg}\n')

def passed(test, test_name, msg):
	if test:
		print(f'\n{msg} --> {test_name.upper()} TEST PASSED\n')
	else:
		if test_name == 'storage':
			raise ValueError('\n STORAGE INCONGRUENCY \n')
		raise(f'\n{msg} --> {test_name.upper()} TEST FAILED\n')

def normalize_storage_for_comparison(storage):
    """Normalize storage by replacing OP objects with placeholders for comparison."""
    if isinstance(storage, dict):
        normalized = {}
        for key, value in storage.items():
            if key == 'op' and hasattr(value, 'name'):  # It's an OP object
                normalized[key] = "<OP_OBJECT>"
            else:
                normalized[key] = normalize_storage_for_comparison(value)
        return normalized
    elif isinstance(storage, list):
        return [normalize_storage_for_comparison(item) for item in storage]
    else:
        return storage

def current_storage(msg=None):
	current_storage = parent.src.fetch('rootStored').getRaw()
	if msg:
		# Normalize for JSON serialization before printing
		normalized_for_print = normalize_storage_for_comparison(current_storage)
		print(f'\n{msg} --> {json.dumps(normalized_for_print, indent=2)}\n')
	return normalize_storage_for_comparison(current_storage)
	
# Clear storage first
opr._clear()
mvs = ['op1','op2','op3']

# _add tests
opr._add('items', mvs) # Create OPContainer Item

# Verify storage after add
current_storage('Storage after _add')

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
passed(current_storage() == expected, 'storage', 'Checking if storage matches expected')

# test accessibility
for i in opr.items:
	print('Accessibility Test: ', i.name)

# test individual acces like so
print('Accessibility Test by [0]', opr.items[0].name)
print('Accessibility Test by [1]', opr.items[1].name)
print('Accessibility Test by [2]', opr.items[2].name)

# Testing Nested structure
info('Testing Nested structure')
opr.items._add('nest', mvs)
opr.items._add('second_nest', mvs)
current_storage('Storage after _add nested')

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

passed(current_storage() == expected, 'storage', 'Checking if nested storage matches expected')

info('Begin testing _remove() functionality')

current_storage('Current storage before _remove')

opr.items._remove('op1')
opr.items._remove('op3')

current_storage('Current storage after removal of op1 and op3')
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

passed(current_storage() == expected, 'storage', 'Checking if _remove() functionality works as expected')

info('Going to add another container and test _remove() functionality')
opr.items.nest._add('ANOTHER_NEST', mvs)
current_storage("Current storage after adding 'ANOTHER_NEST' container")
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

passed(current_storage() == expected, 'storage', 'Checking above test')
info('Gonna remove an entire branch')
opr.items._remove()
current_storage('Current storage after removing entire branch')
expected = {
  "OProxies": {
    "children": {},
    "extensions": {}
  }
}
passed(current_storage() == expected, 'storage', 'Checking above test')
info('Add container and try to remove individual leaves like this opr.items("op1")._remove()')
opr._add('items', mvs)
current_storage('Current storage after adding "items" container for OPLeaf testing')
opr.items('op1')._remove()
opr.items('op2')._remove()
current_storage('Current storage after removing OPLeafs')
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
passed(current_storage() == expected, 'storage', 'Checking above test')

info('Clearing storage!')
opr._clear()
print('==========TESTS COMPLETED==========')
print('Remind me to add more _remove() tests when extensions are implemented')


