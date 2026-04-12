# COMP216-402 - Final Project - Group 1

# Import necessary packages.
import math
import random

# DataGenerator class that generates numbers that is random with a pattern.
class DataGenerator:
    def __init__(self):
        self.t = 0
        self.step = 0.1
        self.base = 50
        self.amplitude = 10
    
    # Generates a number that uses sine wave (Pattern) with random noise (Random).
    def get_value(self):
        value = self.base + self.amplitude * math.sin(self.t)
        value += random.uniform(-2, 2)

        self.t += self.step
        return round(value, 2)