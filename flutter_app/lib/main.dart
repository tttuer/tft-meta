import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'core/theme.dart';
import 'core/constants.dart';
import 'screens/home_screen.dart';
import 'screens/comp_list_screen.dart';
import 'screens/comp_detail_screen.dart';
import 'screens/champion_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    const ProviderScope(
      child: TftMetaAdvisorApp(),
    ),
  );
}

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    ShellRoute(
      builder: (context, state, child) => _RootShell(child: child),
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const HomeScreen(),
        ),
        GoRoute(
          path: '/comps',
          builder: (context, state) => const CompListScreen(),
        ),
        GoRoute(
          path: '/champions',
          builder: (context, state) => const ChampionScreen(),
        ),
      ],
    ),
    // 컴프 상세는 ShellRoute 밖 — 별도 앱바 + 뒤로가기 버튼
    GoRoute(
      path: '/comps/:compId',
      builder: (context, state) {
        final compId = state.pathParameters['compId']!;
        return CompDetailScreen(compId: compId);
      },
    ),
  ],
);

class TftMetaAdvisorApp extends StatelessWidget {
  const TftMetaAdvisorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'TFT Meta Advisor',
      theme: AppTheme.darkTheme,
      routerConfig: _router,
      debugShowCheckedModeBanner: false,
    );
  }
}

class _RootShell extends StatelessWidget {
  final Widget child;

  const _RootShell({required this.child});

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    if (location.startsWith('/comps')) return 1;
    if (location.startsWith('/champions')) return 2;
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        backgroundColor: AppColors.surface,
        indicatorColor: AppColors.primary.withAlpha(102),
        selectedIndex: _currentIndex(context),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined, color: AppColors.textSecondary),
            selectedIcon: Icon(Icons.home, color: AppColors.accent),
            label: '홈',
          ),
          NavigationDestination(
            icon: Icon(Icons.list_outlined, color: AppColors.textSecondary),
            selectedIcon: Icon(Icons.list, color: AppColors.accent),
            label: '컴프',
          ),
          NavigationDestination(
            icon: Icon(Icons.people_outlined, color: AppColors.textSecondary),
            selectedIcon: Icon(Icons.people, color: AppColors.accent),
            label: '챔피언',
          ),
        ],
        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              context.go('/');
            case 1:
              context.go('/comps');
            case 2:
              context.go('/champions');
          }
        },
      ),
    );
  }
}
