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
tf.passed(expected, 'storage', 'Checking if storage matches expected')
opr.one.test._remove()
log('Testing args with call=True')
hey = opr.one._extend('test', func='callTrueTest', dat='extensions_for_tests', args=['I AM AN ARG THATS WORKING'], call=True)
log(hey('SUCCESFULLY SET ARG A SECOND TIME'))

tf.info('Testing trying to overwrite extension class with monkey_patch=False')
tf.info('First clear storage')
opr._clear()

tf.info('Creating extension class')
test = opr._extend('test', cls='myClass', dat='extensions_for_tests')
tf.info('Checkint to make sure we can access "testFunc()" from extension class')
log(test.testFunc())
