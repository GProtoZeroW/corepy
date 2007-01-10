
import array

import corepy.arch.ppc.isa as ppc
import corepy.spre.spe as spe
import corepy.arch.ppc.lib.util as util
  
__doc__ = """
"""

# ------------------------------------------------------------
# 'Type' Classes
# ------------------------------------------------------------

# Type classes implement the operator overloads for a type and hold
# other type-specific information, such as register types and valid
# literal types.

# They are separate from the type so they can be used as mix-ins in
# different contexts, e.g. Variables and Expressions subclasses can
# both share operator semantics by subclassing the same operator
# class.  

# Operator classes also provide static interfaces to typed versions of
# the operations.  

# Operator methods return an Expression of an appropriate type for the
# operation.

# To always return the same type:
#  return SignedWord.expr_class(inst, *(self, other))

# To upcast to the type of the first operand:
#  return self.expr_class(inst, *(self, other))

# To upcast to the type of the second operand:
#  return other.expr_class(inst, *(self, other))

# Upcasting can be useful for two types of different specificity are
# used in expressions and the more specific type should be 
# preserved type the expressions.  For instance, the logical
# operators are the base classes of all integer-like types.  A logical 
# operation, e.g. (a & b), should preserve the most specific type of a
# and b.

def _most_specific(a, b, default = None):
  """
  If a and b are from the same hierarcy, return the more specific of
  [type(a), type(b)], or the default type if they are from different
  hierarchies. If default is None, return type(a), or type(b) if a
  does not have a type_cls
  """
  if (hasattr(a, 'type_cls') and hasattr(a, 'type_cls')):
    if issubclass(b.type_cls, a.type_cls):
      return type(b)
    elif issubclass(a.type_cls, b.type_cls):
      return type(a)
  elif default is None:
    if hasattr(a, 'type_cls'):
      return type(a)
    elif hasattr(b, 'type_cls'):
      return type(b)
    
  return default
  
_int_literals = (spe.Immediate, int, long)

class PPCType(spe.Type):
  def _get_active_code(self):
    return ppc.get_active_code()

  def _set_active_code(self, code):
    return ppc.set_active_code(code)
  active_code = property(_get_active_code, _set_active_code)

# ------------------------------------------------------------
# General Purpose Register Types
# ------------------------------------------------------------

class BitType(PPCType):
  register_type_id = 'gp'
  literal_types = (int,long)

  def _upcast(self, other, inst):
    return inst.ex(self, other, type_cls = _most_specific(self, other))

  def __and__(self, other):
    if isinstance(other, BitType):
      return self._upcast(other, ppc.andx)
    elif isinstance(other, _int_literals):
      return ppc.andi.ex(self, other, type_cls = self.var_cls)
    raise Exception('__and__ not implemented for %s and %s' % (type(self), type(other)))    

  and_ = staticmethod(__and__)

  def __lshift__(self, other):
    if isinstance(other, BitType):
      return ppc.slwx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__lshift__ not implemented for %s and %s' % (type(self), type(other)))    
  lshift = staticmethod(__lshift__)

  def __rshift__(self, other):
    if isinstance(other, BitType):
      return ppc.srwx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__rshift__ not implemented for %s and %s' % (type(self), type(other)))    
  rshift = staticmethod(__rshift__)

  def __or__(self, other):
    if isinstance(other, BitType):
      return self._upcast(other, ppc.orx)
    elif isinstance(other, _int_literals):
      return ppc.ori.ex(self, other, type_cls = self.var_cls)
    raise Exception('__or__ not implemented for %s and %s' % (type(self), type(other)))    
  or_ = staticmethod(__or__)

  def __xor__(self, other):
    if isinstance(other, BitType):
      return self._upcast(other, ppc.xorx)
    elif isinstance(other, _int_literals):
      return ppc.xori.ex(self, other, type_cls = self.var_cls)
    raise Exception('__xor__ not implemented for %s and %s' % (type(self), type(other)))    
  xor = staticmethod(__xor__)

  def _set_literal_value(self, value):
    # Put the lower 16 bits into r-temp
    self.code.add(ppc.addi(self.reg, 0, value))
  
    # Addis r-temp with the upper 16 bits (shifted add immediate) and
    # put the result in r-target
    if (value & 0xFFFF) != value:
      self.code.add(ppc.addis(self.reg, self.reg, ((value + 32768) >> 16)))
      
    return


