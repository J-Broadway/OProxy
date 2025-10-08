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
tf.info('verifying that MonkeyPatch path is correct')
mp = mod('OProxy/MonkeyPatch')
log(mp.sup)
tf.info(" now running opr._extend('items', cls='ResolutionMP', dat='extensions_for_tests', monkey_patch=True)" )
opr._extend('items', cls='ResolutionMP', dat='extensions_for_tests', monkey_patch=True)
tf.info('showing storage after _extend()')
opr._storage()
tf.info('Now going to call the monkey patched container')
log(opr.items('op1').resolution())
log(opr.items('op2').resolution())

tf.info('Now testing storage persistence after container is re-initialized')
parent.src.par.reinitextensions.pulse()
tf.info('Calling "resolution()" on monkey patched containers')
log(opr.items('op1').resolution())
log(opr.items('op2').resolution())

tf.info('Now testing a monkey patched OPLeaf')
opr.items._extend('op1', cls='helloWorld', dat='extensions_for_tests', monkey_patch=True)
tf.info('checking storage after adding helloWorld monkey patch')
opr._storage()
tf.info('Calling "helloWorld()" on monkey patched OPLeaf')
log(opr.items('op1').helloWorld())
tf.info('Now going to run "monkey_patch_outside_tests" to make sure persistence works')
try:
	op('monkey_patch_outside_tests').run()
except Exception as e:
	log(e)

