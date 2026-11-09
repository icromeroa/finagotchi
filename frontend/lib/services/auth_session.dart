
class AuthSession {
  AuthSession._();

  static String? accessToken;
  static String? refreshToken;
  static Map<String, dynamic>? user;

  static bool get isAuthenticated => accessToken != null;

  static void start({
    required String newAccessToken,
    required String newRefreshToken,
    Map<String, dynamic>? userData,
  }) {
    accessToken = newAccessToken;
    refreshToken = newRefreshToken;
    user = userData;
  }

  static void updateTokens({
    required String newAccessToken,
    required String newRefreshToken,
  }) {
    accessToken = newAccessToken;
    refreshToken = newRefreshToken;
  }

  static void clear() {
    accessToken = null;
    refreshToken = null;
    user = null;
  }
}
