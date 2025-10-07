import test_functions as tf
tf.init()
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
            "metadata": {
              "cls": None,
              "func": "hello",
              "dat_path": "/project1/myProject/extensions_for_tests",
              "dat_op": "<OP_OBJECT>",
              "args": None,
              "call": False,
              "created_at": 1759853778.3514366
            },
            "extensions": {}
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
initiate = test()
tf.info('Checking to make sure we can access "testFunc()" from extension class')
log(test.testFunc())
tf.info('checking call=True for class extension')
test = opr._extend('test', cls='myClass', dat='extensions_for_tests', args=['arg'], call=True)
log(test.testFunc())
tf.info('Checking Storage For Root Level Extensions')
tf.current_storage('Should see extensions stored in storage')
expected ={
  "OProxies": {
    "children": {},
    "extensions": {
      "test": {
        "metadata": {
          "cls": "myClass",
          "func": None,
          "dat_path": "/project1/myProject/extensions_for_tests",
          "dat_op": "<OP_OBJECT>",
          "args": [
            "arg"
          ],
          "call": True,
          "created_at": 1759853993.566761
        },
        "extensions": {}
      }
    }
  }
}
tf.passed(expected, 'storage', 'Checking if root extensions storage matches expected')

tf.info('going to reinitiate container extensions to check if extention persistence is working')
parent.src.par.reinitextensions.pulse()
log(test.testFunc())

tf.info('Starting tests to re-name extension dats and check of OPRoxy gracefully handles DAT rename detection.\nClearing Storage...')
# First make sure test dats are named properly
if t := op('renamed_extensions'):
	t.name = "rename_extensions_for_tests"

opr._clear()
opr._storage()
tf.info("Creating opr._extend('test', cls='myClass', dat='rename_extensions_for_tests', call=True) ")
opr._extend('test', cls='myClass', dat='rename_extensions_for_tests', call=True)
tf.info("Here's what storage looks like")
opr._storage()
tf.info("Running log(opr.test.testFunc()) to ake sure it's printing correctly")
log(opr.test.testFunc())

tf.info("Now going to test renaming the dat then reloading extensions to see if the name change is gracefully handled")
op('rename_extensions_for_tests').name = 'renamed_extensions'

tf.info("Going to re-init container extensions")
parent.src.par.reinitextensions.pulse()

tf.info("Running 'opr.test.testFunc()' to see if it still works after name change")
log(opr.test.testFunc())

tf.info("If you're reading this it worked! \nRe-naming the DAT back to it's original...")
op('renamed_extensions').name = 'rename_extensions_for_tests'

tf.info("++++++++++++++++++++++EXTEND TESTS PASSED++++++++++++++++++++++")