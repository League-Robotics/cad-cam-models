// Robot display: firmware for the Waveshare ESP32-S3-Touch-LCD-1.69.
//
// The board is an I2C *slave* on its external header (GPIO17 = SDA, GPIO18 =
// SCL, 3V3, GND) so a robot controller (a micro:bit on a Nezha, or anything
// else that speaks I2C) can write short ASCII commands to it and read back a
// 10-byte status (touch, buttons, battery). The same commands work over the
// USB serial console, one per line, for testing from a computer.
//
// Commands (ASCII, first letter picks the command, fields separated by spaces):
//   C [bg]                clear the screen (optionally to a colour)
//   Z <size>              text size 1..6 for following T/U lines (default 2)
//   F <fg> [bg]           colours by name (white red green blue yellow cyan
//                         magenta orange gray black) or hex RRGGBB
//   T <line> <text>       text on a line (lines are counted at the current size)
//   U <line> <text>       the same, centred
//   N <text>              one huge centred value in the middle of the screen
//   G <n> <0-100> [label] bar gauge n (0 = bottom), with an optional label
//   I <name> [x y r]      icon: smile frown neutral heart check cross up down
//                         left right stop dot
//   R <x> <y> <w> <h> [c] filled rectangle;  L x1 y1 x2 y2 [c] line;  Q x y r [c] circle
//   K [hz] [ms]           beep (default 2000 Hz, 100 ms)
//   D <0-255>             backlight brightness (saved)
//   O <0-3>               orientation (saved): 0 portrait, USB at the bottom;
//                         1 landscape, USB on the left; 2, 3 the other way round
//   A <hex>               I2C slave address (saved, takes effect after reset)
//   ?                     print status on the serial console
// Status, read back over I2C (10 bytes):
//   [0] protocol version (1)
//   [1] flags: bit0 touched now, bit1 PWR button, bit2 BOOT button, bit3 USB power
//   [2..3] touch x (little-endian), [4..5] touch y, in the current orientation
//   [6] last gesture (CST816: 1 up, 2 down, 3 left, 4 right, 5 tap, 11 double
//       tap, 12 long press), cleared once read
//   [7] tap counter (wraps), so a controller can see taps it missed
//   [8] battery, tenths of a volt (0 when no battery)
//   [9] seconds since boot, low byte
//
// Pins are the V2 board's (Waveshare pin_config.h and the V2.1 schematic).

#include <Arduino.h>
#include <Wire.h>
#include <Preferences.h>
#include <Arduino_GFX_Library.h>

// ---- Pins (Waveshare ESP32-S3-Touch-LCD-1.69, V2) -------------------------
static constexpr int LCD_DC = 4, LCD_CS = 5, LCD_SCK = 6, LCD_MOSI = 7, LCD_RST = 8, LCD_BL = 15;
static constexpr int TP_SDA = 11, TP_SCL = 10, TP_RST = 13, TP_INT = 14;   // touch, IMU, RTC bus
static constexpr int EXT_SDA = 17, EXT_SCL = 18;                           // the robot's bus (we are the slave)
static constexpr int PIN_BUZZER = 42, PIN_SYS_EN = 41, PIN_SYS_OUT = 40, PIN_BOOT = 0, PIN_BAT_ADC = 1;
static constexpr uint8_t TOUCH_ADDR = 0x15;
static constexpr uint8_t DEFAULT_I2C_ADDR = 0x42;
static constexpr int NATIVE_W = 240, NATIVE_H = 280;
static constexpr int BL_CH = 2, BUZZ_CH = 3;
static const char *VERSION = "robot-display 0.1 (2026-11-14)";

// ---- Display ----------------------------------------------------------------
Arduino_DataBus *bus = new Arduino_ESP32SPI(LCD_DC, LCD_CS, LCD_SCK, LCD_MOSI, GFX_NOT_DEFINED);
Arduino_GFX *gfx = new Arduino_ST7789(bus, LCD_RST, 0, true, NATIVE_W, NATIVE_H, 0, 20, 0, 20);

Preferences prefs;
uint8_t rotation = 1;
uint8_t i2c_addr = DEFAULT_I2C_ADDR;
uint8_t backlight = 255;
uint16_t fg = WHITE, bg = BLACK;
uint8_t text_size = 2;
bool splash_shown = false;

// ---- Command queue: filled from I2C (slave task) and serial, drained in loop()
struct Cmd { char text[160]; };
QueueHandle_t cmd_queue;

