import utime

_BL = 0x08
_EN = 0x04
_RS = 0x01


class LCD1602:
	def __init__(self, i2c, addr=0x27):
		self._i2c = i2c
		self._addr = addr
		utime.sleep_ms(50)
		self._send_nibble(0x30); utime.sleep_ms(5)
		self._send_nibble(0x30); utime.sleep_us(200)
		self._send_nibble(0x30); utime.sleep_us(200)
		self._send_nibble(0x20); utime.sleep_us(200)
		self._cmd(0x28)
		self._cmd(0x08)
		self._cmd(0x01); utime.sleep_ms(2)
		self._cmd(0x06)
		self._cmd(0x0C)

	def _write(self, value):
		self._i2c.writeto(self._addr, bytes([value | _BL]))

	def _send_nibble(self, nibble):
		self._write(nibble)
		self._write(nibble | _EN)
		utime.sleep_us(2)
		self._write(nibble & ~_EN)
		utime.sleep_us(50)

	def _send(self, value, mode):
		high = (value & 0xF0) | mode
		low = ((value << 4) & 0xF0) | mode
		self._send_nibble(high)
		self._send_nibble(low)

	def _cmd(self, value):
		self._send(value, 0)

	def _data(self, value):
		self._send(value, _RS)

	def clear(self):
		self._cmd(0x01)
		utime.sleep_ms(2)

	def cursor(self, col, row):
		offset = 0x40 if row else 0x00
		self._cmd(0x80 | (offset + col))

	def write(self, text):
		for ch in text:
			self._data(ord(ch))

	def show(self, linha0="", linha1=""):
		self.cursor(0, 0)
		self.write((linha0 + " " * 16)[:16])
		self.cursor(0, 1)
		self.write((linha1 + " " * 16)[:16])
