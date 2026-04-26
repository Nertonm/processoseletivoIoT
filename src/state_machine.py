import gc
import utime

from config import (
	ARREDONDAMENTO_SEGUNDO_MS,
	BOTAO_PRESSIONADO,
	BOTAO_SOLTO,
	COMANDOS_DEBUG_HABILITADOS,
	DEBUG_ATIVO_INICIAL,
	DEBUG_CMD_CLEAR,
	DEBUG_CMD_HELP,
	DEBUG_CMD_STATUS,
	DEBUG_CMD_STATUS_ALT,
	DEBUG_CMD_TOGGLE,
	DEBUG_CMD_UNLOCK,
	DEBOUNCE_BOTAO_MS,
	DURACAO_ACESSO_OK_MS,
	DURACAO_BLOQUEIO_MS,
	ENTRADA_COMPLETA,
	ENTRADA_INVALIDA,
	ENTRADA_OVERFLOW,
	ENTRADA_PARCIAL,
	ESTADO_ACESSO_OK,
	ESTADO_AGUARDANDO,
	ESTADO_BLOQUEADO,
	ESTADO_DIGITANDO,
	ESTADO_LOCKOUT,
	ESTADO_VALIDANDO,
	INTERVALO_LCD_LOCKOUT_MS,
	INTERVALO_LOG_LOCKOUT_MS,
	INTERVALO_PISCA_MS,
	MAX_TENTATIVAS,
	MILLIS_POR_SEGUNDO,
	PIN_CADASTRADO,
	TEMPO_LOCKOUT,
)
from logger import debug, info, mostrar_ajuda, warn