// ---- Status shared with the I2C request callback -----------------------------
static portMUX_TYPE status_mux = portMUX_INITIALIZER_UNLOCKED;
uint8_t status_buf[10] = {1, 0, 0, 0, 0, 0, 0, 0, 0, 0};
volatile bool gesture_pending = false;

void on_i2c_receive(int n) {
    Cmd c; int i = 0;
    while (Wire1.available()) {
        int b = Wire1.read();
        if (i < (int)sizeof(c.text) - 1 && b >= 0) c.text[i++] = (char)b;
    }
    c.text[i] = 0;
    // one write = one command; a trailing newline is tolerated
    while (i > 0 && (c.text[i - 1] == '\n' || c.text[i - 1] == '\r')) c.text[--i] = 0;
    if (i) xQueueSend(cmd_queue, &c, 0);
}

void on_i2c_request() {
    uint8_t copy[sizeof(status_buf)];
    portENTER_CRITICAL(&status_mux);
    memcpy(copy, status_buf, sizeof(copy));
    status_buf[6] = 0;           // gesture is reported once
    portEXIT_CRITICAL(&status_mux);
    Wire1.write(copy, sizeof(copy));
}

// ---- Touch (CST816T on the internal bus) ---------------------------------------
bool touch_ok = false;
struct Touch { bool down; int x, y; uint8_t gesture; } touch;

bool touch_read_regs(uint8_t reg, uint8_t *out, size_t n) {
    Wire.beginTransmission(TOUCH_ADDR);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom((int)TOUCH_ADDR, (int)n) != (int)n) return false;
    for (size_t i = 0; i < n; i++) out[i] = Wire.read();
    return true;
}

void touch_init() {
    pinMode(TP_INT, INPUT_PULLUP);
    pinMode(TP_RST, OUTPUT);
    digitalWrite(TP_RST, LOW);  delay(10);
    digitalWrite(TP_RST, HIGH); delay(60);
    uint8_t id[1];
    touch_ok = touch_read_regs(0xA7, id, 1);            // chip id register
    if (touch_ok) {
        uint8_t v = 0x60; Wire.beginTransmission(TOUCH_ADDR); Wire.write(0xFA); Wire.write(v); Wire.endTransmission(); // IrqCtl: touch + change
        v = 0x01;        Wire.beginTransmission(TOUCH_ADDR); Wire.write(0xFE); Wire.write(v); Wire.endTransmission(); // DisAutoSleep: stay awake so polling works
    }
    Serial.printf("touch %s (id 0x%02X)\n", touch_ok ? "ok" : "not found", touch_ok ? id[0] : 0);
}

// Map a native (portrait) panel point into the current orientation.
void touch_map(int nx, int ny, int &x, int &y) {
    switch (rotation) {
        default: x = nx; y = ny; break;
        case 1:  x = NATIVE_H - 1 - ny; y = nx; break;
        case 2:  x = NATIVE_W - 1 - nx; y = NATIVE_H - 1 - ny; break;
        case 3:  x = ny; y = NATIVE_W - 1 - nx; break;
    }
}

void touch_poll() {
    if (!touch_ok) return;
    // The CST816 only answers while it has something to say (INT low) or just
    // after; polling it idle gets a NAK, so read when INT is low or a finger was down.
    if (digitalRead(TP_INT) == HIGH && !touch.down) return;
    uint8_t r[6];
    bool down = false;
    if (touch_read_regs(0x01, r, 6)) down = (r[1] & 0x0F) > 0;   // gesture, fingers, xH, xL, yH, yL
    else { r[0] = 0; r[2] = r[3] = r[4] = r[5] = 0; }            // no answer: treat as released
    int nx = ((r[2] & 0x0F) << 8) | r[3];
    int ny = ((r[4] & 0x0F) << 8) | r[5];
    uint8_t g = (r[0] <= 12) ? r[0] : 0;
    touch.down = down;
    if (down) touch_map(nx, ny, touch.x, touch.y);
    if (g) touch.gesture = g;
    portENTER_CRITICAL(&status_mux);
    status_buf[1] = (status_buf[1] & ~1) | (down ? 1 : 0);
    status_buf[2] = touch.x & 0xFF; status_buf[3] = touch.x >> 8;
    status_buf[4] = touch.y & 0xFF; status_buf[5] = touch.y >> 8;
    if (g) { status_buf[6] = g; if (g == 5 || g == 11) status_buf[7]++; }
    portEXIT_CRITICAL(&status_mux);
}

