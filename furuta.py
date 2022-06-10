
import os
from time import time, sleep
from threading import Thread
from pathlib import Path
import binascii

from crc import CrcCalculator, Crc16
import numpy as np
import pigpio

from my_config import MyConfig
from motor import MyMotor



class Furuta:
    """Communication entre la Pi et le Furuta hardware."""

    def __init__(self, cf, numero, clavier):
        """self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)"""

        self.cf = cf  # l'objet MyConfig
        self.numero = numero
        self.clavier = clavier
        self.clavier_active = 1
        self.clavier_thread()

        self.config = cf.conf  # le dict de conf
        self.pi = pigpio.pi()

        # alpha = moteur, teta = balancier
        self.alpha, self.alpha_dot, self.teta, self.teta_dot = 0, 0, 0, 0

        PWM = int(self.config['moteur']['pwm'])
        left = int(self.config['moteur']['left'])
        right = int(self.config['moteur']['right'])
        freq_pwm = int(self.config['moteur']['freq_pwm'])
        self.range_pwm = int(self.config[self.numero]['range_pwm'])
        self.ratio_puissance_maxi = float(self.config[self.numero]['ratio_puissance_maxi'])
        self.length_maxi = float(self.config['moteur']['length_maxi'])
        # L'objet d'action sur le moteur
        self.motor = MyMotor(self.pi, PWM, left, right, freq_pwm, self.range_pwm)

        self.time_to_print = time()
        self.cycle = 0

        # SPI
        self.sensor0 = self.pi.spi_open(0, 100000, 2)
        self.crc_calculator = CrcCalculator(Crc16.CCITT, True)
        self.marker = int(self.config[self.numero]['marker'])
        self.timingCommand = int(self.config[self.numero]['timingcommand'])
        self.readCommand = int(self.config[self.numero]['readcommand'])
        self.redundancy = int(self.config[self.numero]['redundancy'])
        self.tempo_spi = float(self.config[self.numero]['tempo_spi'])

    def clavier_thread(self):
        c = Thread(target=self.clavier_loop, )
        c.start()

    def clavier_loop(self):
        while self.clavier_active:
            if self.clavier.a == 1:
                self.impulsion_moteur(50, 0.05, 'right')
                self.clavier.a = 0
            if self.clavier.z == 1:
                self.impulsion_moteur(50, 0.05, 'left')
                self.clavier.z = 0
            sleep(0.2)

    def computeCrc16(self, bufferArray, size):
        # Calc CRC16 for buffer and return one integer
        data = bytes(bufferArray[:size])
        #print("computeCrc16 on", data)
        checksum = self.crc_calculator.calculate_checksum(data) #data)
        return checksum

    def buildCommandPayload(self, marker, command):
        # Build a payload to send a command to the rotary controller
        # Payload: 2 bytes CRC16, 1 byte marker, 1 byte command
        buff = [marker, command]
        crc = self.computeCrc16(buff, 2)
        payload = [crc >> 8, crc & 0x00FF, buff[0], buff[1]]
        return payload

    def buildRedundantCommandPayload(self, marker, command, redundancy):
        payload = self.buildCommandPayload(marker, command)
        buff = []
        for i in range(redundancy):
            buff.extend(payload)
        return buff

    def validateReadPayloadCrc(self, payload):
        #print(payload, type(payload))
        buff = bytearray(payload)
        # # print("Validating crc...")
        # # print("payload", binascii.hexlify(payload))

        computedCrc = self.computeCrc16(buff[2:], 46)
        # # print(computedCrc)

        receivedCrc = (buff[0] << 8) + buff[1]
        # # print(receivedCrc)

        test = computedCrc == receivedCrc
        if not test:
            print("CRC not valid !!! expected: ", receivedCrc, "but got: ", computedCrc)

        return test

    def validateReadPayloadMarker(self, payload, expectedMarker):
        buff = bytearray(payload)
        receivedMarker = buff[2]
        test = expectedMarker == receivedMarker
        if not test:
            print("Marker not valid !!! expected: ", expectedMarker, "but got: ", receivedMarker)

        return test

    def getPosition1FromReadPayload(self, payload):
        #payload is in bytes format
        buff = bytearray(payload)
        pos = (buff[4] << 8) + buff[5]
        return pos

    def getPosition2FromReadPayload(self, payload):
        #payload is in bytes format
        buff = bytearray(payload)
        pos = (buff[6] << 8) + buff[7]
        return pos

    def getSpeeds1FromReadPayload(self, payload):
        buff = bytearray(payload)
        speeds = []
        offset = 8
        for i in range(10):
            #speed = (buff[2*i + offset] << 8) + buff[2*i + 1 + offset]
            speed = int.from_bytes(buff[2*i + offset : 2*i + offset + 2], "big", signed="True")
            speeds.append(speed)

        return speeds

    def getSpeeds2FromReadPayload(self, payload):
        buff = bytearray(payload)
        speeds = []
        offset = 28
        for i in range(10):
            #speed = (buff[2*i + offset] << 8) + buff[2*i + 1 + offset]
            speed = int.from_bytes(buff[2*i + offset : 2*i + offset + 2], "big", signed="True")
            speeds.append(speed)

        return speeds

    def shot(self):

        sleep(self.tempo_spi)

        self.timingCommandPayload = self.buildRedundantCommandPayload(self.marker, self.timingCommand, self.redundancy)
        # # print("self.timingCommandPayload", self.timingCommandPayload)
        self.pi.spi_write(self.sensor0, self.timingCommandPayload)

        # sleep 1ms
        sleep(self.tempo_spi)

        self.readCommandPayload = self.buildRedundantCommandPayload(self.marker, self.readCommand, self.redundancy)
        # # print("self.readCommandPayload", self.readCommandPayload)

        retriesCount = 5
        payloadValid = False
        receivedPayload = None

        while (retriesCount > 0 and not payloadValid):
            retriesCount -= 1
            (length, receivedPayload) = self.pi.spi_xfer(self.sensor0, self.readCommandPayload)
            payloadValid = self.validateReadPayloadCrc(receivedPayload) and self.validateReadPayloadMarker(receivedPayload, self.marker)

        if payloadValid:
            return self.get_position_and_speed(receivedPayload)
        else:
            # On ne peux pas mesurer les données on recommence
            print("payload invalide, shot() relancé")
            self.shot()

    def get_position_and_speed(self, receivedPayload):
        pos1 = self.getPosition1FromReadPayload(receivedPayload)
        self.teta = self.points_to_teta(int(pos1/4)) - 3.05
        speeds1 = self.getSpeeds1FromReadPayload(receivedPayload)
        self.teta_dot = int(100000 / (sum(speeds1) / len(speeds1)))
        # # print("position1: ", pos1, "speeds1: ", speeds1)

        pos2 = self.getPosition2FromReadPayload(receivedPayload)
        self.alpha = self.points_to_alpha(int(pos2/4)) + 3.0
        speeds2 = self.getSpeeds2FromReadPayload(receivedPayload)
        self.alpha_dot = int(100000 / (sum(speeds2) / len(speeds2)))
        # # print("position2: ", pos2, "speeds2: ", speeds2)

        # # print(self.alpha, self.alpha_dot, self.teta, self.teta_dot)
        return self.alpha, self.alpha_dot, self.teta, self.teta_dot

    def points_to_alpha(self, points):
        """Conversion des points en radians du chariot
        1000 points pour 360° soit 2PI rd
        """
        return  (np.pi * points / 500) % 2*np.pi

    def points_to_teta(self, points):
        """Conversion des points en radians du balancier
        4000 points pour 360° soit 2PI rd
        """
        return  (np.pi * points / 2000) % 2*np.pi

    def impulsion_moteur(self, puissance, lenght, sens):
        """Envoi d'une impulsion au moteur
        puissance = puissance de l'impulsion: 1 à range_pwm
        lenght = durée de l'impulsion
        sens = left ou right
        """
        # Sécurité pour ne pas emballer le moteur
        puissance_maxi = self.ratio_puissance_maxi * self.range_pwm

        if puissance > puissance_maxi:
            puissance = puissance_maxi

        if lenght > self.length_maxi:
            lenght = self.length_maxi

        self.motor.motor_run(puissance, sens)
        # Stop du moteur dans lenght seconde non bloquant
        self.wait_and_stop_thread(lenght)

    def wait_and_stop_thread(self, lenght):
        t = Thread(target=self.wait, args=(lenght,))
        t.start()

    def wait(self, some):
        """Attente de lenght, puis stop moteur"""
        sleep(some)
        self.motor.stop()

    def recentering(self):
        """Recentrage du chariot si trop décalé soit plus de 2rd"""
        puissance_maxi = int(self.ratio_puissance_maxi * self.range_pwm)

        # pour print
        alpha_old = self.alpha

        # # n = 0
        # TODO à revoir
        # # while self.alpha > 0.5 and n < 5:
        # # n += 1
        pr = abs(int(puissance_maxi*self.alpha*1.2))
        l = 0.10
        sens = 'right'
        if self.alpha > 0:
            sens = 'left'
        self.impulsion_moteur(pr, l, sens)
        # Attente de la fin du recentrage
        sleep(1)
        print(f"{self.cycle} Recentrage de {pr} sens {sens} "
              f"alpha avant: {round(alpha_old, 2)} "
              f"alpha après {round(self.alpha, 2)}")

    def swing(self):
        """Un swing"""
        puissance_maxi = int(self.ratio_puissance_maxi * self.range_pwm)

        sens = 'right'
        anti_sens = 'left'
        if self.alpha > 0:
            sens = 'left'
            anti_sens = 'right'

        ps = puissance_maxi * 0.4
        self.impulsion_moteur(ps, 0.08, sens)
        sleep(0.35)
        self.impulsion_moteur(ps, 0.1, anti_sens)
        sleep(0.05)
        print(f"{self.cycle} Swing {ps}")

    def quit(self):
        self.motor.cancel()
        self.clavier_active = 0
        # Attente pour que le moteur stoppe
        sleep(0.5)
        print("pigpio stoppé proprement ...")
        self.pi.stop()
        print("... Fin.")


if __name__ == '__main__':

    from furuta_env import Clavier

    current_dir = str(Path(__file__).parent.absolute())
    print("Dossier courrant:", current_dir)

    ini_file = current_dir + '/furuta.ini'
    print("Fichier de configuration:", ini_file)

    cf = MyConfig(ini_file)
    numero = "100"
    clavier = Clavier()
    furuta = Furuta(cf, numero, clavier)
    i = 0
    while i < 10:
        furuta.shot()
        sleep(0.1)

    # # marker = 12
    # # command = 5
    # # redundancy = 11
    # # payload = furuta.buildCommandPayload(marker, command)
    # # print(payload)

    # # p = furuta.buildRedundantCommandPayload(marker, command, redundancy)
    # # print(p)

    # # rxPayload = bytes([0x52, 0xdb, 5, 4, 0, 3, 0, 12])

    # # isValidCrc = furuta.validateReadPayloadCrc(rxPayload)
    # # print(isValidCrc)

    # # isValidMarker = furuta.validateReadPayloadMarker(rxPayload, 5)
    # # print(isValidMarker)

    furuta.quit()
