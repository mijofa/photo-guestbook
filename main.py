PHOTOS_PATH = '/mnt/tmp'

import os
import sys
import time

import kivy
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.core.window import Window

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
""")

screen_manager = ScreenManager()

class FileChooserGalleryView(FileChooserIconView):
    thumbsize = NumericProperty(dp(256))
    _ENTRY_TEMPLATE = 'FileGalleryEntry'
    def __init__(self, *args, **kwargs):
        super(FileChooserGalleryView, self).__init__(*args, **kwargs)
        self.bind(on_submit=self.submit)

        kbd = Window.request_keyboard(None, self)
        kbd.bind(on_key_down=self.go_back)
    def go_back(self, *args):
        if screen_manager.current == 'chooser':
            if self.path == PHOTOS_PATH:
                return False # Let other parts of Kivy handle the keypress, if the key was Esc Kivy will quit here.
            else:
                # This should theoretically never trigger since I'm only working in one directory, but I'll leave it here anyway.
                self.rootpath = os.path.normpath(os.path.join(self.path, os.path.pardir))
                self.path = self.rootpath
        else:
            screen_manager.current = 'chooser'
        return True
    def open_entry(self, entry):
        screen_manager.current = 'viewer'
        screen_manager.current_screen.set_image(entry.path)

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
    def submit(self, entry, selection, touch):
        screen_manager.current = 'viewer'
        screen_manager.current_screen.set_image(selection[0])

class Chooser(Screen):
    def __init__(self, *args, **kwargs):
        super(Chooser, self).__init__(*args, **kwargs)
        self.add_widget(FileChooserGalleryView(rootpath=PHOTOS_PATH))

class blank_canvas(Widget):
    pass

class Viewer(Screen):
    def set_image(self, path):
        self.image0.source = os.path.join(path, '0.jpg')
        self.image1.source = os.path.join(path, '1.jpg')
        self.image2.source = os.path.join(path, '2.jpg')
    def touched(self, screen, event):
        screen_manager.current = 'chooser'
    def __init__(self, *args, **kwargs):
        super(Viewer, self).__init__(*args, **kwargs)
        self.bind(on_touch_down=self.touched)
        self.image0 = Image(source='atlas://data/images/defaulttheme/filechooser_file',size_hint=[0.5,0.5],pos_hint={'top': 1, 'left': 1})
        self.add_widget(self.image0)
        self.image1 = Image(source='atlas://data/images/defaulttheme/filechooser_file',size_hint=[0.5,0.5],pos_hint={'top': 1, 'right': 1})
        self.add_widget(self.image1)
        self.image2 = Image(source='atlas://data/images/defaulttheme/filechooser_file',size_hint=[0.5,0.5],pos_hint={'bottom': 1, 'left': 1})
        self.add_widget(self.image2)
        self.image3 = blank_canvas(size_hint=[0.5,0.5],pos_hint={'bottom': 1, 'right': 1})
        self.add_widget(self.image3)

class Main(App):
    def build(self):
        screen_manager.add_widget(Chooser(name='chooser'))
        screen_manager.add_widget(Viewer(name='viewer'))
        screen_manager.current = 'chooser'
        return screen_manager

Main().run()
