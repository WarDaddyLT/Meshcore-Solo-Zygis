#pragma once

#include "ZygisEinkSplashArt.h"

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
  d.drawXbm(logoX + zygisEmblemWidth + 8, logoCenterY - zygisWordmarkHeight / 2,
            zygisWordmark, zygisWordmarkWidth, zygisWordmarkHeight);

  const int logoBottom = logoY + zygisEmblemHeight;
  const int creditY = logoBottom + (labelY - 9 - logoBottom - zygisCreditHeight - 3) / 2;
  d.drawXbm(cx - zygisCreditWidth / 2, creditY,
            zygisCredit, zygisCreditWidth, zygisCreditHeight);
  d.fillRect(cx - zygisCreditWidth / 2, creditY + zygisCreditHeight + 2, zygisCreditWidth, 1);
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
