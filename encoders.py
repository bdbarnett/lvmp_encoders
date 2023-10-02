# SPDX-FileCopyrightText: 2023 Brad Barnett
#
# SPDX-License-Identifier: MIT

import lvgl as lv
from sys import platform


# EncoderIRQ only works on platforms supported by the RotaryIRQ classes from https://github.com/miketeachman/micropython-rotary
try:
    if platform == "esp8266" or platform == "esp32":
        from rotary_irq_esp import RotaryIRQ as Rotary
    elif platform == "pyboard":
        from rotary_irq_pyb import RotaryIRQ as Rotary
    elif platform == "rp2":
        from rotary_irq_rp2 import RotaryIRQ as Rotary
    else:
        # Platform not detected.  Create an empty Rotary class so EncoderIRQ doesn't throw errors.
        class Rotary:
            pass
except ImportError:
    # The platform is supported, but the rotary_irq_* module from micropython-rotary wasn't found.
    # It is not required unless using the EncoderIRQ class, so create an empty Rotary class.
    class Rotary:
        pass


class Encoder():
    """
    Creates an LVGL indev (input device)
    Usage:
    import display_driver
    import lvgl as lv

    from lv_encoders import Encoder

    enc = Encoder()

    # All of these methods except long_push take one optional int parameter
    enc.inc() # Parameter specifies number of jumps, default 1
    enc.dec() # Ditto
    enc.fast_inc()  # Parameter is multiplied by fast_mult, default 1
    enc.fast_dec()  # Ditto
    enc.push()      # Parameter specifies duration in ms, default 500
    enc.long_push() # No parameter.
    """

    def __init__(
        self,
        group=None,  # Group to register indev
        display=None,  # Display to register indev
        def_dur=500,  # Default duration for switch push
        fast_mult=5,  # Multiplier for fast jumps
    ):
        group = group if group else lv.group_get_default()
        display = display if display else lv.disp_get_default()

        self.def_dur = def_dur
        self.fast_mult = fast_mult

        self.pressed = False
        self._lastpressed = False
        self._value = 0
        self._last_value = self.value()
        self._value_changed = False

        # Register LVGL indev driver
        self.indev = lv.indev_create()
        self.indev.set_type(lv.INDEV_TYPE.ENCODER)
        self.indev.set_read_cb(self._read_cb)

        self.indev.set_group(group)
        self.indev.set_disp(display)

    #         self.indev.long_press_time = dur

    def inc(self, diff=1):
        self._value += diff
        self._set_value_changed()

    def dec(self, diff=1):
        self._value -= diff
        self._set_value_changed()

    def fast_inc(self, diff=1):
        self._value += diff * self.fast_mult
        self._set_value_changed()

    def fast_dec(self, diff=1):
        self._value -= diff * self.fast_mult
        self._set_value_changed()

    def push(self, period=None):
        if not period:
            period = self.def_dur
        self.press_cb()
        t = lv.timer_create_basic()
        t.set_period(period)
        t.set_repeat_count(1)
        t.set_cb(lambda e: self.release_cb())

    def long_push(self):
        if self.indev.get_group().get_editing():
            self.indev.get_group().set_editing(False)
        elif self.indev.get_group().get_focused():
            self.indev.get_group().get_focused().send_event(lv.EVENT.LONG_PRESSED, None)

    def value(self):
        return self._value

    def press_cb(self):
        self.pressed = True

    def release_cb(self):
        self.pressed = False

    def _set_value_changed(self):
        self._value_changed = True

    def _read_cb(self, indev, data):
        if self.pressed != self._lastpressed:
            if self.pressed:
                data.state = lv.INDEV_STATE.PRESSED
            else:
                data.state = lv.INDEV_STATE.RELEASED
            self._lastpressed = self.pressed

        if self._value_changed:
            self._value_changed = False
            value = self.value()
            data.enc_diff = value - self._last_value
            self._last_value = value

        return 0

    def delete(self):
        self.indev.enable(False)

    def get_indev(self, index=0):
        if index == 0:
            return self.indev
        else:
            raise(ValueError("Encoder object only has 1 indev, index is 0"))

