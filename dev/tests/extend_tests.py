import test_functions as tf
opr = parent.src.OProxy
log = tf.log

# Clear Storage
opr._clear()

mvs = ['op1','op2','op3']
opr._add('one', mvs)

tf.info('Begin testing _extend functionality')
tf.info('Testing func extension')
opr.one._extend('test', func='hello', dat='extensions_for_tests')
log(opr.one.test())
log('Testing _remove() on extension.')
tf.current_storage('Current storage before _remove()')
expected = {
  "OProxies": {
    "children": {
      "one": {
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
        "extensions": {
          "test": {
            "cls": None,
            "func": "hello",
            "dat_path": "/project1/myProject/extensions_for_tests",
            "args": None,
            "call": False,
            "created_at": 1759638996.7720973
          }
        }
      }
    },
    "extensions": {}
  }
}
# Get actual storage and compare without timestamps
import copy
actual_storage = tf.current_storage()
expected_copy = copy.deepcopy(expected)

# Remove timestamp from comparison since it changes each run
if 'OProxies' in actual_storage and 'children' in actual_storage['OProxies'] and 'one' in actual_storage['OProxies']['children']:
    if 'extensions' in actual_storage['OProxies']['children']['one'] and 'test' in actual_storage['OProxies']['children']['one']['extensions']:
        actual_ext = actual_storage['OProxies']['children']['one']['extensions']['test']
        expected_ext = expected_copy['OProxies']['children']['one']['extensions']['test']
        # Check that timestamp exists and is a number
        if 'created_at' in actual_ext and isinstance(actual_ext['created_at'], (int, float)):
            expected_ext['created_at'] = actual_ext['created_at']

tf.passed(actual_storage == expected_copy, 'storage', 'Checking if storage matches expected')
opr.one.test._remove()
log('Testing args with call=True')
hey = opr.one._extend('test', func='callTrueTest', dat='extensions_for_tests', args=['I AM AN ARG THATS WORKING'], call=True)
log(hey('SUCCESFULLY SET ARG A SECOND TIME'))

tf.info('testing class extensions now')
