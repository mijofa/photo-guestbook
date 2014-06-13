PHOTOS_PATH = '/mnt/tmp'

import os
import sys
import time

import kivy
if kivy.platform == 'android':
    PHOTOS_PATH = '/sdcard/DCIM'
from kivy.metrics import dp
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, Ellipse, Line

Builder.load_string("""
[FileGalleryEntry@Widget]:
    locked: False
    path: ctx.path
    selected: self.path in ctx.controller().selection
    size_hint: None, None

    on_touch_down: self.collide_point(*args[1].pos) and ctx.controller().entry_touched(self, args[1])
    on_touch_up: self.collide_point(*args[1].pos) and ctx.controller().entry_released(self, args[1])
    size: ctx.controller().thumbsize+dp(52), ctx.controller().thumbsize+dp(52)

    canvas:
        Color:
            rgba: 1, 1, 1, 1 if self.selected else 0
        BorderImage:
            border: 8, 8, 8, 8
            pos: root.pos
            size: root.size
            source: 'atlas://data/images/defaulttheme/filechooser_selected'

    Image:
        size: ctx.controller().thumbsize,ctx.controller().thumbsize
        source: ctx.controller().get_image(ctx)
        pos: root.x + dp(24), root.y + dp(40)
    Label:
        text: ctx.name
        text_size: (root.width, self.height)
        halign: 'center'
        shorten: True
        size: ctx.controller().thumbsize, '16dp'
        pos: root.center_x - self.width /2, root.y + dp(16)

    Label:
        text: '{}'.format(ctx.controller().get_time(ctx))
        font_size: '11sp'
        color: .8, .8, .8, 1
        size: '100dp', '16sp'
        pos: root.pos
        pos: root.center_x - self.width /2, root.y
        halign: 'center'
<blank_canvas>
    canvas.before:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            pos: self.pos
            size: self.size
<red_canvas>
    canvas.before:
        Color:
            rgba: 1,0,0,1
        Rectangle:
            pos: self.pos
            size: self.size
<green_canvas>
    canvas.before:
        Color:
            rgba: 0,1,0,1
        Rectangle:
            pos: self.pos
            size: self.size
<blue_canvas>
    canvas.before:
        Color:
            rgba: 0,0,1,1
        Rectangle:
            pos: self.pos
            size: self.size
""")


class FileChooserGalleryView(FileChooserIconView):
    thumbsize = dp(119)
    _ENTRY_TEMPLATE = 'FileGalleryEntry'
    def __init__(self, *args, **kwargs):
        super(FileChooserGalleryView, self).__init__(*args, **kwargs)
        self.register_event_type('on_select_folder')

    def open_entry(self, entry):
        self.current_entry = entry
        self.dispatch('on_select_folder')
    def on_select_folder(self):
        pass

    def get_image(self, ctx):
        if ctx.path == '../':
            return 'atlas://data/images/defaulttheme/filechooser_folder'
        elif ctx.isdir:
            img_file = os.path.join(ctx.path, '0.jpg')
            if os.path.isfile(img_file):
                return img_file
            else:
                return 'atlas://data/images/defaulttheme/filechooser_folder'
        elif ctx.path.endswith('.jpg'):
            return ctx.path
        else:
            return 'atlas://data/images/defaulttheme/filechooser_%s' % ('folder' if ctx.isdir else 'file')
    def get_time(self, ctx):
        return time.ctime(os.path.getmtime(ctx.path))

class red_canvas(Widget):
    pass
class green_canvas(Widget):
    pass
class blue_canvas(Widget):
    pass
class blank_canvas(Widget):
    pass


class PaintWidget(Widget):
    def on_touch_down(self, touch):
        with self.canvas:
            Color(1,1,1, mode='rgb')
            d = 4
            Ellipse(pos=(touch.x - d / 2, touch.y - d / 2), size=(d, d))
            touch.ud['line'] = Line(points=(touch.x, touch.y), width=d)
            Color(0,0,0, mode='rgb')
            touch.ud['line_inner'] = Line(points=touch.ud['line'].points, width=d-1)
    def on_touch_move(self, touch):
        touch.ud['line'].points += [touch.x, touch.y]
        touch.ud['line_inner'].points = touch.ud['line'].points

