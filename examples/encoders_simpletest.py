#!/opt/bin/lv_micropython -i

# SPDX-FileCopyrightText: 2023 Brad Barnett
#
# SPDX-License-Identifier: MIT

import display_driver
import lvgl as lv
from encoders import Encoder, EncoderWidget, EncoderDisplay, EncoderIRQ

# enc = Encoder() # No UI, must call: #.inc(), .dec(), .push(), .fast_inc(), .fast_dec(), .long_push()
ew = EncoderWidget(lv.scr_act(), alignment=(lv.ALIGN.BOTTOM_MID, 0, 0))
# ed = EncoderDisplay()       # Warning: for Unix only
# enc = EncoderIRQ(pin_num_clk=12, pin_num_dt=13, pull_up=True, half_step=True)

alignments = (
    (lv.ALIGN.TOP_LEFT, 0, 0),
    (lv.ALIGN.TOP_MID, 0, 0),
    (lv.ALIGN.TOP_RIGHT, 0, 0),
    (lv.ALIGN.LEFT_MID, 0, 0),
    (lv.ALIGN.CENTER, 0, 0),
    (lv.ALIGN.RIGHT_MID, 0, 0),
#    (lv.ALIGN.BOTTOM_LEFT, 0, 0),
#    (lv.ALIGN.BOTTOM_MID, 0, 0),
#    (lv.ALIGN.BOTTOM_RIGHT, 0, 0),
    )

style_base = lv.style_t()
style_base.init()
style_base.set_width(lv.pct(33))
style_base.set_height(lv.pct(33))
style_base.set_radius(lv.RADIUS_CIRCLE)

style_pressed = lv.style_t()
style_pressed.init()
style_pressed.set_transform_width(-10)
style_pressed.set_transform_height(-10)

style_focused = lv.style_t()
style_focused.init()
style_focused.set_bg_color(lv.palette_main(lv.PALETTE.GREEN))

parent = lv.scr_act()                  # parent can be any LVGL container object

for alignment in alignments:
    btn = lv.btn(parent)
    btn.set_style_bg_img_src(lv.SYMBOL.HOME, 0)
    btn.align(*alignment)
    btn.add_style(style_base, 0)
    btn.add_style(style_pressed, lv.STATE.PRESSED)
    btn.add_style(style_focused, lv.STATE.FOCUSED)
