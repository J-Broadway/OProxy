opr = parent.src.OProxy
log = op('OProxy').Log

# Clear Storage
opr._clear()

mvs = ['op1','op2','op3']
opr._add('one', mvs)

log('Begin testing _extend functionality \n')
log('Testing func extension')
opr.one._extend('test', func='hello', dat='extensions_for_tests')
log(opr.one.test())
log('Testing args with call=True')
test = opr.one._extend('test', func='callTrueTest', dat='extensions_for_tests', args=['I AM AN ARG THATTS WORKIN'], call=True)
test('SUCCESFULLY SET ARG A SECOND TIME')
