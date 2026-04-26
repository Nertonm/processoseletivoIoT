import utime

from config import INTERVALO_LOOP_MS, MSG_BOOT

print(MSG_BOOT)

from hardware import HardwareVaultSign
from input_handler import SerialInputHandler
from state_machine import VaultSignStateMachine


def main():
	hardware = HardwareVaultSign()
	entrada = SerialInputHandler()
	maquina = VaultSignStateMachine(hardware, entrada)
	maquina.iniciar()
	maquina.registrar_inicio_loop()

	while True:
		agora = utime.ticks_ms()
		char = entrada.ler_char()
		maquina.processar_entrada(char, agora)
		maquina.verificar_botao(agora)
		maquina.atualizar(agora)
		utime.sleep_ms(INTERVALO_LOOP_MS)


if __name__ == "__main__":
	main()
