from rest_framework import serializers

from social_media.models import Comment, Profile, Post


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        read_only_fields = ("author", "post", "created_at")
        model = Comment
        fields = ("author", "post", "content", "created_at")


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("username", "profile_image", "biography")

    def validate(self, attrs):
        user = self.context["request"].user
        attrs["user"] = user
        return attrs


class ProfileListSerializer(ProfileSerializer):
    followers = serializers.IntegerField(source="followers.count")
    following = serializers.IntegerField(source="following.count")

    class Meta:
        model = Profile
        fields = (
            "username",
            "profile_image",
            "biography",
            "followers",
            "following"
        )


class ProfileDetailSerializer(ProfileSerializer):
    followers = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="username"
    )
    following = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="username"
    )

    class Meta:
        model = Profile
        fields = (
            "username",
            "profile_image",
            "biography",
            "followers",
            "following"
        )


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("profile_image",)


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            "title",
            "content",
            "author",
            "scheduled_time",
            "post_image"
        )
        read_only_fields = ("author",)

    def validate(self, attrs):
        user_profile = self.context["request"].user.profile
        attrs["author"] = user_profile

        return attrs

    def create(self, validated_data):
        scheduled_time = validated_data.get("scheduled_time")

        if scheduled_time:
            from .tasks import create_scheduled_post

            create_scheduled_post.apply_async(
                args=[
                    validated_data["title"],
                    validated_data["content"],
                    validated_data["author"],
                    scheduled_time,
                    validated_data["post_image"],
                ],
                eta=scheduled_time,
            )

            return validated_data

        post = Post.objects.create(**validated_data)
        return post


class PostListSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(read_only=True, slug_field="username")
    comments = serializers.IntegerField(source="comments.count", read_only=True)
    likes = serializers.IntegerField(source="likes.count", read_only=True)
    write_only_fields = ("scheduled_time",)

    class Meta:
        model = Post
        fields = (
            "author",
            "title",
            "content",
            "created_at",
            "post_image",
            "comments",
            "likes",
            "scheduled_time"
        )


class PostDetailSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(read_only=True, slug_field="username")
    comments = CommentSerializer(many=True, read_only=True)
    likes = serializers.IntegerField(source="likes.count", read_only=True)
    write_only_fields = ("scheduled_time",)

    class Meta:
        model = Post
        fields = (
            "author",
            "title",
            "content",
            "created_at",
            "post_image",
            "comments",
            "likes",
            "scheduled_time",
        )


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("post_image",)
