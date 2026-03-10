// Augment 모델
// 스키마 기준: contracts/api-spec.yaml

class Augment {
  final String id;
  final String name;
  final String tier; // Silver, Gold, Prismatic
  final String? description;
  final String? imageUrl;
  final List<String> compSynergy;

  const Augment({
    required this.id,
    required this.name,
    required this.tier,
    this.description,
    this.imageUrl,
    required this.compSynergy,
  });

  factory Augment.fromJson(Map<String, dynamic> json) {
    return Augment(
      id: json['id'] as String,
      name: json['name'] as String,
      tier: json['tier'] as String,
      description: json['description'] as String?,
      imageUrl: json['image_url'] as String?,
      compSynergy: (json['comp_synergy'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'tier': tier,
        'description': description,
        'image_url': imageUrl,
        'comp_synergy': compSynergy,
      };
}
