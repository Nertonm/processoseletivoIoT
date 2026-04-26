import utime
from machine import ADC, Pin, PWM

from config import (
	ACTION_CLOSE,
	ACTION_OFF,
	ACTION_ON,
	ACTION_OPEN,
	ACTION_READ,
	ACTION_TOGGLE,
	ADC_ATENUACAO,
	AUTOTESTE_ATUADOR_MS,
	AUTOTESTE_BUZZER_MS,
	AUTOTESTE_LED_MS,
	AUTOTESTE_OK_MS,
	AUTOTESTE_SERVO_MS,
	BOTAO_RESET_PIN,
	BOTAO_SOLTO,
	BOTAO_TESTE_PIN,
	BUZZER_DUTY_MAX,
	BUZZER_FREQ_HZ,
	BUZZER_PIN,
	ADC_VALOR_MAX,
	ATUADOR_FECHADURA_PIN,
	DEVICE_ATUADOR_FECHADURA,
	DEVICE_BOTAO_TESTE,
	DEVICE_BOTAO_RESET,
	DEVICE_BUZZER,
	DEVICE_LED_AMARELO,
	DEVICE_LED_VERDE,
	DEVICE_LED_VERMELHO,
	DEVICE_POT_VOLUME,
	DEVICE_SERVO,
	LCD_AUTOTESTE_OK,
	LCD_BUZZER_POT,
	LCD_FECHADURA_LOCK,
	LCD_LED_AMARELO,
	LCD_LED_VERDE,
	LCD_LED_VERMELHO,
	LCD_SERVO,
	LED_AMARELO_PIN,
	LED_VERDE_PIN,
	LED_VERMELHO_PIN,
	POT_VOLUME_PIN,
	SERVO_DUTY_ABERTO,
	SERVO_DUTY_FECHADO,
	SERVO_FREQ_HZ,
	SERVO_PIN,
)
from display import DisplayVaultSign
from logger import erro_inicializacao, erro_operacao, info


class SaidaDigital:
	def __init__(self, nome, pin):
		self._nome = nome
		self._pin = None
		try:
			self._pin = Pin(pin, Pin.OUT)
			self.desligar()
		except OSError as exc:
			erro_inicializacao(nome, exc)

	def ligar(self):
		if self._pin is None:
			return
		try:
			self._pin.on()
		except OSError as exc:
			erro_operacao(self._nome, ACTION_ON, exc)

	def desligar(self):
		if self._pin is None:
			return
		try:
			self._pin.off()
		except OSError as exc:
			erro_operacao(self._nome, ACTION_OFF, exc)

	def alternar(self):
		if self._pin is None:
			return
		try:
			if self._pin.value():
				self._pin.off()
			else:
				self._pin.on()
		except OSError as exc:
			erro_operacao(self._nome, ACTION_TOGGLE, exc)

class Buzzer:
	def __init__(self, nome, pin):
		self._nome = nome
		self._pwm = None
		try:
			self._pwm = PWM(Pin(pin), freq=BUZZER_FREQ_HZ)
			self.desligar()
		except OSError as exc:
			erro_inicializacao(nome, exc)

	def ligar_por_volume(self, potenciometro):
		if self._pwm is None:
			return
		try:
			leitura = potenciometro.ler()
			duty = (leitura * BUZZER_DUTY_MAX) // ADC_VALOR_MAX
			self._pwm.duty_u16(duty)
		except OSError as exc:
			erro_operacao(self._nome, ACTION_ON, exc)

	def bip_erro(self, potenciometro):
		self.ligar_por_volume(potenciometro)

	def desligar(self):
		if self._pwm is None:
			return
		try:
			self._pwm.duty_u16(0)
		except OSError as exc:
			erro_operacao(self._nome, ACTION_OFF, exc)


class ServoFechadura:
	def __init__(self, nome, pin):
		self._nome = nome
		self._pwm = None
		try:
			self._pwm = PWM(Pin(pin), freq=SERVO_FREQ_HZ)
			self.fechar()
		except OSError as exc:
			erro_inicializacao(nome, exc)

	def abrir(self):
		if self._pwm is None:
			return
		try:
			self._pwm.duty_u16(SERVO_DUTY_ABERTO)
		except OSError as exc:
			erro_operacao(self._nome, ACTION_OPEN, exc)

	def fechar(self):
		if self._pwm is None:
			return
		try:
			self._pwm.duty_u16(SERVO_DUTY_FECHADO)
		except OSError as exc:
			erro_operacao(self._nome, ACTION_CLOSE, exc)


class BotaoEntrada:
	def __init__(self, nome, pin):
		self._nome = nome
		self._pin = None
		try:
			self._pin = Pin(pin, Pin.IN)
		except OSError as exc:
			erro_inicializacao(nome, exc)

	def valor(self):
		if self._pin is None:
			return BOTAO_SOLTO
		try:
			return self._pin.value()
		except OSError as exc:
			erro_operacao(self._nome, ACTION_READ, exc)
			return BOTAO_SOLTO


class Potenciometro:
	def __init__(self, nome, pin):
		self._nome = nome
		self._adc = None
		try:
			self._adc = ADC(Pin(pin))
			self._adc.atten(ADC_ATENUACAO)
		except OSError as exc:
			erro_inicializacao(nome, exc)

	def ler(self):
		if self._adc is None:
			return 0
		try:
			return self._adc.read()
		except OSError as exc:
			erro_operacao(self._nome, ACTION_READ, exc)
			return 0


