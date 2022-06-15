"""
Pilotage d'un moteur branché sur le PWM de la Pi

GPIO 27     Sens droite     IN1
GPIO 17     Sens gauche     IN2
GPIO 18     PWM             PWM

Pour le clavier:
python3 -m pip install pynput

Lancer le deamon
sudo pigpiod
"""

import os
from time import time, sleep
from threading import Thread

import pigpio


class MeinMotor:

    def __init__(self, conn, PWM, left, right, freq_pwm, range_pwm):
        """pi = pigpio
        conn = Pipe du multiprocess
        PWM = pin GPIO du PWM 18
        left = pin GPIO du left 27
        right = pin GPIO du right 17
        """

        self.pi = pigpio.pi()
        self.conn = conn
        self.PWM = PWM
        self.left = left
        self.right = right

        self.set_frequency(18, freq_pwm)
        self.set_range(18, range_pwm)

        self.motor_conn_loop = 1
        if conn:
            self.motor_receive_thread()

    def set_frequency(self, user_gpio, frequency):
        """user_gpio: 0-31 A Broadcom numbered GPIO.
        frequency: 0-40000 Defines the frequency to be used for PWM on a GPIO.
                The closest permitted frequency will be used.
        """
        self.pi.set_PWM_frequency(user_gpio, frequency)

    def set_range(self, user_gpio, range_pwm):
        """Par défaut, range_pwm = 255
        Plage possible: 25 / 40 000
        """
        self.pi.set_PWM_range(user_gpio, range_pwm)

    def set_dutycycle(self, user_gpio, dutycycle):
        """Starts (non-zero dutycycle) or stops (0) PWM pulses on the GPIO.
        Parameters:
            user_gpio:= 0-31.
            dutycycle:= 0-range (range defaults to 255).
            The set_PWMrange_pwm function can change the default range of 255.
        Example:
            pi.set_PWM_dutycycle(4,   0) # PWM off
            pi.set_PWM_dutycycle(4,  64) # PWM 1/4 on
            pi.set_PWM_dutycycle(4, 128) # PWM 1/2 on
            pi.set_PWM_dutycycle(4, 192) # PWM 3/4 on
            pi.set_PWM_dutycycle(4, 255) # PWM full on
        """
        self.pi.set_PWM_dutycycle(user_gpio, dutycycle)

    def set_pin_low(self, GPIO_number):
        """set local Pi's GPIO GPIO_number low"""
        self.pi.write(GPIO_number, 0)

    def set_pin_high(self, GPIO_number):
        """set local Pi's GPIO GPIO_number low"""
        self.pi.write(GPIO_number, 1)

    def cancel(self):
        print("cancel moteur")
        self.PWM = 0
        self.set_pin_low(self.left)
        self.set_pin_low(self.right)
        sleep(0.1)
        self.pi.stop()


    def motor_receive_thread(self):
        print("Lancement du thread receive dans MeinMotor")
        t = Thread(target=self.motor_receive)
        t.start()

    def motor_receive(self):
        while self.motor_conn_loop:
            data = self.conn.recv()

            if data:
                if data[0] == 'quit':
                    print("quit reçu pour le moteur")
                    self.motor_conn_loop = 0
                    self.cancel()

                elif data[0] == 'impulsion':
                    speed = data[2]
                    speed = abs(speed)

                    if data[1] == 'right':
                        self.set_pin_low(self.left)
                        self.set_pin_high(self.right)
                        self.set_dutycycle(self.PWM, speed)

                    if data[1] == 'left':
                        self.set_pin_high(self.left)
                        self.set_pin_low(self.right)
                        self.set_dutycycle(self.PWM, speed)

                elif data[0] == 'stop':
                    self.set_pin_low(self.left)
                    self.set_pin_low(self.right)

            sleep(0.001)
        print("Fin du thread du moteur")
        sleep(0.1)
        os._exit(0)



def mein_motor_run(conn, PWM, left, right, freq_pwm, range_pwm):

    print("Lancement de la commande moteur")
    mein_motor = MeinMotor(conn, PWM, left, right, freq_pwm, range_pwm)
