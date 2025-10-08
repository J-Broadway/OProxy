import test_functions as tf
tf.init()
opr = parent.src.OProxy
log = tf.log

tf.info('Begin testing monkey patch functionality')
tf.info('Clearing storage')
opr._clear()
