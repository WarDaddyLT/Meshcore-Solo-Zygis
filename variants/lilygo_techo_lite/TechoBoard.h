#pragma once

#include <MeshCore.h>
#include <Arduino.h>
#include <helpers/NRF52Board.h>
#ifdef TECHO_STATUS_LEDS
#include <helpers/ui/LedBlinkBurst.h>
#endif

// ============================================================
// T-Echo Lite battery pins — hardcoded from LilyGo t_echo_lite_config.h
// NOT using any defines from variant.h for battery measurement
// ============================================================
#define PIN_VBAT_READ         _PINNUM(0, 2)   // BATTERY_ADC_DATA
#define PIN_VBAT_MEAS_EN      _PINNUM(0, 31)  // BATTERY_MEASUREMENT_CONTROL

class TechoBoard : public NRF52BoardDCDC {
#ifdef ZYGIS_KIT_UX
public:
  enum class LedEvent : uint8_t { ChannelMessage, PrivateMessage, RoomMessage, NewChannel,
                                  NewClient, NewRoom, NewRepeater, Count };
  static constexpr uint8_t LED_PATTERN_COUNT = 4;
  static constexpr uint8_t LED_EVENT_COUNT = uint8_t(LedEvent::Count);

private:
  uint8_t ledPatterns[LED_EVENT_COUNT][2] = {};
  struct LedNotice {
    uint32_t started = 0;
    uint8_t pattern = 0;
    bool isOn(uint32_t now) const {
      const uint32_t elapsed = now - started;
      if (elapsed >= 2200) return false;
      if (pattern == 1) return elapsed < 120;
      if (pattern == 2) return elapsed < 360 && elapsed % 240 < 120;
      return pattern == 3 && elapsed < 2100 && elapsed % 700 < 150;
    }
  } ledNotices[2];
#endif
#ifdef TECHO_STATUS_LEDS
  LedBlinkBurst status_led, gps_led;
#endif
public:
#ifdef TECHO_STATUS_LEDS
  void onStatusTransmitted() { status_led.trigger(millis()); }
  void onGPSFix() { gps_led.trigger(millis()); }
  void updateTrackerLeds() {
    uint32_t now = millis();
    bool blueTracking = status_led.isActive(now);
    bool greenTracking = gps_led.isActive(now);
    bool blue = status_led.isOn(now), green = gps_led.isOn(now);
#ifdef ZYGIS_KIT_UX
    if (!blueTracking) blue = ledNotices[0].isOn(now);
    if (!greenTracking) green = ledNotices[1].isOn(now);
#endif
    digitalWrite(LED_BLUE, blue ? LED_STATE_ON : !LED_STATE_ON);
    digitalWrite(LED_GREEN, green ? LED_STATE_ON : !LED_STATE_ON);
  }
#endif
#ifdef ZYGIS_KIT_UX
  uint8_t ledPattern(LedEvent event, uint8_t led) const { return ledPatterns[uint8_t(event)][led]; }
  void setLedPattern(LedEvent event, uint8_t led, uint8_t pattern) { ledPatterns[uint8_t(event)][led] = pattern; }
  void previewLed(uint8_t led, uint8_t pattern) { ledNotices[led] = {millis(), pattern}; }
  void notifyLed(LedEvent event) {
    for (uint8_t led = 0; led < 2; ++led) {
      uint8_t pattern = ledPattern(event, led);
      if (pattern) previewLed(led, pattern);
    }
  }
#endif
  TechoBoard() : NRF52Board("TECHO_OTA") {}
  void begin();
  uint16_t getBattMilliVolts() override;

  const char* getManufacturerName() const override {
    return "LilyGo T-Echo Lite";
  }

  #if defined(P_LORA_TX_LED)
  void onBeforeTransmit() override {
    digitalWrite(P_LORA_TX_LED, LOW);   // turn TX LED on
  }

  void onAfterTransmit() override {
    digitalWrite(P_LORA_TX_LED, HIGH);   // turn TX LED off
  }
  #endif

  void shutdownPeripherals() override {
    NRF52Board::shutdownPeripherals();

    digitalWrite(PIN_VBAT_MEAS_EN, LOW);
    #ifdef LED_RED
    digitalWrite(LED_RED, LOW);
    #endif
    #ifdef LED_GREEN
#ifdef TECHO_STATUS_LEDS
    digitalWrite(LED_GREEN, !LED_STATE_ON);
#else
    digitalWrite(LED_GREEN, LOW);
#endif
    #endif
    #ifdef LED_BLUE
#ifdef TECHO_STATUS_LEDS
    digitalWrite(LED_BLUE, !LED_STATE_ON);
#else
    digitalWrite(LED_BLUE, LOW);
#endif
    #endif
    #ifdef DISP_BACKLIGHT
    digitalWrite(DISP_BACKLIGHT, LOW);
    #endif
    #ifdef PIN_PWR_EN
    digitalWrite(PIN_PWR_EN, LOW);
    #endif
  }
};