// ---- Buttons, battery, buzzer, backlight ----------------------------------------
uint32_t pwr_down_since = 0;
uint32_t beep_until = 0;

void beep(int hz, int ms) {
    ledcWriteTone(BUZZ_CH, hz);
    ledcWrite(BUZZ_CH, 128);
    beep_until = millis() + ms;
}

float battery_volts() {
    // GPIO1 behind a 200k/100k divider (Waveshare demo 07): Vbat = 3 * Vadc
    uint32_t mv = 0;
    for (int i = 0; i < 8; i++) mv += analogReadMilliVolts(PIN_BAT_ADC);
    return 3.0f * (mv / 8) / 1000.0f;
}

void poll_inputs() {
    static uint32_t last = 0;
    uint32_t now = millis();
    if (now - last < 50) return;
    last = now;
    bool pwr = digitalRead(PIN_SYS_OUT) == LOW;      // PWR button pulls SYS_OUT low (Waveshare demo 09)
    bool boot = digitalRead(PIN_BOOT) == LOW;
    float vb = battery_volts();
    portENTER_CRITICAL(&status_mux);
    status_buf[1] = (status_buf[1] & ~0x06) | (pwr ? 2 : 0) | (boot ? 4 : 0);
    status_buf[8] = vb > 2.5f ? (uint8_t)(vb * 10 + 0.5f) : 0;
    status_buf[9] = (now / 1000) & 0xFF;
    portEXIT_CRITICAL(&status_mux);
    // Long press PWR: release the power latch (turns the board off on battery)
    if (pwr) { if (!pwr_down_since) pwr_down_since = now; else if (now - pwr_down_since > 2000) { digitalWrite(PIN_SYS_EN, LOW); } }
    else pwr_down_since = 0;
    if (beep_until && now > beep_until) { ledcWrite(BUZZ_CH, 0); beep_until = 0; }
}

