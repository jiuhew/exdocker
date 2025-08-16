from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health(_: object) -> JsonResponse:
	return JsonResponse({"status": "ok"})

urlpatterns = [
	path("admin/", admin.site.urls),
	path("api/health/", health),
	path("api/common/", include("apps.common.urls")),
]


