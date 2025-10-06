import test_functions as tf
opr = parent.src.OProxy
log = tf.log

mvs = ['op1','op2','op3']

tf.info('Begin testing _storage()')
tf.info('Clearing storage')
opr._clear()

tf.info('Adding container')
opr._add('items', mvs)
tf.info('Now showing storage')
opr._storage()
expected = {
    "children": {
        "items": {
            "children": {},
            "ops": {
                "op1": {
                    "op": {
                        "name": "op1",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/op1"
                    },
                    "extensions": {}
                },
                "op2": {
                    "op": {
                        "name": "op2",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/op2"
                    },
                    "extensions": {}
                },
                "op3": {
                    "op": {
                        "name": "op3",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/op3"
                    },
                    "extensions": {}
                }
            },
            "extensions": {}
        }
    },
    "extensions": {}
}

tf.passed(expected, '_storage()', 'Checking above test')

tf.info('going to try to nest a container and then see if correct storage branch is printed')
opr.items._add('item2', mvs)
tf.info('nested "item2" added now showing storage')
opr.items.item2._storage()
tf.info('adding an extension to the nested container to test showing storage for extensions')
opr.items.item2._extend('test', func='hello', dat='extensions_for_tests')
tf.info('now showing storage for "item2" extension')
opr.items.item2.test._storage()
tf.info('now gonna try on an OPLeaf')
opr.items('op1')._storage()

opr._clear()
tf.info('++++++++++++++++++++++_Store() TESTS PASSED++++++++++++++++++++++')
