#pragma once

#include "KitEmblem.h"
#include "ZygisEinkSplashArt.h"

inline void drawKitBoot(DisplayDriver& d, unsigned stage, const char* label) {
  d.setColor(UIColor::primary_txt);
  d.setTextSize(1);
  const int cx = d.width() / 2;
  const int labelY = d.height() - d.getLineHeight() - 5;
  const int creditY = labelY - 7 - zygisCreditHeight;
  const int wordmarkY = creditY - zygisWordmarkHeight - 2;
  const bool large = d.width() >= kitEmblemWidth && wordmarkY >= kitEmblemHeight;
  const int emblemW = large ? kitEmblemWidth : zygisEmblemWidth;
  const int emblemH = large ? kitEmblemHeight : zygisEmblemHeight;
  const int emblemY = max(0, (wordmarkY - emblemH) / 2);
  d.drawXbm(cx - emblemW / 2, emblemY, large ? kitEmblem : zygisEmblem, emblemW, emblemH);
  d.drawXbm(cx - zygisWordmarkWidth / 2, wordmarkY,
            zygisWordmark, zygisWordmarkWidth, zygisWordmarkHeight);
  d.drawXbm(cx - zygisCreditWidth / 2, creditY,
            zygisCredit, zygisCreditWidth, zygisCreditHeight);
  const int width = d.width() - 20;
  d.drawRect(10, labelY - 6, width, 5);
  if (stage > 0) d.fillRect(11, labelY - 5, (width - 2) * stage / 5, 3);
  d.drawTextCentered(cx, labelY, label);
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
  if (d.getTextWidth("Press Up then Square") <= d.width() - 4) {
    d.drawTextCentered(cx, y + 18, "Press Up then Square");
  } else {
    d.drawTextCentered(cx, y + 18, "Press Up then");
    d.drawTextCentered(cx, y + 18 + d.getLineHeight(), "Square");
  }
}
