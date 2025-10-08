import test_functions as tf
tf.init()
opr = parent.src.OProxy
log = tf.log

tf.info('Begin testing monkey patch functionality')
tf.info('Clearing storage')
opr._clear()

tf.info("Adding containe opr._add('items', tf.mvs) ")
opr._add('items', tf.mvs)
tf.info("Showing storage after _add()")
opr._storage()
tf.info('Now going to monkey patch the "items" container')
opr._extend('items', cls='ResolutionMP', dat='extensions_for_tests', monkey_patch=True)
tf.info('Now going to call the monkey patched container')
opr.items('op1').resolution()

