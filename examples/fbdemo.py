# Framebuffer Demo

import corepy.arch.spu.platform as synspu
import corepy.arch.spu.isa as spu
import corepy.arch.spu.types.spu_types as var
import corepy.arch.spu.lib.dma as dma
import corepy.arch.spu.lib.iterators as spuiter


class FBDraw:
  def __init__(self):
    self.buffers = None
    self.stride  = None
    return

  def set_buffers(self, fb0, fb1):
    self.buffers = (fb0, fb1)
    return

  def set_stride(self, s): self.stride = s * 4
  
  def synthesize(self, code):
    old_code = spu.get_active_code()
    spu.set_active_code(code)

    if self.buffers is None: raise Exception('Please set buffers')
    if self.stride is None: raise Exception('Please set stride')
    
    # Draw a square
    color  = var.SignedWord(0x0F0F0FFF)
    fb0    = var.Word(self.buffers[0])
    fb1    = var.Word(self.buffers[1])
    stride = var.Word(self.stride)
    addr   = var.Word(0)
    
    # Draw one line
    line_pixels = 256
    for i in spuiter.syn_iter(code, line_pixels*4, step = 16):
      spu.stqx(color, addr, i)

    # Transfer the line to the frame buffer
    md_fb = spuiter.memory_desc('I', size = line_pixels)
    md_fb.set_addr_reg(addr.reg)
    
    addr.v = fb0

    for i in spuiter.syn_iter(code, 128):
      md_fb.put(code, 0)
      addr.v = addr + stride
    
    spu.set_active_code(old_code)
    return


cell_fb = synspu.cell_fb

def fb_draw():
  code0 = synspu.InstructionStream()
  code1 = synspu.InstructionStream()  
  proc = synspu.Processor()

  fb = cell_fb.framebuffer()
  cell_fb.fb_open(fb)

  draw0 = FBDraw()
  draw0.set_buffers(cell_fb.fb_addr(fb, 0), cell_fb.fb_addr(fb, 1))
  draw0.set_stride(fb.stride)

  draw0.synthesize(code0)

  draw1 = FBDraw()
  draw1.set_buffers(cell_fb.fb_addr(fb, 1), cell_fb.fb_addr(fb, 0))cell_fb.fb_addr(fb, 0))
  draw1.set_stride(fb.stride)

  draw1.synthesize(code1)

  while True:

    # cell_fb.fb_clear(fb, 0)
    proc.execute(code0)
    cell_fb.fb_wait_vsync(fb)
    cell_fb.fb_flip(fb, 0)

    # cell_fb.fb_clear(fb, 1)
    proc.execute(code1)
    cell_fb.fb_wait_vsync(fb)
    cell_fb.fb_flip(fb, 1)
    

  cell_fb.fb_close(fb)
  return

if __name__=='__main__':
  fb_draw()