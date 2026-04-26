from config import (
	MASCARAR_PIN_NO_LOG,
	PIN_LOG_EMPTY,
	PIN_MASK_CHAR,
)

LOG_PREFIX_INFO = "[INFO]"
LOG_PREFIX_WARN = "[WARN]"
LOG_PREFIX_ERROR = "[ERROR]"
LOG_PREFIX_DEBUG = "[DBG]"


def mascarar_pin(pin_texto):
	if not pin_texto:
		return PIN_LOG_EMPTY
	if MASCARAR_PIN_NO_LOG:
		return PIN_MASK_CHAR * len(pin_texto)
	return pin_texto


def info(mensagem):
	print("{} {}".format(LOG_PREFIX_INFO, mensagem))


def warn(mensagem):
	print("{} {}".format(LOG_PREFIX_WARN, mensagem))


def error(mensagem):
	print("{} {}".format(LOG_PREFIX_ERROR, mensagem))


def debug(ativo, mensagem, agora_ms, estado, tentativas, max_tentativas, pin_texto):
	if not ativo:
		return
	print(
		"{} t={}ms estado={} tentativas={}/{} pin={} {}".format(
			LOG_PREFIX_DEBUG,
			agora_ms,
			estado,
			tentativas,
			max_tentativas,
			mascarar_pin(pin_texto),
			mensagem,
		)
	)


def erro_inicializacao(nome, excecao):
	error("Falha ao inicializar {}: {}".format(nome, excecao))


def erro_operacao(nome, acao, excecao):
	error("Falha em {}.{}: {}".format(nome, acao, excecao))


def mostrar_ajuda():
	info("Comandos serial de debug:")
	info("? ou s  -> status atual")
	info("d       -> toggle de logs de debug")
	info("c       -> limpa buffer e volta para AGUARDANDO")
	info("u       -> unlock: limpa lockout/tentativas")
	info("h       -> ajuda")
