# MonkeyPatch.DAT
'''Helpers for monkey patching'''
OProxyBaseWrapper   = mod('OProxyBaseWrapper')
OProxyContainer     = OProxyBaseWrapper.OProxyContainer
OProxyLeaf = OProxyBaseWrapper.OProxyLeaf
utils = mod('utils')
log = parent.opr.Log
sup = 'hello world'