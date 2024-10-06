from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class MyPagination(LimitOffsetPagination):
    """Переопределяет стандартный класс пагинации, 
    убирает общий хэдер с навигацией."""

    def get_paginated_response(self, data):
        return Response(data)
