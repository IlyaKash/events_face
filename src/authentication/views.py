from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .serializers import LogoutSerializer, UserLoginSerializer, TokenRefreshSerializer, UserRegistrationSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
# Create your views here.

class RegisterView(APIView):
    permission_classes=[AllowAny]

    def post(self, request):
        serializer=UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user=serializer.save()

            refresh=RefreshToken.for_user(user)
            return Response(
                {
                    'message' : 'User created successfully',
                    'access_token' : str(refresh.access_token),
                    'refresh_token' : str(refresh),
                },
                status=status.HTTP_201_CREATED,

            )
        return Response(
            {"error" : serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

class LoginView(APIView):
    permission_classes=[AllowAny]

    def post(self, request):
        serializer=UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            username=serializer.validated_data['username']
            password=serializer.validated_data['password']

            user=authenticate(username=username, password=password)
            if user:
                refresh=RefreshToken.for_user(user)
                return Response(
                    {
                        'access_token' : str(refresh.access_token),
                        'refresh_token' : str(refresh),
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {'error' : "Invalid username or password"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
class TokenRefreshView(APIView):
    permission_classes=[AllowAny]

    def post(self, request):
        serializer=TokenRefreshSerializer(data=request.data)

        if serializer.is_valid():
            try:
                refresh=RefreshToken(serializer.validated_data['refresh'])
                return Response(
                    {
                        "access_token" : str(refresh.access_token),
                    },
                    status=status.HTTP_200_OK,
                )
            except TokenError:
                return Response(
                    {'error': 'Invalid or expired refresh token'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        return Response(
            {'error': serializer._errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
class LogoutView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self, request):
        serializer=LogoutSerializer(data=request.data)

        if serializer.is_valid():
            try:
                refres_token=RefreshToken(serializer.validated_data)
                refres_token.blacklist()
                return Response(
                    {'message': "Successfully logged out"},
                    status=status.HTTP_200_OK,
                )
            except TokenError:
                return Response(
                    {"error": "Invalid refresh token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {"error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )