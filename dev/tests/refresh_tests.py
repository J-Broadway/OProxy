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
opr._storage()

tf.info("Calling opr.items('op1').name")
log(f"opr.items('op1') ------> {opr.items('op1').name}")

tf.info('Renaming "op1" to "changed1"')
opr.items[0].name = 'changed1'
tf.info("Logging opr.items('op1').name to show it still works before refresh. Below you should see name is 'changed1'")
log(opr.items('op1').name)
tf.info("showing storage before opr._refresh() ")
opr._storage()

tf.info('Now Running _refresh()')
opr._refresh()
tf.info('checking if name was changed to "changed1"')
try:
    op = opr.items('changed1')
    if op.name == 'changed1':
        tf.info(f'Name was changed to {op.name}')
    else:
        raise Exception('NAME WAS NOT CHANGED _REFRESH() FAILED')
except KeyError as e:
    log(e)
    raise
tf.info("Here's the storage after refresh")
opr._storage()
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
opr._storage()