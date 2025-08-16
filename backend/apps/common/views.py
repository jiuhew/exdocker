from django.http import JsonResponse
from .tasks import add


def add_view(request):
	try:
		x = int(request.GET.get("x", "1"))
		y = int(request.GET.get("y", "2"))
		result = add.delay(x, y)
		return JsonResponse({"task_id": result.id, "queued": True})
	except Exception as exc:  # noqa: BLE001
		return JsonResponse({"error": str(exc)}, status=400)


