from urllib.request import Request

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from social_media.models import Profile, Post
from social_media.permissions import IsProfileOwner, IsPostOwner
from social_media.serializers import (
    ProfileListSerializer,
    ProfileDetailSerializer,
    ProfileImageSerializer,
    ProfileSerializer,
    PostSerializer,
    PostListSerializer,
    PostDetailSerializer,
    PostImageSerializer,
    CommentSerializer
)


class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProfileOwner]

    def get_queryset(self) -> QuerySet:
        queryset = Profile.objects.all().prefetch_related(
            "followers", "following"
        )
        username = queryset.query_params.get("username", None)

        if username:
            queryset = queryset.filter(username__icontains=username)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileListSerializer
        elif self.action == "retrieve":
            return ProfileDetailSerializer
        elif self.action == "upload_image":
            return ProfileImageSerializer

        return ProfileSerializer

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def follow(self, request: Request, pk: int = None) -> Response:
        profile = self.get_object()
        user_profile = self.request.user.profile

        if user_profile != profile and profile not in user_profile.following.all():
            user_profile.follow(profile)
            return Response(
                {"detail": "Profile followed successfully"},
                status=status.HTTP_200_OK
            )
        return Response(
            {"detail": "Unable to follow the profile"},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def unfollow(self, request: Request, pk: int = None) -> Response:
        profile = self.get_object()
        user_profile = self.request.user.profile

        if user_profile != profile and profile not in user_profile.following.all():
            user_profile.unfollow(profile)
            return Response(
                {"detail": "Profile unfollowed successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"detail": "Unable to unfollow the profile"},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload_image",
        permission_classes=[IsAuthenticated]
    )
    def upload_image(self, request: Request, pk: int = None) -> Response:
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "username",
                type=OpenApiTypes.STR,
                description="Filter by username (ex. ?username=user)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs) -> list:
        return super().list(request, *args, **kwargs)


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPostOwner]

    def get_queryset(self) -> QuerySet:
        queryset = (
            Post.objects.all()
            .prefetch_related("comments")
            .select_related("author")
        )
        user = self.request.user
        author = self.request.query_params.get("author", None)
        title = self.request.query_params.get("title", None)

        queryset = queryset.filter(
            author__in=user.profile.following.all() | Profile.objects.filter(user=user)
        )

        if author:
            queryset = queryset.filter(author__username__icontains=author)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer
        if self.action == "comment":
            return CommentSerializer
        if self.action == "upload_image":
            return PostImageSerializer
        if self.action == "list":
            return PostListSerializer
        return PostSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload_image",
        permission_classes=[IsAuthenticated, IsPostOwner]
    )
    def upload_image(self, request: Request, pk: int = None) -> Response:
        post = self.get_object()
        serializer = self.get_serializer(post, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def comment(self, request: Request, pk: int = None) -> Response:
        post = self.get_object()
        user_profile = self.request.user.profile
        serializer = CommentSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(
            author=user_profile,
            post=post,
            content=serializer.validated_data["content"]
        )

        return Response(
            {"detail": "Comment added successfully"},
            status=status.HTTP_200_OK
        )

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def like_unlike(self, request: Request, pk: int = None) -> Response:
        post = self.get_object()
        user_profile = self.request.user.profile

        if user_profile not in post.likes.all():
            post.likes.add(user_profile)
            return Response(
                {"detail": "Post liked successfully"},
                status=status.HTTP_200_OK
            )

        post.likes.remove(user_profile)
        return Response(
            {"detail": "Your like was removed"},
            status=status.HTTP_200_OK
        )

    @action(
        methods=["GET"],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def liked_post(self, request: Request) -> Response:
        user_profile = self.request.user.profile
        queryset = Post.objects.filter(likes=user_profile)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "title",
                type=OpenApiTypes.STR,
                description="Filter by title (ex. ?title=title)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs) -> list:
        return super().list(request, *args, **kwargs)
