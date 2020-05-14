#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Germain GAILLARD <gaillard.germain@gmail.com>
# Version: 0.1
# License: MIT

"""Importation des modules"""
import sys
import pygame
from random import randint
import json

def weighted(weighted_list):
    #Merci a Simon <Relic> GAILLARD pour cette fonction.
    '''return an item randomly from dict based on is weight
    (higher weights tend to be chosen more often)
    dict must be of the form : {'a': 10, 'b':4, 'c': 1}'''
    length = sum(weighted_list.values())
    index = randint(1,length)
    x = 0
    for key in weighted_list:
        x += weighted_list[key]
        if index <= x:
            return key

def rotate(pipe):
    """Fait tourner le tuyau (anti-horaire)"""
    coef = randint(0, 3)
    for i in range(coef):
        pipe.apertures.append(pipe.apertures.pop(0))
        pipe.image = pygame.transform.rotate(pipe.image, 90)
        if pipe.image_2:
            pipe.image_2 = pygame.transform.rotate(pipe.image_2, 90)
    return pipe

def open_to(pipe):
    """Pointe les coordonnees vers lesquels le tuyau est ouvert"""
    for index, aperture in enumerate(pipe.apertures):
        if aperture:
            if index == 0:
                yield ((pipe.rect.left - 60), pipe.rect.top)
            if index == 1:
                yield (pipe.rect.left, (pipe.rect.top - 60))
            if index == 2:
                yield (pipe.rect.right, pipe.rect.top)
            if index == 3:
                yield (pipe.rect.left, pipe.rect.bottom)

def pipe_dispenser():
    """Retourne un tuyau en fonction de sa 'rareté' """
    stock = {('images/cross.png', (1, 1, 1, 1)) : 10,
             ('images/regular_1.png', (0, 1, 0, 1)) : 50,
             ('images/regular_2.png', (0, 1, 1, 0)) : 40}
    return Pipe(weighted(stock))

def fill_box(box):
    """initialise la pioche"""
    box = []
    for i in range(3):
        pipe = pipe_dispenser()
        pipe = rotate(pipe)
        box.append(pipe)
    return box

def pick_up(box):
    """Pioche le tuyau courant et replace un autre en bout de pile"""
    pipe = box.pop(0)
    new = pipe_dispenser()
    new = rotate(new)
    box.append(new)
    return pipe

def cursor_pos(cursor, board_pos, coords, area):
    """Maitien le curseur dans une zone definie"""
    x = coords[0] - board_pos[0]
    y = coords[1] - board_pos[1]
    cursor.topleft = (x-x%60, y-y%60)
    if cursor.left < area.left:
        cursor.left = area.left
    elif cursor.right > area.right:
        cursor.right = area.right
    if cursor.top < area.top:
        cursor.top = area.top
    elif cursor.bottom > area.bottom:
        cursor.bottom = area.bottom
    return cursor.topleft

def add(circuit, current):
    """Ajoute le tuyau courant au circuit"""
    for pipe in circuit:
        if pipe.rect.topleft == current.rect.topleft:
            circuit.remove(pipe)
    circuit.append(current)
    return circuit

def check(circuit, previous, path):
    """Retourne le bon tuyau"""
    eligibles = []
    elected = None
    for pipe in circuit:
        if (pipe.rect.topleft in list(open_to(previous)) and
        previous.rect.topleft in list(open_to(pipe))):
            eligibles.append(pipe)
    for pipe in eligibles:
        if previous.name == 'regular':
            elected = pipe
        elif previous.name == 'cross':
            if pipe.rect.topleft == (previous.rect.left + path[0],
                                     previous.rect.top + path[1]):
                elected = pipe
    return elected

def clog(path, apertures):
    """Bouche l'ouverture par laquelle le liquide est passé"""
    if path[0] < 0:
        apertures[2] = 0
    elif path[0] > 0:
        apertures[0] = 0
    if path[1] < 0:
        apertures[3] = 0
    elif path[1] > 0:
        apertures[1] = 0
    return apertures

def place_block(valve_1, valve_2, locked):
    """Empeche un block de se placer devant l'entree ou la sortie"""
    pos = (randint(0, 14) * 60,randint(0, 9) * 60)
    if pos in list(open_to(valve_1)) or pos in list(open_to(valve_2)):
        pos = place_block(valve_1, valve_2, locked)
    elif pos in locked:
        pos = place_block(valve_1, valve_2, locked)
    return pos

def load_json(data_file):
    with open(data_file) as data:
        return json.load(data)

def new_record(score, topten):
    """Verifie si le score peu entrer dans le top ten"""
    for index, player in enumerate(topten):
        if score > player["score"]:
            return index
    return None

def update_json(data_file, topten, index, winner, score):
    """met a jour le fichier json"""
    topten.insert(index, dict(name = winner, score = score))
    if len(topten) > 10:
        del topten[-1]
    with open(data_file, 'w') as file:
        json.dump(topten, file, indent = 4)
    return 0

