import test_functions as tf 
opr = parent.src.OProxy
log = tf.log
tf.info('Begin testing _refresh()... Clearing storage')
tf.init()
tf.info('Clearing Storage')
opr._clear()

tf.info('Adding container')
opr._add('items', tf.mvs)
tf.info('Showing storage after _add()')
current_storage = opr._storage()
expected = '''{
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
}'''
tf.testCheck(current_storage == expected, 'storage', 'Checking if storage matches expected after _add()')

tf.info("Calling opr.items('op1').name")
log(f"opr.items('op1') ------> {opr.items('op1').name}")

tf.info('Renaming "op1" to "changed1"')
opr.items[0].name = 'changed1'
tf.info("Logging opr.items('op1').name to show it still works before refresh. Below you should see name is 'changed1'")
log(opr.items('op1').name)
tf.info("showing storage before opr._refresh() ")
current_storage = opr._storage()
expected = '''{
    "children": {
        "items": {
            "children": {},
            "ops": {
                "op1": {
                    "op": {
                        "name": "changed1",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/changed1"
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
}'''
tf.testCheck(current_storage == expected, 'storage', 'Checking if storage matches expected after renaming "op1" to "changed1" "op1" does not have the proper name yet because _refresh() has not been run yet')

tf.info('Now Running _refresh()')
opr._refresh()
tf.info('checking if name was changed to "changed1"')
try:
    operator = opr.items('changed1')
    if operator.name == 'changed1':
        tf.info(f'Name was changed to {operator.name}')
    else:
        raise Exception('NAME WAS NOT CHANGED _REFRESH() FAILED')
except KeyError as e:
    log(e)
    raise
tf.info("Here's the storage after refresh")
current_storage = opr._storage()
expected = '''{
    "children": {
        "items": {
            "children": {},
            "ops": {
                "changed1": {
                    "op": {
                        "name": "changed1",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/changed1"
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
}'''
tf.testCheck(current_storage == expected, 'storage', 'Checking if storage matches expected after refresh')
tf.info("Changing name back to 'op1")
opr.items('changed1').name = 'op1'
tf.info("going to call the new name without refreshing to make sure an error gets called")
try:
    opr.items('op1').name
except KeyError as e:
    log(f'Error triggered as expected...')

tf.info("Now doing opr.items._refresh() to make sure it works")
opr.items._refresh()
tf.info("checking if name was changed")
try:
    if opr.items('op1').name == 'op1':
        tf.info('Can confirm name is "op1"')
    else:
        raise Exception('NAME WAS NOT CHANGED _REFRESH() FAILED')
except KeyError as e:
    log(e)

tf.info("Here's storage")
current_storage = opr._storage()
expected = '''{
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
}'''
tf.testCheck(current_storage == expected, 'storage', 'Checking if storage matches expected after refresh')
tf.info('Now going to rename "op1" --> "changed1" and "op2" --> "changed2" but only call refresh on "op1" to make sure only one name change is detected')
opr.items('op1').name = 'changed1'
opr.items('op2').name = 'changed2'
tf.info('Here is storage before refresh')
current_storage = opr._storage()
expected = '''{
    "children": {
        "items": {
            "children": {},
            "ops": {
                "op1": {
                    "op": {
                        "name": "changed1",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/changed1"
                    },
                    "extensions": {}
                },
                "op2": {
                    "op": {
                        "name": "changed2",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/changed2"
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
}'''
tf.testCheck(current_storage == expected, 'storage', 'Checking if storage matches expected before refresh')
tf.info('Running _refresh() on "op1"')
opr.items('op1')._refresh() # _refresh() not working here
tf.info('Here is storage after refresh')
current_storage = opr._storage()
expected = '''{
    "children": {
        "items": {
            "children": {},
            "ops": {
                "changed1": {
                    "op": {
                        "name": "changed1",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/changed1"
                    },
                    "extensions": {}
                },
                "op2": {
                    "op": {
                        "name": "changed2",
                        "type": "moviefileinTOP",
                        "path": "/project1/myProject/changed2"
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
}'''
tf.testCheck(current_storage == expected, 'storage', 'Checking if storage matches expected after refresh')

tf.info('Now going to test adding an extension then renaming it and calling _refresh on the extension')
opr._extend('testing', func='hello', dat='rename_extensions_for_tests')
tf.info('Here is storage before refresh')
tf.info('Now changing name of "rename_extensions_for_tests" to "renamed_extension"')
op('rename_extensions_for_tests').name = 'renamed_extension'
tf.info('Now going to refresh the extension')
opr.testing._refresh()
tf.info('Here is storage after refresh')
opr._storage()


#tf.done('_refresh')