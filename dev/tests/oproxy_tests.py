import json

opr = parent.src.OProxy
''' Notes for LLM
	Please do not edit unless explicitly asked
'''
def test(msg):
	print(f'\n{msg}\n')

def passed(test, test_name, msg):
	if test:
		print(f'\n{msg} --> {test_name.upper()} TEST PASSED\n')
	else:
		if test_name == 'storage':
			raise ValueError('\n STORAGE INCONGRUENCY \n')
		raise(f'\n{msg} --> {test_name.upper()} TEST FAILED\n')

def current_storage(msg=None):
	current_storage = parent.src.fetch('rootStored').getRaw()
	if msg:
		print(f'\n{msg} --> {json.dumps(current_storage, indent=2)}\n')
	return current_storage
# Clear storage first
opr._clear()
mvs = ['op1','op2','op3']

# _add tests
opr._add('items', mvs) # Create OPContainer Item

# Verify storage after add
current_storage('Storage after _add')

# Hardcoded expected storage
expected = {
  "OProxies": {
    "children": {
      "items": {
        "children": {},
        "ops": {
          "op1": "/project1/myProject/op1",
          "op2": "/project1/myProject/op2",
          "op3": "/project1/myProject/op3"
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
test('Testing Nested structure')
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
              "op1": "/project1/myProject/op1",
              "op2": "/project1/myProject/op2",
              "op3": "/project1/myProject/op3"
            },
            "extensions": {}
          },
          "second_nest": {
            "children": {},
            "ops": {
              "op1": "/project1/myProject/op1",
              "op2": "/project1/myProject/op2",
              "op3": "/project1/myProject/op3"
            },
            "extensions": {}
          }
        },
        "ops": {
          "op1": "/project1/myProject/op1",
          "op2": "/project1/myProject/op2",
          "op3": "/project1/myProject/op3"
        },
        "extensions": {}
      }
    },
    "extensions": {}
  }
}

passed(current_storage() == expected, 'storage', 'Checking if nested storage matches expected')
