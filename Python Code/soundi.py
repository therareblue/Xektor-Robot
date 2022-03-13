import pygame, sys, time
from pygame.locals import *
import random
pygame.init()

#pygame.mixer.music.set_volume(0.1)
'''
pygame.mixer.music.load("./music/lambada.mp3")
pygame.mixer.music.play()
time.sleep(5)
pygame.mixer.music.fadeout(5000)
pygame.mixer.music.stop()
'''

def tapRespond1():
    clock = pygame.time.Clock()
    pygame.mixer.music.set_volume(0.7)

    i = random.randint(0, 8)
    filename = "./audio/sp_neg/chc" + str(i) + ".mp3"
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)

def hitRespond():
    clock = pygame.time.Clock()
    pygame.mixer.music.set_volume(0.7)
    filename = "./audio/ohcomone.mp3"
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)

def initialize():
    clock = pygame.time.Clock()
    pygame.mixer.music.set_volume(0.7)
    filename = "./audio/sp_pos/r_sp11.mp3"
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)

    filename = "./audio/sp_pos/r_sp14.mp3"
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)

    filename = "./audio/sp_pos/r_sp18.mp3"
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)

    filename = "./audio/sp_good_morning.mp3"
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)


def tapRespond2():
    clock = pygame.time.Clock()
    pygame.mixer.music.set_volume(0.7)

    j = random.randint(1, 3)
    for k in range(j):
        i = random.randint(0, 12)
        filename = "./audio/sp_neg/neg" + str(i) + ".mp3"
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            clock.tick(30)

def sleeping_sound():
    clock = pygame.time.Clock()
    pygame.mixer.music.set_volume(0.7)
    filename = "./audio/trance.mp3"
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)

def going_sleep():
    clock = pygame.time.Clock()
    pygame.mixer.music.set_volume(0.7)
    i = random.randint(1, 11)
    try:
        filename = "./audio/fart/fart" + str(i) + ".mp3"
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            clock.tick(30)
    except:
        pass

