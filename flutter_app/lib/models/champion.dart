// Champion 모델
// 스키마 기준: contracts/api-spec.yaml

class Champion {
  final String id;
  final String name;
  final int cost;
  final List<String> traits;
  final Map<String, dynamic> bestItems;
  final Map<String, dynamic> itemReasoning;
  final String? imageUrl;

  const Champion({
    required this.id,
    required this.name,
    required this.cost,
    required this.traits,
    required this.bestItems,
    required this.itemReasoning,
    this.imageUrl,
  });

  factory Champion.fromJson(Map<String, dynamic> json) {
    return Champion(
      id: json['id'] as String,
      name: json['name'] as String,
      cost: (json['cost'] as num).toInt(),
      traits: (json['traits'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      bestItems: (json['best_items'] as Map<String, dynamic>?) ?? {},
      itemReasoning: (json['item_reasoning'] as Map<String, dynamic>?) ?? {},
      imageUrl: json['image_url'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'cost': cost,
        'traits': traits,
        'best_items': bestItems,
        'item_reasoning': itemReasoning,
        'image_url': imageUrl,
      };
}