class Viewer(GridLayout):
    def set_image(self, path = None):
        if type(path) != str and type(path) != unicode:
            source = 'atlas://data/images/defaulttheme/filechooser_file'
            self.image0.source = source
            self.image1.source = source
            self.image2.source = source
            return
 #       self.image0.source = os.path.join(path, '0.jpg')
  #      self.image1.source = os.path.join(path, '1.jpg')
   #     self.image2.source = os.path.join(path, '2.jpg')
    def __init__(self, *args, **kwargs):
        super(Viewer, self).__init__(rows=2, cols=2, padding=8, spacing=16, *args, **kwargs)
        self.image0 = red_canvas()
#        self.image0 = Image(source='atlas://data/images/defaulttheme/filechooser_file')
        self.add_widget(self.image0)
        self.image1 = green_canvas()
#        self.image1 = Image(source='atlas://data/images/defaulttheme/filechooser_file')
        self.add_widget(self.image1)
        self.image2 = blue_canvas()
#        self.image2 = Image(source='atlas://data/images/defaulttheme/filechooser_file')
        self.add_widget(self.image2)
        self.image3 = blank_canvas()
        self.add_widget(self.image3)

class Main(App):
    def pressed_back(self, *args):
        if self.screen_manager.current == 'viewer':
            self.screen_manager.transition.direction = 'right'
            self.screen_manager.current = 'chooser'
            return True
        elif self.screen_manager.current == 'chooser':
            if os.path.samefile(self.chooser.path, PHOTOS_PATH):
                return False # Let other parts of Kivy handle the keypress, if the key was Esc Kivy will quit here.
            self.chooser.rootpath = os.path.normpath(os.path.join(self.chooser.path, os.path.pardir))
            self.chooser.path = self.chooser.rootpath
            return True
        return False
    def pressed_home(self, *args):
        if self.screen_manager.current == 'viewer':
            self.painter.texture.save('/tmp/blah.jpg')
        elif self.screen_manager.current == 'chooser':
            self.chooser._trigger_update()
    def pressed_win(self, *args):
        pass
    def select_folder(self, chooser):
        self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'viewer'
        self.viewer.set_image(chooser.current_entry.path)
    def enter_chooser(self, *args):
        self.home_btn.text = 'Refresh'
        self.back_btn.text = 'Back'
    def enter_viewer(self, *args):
        self.home_btn.text = 'Save'
        self.back_btn.text = 'Cancel'
    def build(self):
        root = FloatLayout()
        self.screen_manager = ScreenManager(transition=SlideTransition(), size_hint=[0.925,1],pos_hint={'left': 1})
        root.add_widget(self.screen_manager)

        ## Buttons.
        ## These are meant to work like the Android navbar would, and I have named them as such.
        # I'd like to have 'back', 'refresh', 'save', & 'cancel' buttons. I don't know how well I can make this work on the navbar though.
        self.win_btn = Button(text='', size_hint=[0.075,0.1],pos_hint={'right': 1, 'center_y': 0.8})
        self.win_btn.bind(on_press=self.pressed_win)
        root.add_widget(self.win_btn)

        self.home_btn = Button(text='', size_hint=[0.075,0.1],pos_hint={'right': 1, 'center_y': 0.5})
        self.home_btn.bind(on_press=self.pressed_home)
        root.add_widget(self.home_btn)

        self.back_btn = Button(text='', size_hint=[0.075,0.1],pos_hint={'right': 1, 'center_y': 0.2})
        self.back_btn.bind(on_press=self.pressed_back)
        root.add_widget(self.back_btn)

        ## FileChooser
        chooser_screen = Screen(name='chooser')
        chooser_screen.bind(on_enter=self.enter_chooser)
        self.chooser = FileChooserGalleryView(rootpath=PHOTOS_PATH)
        self.chooser.bind(on_select_folder=self.select_folder)
        chooser_screen.add_widget(self.chooser)
        self.screen_manager.add_widget(chooser_screen)

        def update_rect(instance, value):
            instance.bg.pos = instance.pos
            instance.bg.size = instance.size
        self.screen_manager.bind(size=update_rect,pos=update_rect)
        with self.screen_manager.canvas.before:
            self.screen_manager.bg = Rectangle(source='background.png')

        ## Image viewer
        viewer_screen = Screen(name='viewer')
        viewer_screen.bind(on_enter=self.enter_viewer)
        self.viewer = Viewer()
        viewer_screen.bind(on_leave=self.viewer.set_image)
        viewer_screen.add_widget(self.viewer)
        self.painter = PaintWidget()
        viewer_screen.add_widget(self.painter)
        self.screen_manager.add_widget(viewer_screen)

        return root

Main().run()
