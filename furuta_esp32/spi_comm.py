
from time import time, sleep

from crc import CrcCalculator, Crc16


class SPI_Comm:
    """Communication SPI entre Raspi et ESP32,
    pour récupérer les datas des codeurs
    demander à Max
    """

    def __init__(self, cf, numero, pi, clavier):
        """cf:  l'objet MyConfig
        numero: string du numéro d'apprentissage = section dans *.ini
        pi: pigpio
        clavier: capture input clavier

        Valeur définies dans *.ini
            marker: 12
            timingCommand: 5
            readCommand: 42
            redundancy: 16
            retriesCount: 5 Nombre de lecture des datas maxi,
                          on relit tant que le hash est faux
        """

        self.cf = cf
        self.config = cf.conf  # le dict de conf
        self.numero = numero
        self.pi = pi
        self.clavier = clavier

        self.crc_calculator = CrcCalculator(Crc16.CCITT, True)
        self.marker = int(self.config[self.numero]['marker'])
        self.timingCommand = int(self.config[self.numero]['timingcommand'])
        self.readCommand = int(self.config[self.numero]['readcommand'])
        self.redundancy = int(self.config[self.numero]['redundancy'])
        self.retriesCount = int(self.config[self.numero]['retriescount'])

        self.timingCommandPayload = self.buildRedundantCommandPayload(self.marker,
                                                                      self.timingCommand,
                                                                      self.redundancy)

        self.readCommandPayload = self.buildRedundantCommandPayload(self.marker,
                                                                    self.readCommand,
                                                                    self.redundancy)

        # SPI
        self.tempo_spi = float(self.config[self.numero]['tempo_spi'])
        self.spi_freq = int(self.config[self.numero]['spi_freq'])
        self.sensor0 = self.pi.spi_open(0, self.spi_freq, 2)

    def computeCrc16(self, bufferArray, size):
        """Calc CRC16 of bufferArray and return one integer."""

        data = bytes(bufferArray[:size])
        checksum = self.crc_calculator.calculate_checksum(data)
        return checksum

    def buildCommandPayload(self, marker, command):
        """Build one payload to send a command to the ESP32 with the rotary controller.
        Retourne: Payload =
            - 2 bytes CRC16
            - 1 byte marker
            - 1 byte command
        """
        buff = [marker, command]
        crc = self.computeCrc16(buff, 2)
        payload = [crc >> 8, crc & 0x00FF, buff[0], buff[1]]
        return payload

    def buildRedundantCommandPayload(self, marker, command, redundancy):
        """Construction de la demande des datas, la payload redondée.
                marker: = 1 octect mini 1 maxi 255
                command: 5 pour timming 42 pour read
                redundancy: répétition de la payload de commande
        """
        payload = self.buildCommandPayload(marker, command)
        buff = []
        for i in range(redundancy):
            buff.extend(payload)
        return buff

    def validateReadPayloadCrc(self, payload):
        """Contrôle du hash des datas reçues.
        Retourne True si ok, sinon False
        """

        buff = bytearray(payload)
        computedCrc = self.computeCrc16(buff[2:], 46)
        receivedCrc = (buff[0] << 8) + buff[1]

        test = computedCrc == receivedCrc
        if not test:
            print(f"CRC not valid !!! expected: {receivedCrc} "
                  f"but got: {computedCrc})")

        return test

    def validateReadPayloadMarker(self, payload, expectedMarker):
        """Contrôle du Marker
        je ne vois plus à quoi ça sert !
            payload:
            expectedMarker:
        """
        buff = bytearray(payload)
        receivedMarker = buff[2]
        test = expectedMarker == receivedMarker

        if not test:
            print(f"Marker not valid! expected: {expectedMarker} "
                  f"but got: {receivedMarker}")

        return test

    def getPosition1FromReadPayload(self, payload):
        """Récupération de la position 1,
        soit les points du codeur du balancier
        payload is in bytes format
        """
        buff = bytearray(payload)
        pos = (buff[4] << 8) + buff[5]
        return pos

    def getSpeeds1FromReadPayload(self, payload):
        """Récupération de la liste des vitesses 1,
        donc du codeur du balancier
        payload is in bytes format
        """
        buff = bytearray(payload)
        speeds = []
        offset = 6  #8
        for i in range(10):
            speed = int.from_bytes( buff[2*i + offset : 2*i + offset + 2],
                                    "big",
                                    signed="True")
            speeds.append(speed)

        return speeds

    def getPosition2FromReadPayload(self, payload):
        """Récupération de la position 2,
        soit les points du codeur du chariot
        payload is in bytes format
        """
        buff = bytearray(payload)
        offset = 26
        pos = (buff[offset] << 8) + buff[offset + 1]
        return pos

    def getSpeeds2FromReadPayload(self, payload):
        """Récupération de la liste des vitesses 2,
        donc du codeur du chariot
        payload is in bytes format
        """
        buff = bytearray(payload)
        speeds = []
        offset = 28
        for i in range(10):
            speed = int.from_bytes(buff[2*i + offset : 2*i + offset + 2],
                                   "big",
                                   signed="True")
            speeds.append(speed)

        return speeds

    def get_rotary_encoder_datas(self):
        """Demande et récupére les datas sur l'ESP32:
            - Write
            - tempo: pourquoi on attends ?
            - Read: on recommence jusqu'à 5 fois,
                    jusqu'à avoir des datas validées par le hash
        Retourne les positions et vitesses des 2 codeurs
            - teta en points, alpha en points,
              liste des temps de teta, liste des temps de alpha
            - temps entre 10 derniers tops codeurs
            Si datas non valides, retourne tuple de 0
        """

        t0 = time()
        # # print("timingCommandPayload", self.timingCommandPayload)
        self.pi.spi_write(self.sensor0, self.timingCommandPayload)
        sleep(self.tempo_spi)  # 0.001

        payloadValid = False
        receivedPayload = None
        n = 0
        while n < self.retriesCount and not payloadValid:
            n += 1
            length, receivedPayload = self.pi.spi_xfer( self.sensor0,
                                                        self.readCommandPayload)
            a = self.validateReadPayloadCrc(receivedPayload)
            b = self.validateReadPayloadMarker(receivedPayload, self.marker)
            payloadValid = a and b
            sleep(0.0001)

        if n > 1:
            print(f"Nombre de tentatives de lecture sur l'ESP32 supérieure "
                  f"à 1: {n} tentatives")

        if payloadValid:
            pos1 = self.getPosition1FromReadPayload(receivedPayload)
            speeds1 = self.getSpeeds1FromReadPayload(receivedPayload)
            pos2 = self.getPosition2FromReadPayload(receivedPayload)
            speeds2 = self.getSpeeds2FromReadPayload(receivedPayload)

            if self.clavier.m:
                print(f"Position: alpha {pos2:^4} teta {pos1:^4} "
                      f"Vitesses alpha {speeds2} vitesse teta {speeds1} "
                      f"Nombre de lecture: {n})")
            if self.clavier.k:
                c = round(1000*(time() - t0), 2)
                print(f"Temps de récupération des datas sur ESP32: {c} ms")
            return pos1, pos2, speeds1, speeds2

        else:
            print(f"Lecture sur ESP32 ratée: payloadValid invalid")
            return 0, 0, 0, 0
