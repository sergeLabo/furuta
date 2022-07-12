
"""
Pilotage d'un moteur branché sur le PWM de la Pi

GPIO 27     Sens droite     IN1
GPIO 17     Sens gauche     IN2
GPIO 18     PWM             PWM

"""

import os
from time import sleep

import pigpio



class MyMotor:

    def __init__(self, pi, PWM, left, right, freq_pwm, range_pwm):
        """pi = pigpio
        PWM = pin GPIO du PWM 18
        left = pin GPIO du left 27
        right = pin GPIO du right 17
        """

        self.pi = pi
        self.PWM = PWM
        self.left = left
        self.right = right

        self.set_frequency(self.PWM, freq_pwm)
        self.set_range(self.PWM, range_pwm)

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
        print("Cancel moteur")
        self.PWM = 0
        self.stop()
        sleep(0.5)
        print("Motor cancelled.")

    def motor_run(self, speed, sens):
        """Active le moteur à la puissance définie par speed
        speed = entier entre 0 et range_pwm
        Cela lance le moteur mais ne le stoppe pas !
        Il est stoppé par do_impulsion_thread() dans furuta.py
        """
        speed = abs(speed)

        try:
            if sens == 'right':
                self.set_pin_low(self.left)
                self.set_pin_high(self.right)
                self.set_dutycycle(self.PWM, speed)

            if sens == 'left':
                self.set_pin_high(self.left)
                self.set_pin_low(self.right)
                self.set_dutycycle(self.PWM, speed)
        except:
            print(f"Si il y a une erreur qui suit, elle vient d'une action sur le moteur "
                  f"demandée alors que pigpio est stoppé !!!!!!!!!!!!!!")

    def stop(self):
        """Stoppe le moteur"""
        if self.pi:
            self.set_pin_low(self.left)
            self.set_pin_low(self.right)



if __name__ == "__main__":

    """Test du moteur au clavier:
        - a impulsion à droite
        - z impulsion à gauche
    pendant 6 secondes.
    """

    from clavier import Clavier
    cl = Clavier()

    from my_config import MyConfig
    cf = MyConfig('./furuta.ini')
    config = cf.conf

    pi = pigpio.pi()
    PWM = int(config['moteur']['pwm'])
    left = int(config['moteur']['left'])
    right = int(config['moteur']['right'])
    range_pwm = 200
    freq_pwm = 10000

    motor = MyMotor(pi, PWM, left, right, freq_pwm, range_pwm)

    from time import time, sleep
    t = time()
    while time() - t < 6:
        if cl.a == 1:
            motor.motor_run(50, 'right')
            cl.a = 0
            sleep(0.05)
            motor.stop()
        if cl.z == 1:
            motor.motor_run(50, 'left')
            cl.z = 0
            sleep(0.05)
            motor.stop()
        sleep(0.1)