# ------------------------------
# Integer Types
# ------------------------------

class UnsignedWordType(BitType):
  def __add__(self, other):
    if isinstance(other, UnsignedWordType):
      return ppc.addx.ex(self, other, type_cls = self.var_cls)
    elif isinstance(other, (spe.Immediate, int)):
      return self.expr_cls(ppc.addi, *(self, other))
    raise Exception('__add__ not implemented for %s and %s' % (type(self), type(other)))    
  add = staticmethod(__add__)
  
  def __div__(self, other):
    if isinstance(other, SignedWordType):
      return self.expr_cls(ppc.divwux, *(self, other))
    raise NotImplemented
  div = staticmethod(__div__)

class SignedWordType(BitType):

  def __add__(self, other):
    if isinstance(other, SignedWordType):
      return ppc.addx.ex(self, other, type_cls = self.var_cls)
    elif isinstance(other, (spe.Immediate, int)):
      return self.expr_cls(ppc.addi, *(self, other))
    raise Exception('__add__ not implemented for %s and %s' % (type(self), type(other)))    
  add = staticmethod(__add__)
  
  def __div__(self, other):
    if isinstance(other, SignedWordType):
      return self.expr_cls(ppc.divwx, *(self, other))
    raise Exception('__div__ not implemented for %s and %s' % (type(self), type(other)))      
  div = staticmethod(__div__)

  def __mul__(self, other):
    if isinstance(other, SignedWordType):
      return self.expr_cls(ppc.mullwx, *(self, other))
    elif isinstance(other, (spe.Immediate, int)):
      return self.expr_cls(ppc.mulli, *(self, other))      
    raise Exception('__mul__ not implemented for %s and %s' % (type(self), type(other)))          
  div = staticmethod(__div__)

  def __neg__(self):
    return ppc.negx(self, type_cls = self.var_cls)

  def __sub__(self, other):
    if isinstance(other, SignedWordType):
      return self.expr_cls(ppc.subfx, other, self) # swap a and b
    raise Exception('__add__ not implemented for %s and %s' % (type(self), type(other)))    
  sub = staticmethod(__sub__)

  
# ------------------------------------------------------------
# Floating Point Register Types
# ------------------------------------------------------------

class SingleFloatType(PPCType):
  register_type_id = 'fp'
  literal_types = (float,)

  def __abs__(self):
    return ppc.fabsx.ex(self, type_cls = self.var_cls)
  abs = staticmethod(__abs__)
  
  def __add__(self, other):
    if isinstance(other, SingleFloatType):
      return ppc.faddsx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__add__ not implemented for %s and %s' % (type(self), type(other)))        
  add = staticmethod(__add__)
  
  def __div__(self, other):
    if isinstance(other, SingleFloatType):
      return ppc.fdivsx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__div__ not implemented for %s and %s' % (type(self), type(other)))    
  div = staticmethod(__div__)

  def __mul__(self, other):
    if isinstance(other, SingleFloatType):
      return ppc.fmulsx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__mul__ not implemented for %s and %s' % (type(self), type(other)))
  mul = staticmethod(__mul__)

  def __neg__(self):
    return ppc.fnegx.ex(self, type_cls = self.var_cls)
  neg = staticmethod(__neg__)

  def __sub__(self, other):
    if isinstance(other, SingleFloatType):
      return ppc.fsubsx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__sub__ not implemented for %s and %s' % (type(self), type(other)))
  sub = staticmethod(__sub__)

  def _set_literal_value(self, value):
    storage = array.array('f', (float(self.value),))
    self.code.add_storage(storage)
    
    r_storage = self.code.acquire_register()
    addr = Bits(storage.buffer_info()[0], reg = r_storage)
    self.code.add(ppc.lfs(self.reg, addr.reg, 0))
    self.code.release_register(r_storage)

    return

