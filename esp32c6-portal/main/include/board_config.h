#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

/**
 * Hardware Pinout & Wi-Fi AP Configuration for AITY Xmas Tree 2026 PCB
 * Target Board: Seeed Studio XIAO ESP32-C6
 *
 * PCB Pin Mapping (see root README.md):
 *   D0  / A0   -> GPIO 0  : Piezo Speaker / Buzzer (LS101)
 *   D10 / MOSI -> GPIO 18 : 60 x WS2812B NeoPixel LEDs Data In
 *   RF Enable  -> GPIO 3  : XIAO ESP32-C6 RF Switch Power Enable (active LOW)
 *   RF Select  -> GPIO 14 : XIAO ESP32-C6 Antenna Select (LOW = internal ceramic, HIGH = U.FL)
 *   User LED   -> GPIO 15 : XIAO ESP32-C6 Onboard Yellow LED (active LOW)
 */

#define XMAS_FIRMWARE_VERSION "1.0.0"

// NeoPixel LED Strip (60 x WS2812B on XIAO D10 / GPIO 18)
#define LED_STRIP_GPIO_PIN 18
#define LED_STRIP_NUM_LEDS 60
#define LED_FRAME_PERIOD_MS 20

// Speaker / Piezo Buzzer (on XIAO D0 / GPIO 0)
#define SPEAKER_LEDC_GPIO_PIN 0
#define SPEAKER_LEDC_TIMER 0
#define SPEAKER_LEDC_CHANNEL 0
#define SPEAKER_LEDC_RES_BITS 10
#define SPEAKER_LEDC_DEFAULT_FREQ_HZ 440

// Seeed Studio XIAO ESP32-C6 Onboard RF Antenna Switch & Status LED
#define XIAO_RF_SWITCH_ENABLE_GPIO 3
#define XIAO_RF_SWITCH_SELECT_GPIO 14
#define XIAO_USE_EXTERNAL_ANTENNA 0
#define XIAO_STATUS_LED_GPIO 15

// Wi-Fi Access Point & Captive Portal Settings
#define XMAS_AP_SSID "AITY-Xmas-Tree"
#define XMAS_AP_PASSWORD ""
#define XMAS_AP_CHANNEL 6
#define XMAS_AP_MAX_CLIENTS 4
#define XMAS_AP_IP_STR "192.168.4.1"
#define XMAS_AP_IP_OCTET_0 192
#define XMAS_AP_IP_OCTET_1 168
#define XMAS_AP_IP_OCTET_2 4
#define XMAS_AP_IP_OCTET_3 1

#define XMAS_DNS_PORT 53
#define XMAS_HTTP_PORT 80

#endif // BOARD_CONFIG_H
