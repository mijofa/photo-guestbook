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
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, Ellipse, Line, Fbo, ClearColor, ClearBuffers, Translate

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

<image_button>
    canvas:
        Clear

<blank_canvas>
    canvas.before:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            pos: self.pos
            size: self.size
""")

class blank_canvas(Widget):
    pass

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


class PaintWidget(Widget):
    def save_png(self, filename):
        ### Kivy 1.8.1 has an export_to_png function in the widget class. I'm not using 1.8.1 so I'm writing my own.
        ## Mostly copy-pasted from: https://github.com/kivy/kivy/blob/master/kivy/uix/widget.py (2014/06/16)
        if self.parent is not None:
            canvas_parent_index = self.parent.canvas.indexof(self.canvas)
            self.parent.canvas.remove(self.canvas)
        fbo = Fbo(size=self.size)
        with fbo:
            ClearColor(0, 0, 0, 0) # I changed this from 0,0,0,1 to 0,0,0,0 so that I could have a transparent background.
            ClearBuffers()
            Translate(-self.x, -self.y, 0)

        fbo.add(self.canvas)
        fbo.draw()
        try:
            fbo.texture.save(filename)
            success = True
            kivy.logger.Logger.debug("PaintWidget: Saved file %s" % filename)
        except Exception as e:
            success = False
            kivy.logger.Logger.error("PaintWidget: Can't save file: %s" % filename)
            kivy.logger.Logger.exception(e)
        finally:
            fbo.remove(self.canvas)

            if self.parent is not None:
                self.parent.canvas.insert(canvas_parent_index, self.canvas)

            return success
    def on_touch_down(self, touch):
        with self.canvas:
            Color(1,1,1)
            diameter = 4
            Ellipse(pos=(touch.x - diameter / 2, touch.y - diameter / 2), size=(diameter, diameter))
            touch.ud['line_outer'] = Line(points=(touch.x, touch.y), width=diameter)
            Color(0,0,0)
            touch.ud['line_inner'] = Line(points=touch.ud['line_outer'].points, width=diameter-1)
    def on_touch_move(self, touch):
        if touch.ud.has_key('line_outer'):
            touch.ud['line_outer'].points += [touch.x, touch.y]
        if touch.ud.has_key('line_inner'):
            touch.ud['line_inner'].points = touch.ud['line_outer'].points

class image_button(Button):
    def __init__(self, source = '', *args, **kwargs):
        super(image_button, self).__init__(*args, **kwargs)
        if type(source) == str:
            self.img = Image(source=source, allow_stretch=True)
        else:
            self.img = source
        self.add_widget(self.img)
        self.bind(size=self.update_img, pos=self.update_img)
    def update_img(self, instance, value):
        instance.img.size = instance.size
        instance.img.pos = instance.pos
    def set_image(self, filename):
        self.img.source = filename

class PhotoStrip(ScrollView):
    def set_path(self, path):
        self.path = path
        self.image0.set_image(os.path.join(path, '0.jpg'))
        self.image1.set_image(os.path.join(path, '1.jpg'))
        self.image2.set_image(os.path.join(path, '2.jpg'))
    def clear_path(self, *args):
        self.path = None
        source = ''
        self.image0.set_image(source)
        self.image1.set_image(source)
        self.image2.set_image(source)
    def __init__(self, *args, **kwargs):
        super(PhotoStrip, self).__init__(size_hint=(1,1), pos_hint={'center_x': 0.5, 'center_y': 0.5}, do_scroll_x=False, *args, **kwargs)
        self.strip = Image(source='photos-strip.png', allow_stretch=True, size_hint_y=2)
        self.add_widget(self.strip)

        self.image0 = image_button()
        self.image0.bind(on_press=self.press_btn, on_release=self.release_btn)
        self.strip.add_widget(self.image0)
        self.image1 = image_button()
        self.image1.bind(on_press=self.press_btn, on_release=self.release_btn)
        self.strip.add_widget(self.image1)
        self.image2 = image_button()
        self.image2.bind(on_press=self.press_btn, on_release=self.release_btn)
        self.strip.add_widget(self.image2)
        self.image3 = image_button(source=blank_canvas())
        self.image3.bind(on_press=self.press_btn, on_release=self.release_btn)
        self.strip.add_widget(self.image3)

        self.strip.bind(size=self.update_buttons,pos=self.update_buttons)
    def press_btn(self, *args):
        kivy.logger.Logger.debug('PhotoStrip: pressed an image button: '+str(args))
    def release_btn(self, *args):
        kivy.logger.Logger.debug('PhotoStrip: released an image button: '+str(args))
    def update_buttons(self, instance, value):
        spacing = 20
        padding = 25
        offset = padding
        for img in [self.image0, self.image1, self.image2, self.image3]:
            img.size = (instance.norm_image_size[0]/60)*43, (instance.norm_image_size[1]-((spacing*3)+(padding*2)))/4
            img.center_x = instance.center_x
            img.center_y = instance.top-((img.height/2)+offset)
            offset += img.height+spacing

class Main(App):
    def pressed_back(self, *args):
        if self.screen_manager.current == 'photostrip':
            self.screen_manager.transition.direction = 'right'
            self.screen_manager.current = 'chooser'
        elif self.screen_manager.current == 'chooser':
            if os.path.samefile(self.chooser.path, PHOTOS_PATH):
                return
            self.chooser.rootpath = os.path.normpath(os.path.join(self.chooser.path, os.path.pardir))
            self.chooser.path = self.chooser.rootpath
        return True
    def pressed_home(self, *args):
        if self.screen_manager.current == 'photostrip':
            pass
#            self.painter.save_png('/sdcard/DCIM/tmp/blah.png')
        elif self.screen_manager.current == 'chooser':
            self.chooser._show_progress()
            self.chooser._trigger_update()
        return True
    def pressed_win(self, *args):
        pass
    def select_folder(self, chooser):
        self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'photostrip'
        self.photostrip.set_path(chooser.current_entry.path)
    def enter_chooser(self, *args):
        self.home_btn.text = 'Refresh'
        self.back_btn.text = '<-'
    def enter_strip(self, *args):
        self.home_btn.text = ''
        self.back_btn.text = '<-'
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

        ## Photo strip
        photostrip_screen = Screen(name='photostrip')
        photostrip_screen.bind(on_enter=self.enter_strip)
        self.photostrip = PhotoStrip()
        photostrip_screen.bind(on_leave=self.photostrip.clear_path)
        photostrip_screen.add_widget(self.photostrip)
#        self.painter = PaintWidget()
#        viewer_screen.bind(on_leave=lambda args: self.painter.canvas.clear())
#        viewer_screen.add_widget(self.painter)
        self.screen_manager.add_widget(photostrip_screen)

        return root

Main().run()
