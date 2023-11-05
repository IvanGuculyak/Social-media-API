import os.path
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify


def profile_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.username)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/profile_image/", filename)


class Profile(models.Model):
    username = models.CharField(
        max_length=64,
        unique=True,
        default="username"
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    followers = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="following",
        blank=True
    )
    profile_image = models.ImageField(
        upload_to=profile_image_file_path,
        blank=True,
        null=True
    )
    biography = models.TextField(blank=True)

    def follow(self, profile):
        self.following.add(profile)

    def unfollow(self, profile):
        self.following.remove(profile)


def post_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.created_at)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/posts/", filename)


class Post(models.Model):
    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    title = models.CharField(max_length=64, default="Title")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(
        upload_to=post_image_file_path,
        blank=True,
        null=True
    )
    likes = models.ManyToManyField(
        Profile,
        related_name="post_liked",
        blank=True
    )
    scheduled_time = models.DateTimeField(null=True, blank=True)


class Comment(models.Model):
    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
