from machine import I2C, Pin

from config import (
	ACTION_WRITE,
	DEVICE_LCD,
	EMPTY_TEXT,
	LCD_ACESSO_OK,
	LCD_AGUARDE_FORMAT,
	LCD_AGUARDANDO,
	LCD_AUTOTESTE,
	LCD_BEM_VINDO,
	LCD_BLOQUEADO,
	LCD_DIGITE_PIN,
	LCD_I2C_ADDR,
	LCD_I2C_FREQ,
	LCD_I2C_ID,
	LCD_PIN_INVALIDO,
	LCD_SCL_PIN,
	LCD_SDA_PIN,
	LCD_TENTATIVAS_FORMAT,
	LCD_TITULO,
	LCD_VALIDANDO,
	PIN_MASK_CHAR,
	TEMPO_LOCKOUT,
)
from lcd1602 import LCD1602
from logger import erro_inicializacao, erro_operacao


class DisplayVaultSign:
	def __init__(self):
		self._lcd = None
		try:
			i2c = I2C(
				LCD_I2C_ID,
				sda=Pin(LCD_SDA_PIN),
				scl=Pin(LCD_SCL_PIN),
				freq=LCD_I2C_FREQ,
			)
			self._lcd = LCD1602(i2c, addr=LCD_I2C_ADDR)
		except OSError as exc:
			erro_inicializacao(DEVICE_LCD, exc)

	def _mostrar(self, linha0, linha1):
		if self._lcd is None:
			return
		try:
			self._lcd.show(linha0, linha1)
		except OSError as exc:
			erro_operacao(DEVICE_LCD, ACTION_WRITE, exc)

	def mostrar_aguardando(self):
		self._mostrar(LCD_TITULO, LCD_AGUARDANDO)

	def mostrar_digitando(self, qtd_digitos):
		qtd_digitos = int(qtd_digitos)
		self._mostrar(LCD_DIGITE_PIN, PIN_MASK_CHAR * qtd_digitos)

	def mostrar_validando(self):
		self._mostrar(LCD_VALIDANDO, EMPTY_TEXT)

	def mostrar_acesso_ok(self):
		self._mostrar(LCD_ACESSO_OK, LCD_BEM_VINDO)

	def mostrar_bloqueado(self, tentativas, max_tentativas):
		self._mostrar(LCD_PIN_INVALIDO, LCD_TENTATIVAS_FORMAT.format(tentativas, max_tentativas))

	def mostrar_lockout(self, restante_s=TEMPO_LOCKOUT):
		self._mostrar(LCD_BLOQUEADO, LCD_AGUARDE_FORMAT.format(restante_s))

	def mostrar_autoteste(self, rotulo):
		self._mostrar(LCD_AUTOTESTE, rotulo)
