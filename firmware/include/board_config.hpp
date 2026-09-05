#pragma once
// Unverified pins are deliberately disabled. Hardware session owns final pin map.
#ifndef LB_PIN_LED_R
#define LB_PIN_LED_R -1
#endif
#ifndef LB_PIN_LED_G
#define LB_PIN_LED_G -1
#endif
#ifndef LB_PIN_LED_B
#define LB_PIN_LED_B -1
#endif
#ifndef LB_PIN_TOUCH
#define LB_PIN_TOUCH -1
#endif
#ifndef LB_TOUCH_THRESHOLD
#define LB_TOUCH_THRESHOLD 0
#endif
#ifndef LB_PIN_PRIVACY
#define LB_PIN_PRIVACY -1
#endif
#ifndef LB_PIN_SDA
#define LB_PIN_SDA -1
#endif
#ifndef LB_PIN_SCL
#define LB_PIN_SCL -1
#endif
#ifndef LB_SCREEN_ADDRESS
#define LB_SCREEN_ADDRESS -1
#endif
// Prototype privacy wiring: LOW explicitly enables interaction; HIGH/disconnected is private.
// EVT-A: SW3V3 common-anode RGB, 470 ohm series per GPIO sink. OFF=HIGH / PWM255.
// Privacy removes SW3V3: no LED privacy light; all peripheral pins become INPUT high-Z.