def font_size(size):
    """Change la taille de la police principale"""
    return pygame.font.Font('fonts/Amatic-Bold.ttf', size)

def centerx(surface, font, txt):
    """retourne la position x pour que le txt soit centrer"""
    x = surface.get_width()
    w = font.size(txt)[0]
    return (x - w)/2

class Pipe(object):
    """Un tuyau"""
    def __init__(self, ref):
        self.image = pygame.image.load(ref[0])
        self.image_2 = None
        self.apertures = list(ref[1])
        self.points = 100
        self.rect = self.image.get_rect()
        self.name = 'regular'
        if sum(self.apertures) == 4:
            self.name = 'cross'

class Plumbit(object):
    """Plumbit"""
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        pygame.init()
        pygame.display.set_caption("Plumb'it")

        self.topten = load_json('topten.json')
        self.layer1 = pygame.Surface((900, 660), 32)
        self.layer2 = pygame.Surface((900, 660), pygame.SRCALPHA, 32)
        self.layer3 = pygame.Surface((134, 682), pygame.SRCALPHA, 32)
        self.circuit = []
        self.locked = []
        self.box = []
        self.valve = Pipe(('images/valve_1.png', (0, 0, 1, 0)))
        self.valve.image_2 = pygame.image.load('images/valve_1a.png')
        self.end = Pipe(('images/valve_2.png', (0, 0, 1, 0)))
        self.liquid_image = pygame.image.load('images/liquid.png')
        self.liquid = self.liquid_image.get_rect()

    def set_up(self, score):
        self.circuit.clear()
        self.locked.clear()
        self.box.clear()
        self.layer2.fill((255, 255, 255, 0))
        self.valve.rect.topleft = (randint(1, 5) * 60,
                              randint(1, 9) * 60)
        self.end.rect.topleft = (randint(9, 13) * 60,
                                 randint(1, 9) * 60)
        self.valve = rotate(self.valve)
        self.end = rotate(self.end)
        self.circuit.append(self.valve)
        self.circuit.append(self.end)
        self.locked.append(self.valve.rect.topleft)
        self.locked.append(self.end.rect.topleft)
        for i in range(randint(0, 5)):
            block = Pipe(('images/block.png', (0, 0, 0, 0)))
            block.rect.topleft = place_block(self.valve, self.end, self.locked)
            self.circuit.append(block)
            self.locked.append(block.rect.topleft)
        self.box = fill_box(self.box)
        self.previous = self.valve
        self.liquid.topleft = self.valve.rect.topleft
        self.countdown = 60
        self.score = score
        self.message = ''

    def main(self):
        screen = pygame.display.set_mode((1440, 900))
        COUNTDOWN = pygame.USEREVENT +1
        FLOOD = pygame.USEREVENT +2
        ANIM1 = pygame.USEREVENT +3
        ANIM2 = pygame.USEREVENT +4
        music = pygame.mixer.Sound('son/Solve The Puzzle.ogg')
        put = pygame.mixer.Sound('son/put.ogg')
        tic = pygame.mixer.Sound('son/tic.ogg')
        sub = pygame.mixer.Sound('son/sub.ogg')
        loose = pygame.mixer.Sound('son/loose.ogg')
        win = pygame.mixer.Sound('son/win.ogg')
        dashboard = pygame.image.load('images/dashboard.png')
        back = pygame.image.load('images/dashboard_back.png')
        arrow_image = pygame.image.load('images/arrow.png')
        pointer_image = pygame.image.load('images/pointer.png')
        locked_image = pygame.image.load('images/locked.png')
        cursor_image = pointer_image
        cursor = cursor_image.get_rect()
        arrow = arrow_image.get_rect()
        board_pos = (250, 120)
        arrow.topleft = (120, 495)
        path = (0, 0)
        music.play()
        pygame.time.set_timer(ANIM1, 500)
        pygame.time.set_timer(ANIM2, 30)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEMOTION:
                    cursor.topleft = cursor_pos(cursor, board_pos,
                                                pygame.mouse.get_pos(),
                                                self.layer1.get_rect())
                    if cursor.topleft in self.locked:
                        cursor_image = locked_image
                    else:
                        cursor_image = pointer_image
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.countdown == 60:
                            pygame.time.set_timer(COUNTDOWN, 1000)
                        if cursor.topleft not in self.locked:
                            put.play()
                            pipe = pick_up(self.box)
                            pipe.rect.topleft = cursor.topleft
                            self.circuit = add(self.circuit, pipe)
                            self.score -= 50
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        sub.play()
                        pygame.time.set_timer(COUNTDOWN, 0)
                        pygame.time.set_timer(FLOOD, 20)
                elif event.type == ANIM1:
                    self.valve.image, self.valve.image_2 = (self.valve.image_2,
                                                            self.valve.image)
                elif event.type == ANIM2:
                    if arrow.left > 90:
                        arrow = arrow.move(-2, 0)
                    else:
                        arrow.left = 120
                elif event.type == COUNTDOWN:
                    tic.play()
                    self.countdown -= 1
                    if self.countdown == 0:
                        pygame.time.set_timer(COUNTDOWN, 0)
                        pygame.time.set_timer(FLOOD, 40)
                        sub.play()
                elif event.type == FLOOD:
                    pipe = check(self.circuit, self.previous, path)
                    if pipe:
                        path = (pipe.rect.left - self.previous.rect.left,
                                pipe.rect.top - self.previous.rect.top)
                        self.liquid = self.liquid.move(path[0]/60, path[1]/60)
                        if self.liquid.topleft == self.end.rect.topleft:
                            pygame.time.set_timer(FLOOD, 0)
                            self.message = 'YOU WIN'
                        elif self.liquid.topleft == pipe.rect.topleft:
                            pipe.apertures = clog(path, pipe.apertures)
                            self.locked.append(pipe.rect.topleft)
                            self.score += 100
                            self.previous = pipe
                    else:
                        pygame.time.set_timer(FLOOD, 0)
                        self.message = 'YOU LOOSE'

            screen.fill((66, 63, 56))
            screen.blit(self.layer1, board_pos)
            screen.blit(self.layer2, board_pos)
            screen.blit(dashboard, (0, 0))
            screen.blit(self.layer3, (1167, 115))
            screen.blit(arrow_image, arrow.topleft)
            for i, pipe in enumerate(self.box):
                screen.blit(pipe.image, (150, 480 + i * 80))
            self.layer1.fill((96, 93, 86))
            for pipe in self.circuit:
                self.layer1.blit(pipe.image, pipe.rect.topleft)
            self.layer1.blit(cursor_image, cursor.topleft)
            self.layer2.blit(self.liquid_image, self.liquid.topleft)
            self.layer3.blit(back, (0, 0))
            img_txt = font_size(40).render(str(self.score), True,
                                             (83, 162, 162))
            self.layer3.blit(img_txt, (centerx(self.layer3,
                             font_size(40), str(self.score)), 5))
            img_txt = font_size(40).render(str(self.countdown), True,
                                        (70, 170, 60))
            self.layer3.blit(img_txt, (centerx(self.layer3,
                             font_size(40), str(self.countdown)), 625))
            pygame.display.update()

            if self.message:
                """Fin de partie"""
                music.stop()
                if self.message == 'YOU WIN':
                    win.play()
                else:
                    loose.play()
                img_txt = font_size(72).render(self.message, True,
                                                   (194, 69, 26))
                screen.blit(img_txt, (centerx(screen, font_size(72),
                                      self.message), 20))
                txt = 'Press ENTER to continue'
                img_txt = font_size(40).render(txt, True, (194, 69, 26))
                screen.blit(img_txt, (centerx(screen, font_size(40), txt), 800))
                pygame.display.update()
                pygame.event.clear()
                while True:
                    event = pygame.event.wait()
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.message == 'YOU WIN':
                                self.score += 200
                                self.set_up(self.score)
                                music.play()
                                break
                            else:
                                rank = new_record(self.score, self.topten)
                                if rank != None:
                                    return self.entry(rank)
                                else:
                                    return self.menu()

    def menu(self):
        screen = pygame.display.set_mode((600, 900))
        txt = "PLUMB'IT"
        img_txt = font_size(72).render(txt, True, (170, 60, 60))
        screen.blit(img_txt, (centerx(screen, font_size(72), txt), 50))
        for i, player in enumerate(self.topten):
            name = font_size(40).render(player["name"], True, (50, 162, 162))
            score = font_size(40).render(str(player["score"]), True,
                                         (50, 162, 162))
            screen.blit(name, (140, 170 + i * 50))
            screen.blit(score, (380, 170 + i * 50))
        txt = 'Press ENTER to play'
        img_txt = font_size(32).render(txt, True, (170, 60, 60))
        screen.blit(img_txt, (centerx(screen, font_size(32), txt), 800))
        pygame.display.update()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.set_up(25000)
                    break
        return self.main()

    def entry(self, rank):
        screen = pygame.display.set_mode((600, 240))
        name = 'Enter your name'
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if len(name) > 0:
                        name = name[:-1]
                elif event.key == pygame.K_RETURN:
                    update_json('topten.json', self.topten, rank, name,
                                self.score)
                    break
                else:
                    if name == 'Enter your name':
                        name = ''
                    if len(name) < 18:
                        name += event.unicode
            screen.fill((0, 0, 0))
            txt = str(self.score) + ' is a new record !'
            img_txt = font_size(48).render(txt, True, (83, 162, 162))
            screen.blit(img_txt, (centerx(screen, font_size(48), txt), 20))
            img_txt = font_size(40).render(name, True, (170, 60, 60))
            screen.blit(img_txt, (centerx(screen, font_size(40), name), 100))
            pygame.display.update()
        return self.menu()

if __name__ == '__main__':
    Plumbit().menu()
