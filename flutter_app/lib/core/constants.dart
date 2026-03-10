import 'package:flutter/material.dart';

// 챔피언 코스트별 테두리 색상
const Map<int, Color> costColors = {
  1: Color(0xFF808080),
  2: Color(0xFF2EA94E),
  3: Color(0xFF2277BE),
  4: Color(0xFF9B4FC4),
  5: Color(0xFFCDA855),
};

// 티어 색상
const Map<String, Color> tierColors = {
  'S': Color(0xFFFF6B35),
  'A': Color(0xFFCDA855),
  'B': Color(0xFF9B9B9B),
  'C': Color(0xFF6B8CAE),
};

// 증강 티어 색상
const Map<String, Color> augmentTierColors = {
  'Silver': Color(0xFF9B9B9B),
  'Gold': Color(0xFFCDA855),
  'Prismatic': Color(0xFF9B4FC4),
};

// 앱 색상 팔레트
class AppColors {
  static const Color primary = Color(0xFF1A4B8C);
  static const Color accent = Color(0xFF2E86DE);
  static const Color background = Color(0xFF0F1923);
  static const Color surface = Color(0xFF1C2A3A);
  static const Color gold = Color(0xFFCDA855);
  static const Color textPrimary = Color(0xFFE8E8E8);
  static const Color textSecondary = Color(0xFF9B9B9B);
  static const Color divider = Color(0xFF2A3A4A);
  static const Color error = Color(0xFFE74C3C);
  static const Color emptySlot = Color(0xFF3A3A3A);
}

// 폰트 크기
class AppFontSizes {
  static const double xs = 10.0;
  static const double sm = 12.0;
  static const double md = 14.0;
  static const double lg = 16.0;
  static const double xl = 18.0;
  static const double xxl = 22.0;
  static const double title = 26.0;
}

// 패딩/마진 상수
class AppSpacing {
  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 12.0;
  static const double lg = 16.0;
  static const double xl = 20.0;
  static const double xxl = 24.0;
}

// BoardPainter 상수
class BoardConstants {
  static const int cols = 7;
  static const int rows = 4;
  static const double hexSize = 60.0; // 육각형 가로 크기
  static const double itemSize = 24.0;
  static const double starSize = 12.0;
}