class VaultSignStateMachine:
	def __init__(self, hardware, entrada):
		self.hardware = hardware
		self.entrada = entrada
		self.estado_atual = ESTADO_AGUARDANDO
		self.tentativas = 0
		self.marco_estado_ms = utime.ticks_ms()
		self.inicio_lockout_ms = None
		self.ultimo_pisca_ms = self.marco_estado_ms
		self.ultimo_log_lockout_ms = self.marco_estado_ms
		self.ultimo_lcd_lockout_ms = self.marco_estado_ms
		self.led_amarelo_ligado = False
		self.botao_estado_anterior = BOTAO_SOLTO
		self.ultimo_botao_ms = self.marco_estado_ms
		self.botao_reset_estado_anterior = BOTAO_SOLTO
		self.ultimo_botao_reset_ms = self.marco_estado_ms
		self.debug_ativo = DEBUG_ATIVO_INICIAL

	def iniciar(self):
		self.hardware.desligar_sinalizadores()
		if COMANDOS_DEBUG_HABILITADOS:
			mostrar_ajuda()
		self.entrar_aguardando()

	def registrar_inicio_loop(self):
		self._log_debug("Loop principal iniciado")

	def processar_entrada(self, dado, agora_ms):
		# Mantido para evolucao de timeout de entrada.
		_ = agora_ms
		if dado is not None:
			self.processar_entrada_serial(dado)

	def verificar_botao(self, agora_ms):
		if self.verificar_botao_reset_pressionado(agora_ms):
			warn("Reset manual acionado")
			self.hardware.reiniciar()
			return

		if self.estado_atual == ESTADO_AGUARDANDO and self.verificar_botao_pressionado(agora_ms):
			self.hardware.executar_autoteste()
			self.entrar_aguardando()

	def atualizar(self, agora_ms):
		self.tratar_estado_atual(agora_ms)

	def entrar_aguardando(self):
		self._registrar_estado(ESTADO_AGUARDANDO)
		self.ultimo_pisca_ms = self.marco_estado_ms
		self.led_amarelo_ligado = False
		self.hardware.fechar_servo()
		self.hardware.mostrar_aguardando()

	def entrar_digitando(self):
		self._registrar_estado(ESTADO_DIGITANDO)
		self.hardware.mostrar_digitando(self.entrada.tamanho_pin())

	def entrar_validando(self):
		self._registrar_estado(ESTADO_VALIDANDO)
		self.hardware.mostrar_validando()

	def entrar_acesso_ok(self):
		self._registrar_estado(ESTADO_ACESSO_OK)
		self.hardware.abrir_servo()
		self.hardware.mostrar_acesso_ok()
		gc.collect()

	def entrar_bloqueado(self):
		self._registrar_estado(ESTADO_BLOQUEADO)
		self.hardware.mostrar_bloqueado(self.tentativas, MAX_TENTATIVAS)

	def entrar_lockout(self):
		self._registrar_estado(ESTADO_LOCKOUT)
		self.inicio_lockout_ms = self.marco_estado_ms
		self.ultimo_log_lockout_ms = self.marco_estado_ms
		self.ultimo_lcd_lockout_ms = self.marco_estado_ms
		self.hardware.mostrar_lockout(TEMPO_LOCKOUT)
		gc.collect()

	def processar_entrada_serial(self, dado):
		if self.entrada.eh_ignorado(dado):
			return

		if self._executar_comando_debug(dado):
			return

		if self.estado_atual == ESTADO_LOCKOUT:
			self._log_debug("Entrada ignorada durante LOCKOUT")
			return

		resultado = self.entrada.adicionar_digito(dado)
		if resultado == ENTRADA_INVALIDA:
			self._log_debug("Caractere ignorado: {}".format(repr(dado)))
			return
		if resultado == ENTRADA_OVERFLOW:
			self._log_debug("Buffer cheio; digito extra ignorado")
			return
		if resultado == ENTRADA_PARCIAL:
			self._log_debug("Digito recebido")
			if self.estado_atual != ESTADO_DIGITANDO:
				self.entrar_digitando()
			else:
				self.hardware.mostrar_digitando(self.entrada.tamanho_pin())
			return
		if resultado == ENTRADA_COMPLETA:
			self._log_debug("Digito recebido")
			self._log_debug("Buffer completo. Iniciando validacao")
			self.entrar_validando()

	def verificar_botao_pressionado(self, agora_ms):
		leitura = self.hardware.ler_botao_teste()
		if leitura == self.botao_estado_anterior:
			return False
		if utime.ticks_diff(agora_ms, self.ultimo_botao_ms) < DEBOUNCE_BOTAO_MS:
			return False

		self.ultimo_botao_ms = agora_ms
		pressionado = leitura == BOTAO_PRESSIONADO and self.botao_estado_anterior == BOTAO_SOLTO
		self.botao_estado_anterior = leitura
		return pressionado

	def verificar_botao_reset_pressionado(self, agora_ms):
		leitura = self.hardware.ler_botao_reset()
		if leitura == self.botao_reset_estado_anterior:
			return False
		if utime.ticks_diff(agora_ms, self.ultimo_botao_reset_ms) < DEBOUNCE_BOTAO_MS:
			return False

		self.ultimo_botao_reset_ms = agora_ms
		pressionado = leitura == BOTAO_PRESSIONADO and self.botao_reset_estado_anterior == BOTAO_SOLTO
		self.botao_reset_estado_anterior = leitura
		return pressionado

	def tratar_estado_atual(self, agora_ms):
		if self.estado_atual == ESTADO_AGUARDANDO:
			self.tratar_aguardando(agora_ms)
		elif self.estado_atual == ESTADO_DIGITANDO:
			self.tratar_digitando(agora_ms)
		elif self.estado_atual == ESTADO_VALIDANDO:
			self.tratar_validando()
		elif self.estado_atual == ESTADO_ACESSO_OK:
			self.tratar_acesso_ok(agora_ms)
		elif self.estado_atual == ESTADO_BLOQUEADO:
			self.tratar_bloqueado(agora_ms)
		elif self.estado_atual == ESTADO_LOCKOUT:
			self.tratar_lockout(agora_ms)

	def tratar_aguardando(self, agora_ms):
		if utime.ticks_diff(agora_ms, self.ultimo_pisca_ms) >= INTERVALO_PISCA_MS:
			self.led_amarelo_ligado = not self.led_amarelo_ligado
			self.ultimo_pisca_ms = agora_ms
		self.hardware.sinalizar_aguardando(self.led_amarelo_ligado)

	def tratar_digitando(self, _agora_ms):
		self.hardware.sinalizar_digitando()

	def tratar_validando(self):
		if self.entrada.valor_pin() == PIN_CADASTRADO:
			self.tentativas = 0
			self.entrada.limpar_buffer()
			info("PIN valido. Acesso liberado.")
			self.entrar_acesso_ok()
			return

		self.tentativas += 1
		self.entrada.limpar_buffer()
		warn("PIN invalido. Tentativa {}/{}.".format(self.tentativas, MAX_TENTATIVAS))

		if self.tentativas >= MAX_TENTATIVAS:
			warn("LOCKOUT por {}s.".format(TEMPO_LOCKOUT))
			self.entrar_lockout()
		else:
			self.entrar_bloqueado()

	def tratar_acesso_ok(self, agora_ms):
		self.hardware.sinalizar_acesso_ok()
		if utime.ticks_diff(agora_ms, self.marco_estado_ms) >= DURACAO_ACESSO_OK_MS:
			self.entrar_aguardando()

	def tratar_bloqueado(self, agora_ms):
		self.hardware.sinalizar_bloqueado()
		if utime.ticks_diff(agora_ms, self.marco_estado_ms) >= DURACAO_BLOQUEIO_MS:
			self.hardware.desligar_sinalizadores()
			self.entrar_aguardando()

	def tratar_lockout(self, agora_ms):
		self.hardware.sinalizar_bloqueado()
		if self.inicio_lockout_ms is None:
			return

		duracao_ms = TEMPO_LOCKOUT * MILLIS_POR_SEGUNDO
		decorrido_ms = utime.ticks_diff(agora_ms, self.inicio_lockout_ms)
		restante_ms = duracao_ms - decorrido_ms
		if restante_ms < 0:
			restante_ms = 0
		restante_s = (restante_ms + ARREDONDAMENTO_SEGUNDO_MS) // MILLIS_POR_SEGUNDO

		if self.debug_ativo and utime.ticks_diff(agora_ms, self.ultimo_log_lockout_ms) >= INTERVALO_LOG_LOCKOUT_MS:
			self._log_debug("LOCKOUT restante: {}s".format(restante_s))
			self.ultimo_log_lockout_ms = agora_ms

		if utime.ticks_diff(agora_ms, self.ultimo_lcd_lockout_ms) >= INTERVALO_LCD_LOCKOUT_MS:
			self.hardware.mostrar_lockout(restante_s)
			self.ultimo_lcd_lockout_ms = agora_ms

		if decorrido_ms >= duracao_ms:
			self.entrada.limpar_buffer()
			self.tentativas = 0
			self.hardware.desligar_sinalizadores()
			info("Fim do lockout. Sistema rearmado.")
			self.entrar_aguardando()

	def _registrar_estado(self, novo_estado):
		estado_anterior = self.estado_atual
		self.estado_atual = novo_estado
		self.marco_estado_ms = utime.ticks_ms()
		if estado_anterior != novo_estado:
			self._log_debug("Transicao {} -> {}".format(estado_anterior, novo_estado))

	def _executar_comando_debug(self, dado):
		if not COMANDOS_DEBUG_HABILITADOS:
			return False

		cmd = dado.lower()
		if cmd == DEBUG_CMD_STATUS or cmd == DEBUG_CMD_STATUS_ALT:
			self._log_debug("STATUS solicitado")
			return True
		if cmd == DEBUG_CMD_TOGGLE:
			self.debug_ativo = not self.debug_ativo
			info("DEBUG_ATIVO={}".format(self.debug_ativo))
			return True
		if cmd == DEBUG_CMD_CLEAR:
			self.entrada.limpar_buffer()
			self.entrar_aguardando()
			self._log_debug("Buffer limpo manualmente")
			return True
		if cmd == DEBUG_CMD_UNLOCK:
			if self.debug_ativo:
				self._executar_unlock_debug()
			else:
				warn("unlock ignorado: debug inativo")
			return True
		if cmd == DEBUG_CMD_HELP:
			mostrar_ajuda()
			return True
		return False

	def _executar_unlock_debug(self):
		self.entrada.limpar_buffer()
		self.tentativas = 0
		self.inicio_lockout_ms = None
		self.hardware.desligar_sinalizadores()
		self.entrar_aguardando()
		self._log_debug("Unlock manual aplicado")

	def _log_debug(self, mensagem):
		debug(
			self.debug_ativo,
			mensagem,
			utime.ticks_ms(),
			self.estado_atual,
			self.tentativas,
			MAX_TENTATIVAS,
			self.entrada.valor_pin(),
		)
