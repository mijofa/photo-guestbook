#!/usr/bin/python
PHOTOS_PATH = '/mnt/tmp'

import os
import time

import kivy
if kivy.platform() == 'android':
    PHOTOS_PATH = '/sdcard/DCIM'
    kivy.logger.Logger.debug(str(kivy.platform()))
from kivy.metrics import dp
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color, Ellipse, Line, Fbo, ClearColor, ClearBuffers, Translate
from kivy.clock import Clock
from kivy.uix.widget import WidgetException

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
    def __init__(self, line_width=40, *args):
        super(blank_canvas, self).__init__(*args)
        self.line_width=line_width
        self.bind(size=self.draw_lines, pos=self.draw_lines)
    def draw_lines(self, *args):
        line_offset = 0
        num_lines = (self.height/self.line_width)
        self.canvas.clear()
        with self.canvas:
            for i in xrange(1,int(num_lines/2)):
                line_offset += self.line_width
                Color(0,0,0,0.75)
                Line(width=1, points=[self.pos[0], self.pos[1]+line_offset, self.pos[0]+self.width, self.pos[1]+line_offset])
                line_offset += self.line_width
                Color(0.5,0.5,1,0.5)
                Line(width=1, points=[self.pos[0], self.pos[1]+line_offset, self.pos[0]+self.width, self.pos[1]+line_offset])
            line_offset += self.line_width
            Color(0,0,0,0.75)
            Line(width=1, points=[self.pos[0], self.pos[1]+line_offset, self.pos[0]+self.width, self.pos[1]+line_offset])

            Color(1,0,0,0.25)
            Line(width=1.5, points=[self.pos[0]+(self.line_width*1.5), self.pos[1]+self.height, self.pos[0]+(self.line_width*1.5), self.pos[1]])

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

class PaintWidget(Image):
    do_drawing = True
    done_draw = False
    def save_png(self, filename):
        if not self.done_draw: # Don't save a blank drawing.
            return False
        self.do_drawing = False
        ### Kivy 1.8.1 has an export_to_png function in the widget class. I'm not using 1.8.1 so I'm writing my own.
        ## Mostly copy-pasted from: https://github.com/kivy/kivy/blob/master/kivy/uix/widget.py (2014/06/16)
        if self.parent is not None:
            canvas_parent_index = self.parent.canvas.indexof(self.canvas)
            self.parent.canvas.remove(self.canvas)
        fbo = Fbo(size=self.size_const)
        with fbo:
            ClearColor(0, 0, 0, 0) # I changed this from 0,0,0,1 to 0,0,0,0 so that I could have a transparent background.
            ClearBuffers()
            Translate(self.draw_const[0], -self.draw_const[2], 0)

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

            self.do_drawing = True
            return success
    def on_touch_down(self, touch):
        if self.do_drawing:
            center = self.size[0]/2, self.size[1]/2
            const_halved = self.size_const[0]/2, self.size_const[1]/2
            self.draw_const = [center[0]-const_halved[0], center[0]+const_halved[0], center[1]-const_halved[1], center[1]+const_halved[1]]
            if touch.x > self.draw_const[0] and touch.x < self.draw_const[1] and touch.y > self.draw_const[2] and touch.y < self.draw_const[3]:
                self.done_draw = True
                with self.canvas:
                    Color(1,1,1)
                    diameter = 4
                    Ellipse(pos=(touch.x-(diameter/2), touch.y-(diameter/2)), size=(diameter, diameter))
                    touch.ud['line_outer'] = Line(points=(touch.x, touch.y), width=diameter)
                    Color(0,0,0)
                    Ellipse(pos=(touch.x-((diameter-1)/2), touch.y-((diameter-1)/2)), size=(diameter-1, diameter-1))
                    touch.ud['line_inner'] = Line(points=touch.ud['line_outer'].points, width=diameter-1)
    def on_touch_move(self, touch):
        if touch.x < self.draw_const[0]:
            touch.x = self.draw_const[0]
        if touch.x > self.draw_const[1]:
            touch.x = self.draw_const[1]
        if touch.y < self.draw_const[2]:
            touch.y = self.draw_const[2]
        if touch.y > self.draw_const[3]:
            touch.y = self.draw_const[3]
        if touch.ud.has_key('line_outer'):
            touch.ud['line_outer'].points += [touch.x, touch.y]
        if touch.ud.has_key('line_inner'):
            touch.ud['line_inner'].points = touch.ud['line_outer'].points
    def clear(self):
        self.canvas.clear()
        self.do_drawing = True
        self.done_draw = False

