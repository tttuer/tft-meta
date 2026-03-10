// CompSummary, CompDetail, Board 모델
// 스키마 기준: contracts/api-spec.yaml

class CompSummary {
  final String id;
  final String name;
  final String tier; // S, A, B, C
  final double winRate;
  final double top4Rate;
  final double avgPlacement;
  final double playRate;
  final int sampleCount;
  final String patchVersion;
  final DateTime updatedAt;

  const CompSummary({
    required this.id,
    required this.name,
    required this.tier,
    required this.winRate,
    required this.top4Rate,
    required this.avgPlacement,
    required this.playRate,
    required this.sampleCount,
    required this.patchVersion,
    required this.updatedAt,
  });

  factory CompSummary.fromJson(Map<String, dynamic> json) {
    return CompSummary(
      id: json['id'] as String,
      name: json['name'] as String,
      tier: json['tier'] as String,
      winRate: (json['win_rate'] as num).toDouble(),
      top4Rate: (json['top4_rate'] as num).toDouble(),
      avgPlacement: (json['avg_placement'] as num).toDouble(),
      playRate: (json['play_rate'] as num).toDouble(),
      sampleCount: json['sample_count'] as int,
      patchVersion: json['patch_version'] as String,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'tier': tier,
        'win_rate': winRate,
        'top4_rate': top4Rate,
        'avg_placement': avgPlacement,
        'play_rate': playRate,
        'sample_count': sampleCount,
        'patch_version': patchVersion,
        'updated_at': updatedAt.toIso8601String(),
      };
}

class CompDetail extends CompSummary {
  final Map<String, dynamic> coreUnits;
  final List<dynamic> boardPositions;
  final Map<String, dynamic> recommendedAugments;
  final List<String> entryConditions;
  final String? aiSummary;

  const CompDetail({
    required super.id,
    required super.name,
    required super.tier,
    required super.winRate,
    required super.top4Rate,
    required super.avgPlacement,
    required super.playRate,
    required super.sampleCount,
    required super.patchVersion,
    required super.updatedAt,
    required this.coreUnits,
    required this.boardPositions,
    required this.recommendedAugments,
    required this.entryConditions,
    this.aiSummary,
  });

  factory CompDetail.fromJson(Map<String, dynamic> json) {
    return CompDetail(
      id: json['id'] as String,
      name: json['name'] as String,
      tier: json['tier'] as String,
      winRate: (json['win_rate'] as num).toDouble(),
      top4Rate: (json['top4_rate'] as num).toDouble(),
      avgPlacement: (json['avg_placement'] as num).toDouble(),
      playRate: (json['play_rate'] as num).toDouble(),
      sampleCount: json['sample_count'] as int,
      patchVersion: json['patch_version'] as String,
      updatedAt: DateTime.parse(json['updated_at'] as String),
      coreUnits: (json['core_units'] as Map<String, dynamic>?) ?? {},
      boardPositions: (json['board_positions'] as List<dynamic>?) ?? [],
      recommendedAugments:
          (json['recommended_augments'] as Map<String, dynamic>?) ?? {},
      entryConditions: (json['entry_conditions'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      aiSummary: json['ai_summary'] as String?,
    );
  }
}

class BoardPosition {
  final int row;
  final int col;
  final String championId;
  final List<String> items;
  final int starLevel;

  const BoardPosition({
    required this.row,
    required this.col,
    required this.championId,
    required this.items,
    this.starLevel = 1,
  });

  factory BoardPosition.fromJson(Map<String, dynamic> json) {
    return BoardPosition(
      row: json['row'] as int,
      col: json['col'] as int,
      championId: json['champion_id'] as String,
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      starLevel: (json['star_level'] as int?) ?? 1,
    );
  }
}

class Board {
  final String compId;
  final String compName;
  final List<BoardPosition> boardPositions;

  const Board({
    required this.compId,
    required this.compName,
    required this.boardPositions,
  });

  factory Board.fromJson(Map<String, dynamic> json) {
    return Board(
      compId: json['comp_id'] as String,
      compName: json['comp_name'] as String,
      boardPositions: (json['board_positions'] as List<dynamic>? ?? [])
          .map((e) => BoardPosition.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class MetaSummary {
  final String patchVersion;
  final String generatedAt;
  final List<CompSummary> topComps;
  final String aiSummary;

  const MetaSummary({
    required this.patchVersion,
    required this.generatedAt,
    required this.topComps,
    required this.aiSummary,
  });

  factory MetaSummary.fromJson(Map<String, dynamic> json) {
    return MetaSummary(
      patchVersion: json['patch_version'] as String,
      generatedAt: json['generated_at'] as String,
      topComps: (json['top_comps'] as List<dynamic>? ?? [])
          .map((e) => CompSummary.fromJson(e as Map<String, dynamic>))
          .toList(),
      aiSummary: (json['ai_summary'] as String?) ?? '',
    );
  }
}