class HardwareVaultSign:
	def __init__(self):
		self.display = DisplayVaultSign()
		self.led_verde = SaidaDigital(DEVICE_LED_VERDE, LED_VERDE_PIN)
		self.led_vermelho = SaidaDigital(DEVICE_LED_VERMELHO, LED_VERMELHO_PIN)
		self.led_amarelo = SaidaDigital(DEVICE_LED_AMARELO, LED_AMARELO_PIN)
		self.atuador_fechadura = SaidaDigital(
			DEVICE_ATUADOR_FECHADURA,
			ATUADOR_FECHADURA_PIN,
		)
		self.buzzer = Buzzer(DEVICE_BUZZER, BUZZER_PIN)
		self.servo = ServoFechadura(DEVICE_SERVO, SERVO_PIN)
		self.botao_teste = BotaoEntrada(DEVICE_BOTAO_TESTE, BOTAO_TESTE_PIN)
		self.botao_reset = BotaoEntrada(DEVICE_BOTAO_RESET, BOTAO_RESET_PIN)
		self.pot_volume = Potenciometro(DEVICE_POT_VOLUME, POT_VOLUME_PIN)

	def desligar_sinalizadores(self):
		self.led_verde.desligar()
		self.led_vermelho.desligar()
		self.led_amarelo.desligar()
		self.atuador_fechadura.desligar()
		self.buzzer.desligar()
		self.servo.fechar()

	def abrir_servo(self):
		self.servo.abrir()

	def fechar_servo(self):
		self.servo.fechar()

	def ler_botao_teste(self):
		return self.botao_teste.valor()

	def ler_botao_reset(self):
		return self.botao_reset.valor()

	def mostrar_aguardando(self):
		self.display.mostrar_aguardando()

	def mostrar_digitando(self, tamanho_pin):
		self.display.mostrar_digitando(tamanho_pin)

	def mostrar_validando(self):
		self.display.mostrar_validando()

	def mostrar_acesso_ok(self):
		self.display.mostrar_acesso_ok()

	def mostrar_bloqueado(self, tentativas, max_tentativas):
		self.display.mostrar_bloqueado(tentativas, max_tentativas)

	def mostrar_lockout(self, restante_s):
		self.display.mostrar_lockout(restante_s)

	def mostrar_autoteste(self, rotulo):
		self.display.mostrar_autoteste(rotulo)

	def sinalizar_aguardando(self, led_amarelo_ligado):
		self.led_verde.desligar()
		self.led_vermelho.desligar()
		self.atuador_fechadura.desligar()
		self.buzzer.desligar()
		if led_amarelo_ligado:
			self.led_amarelo.ligar()
		else:
			self.led_amarelo.desligar()

	def sinalizar_digitando(self):
		self.led_verde.desligar()
		self.led_vermelho.desligar()
		self.atuador_fechadura.desligar()
		self.buzzer.desligar()
		self.led_amarelo.ligar()

	def sinalizar_acesso_ok(self):
		self.led_verde.ligar()
		self.led_vermelho.desligar()
		self.led_amarelo.desligar()
		self.atuador_fechadura.ligar()
		self.buzzer.desligar()

	def sinalizar_bloqueado(self):
		self.led_verde.desligar()
		self.led_vermelho.ligar()
		self.led_amarelo.desligar()
		self.atuador_fechadura.desligar()
		self.buzzer.bip_erro(self.pot_volume)

	def reiniciar(self):
		try:
			from machine import reset
			reset()
		except Exception as e:
			# Falha aqui deve ser registrada e o firmware segue vivo.
			erro_operacao("hardware", "reiniciar", e)

	# Auto-teste bloqueante: aceitável em simulação Wokwi.
	# Para uso em produção, converter para máquina de estados com ticks_ms.
	def executar_autoteste(self):
		info("Auto-teste iniciado")
		self.desligar_sinalizadores()

		for rotulo, led in (
			(LCD_LED_AMARELO, self.led_amarelo),
			(LCD_LED_VERMELHO, self.led_vermelho),
			(LCD_LED_VERDE, self.led_verde),
		):
			self.mostrar_autoteste(rotulo)
			led.ligar()
			utime.sleep_ms(AUTOTESTE_LED_MS)
			led.desligar()

		self.mostrar_autoteste(LCD_FECHADURA_LOCK)
		self.atuador_fechadura.ligar()
		utime.sleep_ms(AUTOTESTE_ATUADOR_MS)
		self.atuador_fechadura.desligar()

		self.mostrar_autoteste(LCD_SERVO)
		self.servo.abrir()
		utime.sleep_ms(AUTOTESTE_SERVO_MS)
		self.servo.fechar()

		self.mostrar_autoteste(LCD_BUZZER_POT)
		self.buzzer.ligar_por_volume(self.pot_volume)
		utime.sleep_ms(AUTOTESTE_BUZZER_MS)
		self.buzzer.desligar()

		self.mostrar_autoteste(LCD_AUTOTESTE_OK)
		utime.sleep_ms(AUTOTESTE_OK_MS)
		info("Auto-teste finalizado.")
