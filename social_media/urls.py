from rest_framework.routers import DefaultRouter

from social_media.views import PostViewSet, ProfileViewSet

router = DefaultRouter()
router.register(r"profiles", ProfileViewSet, basename="profile")
router.register(r"posts", PostViewSet, basename="post")

urlpatterns = router.urls

app_name = "social_media"
