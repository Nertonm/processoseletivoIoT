import select
import sys

from config import (
	CARACTERES_IGNORADOS,
	EMPTY_TEXT,
	ENTRADA_COMPLETA,
	ENTRADA_IGNORADA,
	ENTRADA_INVALIDA,
	ENTRADA_OVERFLOW,
	ENTRADA_PARCIAL,
	STDIN_POLL_TIMEOUT_MS,
	TAMANHO_PIN,
)
from logger import error, warn


class SerialInputHandler:
	def __init__(self):
		self._buffer = EMPTY_TEXT
		try:
			self._poll = select.poll()
			self._poll.register(sys.stdin, select.POLLIN)
		except Exception as e:
			# Em alguns ambientes de teste, stdin nao suporta poll.
			error("poll indisponivel: {}".format(e))
			self._poll = None

	def ler_char(self, timeout_ms=STDIN_POLL_TIMEOUT_MS):
		if self._poll is None:
			return None
		if not self._poll.poll(timeout_ms):
			return None
		try:
			ch = sys.stdin.read(1)
			if not ch:
				return None
			return ch
		except Exception:
			# Falha de leitura nao deve derrubar o loop principal.
			warn("Erro lendo stdin")
			return None

	def limpar_buffer(self):
		self._buffer = EMPTY_TEXT

	def valor_pin(self):
		return self._buffer

	def tamanho_pin(self):
		return len(self._buffer)

	def eh_ignorado(self, dado):
		return dado in CARACTERES_IGNORADOS

	def eh_digito(self, dado):
		return "0" <= dado <= "9"

	def adicionar_digito(self, dado):
		if self.eh_ignorado(dado):
			return ENTRADA_IGNORADA
		if not self.eh_digito(dado):
			return ENTRADA_INVALIDA
		if len(self._buffer) >= TAMANHO_PIN:
			return ENTRADA_OVERFLOW

		self._buffer += dado
		if len(self._buffer) == TAMANHO_PIN:
			return ENTRADA_COMPLETA
		return ENTRADA_PARCIAL