class DoubleFloatType(PPCType):
  register_type_id = 'fp'
  literal_types = (float,)

  def __abs__(self):
    return ppc.fabsx.ex(self, type_cls = self.var_cls)
  abs = staticmethod(__abs__)
  
  def __add__(self, other):
    if isinstance(other, DoubleFloatType):
      return ppc.faddx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__add__ not implemented for %s and %s' % (type(self), type(other)))
  add = staticmethod(__add__)
  
  def __div__(self, other):
    if isinstance(other, DoubleFloatType):
      return ppc.fdivx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__div__ not implemented for %s and %s' % (type(self), type(other)))
  div = staticmethod(__div__)

  def __mul__(self, other):
    if isinstance(other, DoubleFloatType):
      return ppc.fmulx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__mul__ not implemented for %s and %s' % (type(self), type(other)))
  mul = staticmethod(__mul__)

  def __neg__(self):
    return ppc.fnegx.ex(self, type_cls = self.var_cls)
  neg = staticmethod(__neg__)
    
  def __sub__(self, other):
    if isinstance(other, DoubleFloatType):
      return ppc.fsubx.ex(self, other, type_cls = self.var_cls)
    raise Exception('__sub__ not implemented for %s and %s' % (type(self), type(other)))
  sub = staticmethod(__sub__)
    
  def _set_literal_value(self, value):
    storage = array.array('d', (float(self.value),))
    self.code.add_storage(storage)

    r_storage = self.code.acquire_register()
    addr = Bits(storage.buffer_info()[0], reg = r_storage)
    self.code.add(ppc.lfd(self.reg, addr.reg, 0))
    self.code.release_register(r_storage)

    return


# ------------------------------
# Floating Point Free Functions
# ------------------------------

class _float_function(object):
  """
  Callable object that performs basic type checking and dispatch for
  floating point operations.
  """

  def __init__(self, name, single_func, double_func):
    self.name = name
    self.single_func = single_func
    self.double_func = double_func
    return

  def __call__(self, *operands, **koperands):
    a = operands[0]
    for op in operands[1:]:
      if op.var_cls != a.var_cls:
        raise Exception('Types for all operands must be the same')
      
    if isinstance(a, SingleFloatType):
      return self.single_func.ex(*operands, **{'type_cls': SingleFloat})
    elif isinstance(a, DoubleFloatType):
      return self.double_func.ex(*operands, **{'type_cls': DoubleFloat})    

    raise Exception(self.name + ' is not implemeneted for ' + str(type(a)))

    
fmadd = _float_function('fmadd', ppc.fmaddsx, ppc.fmaddx)
fmsub = _float_function('fmsub', ppc.fmsubsx, ppc.fmsubx)
fnmadd = _float_function('fnmadd', ppc.fnmaddsx, ppc.fnmaddx)
fnmsub = _float_function('fnmsub', ppc.fnmsubsx, ppc.fnmsubx)
fsqrt = _float_function('fsqrt', ppc.fsqrtsx, ppc.fsqrtx)

# ------------------------------------------------------------
# User Types
# ------------------------------------------------------------

# Type classes are mixed-in with Variables and Expressions to form the
# final user types.  

