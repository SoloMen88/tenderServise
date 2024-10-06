from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenderViewSet, BidViewSet, PingView

router = DefaultRouter(trailing_slash=False)
router.register(r'tenders', TenderViewSet)
router.register(r'bids', BidViewSet)
router.register(r'ping', PingView, basename='ping')

urlpatterns = [
    path('api/', include(router.urls)),
]
