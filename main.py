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
    def __init__(self, *args):
        super(blank_canvas, self).__init__(*args)
        self.bind(size=self.draw_lines, pos=self.draw_lines)
    def draw_lines(self, *args):
        line_dist = 40
        line_offset = 0
        num_lines = (self.height/line_dist)
        self.canvas.clear()
        with self.canvas:
            for i in xrange(1,int(num_lines/2)):
                line_offset += line_dist
                Color(0,0,0,1)
                Line(width=1, points=[self.pos[0], self.pos[1]+line_offset, self.pos[0]+self.width, self.pos[1]+line_offset])
                line_offset += line_dist
                Color(0.5,0.5,1,0.5)
                Line(width=1, points=[self.pos[0], self.pos[1]+line_offset, self.pos[0]+self.width, self.pos[1]+line_offset])
            line_offset += line_dist
            Color(0,0,0,1)
            Line(width=1, points=[self.pos[0], self.pos[1]+line_offset, self.pos[0]+self.width, self.pos[1]+line_offset])

            Color(1,0,0,0.25)
            Line(width=1.5, points=[self.pos[0]+(line_dist*1.5), self.pos[1]+self.height, self.pos[0]+(line_dist*1.5), self.pos[1]])

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
            kivy.logger.Logger.info("PaintWidget: Saved file %s" % filename)
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
            Ellipse(pos=(touch.x-(diameter/2), touch.y-(diameter/2)), size=(diameter, diameter))
            touch.ud['line_outer'] = Line(points=(touch.x, touch.y), width=diameter)
            Color(0,0,0)
            Ellipse(pos=(touch.x-((diameter-1)/2), touch.y-((diameter-1)/2)), size=(diameter-1, diameter-1))
            touch.ud['line_inner'] = Line(points=touch.ud['line_outer'].points, width=diameter-1)
    def on_touch_move(self, touch):
        if touch.ud.has_key('line_outer'):
            touch.ud['line_outer'].points += [touch.x, touch.y]
        if touch.ud.has_key('line_inner'):
            touch.ud['line_inner'].points = touch.ud['line_outer'].points
    def clear(self):
        self.canvas.clear()

class PaintScreen(Screen):
    def update_rect(self, instance, value):
        instance.bg_col.size = instance.size
        instance.bg_col.pos = instance.pos
    def __init__(self, *args, **kwargs):
        super(PaintScreen, self).__init__(*args, **kwargs)
        self.source = ''
        with self.canvas.before:
            Color(0,0,0,1)
            self.bg_col = Rectangle()

        self.blank = blank_canvas()
        self.blank.source = self.source
        self.add_widget(self.blank)
        self.blank.opacity = 1

        self.img = Image(source=self.source, allow_stretch=True)
        self.add_widget(self.img)

        self.painter = PaintWidget()
        self.add_widget(self.painter)

        self.bind(size=self.update_rect, pos=self.update_rect)
    def set_image(self, bg_filename, *args):
        self.source = bg_filename
        self.img.source = self.source

        if os.path.exists(self.source):
            self.blank.opacity = 0
            self.img.opacity = 1
        else:
            self.blank.opacity = 1
            self.img.opacity = 0

class image_button(Button):
    def __init__(self, source = '', *args, **kwargs):
        self.source = source
        super(image_button, self).__init__(*args, **kwargs)

        self.blank = blank_canvas()
        self.blank.source = self.source
        self.add_widget(self.blank)

        self.img = Image(source=self.source, allow_stretch=True)
        self.add_widget(self.img)

        if os.path.exists(self.source):
            self.blank.opacity = 0
            self.img.opacity = 1
        else:
            self.blank.opacity = 1
            self.img.opacity = 0

        self.bind(size=self.update_img, pos=self.update_img)
    def update_img(self, instance, value):
        instance.blank.size = instance.size
        instance.blank.pos = instance.pos
        instance.img.size = instance.size
        instance.img.pos = instance.pos
    def set_image(self, filename):
        self.source = filename
        self.img.source = self.source
        if os.path.exists(self.source):
            self.blank.opacity = 0
            self.img.opacity = 1
        else:
            self.blank.opacity = 1
            self.img.opacity = 0