def make_user_type(name, type_cls, g = None):
  """
  Create a Variable class and an Expression class for a type class.

  This is equivalent to creating two classes and updating the type
  class (except that the Expression class is not added to the global 
  namespace):

    class [name](spe.Variable, type_cls):
      type_cls = type_cls
    class [name]Ex(spe.Expression, type_cls):
      type_cls = type_cls    
    type_class.var_cls = [name]
    type_class.expr_cls = [name]Ex

  type_cls is added to help determine type precedence among Variables
  and Expressions.

  (note: there's probably a better way to model these hierarchies that
   avoids the type_cls, var_cls, expr_cls references.  But, this works
   and keeping explicit references avoids tricky introspection
   operations) 
  """

  # Create the sublasses of Varaible and Expression
  var_cls = type(name, (spe.Variable, type_cls), {'type_cls': type_cls})
  expr_cls = type(name + 'Ex', (spe.Expression, type_cls), {'type_cls': type_cls})

  # Update the type class with references to the variable and
  # expression classes 
  type_cls.var_cls = var_cls
  type_cls.expr_cls = expr_cls

  # Add the Variable class to the global namespace
  if g is None: g = globals()
  g[name] = var_cls

  return


_user_types = ( # name, type class
  ('Bits', BitType),
  ('UnsignedWord', UnsignedWordType),
  ('SignedWord', SignedWordType),
  ('SingleFloat', SingleFloatType),
  ('DoubleFloat', DoubleFloatType)
  )

for t in _user_types:
  util.make_user_type(*(t + (globals(),)))


# ------------------------------------------------------------
# Unit Tests
# ------------------------------------------------------------

def SimpleTest():
  """
  Just make sure things are working...
  """
  from corepy.arch.ppc.platform import Processor, InstructionStream

  code = InstructionStream()
  proc = Processor()

  # Without active code
  a = SignedWord(11, code)
  b = SignedWord(31, reg = code.acquire_register())
  c = SignedWord(reg = code.gp_return)

  byte_mask = Bits(0xFF, code)
  code.add(ppc.addi(code.gp_return, 0, 31))

  # c.v = a + SignedWord.cast(b & byte_mask) + 12
  c.v = a + (byte_mask & b) + 12

  if True:
    r = proc.execute(code)
    assert(r == (42 + 12))
  
  # With active code
  code.reset()

  ppc.set_active_code(code)
  
  a = SignedWord(11)
  b = SignedWord(31)
  c = SignedWord(reg = code.gp_return)

  byte_mask = Bits(0xFF)

  c.v = a + (b & byte_mask)

  ppc.set_active_code(None)
  r = proc.execute(code)
  # code.print_code()
  assert(r == 42)
  return


def TestBits():
  from corepy.arch.ppc.platform import Processor, InstructionStream

  code = InstructionStream()
  proc = Processor()

  ppc.set_active_code(code)
  
  b = Bits(0xB0)
  e = Bits(0xE0000)
  a = Bits(0xCA)
  f = Bits(0x5)
  x = Bits(0, reg = code.gp_return)
  
  mask = Bits(0xF)
  byte = Bits(8) # 8 bits
  halfbyte = Bits(4) 

  f.v = (a & mask) ^ f
  x.v = (b << byte) | (e >> byte) | ((a & mask) << halfbyte) | (f | mask)

  r = proc.execute(code)
  assert(r == 0xBEAF)
  return
  
def TestFloatingPoint(float_type):
  from corepy.arch.ppc.platform import Processor, InstructionStream
  
  code = InstructionStream()
  proc = Processor()

  ppc.set_active_code(code)

  x = float_type(1.0)
  y = float_type(2.0)
  z = float_type(3.0)
  a = float_type(reg = code.fp_return)

  a.v = (x + y) / y

  a.v = fmadd(a, y, z + z) + fnmadd(a, y, z + z) + fmsub(x, y, z) + fnmsub(x, y, z) 
  x.v = -x
  a.v = a + x - x
  r = proc.execute(code, mode='fp')
  assert(r == 0.0)

  return

if __name__=='__main__':
  from corepy.arch.ppc.lib.util import RunTest
  RunTest(SimpleTest)
  RunTest(TestFloatingPoint, SingleFloat)
  RunTest(TestFloatingPoint, DoubleFloat)
  RunTest(TestBits)
