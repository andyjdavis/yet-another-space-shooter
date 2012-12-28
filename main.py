# This is a game called "Yet Another Space Shooter" (YASS)
#
# YASS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YASS is distributed in the hope that it will be useful and maybe even fun,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YASS.  If not, see <http://www.gnu.org/licenses/>.
#
# copyright  2012 onwards Andrew Davis
# license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
#

import os, pygame
from pygame.locals import *

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

import math
import random

class Globals:
    
    def __init__(self):
        self.width = 800
        self.height = 600

        self.wave = 0
        self.wave_rocks_left = 0
        
        self.lives = 1
        self.time = 0
        
        self.playing = False
        self.betweenwaves = False
        self.dead = False
        
        self.wavedelaystarttime = 0

        self.text_antialias = 1
        self.text_color = (255, 255, 255)
        self.text_bg_color = (0, 0, 0)

        # globals for tuning
        self.ship_turn_speed = 3
        self.friction = 0.98
        self.missile_initial_vel = 5

g = Globals()
my_ship = None
splash_surface = None

pygame.init()
screen = pygame.display.set_mode((g.width, g.height))
pygame.display.set_caption('Yet Another Space Shooter')
#pygame.mouse.set_visible(0)

missile_group = pygame.sprite.RenderPlain()
rock_group = pygame.sprite.RenderPlain()
explosion_group = pygame.sprite.RenderPlain()

