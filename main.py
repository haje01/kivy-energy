import time
import random

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, ObjectProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.vector import Vector
from kivy.core.image import Image as CoreImage
from kivy.graphics import Rectangle
from kivy.animation import Animation
from kivy.core.audio import SoundLoader

SOUND = True

if SOUND:
    snd_start = SoundLoader.load('sounds/appear.wav')
    snd_bgm = SoundLoader.load('sounds/alien.wav')
    snd_hit = SoundLoader.load('sounds/torpedo.wav')
    snd_explode = SoundLoader.load('sounds/bomb.wav')


UPDATE_TERM = 0.03

__version__ = '0.0.1'


class ScrollingBackground(Widget):
    text_rectangle = ObjectProperty()
    speed = NumericProperty(0.5)
    x_offset = NumericProperty(0)

    def __init__(self, **kwargs):
        super(ScrollingBackground, self).__init__(**kwargs)
        texture = CoreImage('images/background.png').texture
        texture.wrap = 'repeat'

        with self.canvas:
            self.text_rectangle = Rectangle(
                texture=texture,
                size=self.size,
                pos=self.pos,
            )
        Clock.schedule_interval(self.update, UPDATE_TERM)

    def update(self, delta):
        self.text_rectangle.size = self.size
        t = Clock.get_boottime()
        y_incr = t * -1 * self.speed
        x_scale = self.size[0] / float(self.text_rectangle.texture.size[0])
        y_scale = self.size[1] / float(self.text_rectangle.texture.size[1])
        self.text_rectangle.tex_coords = [
            self.x_offset, y_incr + y_scale,
            self.x_offset + x_scale, y_incr + y_scale,
            self.x_offset + x_scale, y_incr,
            self.x_offset, y_incr
        ]


class Enemy(FloatLayout):
    score = NumericProperty(0)
    velocity = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super(Enemy, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, UPDATE_TERM)

    def update(self, delta):
        app = App.get_running_app()
        pos = Vector(self.pos)
        self.pos = pos + Vector(self.direction) * delta
        self.score = min(5, int(pos.distance(app.root.center) / 50) + 1)

        if app.ship:
            if (
                (Vector(self.center) - app.root.center).length()
                <
                (self.width + app.ship.width) / 2
            ):
                if app.ship.growth > 0:
                    Clock.unschedule(self.update)
                    self.parent.remove_widget(self)
                    app.score += self.score
                    if SOUND:
                        snd_hit.play()
                    anim = Animation(
                        font_size=dp(140),
                        duration=0.3,
                    ) + Animation(
                        font_size=dp(80),
                        duration=1.0,
                        t="out_bounce"
                    )
                    anim.start(app.root.score_label)
                    print("CURRENT SCORE: %s" % app.score)
                else:
                    if SOUND:
                        snd_explode.play()
                    app.root.remove_widget(app.ship)
                    app.ship = ""
                    print("GAME OVER")
                    print("FINAL SCORE: %s" % app.score)


class Ship(Widget):
    growth = NumericProperty(0)
    min_size = NumericProperty(dp(20))
    energy = NumericProperty(1.0)
    energy_growth = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Ship, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, UPDATE_TERM)
        App.get_running_app().ship = self
        self.last_fps = 0

    def on_touch_down(self, event):
        self.energy_growth = -0.05
        self.growth = dp(8)

    def on_touch_up(self, event):
        self.energy_growth = 0.03
        self.growth = dp(-16)

    def update(self, delta):
        self.width += self.growth * delta
        self.energy += self.energy_growth * delta
        t = time.time()
        if t - self.last_fps > 1:
            self.last_fps = t

        if self.energy <= 0 and self.growth > 0:
            self.energy = 0
            self.growth = 0
            self.energy_growth = 0

        if self.width <= self.min_size:
            self.width = self.min_size
            self.growth = 0
            self.energy_growth = 0.05

        if self.energy >= 1:
            self.energy = 1
            self.energy_growth = 0


class EnergyApp(App):
    enemy_rate = NumericProperty(3)
    score = NumericProperty(0)
    ship = ObjectProperty()

    def __init__(self):
        super(EnergyApp, self).__init__()
        if SOUND:
            snd_start.play()
        Clock.schedule_once(self.play_bgm, 6)
        Clock.schedule_once(self.print_fps, 1)
        self.schedule_next_enemy()

    def print_fps(self, delta):
        print Clock.get_fps()
        Clock.schedule_once(self.print_fps, 1)

    def play_bgm(self, delta):
        if SOUND:
            snd_bgm.play()
        Clock.schedule_once(self.play_bgm, 30)

    def schedule_next_enemy(self):
        Clock.schedule_once(self.make_enemy, random.random() * self.enemy_rate)

    def make_enemy(self, delta):
        pos = Vector(self.root.center).rotate(random.randint(0, 360))
        direction = (-1 * pos).normalize() * dp(50)
        enemy = Enemy()
        enemy.pos = pos + self.root.center - Vector(enemy.size) / 2
        enemy.direction = direction
        self.root.add_widget(enemy)
        self.schedule_next_enemy()


if __name__ == "__main__":
    app = EnergyApp()
    app.run()
