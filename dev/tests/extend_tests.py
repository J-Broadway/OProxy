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
log('Testing _remove() on extension')
opr.one.test._remove()
log('Testing args with call=True')
hey = opr.one._extend('test', func='callTrueTest', dat='extensions_for_tests', args=['I AM AN ARG THATS WORKING'], call=True)
log(hey('SUCCESFULLY SET ARG A SECOND TIME'))