class PhotoStrip(ScrollView):
    def on_press(self, filename):
        pass
    def on_release(self, filename):
        pass
    def __init__(self, *args, **kwargs):
        super(PhotoStrip, self).__init__(size_hint=(1,1), pos_hint={'center_x': 0.5, 'center_y': 0.5}, do_scroll_x=False, *args, **kwargs)
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        self.strip = Image(source='photos-strip.png', allow_stretch=True, size_hint_y=1.8)
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
        self.image3 = image_button()
        self.image3.bind(on_press=self.press_btn, on_release=self.release_btn)
        self.strip.add_widget(self.image3)

        self.strip.bind(size=self.update_buttons,pos=self.update_buttons)
    def set_path(self, path):
        self.path = path
        self.image0.set_image(os.path.join(path, '0.jpg'))
        self.image1.set_image(os.path.join(path, '1.jpg'))
        self.image2.set_image(os.path.join(path, '2.jpg'))
        self.image3.set_image(os.path.join(path, 'blank'))
    def clear_path(self, *args):
        self.scroll_y = 1
        if 'effect_y' in dir(self): # Kivy 1.6.0 doesn't have effect_y
            self.effect_y.value = self.effect_y.min # This is to work around a bug with the ScrollView (https://github.com/kivy/kivy/issues/2038)
        self.path = None
        source = ''
        self.image0.set_image(source)
        self.image1.set_image(source)
        self.image2.set_image(source)
    def press_btn(self, btn):
        self.dispatch('on_press', btn.source)
    def release_btn(self, btn):
        self.dispatch('on_release', btn.source)
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
    def pressed_win(self, *args):
        if self.screen_manager.current == 'painter':
            savedir = os.path.normpath(self.paint_screen.painter.source+'.overlays'+os.path.sep)
            if not os.path.isdir(savedir):
                os.mkdir(savedir)
            index = 0
            filename = '%02d.png'
            dircontents = os.listdir(savedir)
            while filename % index in dircontents:
                index += 1
            self.paint_screen.painter.save_png(os.path.join(savedir, filename % index))
        return False # I'm returning false here so that the button still triggers the next on_release event
    def pressed_home(self, *args):
        if self.screen_manager.current == 'painter':
            self.goto_screen('photostrip', 'right')
        elif self.screen_manager.current == 'chooser':
            self.chooser._show_progress()
            self.chooser._trigger_update()
        return False # I'm returning false here so that the button still triggers the next on_release event
    def pressed_back(self, *args):
        if self.screen_manager.current == 'photostrip':
            self.goto_screen('chooser', 'right')
        elif self.screen_manager.current == 'chooser':
            if os.path.samefile(self.chooser.path, PHOTOS_PATH):
                return False # I'm returning false here so that the button still triggers the next on_release event
            self.chooser.rootpath = os.path.normpath(os.path.join(self.chooser.path, os.path.pardir))
            self.chooser.path = self.chooser.rootpath
        return False # I'm returning false here so that the button still triggers the next on_release event
    def goto_screen(self, screen_name, direction):
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = screen_name
    def select_folder(self, chooser):
        self.goto_screen('photostrip', 'left')
        self.photostrip.set_path(chooser.current_entry.path)
    def enter_chooser(self, *args):
        self.win_btn.opacity = 0
        self.home_btn.opacity = 1
        self.home_btn.background_normal = 'ic_action_refresh.png'
        self.home_btn.background_down = self.home_btn.background_normal
        self.back_btn.opacity = 1
        self.back_btn.background_normal = 'ic_sysbar_back.png'
        self.back_btn.background_down = self.back_btn.background_normal
        self.photostrip.clear_path()
    def enter_strip(self, *args):
        self.win_btn.opacity = 0
        self.home_btn.opacity = 0
        self.back_btn.opacity = 1
        self.back_btn.background_normal = 'ic_sysbar_back.png'
        self.back_btn.background_down = self.back_btn.background_normal
    def enter_painter(self, *args):
        self.win_btn.opacity = 1
        self.win_btn.background_normal = 'ic_action_save.png'
#        self.win_btn.background_normal = 'ic_action_sd_storage.png'
        self.win_btn.background_down = self.win_btn.background_normal
        self.home_btn.opacity = 1
        self.home_btn.background_normal = 'ic_action_discard.png'
        self.home_btn.background_down = self.home_btn.background_normal
        self.back_btn.opacity = 0
    def update_size(self, root, value):
        self.screen_manager.size = (root.width-96, root.height)
    def build(self):
        root = FloatLayout()
        self.screen_manager = ScreenManager(transition=SlideTransition(),size_hint=[None,None], pos_hint={'left': 1})
        root.bind(size=self.update_size)
        root.add_widget(self.screen_manager)

        def rend_circle(btn):
            with btn.canvas:
                Color(1,1,1,0.25)
                btn.hl = Ellipse(pos=btn.pos, size=btn.size)
        def derend_circle(btn):
            btn.canvas.remove(btn.hl)
        ## Buttons.
        ## These are meant to work like the Android navbar would, and I have named them as such.
        # I'd like to have 'back', 'refresh', 'save', & 'cancel' buttons. I don't know how well I can make this work on the navbar though.
        self.win_btn = Button(text='', size_hint=[None,None],size=[96,96],height=96,pos_hint={'right': 1, 'center_y': 0.8})
        self.win_btn.bind(on_press=rend_circle)
        self.win_btn.bind(on_release=derend_circle)
        self.win_btn.bind(on_release=self.pressed_win)

        self.home_btn = Button(text='', size_hint=[None,None],size=[96,96],pos_hint={'right': 1, 'center_y': 0.5})
        self.home_btn.bind(on_press=rend_circle)
        self.home_btn.bind(on_release=derend_circle)
        self.home_btn.bind(on_release=self.pressed_home)

        self.back_btn = Button(text='', size_hint=[None,None],size=[96,96],pos_hint={'right': 1, 'center_y': 0.2})
        self.back_btn.bind(on_press=rend_circle)
        self.back_btn.bind(on_release=derend_circle)
        self.back_btn.bind(on_release=self.pressed_back)

        root.add_widget(self.win_btn)
        root.add_widget(self.home_btn)
        root.add_widget(self.back_btn)

        ## FileChooser
        chooser_screen = Screen(name='chooser')
        chooser_screen.bind(on_enter=self.enter_chooser)
        self.chooser = FileChooserGalleryView(rootpath=PHOTOS_PATH)
        self.chooser.bind(on_select_folder=self.select_folder)
        chooser_screen.add_widget(self.chooser)
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
        photostrip_screen.add_widget(self.photostrip)

        self.paint_screen = PaintScreen(name='painter')
        self.paint_screen.bind(on_enter=self.enter_painter)
        self.paint_screen.bind(on_leave=lambda src: self.paint_screen.painter.clear())
        self.photostrip.bind(
                on_press=lambda src, fn: self.paint_screen.set_image(fn),
                on_release=lambda src, fn: self.goto_screen('painter', 'left'),
        )

        self.screen_manager.add_widget(chooser_screen)
        self.screen_manager.add_widget(photostrip_screen)
        self.screen_manager.add_widget(self.paint_screen)

        return root

Main().run()