// ---- Drawing helpers ------------------------------------------------------------
uint16_t colour_from(const char *s, uint16_t dflt) {
    if (!s || !*s) return dflt;
    struct { const char *n; uint16_t c; } names[] = {
        {"white", WHITE}, {"black", BLACK}, {"red", RED}, {"green", GREEN}, {"blue", BLUE}, {"yellow", YELLOW},
        {"cyan", CYAN}, {"magenta", MAGENTA}, {"orange", ORANGE}, {"gray", DARKGREY}, {"grey", DARKGREY},
        {"purple", PURPLE}, {"pink", 0xFE19}, {"navy", NAVY}, {"olive", OLIVE}, {"maroon", MAROON}};
    for (auto &nm : names) if (strcasecmp(s, nm.n) == 0) return nm.c;
    if (strlen(s) == 6) {
        char *e; unsigned long v = strtoul(s, &e, 16);
        if (*e == 0) return gfx->color565((v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF);
    }
    return dflt;
}

int line_pitch(int size) { return 8 * size + 4; }

void draw_text_line(int line, const char *text, bool centred) {
    int pitch = line_pitch(text_size);
    int y = 2 + line * pitch;
    if (y >= gfx->height()) return;
    gfx->fillRect(0, y, gfx->width(), pitch, bg);
    int w = strlen(text) * 6 * text_size;
    int x = centred ? max(0, (gfx->width() - w) / 2) : 4;
    gfx->setTextSize(text_size);
    gfx->setTextColor(fg, bg);
    gfx->setCursor(x, y + 2);
    gfx->print(text);
}

void draw_big(const char *text) {
    int size = 6;
    int w = strlen(text) * 6 * size;
    while (size > 1 && w > gfx->width() - 8) { size--; w = strlen(text) * 6 * size; }
    int h = 8 * size;
    int y = (gfx->height() - h) / 2;
    gfx->fillRect(0, y - 6, gfx->width(), h + 12, bg);
    gfx->setTextSize(size);
    gfx->setTextColor(fg, bg);
    gfx->setCursor((gfx->width() - w) / 2, y);
    gfx->print(text);
}

void draw_gauge(int n, int value, const char *label) {
    const int band = 28, h = 22;
    int y = gfx->height() - band * (n + 1) + 3;
    if (y < 0) return;
    value = constrain(value, 0, 100);
    int x0 = 4, w = gfx->width() - 8;
    gfx->fillRect(x0, y, w, h, bg);
    gfx->drawRect(x0, y, w, h, fg);
    int fill = (w - 4) * value / 100;
    uint16_t c = value < 25 ? RED : value < 50 ? ORANGE : GREEN;
    if (fill > 0) gfx->fillRect(x0 + 2, y + 2, fill, h - 4, c);
    gfx->setTextSize(2);
    gfx->setTextColor(fg);
    if (label && *label) { gfx->setCursor(x0 + 6, y + 4); gfx->print(label); }
    char num[8]; snprintf(num, sizeof(num), "%d", value);
    gfx->setCursor(x0 + w - 6 - strlen(num) * 12, y + 4);
    gfx->print(num);
}

void draw_icon(const char *name, int cx, int cy, int r) {
    gfx->fillRect(cx - r - 2, cy - r - 2, 2 * r + 4, 2 * r + 4, bg);
    int t = max(2, r / 8);   // stroke
    if (!strcasecmp(name, "smile") || !strcasecmp(name, "frown") || !strcasecmp(name, "neutral")) {
        gfx->fillCircle(cx, cy, r, YELLOW);
        gfx->fillCircle(cx - r / 3, cy - r / 3, r / 8, BLACK);
        gfx->fillCircle(cx + r / 3, cy - r / 3, r / 8, BLACK);
        if (!strcasecmp(name, "neutral")) gfx->fillRect(cx - r / 2, cy + r / 3, r, t, BLACK);
        else {
            int dir = !strcasecmp(name, "smile") ? 1 : -1;
            for (int i = -r / 2; i <= r / 2; i++) {
                float f = (float)i / (r / 2.0f);
                int yy = cy + dir * (r / 3) + (int)(dir * (-f * f * r / 4));
                gfx->fillRect(cx + i, yy - t / 2 + (dir > 0 ? 0 : r / 2), 1, t, BLACK);
            }
        }
    } else if (!strcasecmp(name, "heart")) {
        gfx->fillCircle(cx - r / 2, cy - r / 4, r / 2, RED);
        gfx->fillCircle(cx + r / 2, cy - r / 4, r / 2, RED);
        gfx->fillTriangle(cx - r, cy - r / 8, cx + r, cy - r / 8, cx, cy + r, RED);
    } else if (!strcasecmp(name, "check")) {
        for (int i = 0; i < t; i++) { gfx->drawLine(cx - r + i, cy, cx - r / 3 + i, cy + r * 2 / 3, GREEN); gfx->drawLine(cx - r / 3 + i, cy + r * 2 / 3, cx + r + i, cy - r * 2 / 3, GREEN); }
    } else if (!strcasecmp(name, "cross")) {
        for (int i = -t / 2; i <= t / 2; i++) { gfx->drawLine(cx - r + i, cy - r, cx + r + i, cy + r, RED); gfx->drawLine(cx - r + i, cy + r, cx + r + i, cy - r, RED); }
    } else if (!strcasecmp(name, "up") || !strcasecmp(name, "down") || !strcasecmp(name, "left") || !strcasecmp(name, "right")) {
        int sx = 0, sy = 0;
        if (!strcasecmp(name, "up")) sy = -1; else if (!strcasecmp(name, "down")) sy = 1; else if (!strcasecmp(name, "left")) sx = -1; else sx = 1;
        int hx = cx + sx * r, hy = cy + sy * r;                       // tip
        int bx = cx - sx * r / 4, by = cy - sy * r / 4;                 // base of the head
        gfx->fillTriangle(hx, hy, bx + sy * r * 3 / 4, by + sx * r * 3 / 4, bx - sy * r * 3 / 4, by - sx * r * 3 / 4, CYAN);
        int sw = r / 3;
        if (sx) gfx->fillRect(min(bx, cx - sx * r), cy - sw / 2, abs(bx - (cx - sx * r)), sw, CYAN);
        else    gfx->fillRect(cx - sw / 2, min(by, cy - sy * r), sw, abs(by - (cy - sy * r)), CYAN);
    } else if (!strcasecmp(name, "stop")) {
        gfx->fillCircle(cx, cy, r, RED);
        gfx->setTextSize(max(1, r / 14)); gfx->setTextColor(WHITE);
        int tw = 4 * 6 * max(1, r / 14); gfx->setCursor(cx - tw / 2, cy - 4 * max(1, r / 14)); gfx->print("STOP");
    } else if (!strcasecmp(name, "dot")) {
        gfx->fillCircle(cx, cy, r, fg);
    }
}

void show_splash() {
    gfx->fillScreen(BLACK);
    gfx->setTextColor(WHITE, BLACK);
    gfx->setTextSize(3); gfx->setCursor(8, 10); gfx->print("Robot");
    gfx->setCursor(8, 38); gfx->print("Display");
    gfx->setTextSize(2);
    char l[40];
    snprintf(l, sizeof(l), "I2C addr 0x%02X", i2c_addr); gfx->setCursor(8, 80); gfx->print(l);
    gfx->setCursor(8, 100); gfx->print("SDA 17  SCL 18");
    snprintf(l, sizeof(l), "rot %d  %dx%d", rotation, gfx->width(), gfx->height()); gfx->setCursor(8, 120); gfx->print(l);
    gfx->setCursor(8, 150); gfx->setTextColor(CYAN, BLACK); gfx->print("waiting for");
    gfx->setCursor(8, 170); gfx->print("the robot...");
    gfx->setTextColor(DARKGREY, BLACK); gfx->setTextSize(1); gfx->setCursor(8, gfx->height() - 12); gfx->print(VERSION);
    splash_shown = true;
}

// ---- Command parser ----------------------------------------------------------------
// Splits off up to `n` leading integer/word fields; the rest is returned as text.
static int split(char *s, char **argv, int maxn) {
    int n = 0; char *p = s;
    while (*p && n < maxn) {
        while (*p == ' ') p++;
        if (!*p) break;
        argv[n++] = p;
        while (*p && *p != ' ') p++;
        if (*p) *p++ = 0;
    }
    return n;
}
static const char *rest_after(char *s, int fields) {
    // the text after `fields` space-separated fields (keeps internal spaces)
    char *p = s;
    for (int i = 0; i < fields; i++) { while (*p == ' ') p++; while (*p && *p != ' ') p++; }
    while (*p == ' ') p++;
    return p;
}

void print_status() {
    uint8_t c[10];
    portENTER_CRITICAL(&status_mux); memcpy(c, status_buf, 10); portEXIT_CRITICAL(&status_mux);
    Serial.printf("%s\nI2C slave 0x%02X on SDA %d SCL %d; rot %d %dx%d; touch %s\n", VERSION, i2c_addr, EXT_SDA, EXT_SCL,
                  rotation, gfx->width(), gfx->height(), touch_ok ? "ok" : "absent");
    Serial.printf("status: flags=0x%02X touch=(%d,%d) gesture=%d taps=%d bat=%.1fV up=%lus\n", c[1], c[2] | (c[3] << 8),
                  c[4] | (c[5] << 8), c[6], c[7], c[8] / 10.0, millis() / 1000);
}

void run_command(char *line) {
    while (*line == ' ') line++;
    if (!*line) return;
    char op = toupper(line[0]);
    if (splash_shown && op != '?' && op != 'A' && op != 'D' && op != 'O') { gfx->fillScreen(bg); splash_shown = false; }
    char copy[160]; strncpy(copy, line, sizeof(copy) - 1); copy[sizeof(copy) - 1] = 0;
    char *argv[8]; int argc = split(copy, argv, 8);
    const char *err = nullptr;
    switch (op) {
        case 'C': if (argc > 1) bg = colour_from(argv[1], bg); gfx->fillScreen(bg); break;
        case 'Z': if (argc > 1) text_size = constrain(atoi(argv[1]), 1, 6); break;
        case 'F': if (argc > 1) fg = colour_from(argv[1], fg); if (argc > 2) bg = colour_from(argv[2], bg); break;
        case 'T': case 'U':
            if (argc < 2) { err = "T <line> <text>"; break; }
            draw_text_line(atoi(argv[1]), rest_after(line, 2), op == 'U'); break;
        case 'N': draw_big(rest_after(line, 1)); break;
        case 'G':
            if (argc < 3) { err = "G <n> <0-100> [label]"; break; }
            draw_gauge(atoi(argv[1]), atoi(argv[2]), rest_after(line, 3)); break;
        case 'I': {
            if (argc < 2) { err = "I <name> [x y r]"; break; }
            int r = argc > 4 ? atoi(argv[4]) : min(gfx->width(), gfx->height()) / 3;
            int cx = argc > 2 ? atoi(argv[2]) : gfx->width() / 2, cy = argc > 3 ? atoi(argv[3]) : gfx->height() / 2;
            draw_icon(argv[1], cx, cy, r); break; }
        case 'R': if (argc < 5) { err = "R x y w h [colour]"; break; }
            gfx->fillRect(atoi(argv[1]), atoi(argv[2]), atoi(argv[3]), atoi(argv[4]), argc > 5 ? colour_from(argv[5], fg) : fg); break;
        case 'L': if (argc < 5) { err = "L x1 y1 x2 y2 [colour]"; break; }
            gfx->drawLine(atoi(argv[1]), atoi(argv[2]), atoi(argv[3]), atoi(argv[4]), argc > 5 ? colour_from(argv[5], fg) : fg); break;
        case 'Q': if (argc < 4) { err = "Q x y r [colour]"; break; }
            gfx->fillCircle(atoi(argv[1]), atoi(argv[2]), atoi(argv[3]), argc > 4 ? colour_from(argv[4], fg) : fg); break;
        case 'K': beep(argc > 1 ? atoi(argv[1]) : 2000, argc > 2 ? atoi(argv[2]) : 100); break;
        case 'D': if (argc > 1) { backlight = constrain(atoi(argv[1]), 0, 255); ledcWrite(BL_CH, backlight); prefs.putUChar("bl", backlight); } break;
        case 'O': if (argc > 1) { rotation = constrain(atoi(argv[1]), 0, 3); gfx->setRotation(rotation); prefs.putUChar("rot", rotation); gfx->fillScreen(bg); } break;
        case 'A': if (argc > 1) { int a = strtol(argv[1], nullptr, 16); if (a >= 8 && a <= 0x77) { prefs.putUChar("addr", a); Serial.printf("I2C address 0x%02X saved; reset to apply\n", a); } else err = "A <08..77 hex>"; } break;
        case '?': print_status(); break;
        case 'S': show_splash(); break;
        default: err = "unknown command";
    }
    if (err) Serial.printf("err: %s\n", err); else Serial.println("ok");
}

// ---- Setup / loop -----------------------------------------------------------------
void setup() {
    pinMode(PIN_SYS_EN, OUTPUT); digitalWrite(PIN_SYS_EN, HIGH);   // hold the power latch on
    pinMode(PIN_SYS_OUT, INPUT);
    pinMode(PIN_BOOT, INPUT_PULLUP);
    pinMode(PIN_BAT_ADC, INPUT);
    Serial.begin(115200);
    delay(300);
    Serial.println(VERSION);

    prefs.begin("disp", false);
    rotation = prefs.getUChar("rot", 1);
    i2c_addr = prefs.getUChar("addr", DEFAULT_I2C_ADDR);
    backlight = prefs.getUChar("bl", 255);

    ledcSetup(BL_CH, 5000, 8); ledcAttachPin(LCD_BL, BL_CH); ledcWrite(BL_CH, 0);
    ledcSetup(BUZZ_CH, 2000, 8); ledcAttachPin(PIN_BUZZER, BUZZ_CH); ledcWrite(BUZZ_CH, 0);

    if (!gfx->begin(40000000)) Serial.println("gfx begin failed");
    gfx->setRotation(rotation);
    gfx->setTextWrap(false);
    show_splash();
    ledcWrite(BL_CH, backlight);

    Wire.begin(TP_SDA, TP_SCL, 400000);
    touch_init();

    cmd_queue = xQueueCreate(16, sizeof(Cmd));
    Wire1.setBufferSize(256);
    Wire1.onReceive(on_i2c_receive);
    Wire1.onRequest(on_i2c_request);
    pinMode(EXT_SDA, INPUT_PULLUP); pinMode(EXT_SCL, INPUT_PULLUP);
    bool ok = Wire1.begin(i2c_addr, EXT_SDA, EXT_SCL, 100000);
    Serial.printf("I2C slave 0x%02X on SDA %d SCL %d: %s\n", i2c_addr, EXT_SDA, EXT_SCL, ok ? "ok" : "FAILED");
    beep(1500, 60);
}

void loop() {
    static char sbuf[160]; static int slen = 0;
    while (Serial.available()) {
        char ch = Serial.read();
        if (ch == '\n' || ch == '\r') { if (slen) { sbuf[slen] = 0; run_command(sbuf); } slen = 0; }
        else if (slen < (int)sizeof(sbuf) - 1) sbuf[slen++] = ch;
    }
    Cmd c;
    while (xQueueReceive(cmd_queue, &c, 0) == pdTRUE) run_command(c.text);
    static uint32_t last_touch = 0;
    if (millis() - last_touch > 20) { last_touch = millis(); touch_poll(); }
    poll_inputs();
    delay(2);
}