class ImageCanvas(Widget):
    def update_rect(self, instance, value):
        self.img.size = self.size
        self.img.pos = self.pos
        self.blank.size = self.size
        self.blank.pos = self.pos
        instance.label.center_x = instance.center_x # I should need to set the y pos of this, but it's magically placed in just the right spot.
    def __init__(self, *args, **kwargs):
        super(ImageCanvas, self).__init__(*args, **kwargs)
        with self.canvas.after:
            self.label = Label(font_size=32, color=(1,0,0,1))
        self.bind(size=self.update_rect, pos=self.update_rect)

        self.blank = blank_canvas()
        self.add_widget(self.blank)
        self.blank.opacity = 1

        self.img = Image(source='', allow_stretch=True)
        self.add_widget(self.img)
    @property
    def source(self):
        return self.img.source
    @source.setter
    def source(self, value):
        self.img.source = value
        if os.path.exists(self.source):
            self.blank.opacity = 0
            self.img.opacity = 1
        else:
            self.blank.opacity = 1
            self.img.opacity = 0

class ViewerScreen(Screen):
    def drawing_toggle(self, *args):
        if self.btns[1] == 'ic_action_view_image.png':
            self.btns[1] = 'ic_action_view_drawing.png'
            self.both.remove_widget(self.overlay)
        elif self.btns[1] == 'ic_action_view_drawing.png':
            self.btns[1] = 'ic_action_view_image.png'
            self.both.add_widget(self.overlay)
        app.update_buttons()
    def set_image(self, img_fn):
        self.image.source = img_fn
        if os.path.isdir(img_fn+'.overlays'):
            self.btns[1] = 'ic_action_view_image.png'
            self.overlay.source = os.path.join(img_fn+'.overlays', sorted(os.listdir(img_fn+'.overlays'))[-1])
            app.paint_screen.painter.color = (1,1,1,1)
            app.paint_screen.painter.source = self.overlay.source
            try: self.both.add_widget(self.overlay)
            except WidgetException: pass # The overlay widget may already be added, in which case I don't care.
        else:
            app.paint_screen.painter.color = (0,0,0,0)
            self.btns[1] = None
            self.both.remove_widget(self.overlay)
        self.both.scale = 1
        self.both.rotation = 0
        self.both.pos = [0,0]
    def __init__(self, *args, **kwargs):
        super(ViewerScreen, self).__init__(*args, **kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        self.image = ImageCanvas(pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.overlay = Image(pos_hint={'center_x': 0.5, 'center_y': 0.5})

        self.both = Scatter(size_hint=[1,1])
        self.both.add_widget(self.image)
        self.layout.add_widget(self.both)
        self.both.bind(size=self.fix_size)
    def fix_size(self, *args):
        self.image.size = self.both.size
        self.overlay.size = self.both.size

class PaintScreen(Screen):
    def update_bg(self, instance, value):
        instance.bg_col.size = instance.size
        instance.bg_col.pos = instance.pos
        self.painter.size_const = self.image.img.get_norm_image_size()
    def __init__(self, *args, **kwargs):
        super(PaintScreen, self).__init__(*args, **kwargs)

        with self.canvas.before:
            Color(0,0,0,1)
            self.bg_col = Rectangle()
        self.bind(size=self.update_bg, pos=self.update_bg)

        self.image = ImageCanvas()
        self.add_widget(self.image)

        self.painter = PaintWidget()
        self.add_widget(self.painter)

class image_button(Button):
    def __init__(self, source = '', *args, **kwargs):
        super(image_button, self).__init__(*args, **kwargs)

        self.blank = blank_canvas(line_width=10)
        self.add_widget(self.blank)

        self.img = Image(source='', allow_stretch=True)
        self.add_widget(self.img)

        self.source = source

        self.bind(size=self.update_img, pos=self.update_img)
    def update_img(self, instance, value):
        instance.blank.size = instance.size
        instance.blank.pos = instance.pos
        instance.img.size = instance.size
        instance.img.pos = instance.pos
    @property
    def source(self):
        return self.img.source
    @source.setter
    def source(self, value):
        self.img.source = value
        if os.path.exists(value):
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
        self.scroll_y = 1
        if 'effect_y' in dir(self): # Kivy 1.6.0 doesn't have effect_y
            self.effect_y.value = self.effect_y.min # This is to work around a bug with the ScrollView (https://github.com/kivy/kivy/issues/2038)
        self.image0.source = os.path.join(path, '0.jpg')
        self.image1.source = os.path.join(path, '1.jpg')
        self.image2.source = os.path.join(path, '2.jpg')
        self.image3.source = os.path.join(path, 'blank')
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
    # These are to handle Android switching away from the app or locking the screen.
    # I don't want to do anything on pause, but I do want to go back to the main screen if it was paused for a while.
    def on_pause(self):
        kivy.logger.Logger.debug('Main: pausing')
        self.pause_time = time.time()
        return True
    def on_resume(self):
        kivy.logger.Logger.debug('Main: resuming')
        if time.time()-self.pause_time > 5:
            self.screen_manager.current = 'chooser'

    # This disables kivy's settings panel, normally accessible by pressing F1
    def open_settings(self, *args):
        pass

    ## "Navbar" button functions
    def pressed_win(self, *args):
        if 'btn_functions' in dir(self.screen_manager.current_screen) and self.screen_manager.current_screen.btn_functions[0] != None:
            self.screen_manager.current_screen.btn_functions[0]()
        return False # I'm returning false here so that the button still triggers the next on_release event
    def pressed_home(self, *args):
        if 'btn_functions' in dir(self.screen_manager.current_screen) and self.screen_manager.current_screen.btn_functions[1] != None:
            self.screen_manager.current_screen.btn_functions[1]()
        return False # I'm returning false here so that the button still triggers the next on_release event
    def pressed_back(self, *args):
        if 'btn_functions' in dir(self.screen_manager.current_screen) and self.screen_manager.current_screen.btn_functions[2] != None:
            self.screen_manager.current_screen.btn_functions[2]()
        return False # I'm returning false here so that the button still triggers the next on_release event
    def update_buttons(self, *args):
        if 'btns' in dir(self.screen_manager.current_screen):
            win, home, back = self.screen_manager.current_screen.btns
            if win == None:
                self.win_btn.opacity = 0
            else:
                self.win_btn.opacity = 1
                self.win_btn.background_normal = win
                self.win_btn.background_down = self.win_btn.background_normal
            if home == None:
                self.home_btn.opacity = 0
            else:
                self.home_btn.opacity = 1
                self.home_btn.background_normal = home
                self.home_btn.background_down = self.home_btn.background_normal
            if back == None:
                self.back_btn.opacity = 0
            else:
                self.back_btn.opacity = 1
                self.back_btn.background_normal = back
                self.back_btn.background_down = self.back_btn.background_normal


    ## These functions should probably be put somewhat inside the painter widget.
    def finish_paint(self, good = True):
        self.paint_screen.image.label.text = ''
        if good:
            self.goto_screen('photostrip', 'right')
    def save_painter(self):
        savedir = os.path.normpath(self.paint_screen.image.source+'.overlays'+os.path.sep)
        if not os.path.isdir(savedir):
            os.mkdir(savedir)
        index = 0
        filename = '%02d.png'
        dircontents = os.listdir(savedir)
        while filename % index in dircontents:
            index += 1
        if self.paint_screen.painter.save_png(os.path.join(savedir, filename % index)):
            self.paint_screen.painter.do_drawing = False # Stop drawing on the image until the canvas gets cleared (by switching screen)
            self.paint_screen.image.label.color = (0,0.75,0,1)
            self.paint_screen.image.label.text = 'Saved'
            Clock.schedule_once(lambda arg: self.finish_paint(True), 2)
        else:
            self.paint_screen.image.label.color = (0.75,0,0,1)
            self.paint_screen.image.label.text = 'FAILED to save the drawing, sorry.'
            Clock.schedule_once(lambda arg: self.finish_paint(False), 3)

    def goto_screen(self, screen_name, direction):
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = screen_name
    # This function is just to keep the screen_manager size with window resizing
    def update_size(self, root, value):
        self.screen_manager.size = (root.width-96, root.height)

    def build(self):
        root = FloatLayout()

        ## Screen Manager
        self.screen_manager = ScreenManager(transition=SlideTransition(),size_hint=[None,None], pos_hint={'left': 1})
        root.bind(size=self.update_size)
        root.add_widget(self.screen_manager)

        ## "Navbar" Buttons
        ## These are meant to work like the Android navbar would, and I have named them as such.
        # These two functions are used for a indicator for the button being pressed.
        def rend_circle(btn):
            with btn.canvas:
                Color(1,1,1,0.25)
                size = (btn.size[0], btn.size[1]*1.5)
                btn.hl = Ellipse(pos=( btn.pos[0]+((btn.size[0]/2)-(size[0]/2)), btn.pos[1]+((btn.size[1]/2)-(size[1]/2)) ), size=size)
                Color(1,1,1,1) # Reset the color, otherwise the background goes dark
        def derend_circle(btn):
            btn.canvas.remove(btn.hl)
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

        # Render the background
        def update_rect(instance, value):
            instance.bg.pos = instance.pos
            instance.bg.size = instance.size
        self.screen_manager.bind(size=update_rect,pos=update_rect)
        with self.screen_manager.canvas.before:
            self.screen_manager.bg = Rectangle(source='background.png')

        ## FileChooser
        chooser_screen = Screen(name='chooser')
        chooser = FileChooserGalleryView(rootpath=PHOTOS_PATH)
        def select_folder(chooser, photostrip):
            photostrip.set_path(chooser.current_entry.path)
            self.goto_screen('photostrip', 'left')
        chooser.bind(on_select_folder=lambda args:select_folder(chooser, photostrip))
        chooser_screen.add_widget(chooser)

        ## Painter
        self.paint_screen = PaintScreen(name='painter')
        self.paint_screen.bind(on_leave=lambda src: self.paint_screen.painter.clear())

        ## ImageViewer
        viewer_screen = ViewerScreen(name='viewer')
        viewer_screen.bind(on_enter=lambda src:setattr(self.paint_screen.image,'source',viewer_screen.image.source))

        ## Photo strip
        photostrip_screen = Screen(name='photostrip')
        photostrip = PhotoStrip()
        photostrip_screen.add_widget(photostrip)
        photostrip.bind(
                on_press=lambda src,fn:viewer_screen.set_image(fn),
                on_release=lambda src,fn: self.goto_screen('viewer', 'left'),
        )

        # Set up the icons and functions for the navbar buttons
        chooser_screen.btns             = [None,                                       'ic_action_refresh.png',      None]
        chooser_screen.btn_functions    = [None,                                       chooser._trigger_update,      None]

        photostrip_screen.btns          = [None,                                       None,                         'ic_sysbar_back.png']
        photostrip_screen.btn_functions = [None,                                       None,                         lambda:self.goto_screen('chooser', 'right')]

        viewer_screen.btns              = ['ic_action_new_edit.png',                   None,                         'ic_sysbar_back.png']
        viewer_screen.btn_functions     = [lambda:self.goto_screen('painter', 'left'), viewer_screen.drawing_toggle, lambda:self.goto_screen('photostrip', 'right')]

        self.paint_screen.btns          = ['ic_action_save.png',                       None,                         'ic_action_discard.png']
        self.paint_screen.btn_functions = [self.save_painter,                          None,                         lambda:self.goto_screen('viewer', 'right')]

        # Finally, add the screens to the manager
        self.screen_manager.add_widget(chooser_screen)
        self.screen_manager.add_widget(photostrip_screen)
        self.screen_manager.add_widget(viewer_screen)
        self.screen_manager.add_widget(self.paint_screen)

        # Set the navbar buttons from the variables set above
        self.screen_manager.transition.bind(on_complete=self.update_buttons)
        self.update_buttons()

        return root

global app
app = Main()
app.run()
