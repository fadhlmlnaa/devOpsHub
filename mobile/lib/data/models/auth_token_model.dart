import 'user_model.dart';

class AuthTokenModel {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final UserModel? user;

  AuthTokenModel({
    required this.accessToken,
    required this.refreshToken,
    this.tokenType = 'bearer',
    this.user,
  });

  factory AuthTokenModel.fromJson(Map<String, dynamic> json) {
    return AuthTokenModel(
      accessToken: json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
      tokenType: json['token_type'] as String? ?? 'bearer',
      user: json['user'] != null && json['user'] is Map<String, dynamic>
          ? UserModel.fromJson(json['user'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'token_type': tokenType,
      if (user != null) 'user': user!.toJson(),
    };
  }
}