def load_image(name, colorkey=-1, perpixelalpha=False):
    fullname = os.path.join('resources', name)
    
    try:
        image = pygame.image.load(fullname)
        if perpixelalpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
    except pygame.error, message:
        print 'Cannot load image:', fullname
        raise SystemExit, message

    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join('resources', name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error, message:
        print 'Cannot load sound:', fullname
        raise SystemExit, message
    return sound

class ImageInfo:
    def __init__(self, center, size, radius = 0, lifespan = None, animated = False):
        self.center = center
        self.size = size
        self.radius = radius
        if lifespan:
            self.lifespan = lifespan
        else:
            self.lifespan = float('inf')
        self.animated = animated

    def get_center(self):
        return self.center

    def get_size(self):
        return self.size

    def get_radius(self):
        return self.radius

    def get_lifespan(self):
        return self.lifespan

    def get_animated(self):
        return self.animated
    
# art assets created by Kim Lathrop and may be freely re-used in non-commercial projects, please credit Kim.

nebula_info = ImageInfo([400, 300], [800, 600])
nebula_image, nebula_image_rect = load_image("nebula_blue.png")

splash_info = ImageInfo([200, 150], [400, 300])

ship_info = ImageInfo([45, 45], [90, 90], 35)
ship_image, ship_image_rect = load_image("double_ship.png", None, True)

missile_info = ImageInfo([5,5], [10, 10], 3, 100)
missile_image, missile_image_rect = load_image("shot2.png")

asteroid_info = ImageInfo([45, 45], [90, 90], 40)
asteroid_image, asteroid_image_rect = load_image("asteroid_blue.png", -1, True)

explosion_info = ImageInfo([64, 64], [128, 128], 17, 24, True)
explosion_image, explosion_image_rect = load_image("explosion_alpha.png", None, True)

soundtrack_path = os.path.join('resources', '516494_Zone-X.mp3')
pygame.mixer.music.load(soundtrack_path)
pygame.mixer.music.set_volume(0.4)

missile_sound = load_sound("laser6.wav")
ship_thrust_sound = load_sound("enginehum3.ogg")
explosion_sound = load_sound("threeTone1.wav")
end_wave_sound = load_sound("threeTone2.wav")

# helper functions to handle transformations
def angle_to_vector(ang):
    return [math.cos(ang), math.sin(ang)]

def pos_to_top_left(pos, size):
    return (pos[0] - (size[0]/2), pos[1] - (size[1]/2))

def pos_to_rect(pos, size):
    (x, y) = pos_to_top_left(pos, size)
    return pygame.Rect(x, y, size[0], size[1])

def dist(p,q):
    return math.sqrt((p[0]-q[0])**2+(p[1]-q[1])**2)

def rand(minimum, maximum):
    return random.random() * (maximum - minimum) + minimum

def degrees_to_radians(degrees):
    return (degrees * math.pi) / 180

def rotate_around_center(surface, angle):
    """rotate a Surface, maintaining position."""
    loc = surface.get_rect().center
    rotated_surface = pygame.transform.rotate(surface, angle)
    rotated_surface.get_rect().center = loc
    return rotated_surface

# Ship class
class Ship:
    def __init__(self, pos, vel, angle, image, info):
        self.pos = [pos[0],pos[1]]
        self.vel = [vel[0],vel[1]]
        self.thrust = False
        self.angle = angle
        self.angle_vel = 0
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()

    def draw(self):

        source_left = 0
        if self.thrust:
            # if thrusting we want the 2nd image
            source_left = self.image_size[0]

        self.surface = ship_image.subsurface((source_left,0), (self.image_size[0], self.image_size[1]))

        rotated_ship_surface = rotate_around_center(self.surface, self.angle)
        w, h = rotated_ship_surface.get_size()
        ship_draw_pos = pos_to_top_left(self.pos, (w, h))
        screen.blit(rotated_ship_surface, ship_draw_pos)

    def update(self):
        self.angle += self.angle_vel

        if self.thrust:
            v = angle_to_vector(degrees_to_radians(self.angle))
            self.vel[0] += v[0]/3
            self.vel[1] -= v[1]/3 # flip the Y as Y is down on screen
        
        self.vel[0] *= g.friction
        self.vel[1] *= g.friction
        
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        
        self.pos[0] %= (g.width + self.radius)
        self.pos[1] %= (g.height + self.radius)
        
        self.rect = pos_to_rect(self.pos, self.image_size)

    def increment_angle_vel(self):
        self.angle_vel += g.ship_turn_speed
        
    def decrement_angle_vel(self):
        self.angle_vel -= g.ship_turn_speed
        
    def thrusters(self, on):
        self.thrust = on
        if (on):
            ship_thrust_sound.play()
        else:
            ship_thrust_sound.stop()
    
    def shoot(self):
        vector = angle_to_vector(degrees_to_radians(self.angle))

        pos = list(self.pos)
        pos[0] += vector[0] * self.radius
        pos[1] += -vector[1] * self.radius
        
        vel = list(self.vel)
        vel[0] += vector[0] * g.missile_initial_vel
        vel[1] += -vector[1] * g.missile_initial_vel
        missile_group.add(Sprite(pos, vel, 0, 0, missile_image, missile_info, missile_sound))

    def get_radius(self):
        return self.radius
    
    def get_position(self):
        return self.pos
    
# Sprite class
class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, vel, ang, ang_vel, image, info, sound = None):
        pygame.sprite.Sprite.__init__(self)
        
        self.pos = [pos[0],pos[1]]
        self.vel = [vel[0],vel[1]]
        self.angle = ang
        self.angle_vel = ang_vel
        #self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.lifespan = info.get_lifespan()
        self.animated = info.get_animated()
        self.age = 0
        if sound:
            sound.play()
        
        self.original_image = self.image = image
        self.rect = pos_to_rect(self.pos, self.image_size)
    
    def update(self):
        self.angle += self.angle_vel
  
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        
        self.pos[0] %= g.width
        self.pos[1] %= g.height
        
        if self.animated:
            index = (g.time % self.lifespan) // 1
            self.image = self.original_image.subsurface((index * self.image_size[0], 0), (self.image_size[0], self.image_size[1]))
        
        if (self.angle == 0):
            self.rect = pos_to_rect(self.pos, self.image_size)
        else:
            self.image = rotate_around_center(self.original_image, self.angle)
            w, h = self.image.get_size()
            self.rect = pos_to_rect(self.pos, (w, h))
        
        self.age += 1
    
    def is_old(self):
        return self.age > self.lifespan
    
    def collide(self, other):
        rtotal = self.get_radius() + other.get_radius()
        d = dist(self.get_position(), other.get_position())
        return d < rtotal
    
    def get_radius(self):
        return self.radius
    
    def get_position(self):
        return self.pos

def group_collide(group, s):
    rem = []
    
    # this works but there is heaps of empty space within the rects:(
    #dokill = True
    #rem = pygame.sprite.spritecollide(s, group, dokill)
    #for e in rem:
        #explosion_group.add(Sprite(e.get_position(), [0,0], 0, 0, explosion_image, explosion_info))

    for element in group:
        if element.collide(s):
            rem.append(element)
            explosion_group.add(Sprite(element.get_position(), [0,0], 0, 0, explosion_image, explosion_info))
            explosion_sound.play()
    
    #group.difference_update(rem)
    for r in rem:
        group.remove(r)
    
    return len(rem)

