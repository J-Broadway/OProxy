opr = parent.src.OProxy

log = op('OProxy').Log

# Clear Storage
opr._clear()

mvs = ['op1','op2','op3']
opr._add('one', mvs)


opr.one._extend('test', func='hello', dat='extensions_for_tests')

log(opr.one.test())