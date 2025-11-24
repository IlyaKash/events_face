from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class UserRegistrationSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True, validators=[validate_password])
    password_confirmation=serializers.CharField(write_only=True)

    class Meta:
        model=User
        fields=['username', 'password', 'password_confirmation']
    
    def validate(self, attrs):
        if attrs['password']!=attrs['password_confirmation']:
            raise serializers.ValidationError({
                "password_confirmation" : "paswwrod do not mathc"
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        user=User.objects.create_user(
            username=validated_data["username"],
            password=validated_data['password']
        )
        return user
    
class UserLoginSerializer(serializers.Serializer):
    username=serializers.CharField()
    password=serializers.CharField(write_only=True)

class TokenRefreshSerializer(serializers.Serializer):
    refresh=serializers.CharField()

class LogoutSerializer(serializers.Serializer):
    refresh=serializers.CharField