def group_group_collide(group1, group2):
    # pygame.sprite.groupcollide() works but there is too much empty space within the rects
    #dokill = True
    #return pygame.sprite.groupcollide(group1, group2, dokill, dokill)

    collisions_total = 0
    rem = []
    for element in group1:
        collisions = group_collide(group2, element)
        if collisions > 0:
            rem.append(element)
            collisions_total += collisions

    #group1.difference_update(rem)
    for r in rem:
        group1.remove(r)
    
    return collisions_total

def stop_game():
    global my_ship
    
    pygame.mixer.music.stop()
    
    g.playing = False
    g.dead = True
    
    my_ship = None
    
    rock_group.empty()
    missile_group.empty()
    explosion_group.empty()
    
def new_game():
    global my_ship
    
    pygame.mixer.music.play()
    
    g.playing = True
    g.dead = False
    
    g.lives = 1
    g.wave = 0
    
    ship_size = ship_info.get_size()
    my_ship = Ship( [(g.width/2)-(ship_size[0]/2), (g.height/2)-(ship_size[1]/2)], [0, 0], 90, ship_image, ship_info)
    
    new_wave()

def new_wave():
    
    g.wave += 1
    g.wave_rocks_left = 5 * g.wave
    
    rock_group.empty()
    missile_group.empty()
    
    end_wave_sound.play()

def click(pos):
    if g.playing:
        return

    center = [g.width / 2, g.height / 2]
    size = splash_info.get_size()
    
    inwidth = (center[0] - size[0] / 2) < pos[0] < (center[0] + size[0] / 2)
    inheight = (center[1] - size[1] / 2) < pos[1] < (center[1] + size[1] / 2)
    
    if inwidth and inheight:
        new_game()

def rock_spawner():
    
    if not g.playing:
        return
    
    if g.betweenwaves:
        # delay for 1 second
        if g.wavedelaystarttime == 0:
            g.wavedelaystarttime = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - g.wavedelaystarttime < 1000:
            return
        else:
            new_wave()
            g.betweenwaves = False
            g.wavedelaystarttime = 0
    
    if len(rock_group) >= g.wave_rocks_left:
        return
    
    minimum = -2
    maximum = 2
    angle = rand(minimum, maximum)
    angle_vel = rand(minimum, maximum)
    
    # vel will slowly increase
    minimum = -1 * g.wave
    maximum =  1 * g.wave

    pos = None
    while pos == None:
        if random.choice((0, 1)) == 0:
            pos = [random.choice((0, g.width)), rand(0, g.height)]
        else:
            pos = [rand(0, g.width), random.choice((0, g.height))]
        
        #dont spawn rocks too near the ship
        if dist(pos, my_ship.get_position()) < (my_ship.get_radius() * 4):
            pos = None
    
    if g.wave % 2 == 0:
        ship_pos = my_ship.get_position()
        x = ( (ship_pos[0] - pos[0]) / g.width ) * rand(0, maximum)
        y = ( (ship_pos[1] - pos[1]) / g.height ) * rand(0, maximum)
        vel = [x, y]
    else:
        vel = [rand(minimum, maximum), rand(minimum, maximum)]
    
    rock = Sprite(pos, vel, angle, angle_vel, asteroid_image, asteroid_info)
    rock_group.add(rock)

def key_down(k):
    if not g.playing:
        return

    if k == K_LEFT:
        my_ship.increment_angle_vel()
    elif k == K_RIGHT:
        my_ship.decrement_angle_vel()
    elif k == K_UP:
        my_ship.thrusters(True)
    elif k == K_SPACE:
        my_ship.shoot();

def key_up(k):
    if not g.playing:
        return

    if k == K_LEFT:
        my_ship.decrement_angle_vel()
    elif k == K_RIGHT:
        my_ship.increment_angle_vel()
    elif k == K_UP:
        my_ship.thrusters(False)

