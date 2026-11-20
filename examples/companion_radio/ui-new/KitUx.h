#pragma once

#include "ZygisEinkSplashArt.h"

// MeshCore Solo subtitle in a 5×7 font for the column beside the emblem.
inline constexpr int kitSubtitleWidth = 77, kitSubtitleHeight = 7;
inline constexpr uint8_t kitSubtitle[] = {
  0x88, 0x00, 0x20, 0x70, 0x00, 0x00, 0x01, 0xe0, 0x18, 0x00,
  0xd8, 0x00, 0x20, 0x88, 0x00, 0x00, 0x02, 0x00, 0x08, 0x00,
  0xa9, 0xc7, 0xac, 0x81, 0xcb, 0x1c, 0x02, 0x07, 0x08, 0x70,
  0xaa, 0x28, 0x32, 0x82, 0x2c, 0xa2, 0x01, 0xc8, 0x88, 0x88,
  0x8b, 0xe7, 0x22, 0x82, 0x28, 0x3e, 0x00, 0x28, 0x88, 0x88,
  0x8a, 0x00, 0xa2, 0x8a, 0x28, 0x20, 0x00, 0x28, 0x88, 0x88,
  0x89, 0xcf, 0x22, 0x71, 0xc8, 0x1c, 0x03, 0xc7, 0x1c, 0x70,
};

inline void drawKitBoot(DisplayDriver& d, unsigned stage, const char* label) {
  d.setColor(UIColor::primary_txt);
  d.setTextSize(1);
  const int cx = d.width() / 2;
  const int labelY = d.height() - d.getLineHeight() - 5;
  const int logoY = 10;
  const int logoCenterY = logoY + zygisEmblemHeight / 2;
  const int logosWidth = zygisEmblemWidth + 8 + zygisWordmarkWidth;
  const int logoX = (d.width() - logosWidth) / 2;
  d.drawXbm(logoX, logoY, zygisEmblem, zygisEmblemWidth, zygisEmblemHeight);
  const int titleX = logoX + zygisEmblemWidth + 8;
  const int titleY = logoCenterY - (zygisWordmarkHeight + 5 + kitSubtitleHeight) / 2;
  d.drawXbm(titleX, titleY, zygisWordmark, zygisWordmarkWidth, zygisWordmarkHeight);
  d.drawXbm(titleX + (zygisWordmarkWidth - kitSubtitleWidth) / 2,
            titleY + zygisWordmarkHeight + 5, kitSubtitle, kitSubtitleWidth, kitSubtitleHeight);

  const int logoBottom = logoY + zygisEmblemHeight;
  const int creditY = logoBottom + (labelY - 9 - logoBottom - zygisCreditHeight - 3) / 2;
  d.drawXbm(cx - zygisCreditWidth / 2, creditY,
            zygisCredit, zygisCreditWidth, zygisCreditHeight);
  d.fillRect(logoX, logoBottom + (creditY - logoBottom) / 2, logosWidth, 1);
  const int width = d.width() - 20;
  d.drawRect(10, labelY - 6, width, 5);
  if (stage > 0) d.fillRect(11, labelY - 5, (width - 2) * stage / 5, 3);
  d.drawTextCentered(cx, labelY, label);
}

inline bool kitLockHintWraps(DisplayDriver& d) {
  return d.getTextWidth("Press Up then Square") > d.width() - 4;
}

inline void drawKitLockHint(DisplayDriver& d, int y) {
  const int cx = d.width() / 2;
  const int x = cx - 19;
  d.drawRect(x, y, 14, 14);
  d.fillRect(x + 6, y + 3, 2, 8);
  d.fillRect(x + 5, y + 4, 4, 2);
  d.fillRect(x + 4, y + 5, 6, 2);
  d.fillRect(x + 18, y + 6, 5, 2);
  d.drawRect(x + 26, y, 14, 14);
  d.drawRect(x + 30, y + 4, 6, 6);
  if (!kitLockHintWraps(d)) {
    d.drawTextCentered(cx, y + 18, "Press Up then Square");
  } else {
    d.drawTextCentered(cx, y + 18, "Press Up then");
    d.drawTextCentered(cx, y + 18 + d.getLineHeight(), "Square");
  }
}