class EncoderWidget(lv.obj):
    """
    Creates a new EncoderWidget
    Usage:
        import display_driver
        import lvgl as lv

        from lv_encoders import EncoderWidget

        # parent can be any LVGL container object
        parent = lv.scr_act()
        ew = EncoderWidget(parent, group)
    """

    style_btn_default = lv.style_t()
    style_btn_default.init()
    style_btn_default.set_width(lv.pct(33))
    style_btn_default.set_height(lv.pct(100))
    style_btn_default.set_radius(lv.RADIUS_CIRCLE)
    style_btn_default.set_pad_all(1)

    style_btnpressed = lv.style_t()
    style_btnpressed.init()
    style_btnpressed.set_transform_width(-10)
    style_btnpressed.set_transform_height(-10)

    style_default = lv.style_t()
    style_default.init()
    style_default.set_pad_all(0)
    style_default.set_margin_top(1)
    style_default.set_margin_bottom(1)
    style_default.set_margin_left(1)
    style_default.set_margin_right(1)
    style_default.set_border_width(0)
    style_default.set_bg_color(lv.palette_lighten(lv.PALETTE.GREY, 1))

    styles = {lv.STATE.DEFAULT: style_default}
    # styles = {}

    def __init__(
        self,
        parent,
        group=None,
        display=None,
        width=None,
        height=None,
        alignment=(lv.ALIGN.CENTER, 0, 0),
        styles=None,
        **args,
    ):
        super().__init__(parent)

        if group is None:
            groups = [lv.group_get_default()]
        elif type(group) is list:
            groups = group
            self.set_flex_flow(lv.FLEX_FLOW.ROW)
        else:
            groups = [group]

        display = display if display else lv.disp_get_default()

        self._num_groups = len(groups)
        width = width if width else 240 * self._num_groups
        height = height if height else 80
        self.set_width(width)
        self.set_height(height)
        
        self.indevs=[]

        # style to be used on the containers for each widget
        if styles:
            self.styles = styles
        for state, style in self.styles.items():
            self.add_style(style, state)
        self.align(*alignment)

        self.conts = []
        self._widget_group = lv.group_create()  # Create a group for the encoder buttons
        for g in groups:
            self._create_encoder(group=g, display=display, **args)

    def _create_encoder(self, group, display, **args):
        enc = Encoder(group, display, **args)

        cont = lv.obj(self)
        for state, style in self.styles.items():
            cont.add_style(style, state)
        cont.set_width(lv.pct(99 // self._num_groups))
        cont.set_height(lv.pct(99))

        # Create the encoder buttons
        btn_switch = lv.btn(cont)
        btn_switch.set_style_bg_img_src(lv.SYMBOL.NEW_LINE, 0)
        btn_switch.align(lv.ALIGN.CENTER, 0, 0)
        btn_switch.add_event(lambda e: enc.push(), lv.EVENT.SHORT_CLICKED, None)
        btn_switch.add_event(lambda e: enc.long_push(), lv.EVENT.LONG_PRESSED, None)

        btn_right = lv.btn(cont)
        btn_right.set_style_bg_img_src(lv.SYMBOL.RIGHT, 0)
        btn_right.align(lv.ALIGN.RIGHT_MID, 0, 0)
        btn_right.add_event(lambda e: enc.inc(), lv.EVENT.SHORT_CLICKED, None)
        btn_right.add_event(lambda e: enc.inc(), lv.EVENT.LONG_PRESSED_REPEAT, None)

        btn_left = lv.btn(cont)
        btn_left.set_style_bg_img_src(lv.SYMBOL.LEFT, 0)
        btn_left.align(lv.ALIGN.LEFT_MID, 0, 0)
        btn_left.add_event(lambda e: enc.dec(), lv.EVENT.SHORT_CLICKED, None)
        btn_left.add_event(lambda e: enc.dec(), lv.EVENT.LONG_PRESSED_REPEAT, None)

        # Assign styles to buttons and add buttons to the group
        for btn in btn_switch, btn_right, btn_left:
            btn.add_style(self.style_btn_default, 0)
            btn.add_style(self.style_btnpressed, lv.STATE.PRESSED)
            self._widget_group.add_obj(btn)
        self.indevs.append(enc.get_indev())
        self.conts.append(cont)

    def get_indev(self, index=0):
        return self.indevs[index]

class EncoderDisplay(EncoderWidget):
    """
    Creates a new SDL Display and Mouse on Unix

        Usage:
        import display_driver
        import lvgl as lv

        from lv_encoders import EncoderDisplay

        ed = EncoderDisplay()
    """

    def __init__(
        self, group=None, width=240, height=80, title="Encoder Display", **args
    ):
        from tools.sdl_disp import sdl_display
        disp, _ = sdl_display(width, height, title)
        parent = disp.get_scr_act()
        super().__init__(
            parent,
            group=group,
            display=None,
            width=lv.pct(100),
            height=lv.pct(100),
            **args,
        )


class EncoderIRQ(Encoder, Rotary):
    """
    LVGL wrapper for Mike Teachman's micropython-rotary module at
          https://github.com/MikeTeachman/micropython-rotary

    Usage:
        import display_driver
        import lvgl as lv

        from lv_encoders import EncoderIRQ

        enc = EncoderIRQ(pin_num_clk=12, pin_num_dt=13,
                         pull_up=True, half_step=True)
    """

    def __init__(
        self,
        *args,
        display=lv.disp_get_default(),  # Display to register indev
        group=lv.group_get_default(),  # Group to register indev
        def_dur=500,  # Default duration for switch push
        fast_mult=5,  # Multiplier for fast jumps
        **kwargs,
    ):
        Encoder.__init__(
            self, display=display, group=group, def_dur=def_dur, fast_mult=fast_mult
        )

        try:
            Rotary.__init__(self, *args, **kwargs)
            self.add_listener(self._set_value_changed)
        except AttributeError:
            raise ImportError("The micropython-rotary module was not found.")

        # Todo: Setup the switch pin and IRQ here with callback = self._??????