def set_up_splash():
    global splash_surface

    splash_surface = pygame.Surface(splash_info.get_size()).convert()
    #splash_surface.blit(splash_image, (0,0))
    font = pygame.font.SysFont("arial",24)
    text = font.render("This is Yet Another Space Shooter", g.text_antialias, g.text_color, g.text_bg_color)
    splash_surface.blit(text, (10, 20))
    
    text = font.render("Prepare to be awe struck...", g.text_antialias, g.text_color, g.text_bg_color)
    splash_surface.blit(text, (10, 80))
    
    font = pygame.font.SysFont("arial", 18)
    text = font.render("Use the left and right arrows to steer.", g.text_antialias, g.text_color, g.text_bg_color)
    splash_surface.blit(text, (10, 150))
    text = font.render("The up arrow fires your boosters.", g.text_antialias, g.text_color, g.text_bg_color)
    splash_surface.blit(text, (10, 180))
    text = font.render("The space bar fires your cannon.", g.text_antialias, g.text_color, g.text_bg_color)
    splash_surface.blit(text, (10, 210))
    text = font.render("Survive as many waves of meteors as you can.", g.text_antialias, g.text_color, g.text_bg_color)
    splash_surface.blit(text, (10, 240))
    text = font.render("Click here to begin.", g.text_antialias, g.text_color, g.text_bg_color)
    splash_surface.blit(text, (10, 270))

def draw_splash(screen):
    splash_size = splash_info.get_size()
    splash_dest_rect = pygame.Rect((g.width/2) - (splash_size[0]/2), (g.height/2) - (splash_size[1]/2), splash_size[0], splash_size[1])
    screen.blit(splash_surface, splash_dest_rect)

def draw_end_game_screen(screen):
    global splash_surface

    surface = pygame.Surface(splash_info.get_size()).convert()
    font = pygame.font.SysFont("arial",24)
    text = font.render("You survived "+str(g.wave - 1)+" waves", g.text_antialias, g.text_color, g.text_bg_color)
    surface.blit(text, (10, 20))
    
    text = font.render("Click here to try again", g.text_antialias, g.text_color, g.text_bg_color)
    surface.blit(text, (10, 80))

    splash_size = splash_info.get_size()
    dest_rect = pygame.Rect((g.width/2) - (splash_size[0]/2), (g.height/2) - (splash_size[1]/2), splash_size[0], splash_size[1])
    screen.blit(surface, dest_rect)

def main():

    font = pygame.font.SysFont("arial",16)
    
    bg = pygame.Surface(screen.get_size()).convert()
    bg.blit(nebula_image, screen.get_rect(), nebula_image.get_rect())
    
    set_up_splash()
    #stop_game()
    
    clock = pygame.time.Clock()
    
    # set up the rock spawner
    pygame.time.set_timer(USEREVENT + 1, 1000)

    while 1:
        clock.tick(60)
        g.time += 1

        #Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == USEREVENT + 1:
                rock_spawner()
            elif event.type == KEYDOWN:
                #if not playing:
                    #new_game()
                    #continue

                if event.key == K_ESCAPE:
                    return
                else:
                    key_down(event.key)
            elif event.type == KEYUP:
                key_up(event.key)
            elif event.type == MOUSEBUTTONDOWN:
                click(event.pos)
       
        #sprites_clicked = [sprite for sprite in all_my_sprites_list if sprite.rect.collidepoint(x, y)]

        screen.blit(bg, (0, 0))

        if not g.playing and not g.dead:
            draw_splash(screen)
        elif g.dead:
            draw_end_game_screen(screen)
        else:
            
            missile_group.update()
            rock_group.update()
            explosion_group.update()
            
            # remove old missiles
            old_missiles = [m for m in missile_group if m.is_old()]
            for m in old_missiles:
                missile_group.remove(m)
            
            #remove completed explosions
            old_explosions = [e for e in explosion_group if e.is_old()]
            for e in old_explosions:
                explosion_group.remove(e)
            
            if my_ship:
                my_ship.update()
                my_ship.draw()

            if group_collide(rock_group, my_ship) > 0:
                g.lives -= 1
                if g.lives == 0:
                    stop_game()
            
            g.wave_rocks_left -= group_group_collide(rock_group, missile_group)
            if (not g.betweenwaves and g.wave_rocks_left <= 0):
                g.betweenwaves = True
            
            text=font.render("Wave "+str(g.wave)+"  rocks left "+str(g.wave_rocks_left), g.text_antialias, g.text_color, g.text_bg_color)
            screen.blit(text,(640, 80))

            missile_group.draw(screen)
            rock_group.draw(screen)
            explosion_group.draw(screen)

        pygame.display.flip()

if __name__ == '__main__': main()

