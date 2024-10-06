from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import MyPagination
from .models import (Tender, Bid, Review, TenderArhive, BidArhive,
                     OrganizationResponsible, Employee)
from .serializers import TenderSerializer, BidSerializer, ReviewSerializer


class TenderViewSet(viewsets.ModelViewSet):
    """Вьюсет для обработки корневого эндпоинта /tenders.
    В методах выполняются проверки на существование/корректность переданых 
    ползователей и тендеров, а также права доступа."""

    queryset = Tender.objects.all()
    serializer_class = TenderSerializer
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('service_type',)

    def get_queryset(self):
        """Возвращает кверисэт предварительно отфильтрованный по пользователю 
        и статусу, автору тендера отдает с любым статусом, всем остальным 
        только опубликованные."""

        queryset = Tender.objects.all()
        username = self.request.query_params.get('username')
        if username:
            username = Employee.objects.get(username=username)
        queryset = queryset.filter(
            creator=username) | queryset.filter(status='Published')
        return queryset

    @action(detail=False, methods=['get'])
    def my(self, request):
        """Метод для обработки GET запроса к эндпоинту tenders/my
        Возвращает список тендеров созданых пользователем."""

        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        tenders = Tender.objects.filter(creator=username)
        if not tenders:
            return Response(
                {'error': 'Пользователь не создал тендеры.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = self.get_serializer(tenders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'put'])
    def status(self, request, pk=None):
        """Метод для обработки GET и PUT запросов к эндпоинту tenders/status
        Возвращает/редактирует статус тендера."""

        try:
            tender = Tender.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Тендер не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if self.request.method == 'GET':
            if tender.status == 'Published' or tender.creator == username:
                return Response({"status": tender.status})
            else:
                return Response(
                    {'error': 'Недостаточно прав для выполнения действия.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        if tender.creator != username:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        status_ = self.request.query_params.get('status')
        if status_ in dict(Tender.STATUS_CHOICES):
            tender.status = status_
            tender.save()
            serializer = self.get_serializer(tender, partial=True)
            return Response(serializer.data)
        return Response(
            {'error': 'Неверный формат запроса или его параметры.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['patch'])
    def edit(self, request, pk=None):
        """Метод для обработки PATCH запросов к эндпоинту tenders/edit
        Редактирует параметры тендера с сохранением текущей версии в 
        архивную модель."""

        try:
            tender = Tender.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Тендер не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if tender.creator != username:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        request.data['version'] = tender.version + 1
        serializer = self.get_serializer(
            tender, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            tender = Tender.objects.get(pk=serializer.data['id'])
            tender_arhive = TenderArhive(
                name=tender.name,
                description=tender.description,
                service_type=tender.service_type,
                status=tender.status,
                organization=tender.organization,
                creator=tender.creator,
                version=tender.version,
                tender_id=tender.pk
            )
            tender_arhive.save()
            return Response(serializer.data)
        return Response(
            {'error': 'Неверный формат запроса или его параметры.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, url_path='new', methods=['post'])
    def new(self, request, pk=None):
        """Метод для обработки POST запросов к эндпоинту tenders/new
        Создает новый тендер с передаными параметрами."""

        try:
            user = Employee.objects.get(
                username=request.data['creatorUsername'])
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        request.data['creatorUsername'] = user.pk
        serializer = self.get_serializer(
            data=request.data, partial=True)
        if 'status' not in request.data:
            request.data['status'] = 'Created'
        if serializer.is_valid():
            try:
                organizationresponsible = OrganizationResponsible.objects.get(
                    organization=serializer.validated_data['organization_id'],
                    user=user
                )
            except:
                return Response(
                    {'error': 'Пользователь не существует или некорректен.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            if user != organizationresponsible.user:
                return Response(
                    {'error': 'Недостаточно прав для выполнения действия.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.validated_data['creator_id'] = user.pk
            serializer.save()
            tender = Tender.objects.get(pk=serializer.data['id'])
            tender_arhive = TenderArhive(
                name=tender.name,
                description=tender.description,
                service_type=tender.service_type,
                status=tender.status,
                organization=tender.organization,
                creator=tender.creator,
                version=tender.version,
                tender_id=tender.pk
            )
            tender_arhive.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'], url_path='rollback/(?P<rollback_id>\d+)')
    def rollback(self, request, pk=None, rollback_id=None):
        """Метод для обработки PUT запросов к эндпоинту tenders/rollback
        Откатывает версию тендера на переданую."""

        try:
            tender = Tender.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Тендер не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if tender.creator != username:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            tender_arhive = TenderArhive.objects.get(
                version=rollback_id, tender_id=pk)
        except:
            return Response(
                {'error': 'Версия не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )
        tender.name = tender_arhive.name
        tender.description = tender_arhive.description
        tender.service_type = tender_arhive.service_type
        tender.status = tender_arhive.status
        tender.organization = tender_arhive.organization
        tender.creator = tender_arhive.creator
        tender.version = tender.version + 1
        tender.save()
        tender_arhive = TenderArhive(
            name=tender.name,
            description=tender.description,
            service_type=tender.service_type,
            status=tender.status,
            organization=tender.organization,
            creator=tender.creator,
            version=tender.version,
            tender_id=tender.pk
        )
        tender_arhive.save()
        serializer = self.get_serializer(tender, partial=True)
        return Response(serializer.data)


class BidViewSet(viewsets.ModelViewSet):
    """Вьюсет для обработки корневого эндпоинта /bids.
    В методах выполняются проверки на существование/корректность переданых 
    ползователей, тендеров и предложений, а также права доступа."""

    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    pagination_class = MyPagination

    STATUS_DISABLE = ['Approved', 'Rejected']

    def get_queryset(self):
        """Возвращает кверисэт предварительно отфильтрованный по пользователю 
        и статусу, автору тендера отдает с любым статусом, всем остальным 
        только опубликованные."""

        queryset = Bid.objects.all()
        username = self.request.query_params.get('username')
        if username:
            username = Employee.objects.get(username=username)
        queryset = queryset.filter(
            creator=username) | queryset.filter(status='Published')
        return queryset

    @action(detail=False, url_path='new', methods=['post'])
    def new(self, request, pk=None):
        """Метод для обработки POST запросов к эндпоинту bids/new
        Создает новое предложение с передаными параметрами."""

        try:
            user = Employee.objects.get(
                pk=request.data['authorId'])
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            tender = Tender.objects.get(pk=request.data['tenderId'])
        except:
            return Response(
                {'error': 'Тендер не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if tender.status != 'Published':
            return Response(
                {'error': 'Тендер не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        request.data['status'] = 'Created'
        if request.data.get('authorType') == "Organization":
            try:
                organizationresponsible = OrganizationResponsible.objects.get(
                    user=user)
            except:
                return Response(
                    {'error': 'Пользователь не существует или некорректен.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            request.data['organizationId'] = organizationresponsible.organization.pk
        else:
            request.data['authorType'] = 'User'
        serializer = self.get_serializer(
            data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            bid = Bid.objects.get(pk=serializer.data['id'])
            bid_arhive = BidArhive(
                name=bid.name,
                description=bid.description,
                tender=bid.tender,
                status=bid.status,
                organization=bid.organization,
                creator=bid.creator,
                version=bid.version,
                bid_id=bid.pk,
                authorType=bid.authorType
            )
            bid_arhive.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='(?P<pk>[^/.]+)/list')
    def lists(self, request, pk=None):
        """Метод для обработки GET запросов к эндпоинту bids/lists
        Возвращает все предложения по указанному тендеру, автоу предложения 
        будут показаны только его предложения, автору тендера будут показаны 
        все предложения со статусом опубликовно."""

        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            bids = Bid.objects.filter(tender=pk)
        except:
            return Response(
                {'error': 'Тендер не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if not bids:
            return Response(
                {'error': 'Предложений не найдено.'},
                status=status.HTTP_404_NOT_FOUND
            )
        bids = bids.filter(
            tender__creator=username, status='Published') | bids.filter(creator=username)
        if not bids:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(bids, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my(self, request):
        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        bids = Bid.objects.filter(creator=username)
        serializer = self.get_serializer(bids, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'put'])
    def status(self, request, pk=None):
        """Метод для обработки GET и PUT запросов к эндпоинту bids/status
        Возвращает/редактирует статус предложения."""

        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            bid = Bid.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Предложение не найдено.'},
                status=status.HTTP_404_NOT_FOUND
            )
        tender = bid.tender
        if self.request.method == 'GET':
            if (
                (tender.creator == username
                 and bid.status not in ('Created', 'Canceled'))
                or (bid.creator == username)
            ):
                return Response(bid.status)
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        status_ = self.request.query_params.get('status')
        if bid.creator != username:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if status_ not in self.STATUS_DISABLE:
            bid.status = status_
            bid.save()
            serializer = self.get_serializer(
                bid, data=request.data, partial=True)
            serializer.is_valid()
            return Response(serializer.data)
        return Response(
            {'error': 'Недостаточно прав для выполнения действия.'},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=True, methods=['patch'])
    def edit(self, request, pk=None):
        """Метод для обработки PATCH запросов к эндпоинту bids/edit
        Редактирует параметры предложения с сохранением текущей версии в 
        архивную модель."""

        try:
            bid = Bid.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Предложение не найдено.'},
                status=status.HTTP_404_NOT_FOUND
            )
        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if bid.creator != username:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        request.data['version'] = bid.version + 1
        serializer = self.get_serializer(
            bid, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            bid = Bid.objects.get(pk=serializer.data['id'])
            bid_arhive = BidArhive(
                name=bid.name,
                description=bid.description,
                tender=bid.tender,
                status=bid.status,
                organization=bid.organization,
                creator=bid.creator,
                version=bid.version,
                bid_id=bid.pk,
                authorType=bid.authorType
            )
            bid_arhive.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def submit_decision(self, request, pk=None):
        """Метод для обработки PUT запросов к эндпоинту bids/submit-decision
        Отклоняет либо приниает предложение по тендеру и закрывает тендер."""

        username = self.request.query_params.get('username')
        status_ = self.request.query_params.get('decision')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            bid = Bid.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Предложение не найдено.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            OrganizationResponsible.objects.get(
                organization=bid.tender.organization, user=username)
        except:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if username.pk in bid.approved_list:
            return Response(
                {'error': 'Вы уже голосовали за это предложение.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if status_ == 'Approved' and bid.status != 'Rejected':
            quorum = min(3, len(OrganizationResponsible.objects.filter(
                organization=bid.tender.organization)))
            bid.quorum += 1
            bid.approved_list.append(username.pk)
            if bid.quorum >= quorum:
                bid.tender.status = 'Closed'
                bid.tender.save()
                bid.status = status_
            bid.save()
        elif bid.status == 'Rejected':
            return Response(
                {'error': 'Предложение уже отклонено другим сотрудником.'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif status_ == 'Rejected' and bid.status == 'Approved':
            bid.approved_list.append(username.pk)
            bid.status = status_
            bid.tender.status = 'Published'
            bid.tender.save()
            bid.save()
        else:
            bid.status = status_
            bid.tender.save()
            bid.save()
        serializer = self.get_serializer(bid, partial=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def feedback(self, request, pk=None):
        """Метод для обработки PUT запросов к эндпоинту bids/feedback
        Сохраняет отзыв по предложению."""

        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            bid = Bid.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Предложение не найдено.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            OrganizationResponsible.objects.get(
                organization=bid.tender.organization, user=username)
        except:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        bidFeedback = self.request.query_params.get('bidFeedback')
        feedback = Review(
            bid=bid,
            author_feedback=username,
            description=bidFeedback,
            user=bid.creator,
        )
        feedback.save()
        serializer = BidSerializer(bid, many=False)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='rollback/(?P<rollback_id>\d+)')
    def rollback(self, request, pk=None, rollback_id=None):
        """Метод для обработки PUT запросов к эндпоинту bids/rollback
        Откатывает версию предложения на переданую."""

        try:
            bid = Bid.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Предложение не найдено.'},
                status=status.HTTP_404_NOT_FOUND
            )
        username = self.request.query_params.get('username')
        try:
            username = Employee.objects.get(username=username)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if bid.creator != username:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            bid_arhive = BidArhive.objects.get(
                version=rollback_id, bid_id=pk)
        except:
            return Response(
                {'error': 'Версия не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )
        bid.name = bid_arhive.name
        bid.description = bid_arhive.description
        bid.tender = bid_arhive.tender
        bid.status = bid_arhive.status
        bid.organization = bid_arhive.organization
        bid.creator = bid_arhive.creator
        bid.authorType = bid_arhive.authorType
        bid.version = bid.version + 1
        bid.save()
        bid_arhive = BidArhive(
            name=bid.name,
            description=bid.description,
            tender=bid.tender,
            status=bid.status,
            organization=bid.organization,
            creator=bid.creator,
            version=bid.version,
            bid_id=bid.pk,
            authorType=bid.authorType
        )
        bid_arhive.save()
        serializer = self.get_serializer(bid, partial=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Метод для обработки GET запросов к эндпоинту bids/reviews
        Возвращает отзывы по предложениям автора."""

        authorUsername = self.request.query_params.get('authorUsername')
        requesterUsername = self.request.query_params.get(
            'requesterUsername')
        try:
            tender = Tender.objects.get(pk=pk)
        except:
            return Response(
                {'error': 'Тендер не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            reviews = Review.objects.filter(bid__tender=pk)
        except:
            return Response(
                {'error': 'Отзывы не найдены.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            requesterUsername = Employee.objects.get(
                username=requesterUsername)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            authorUsername = Employee.objects.get(username=authorUsername)
        except:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            OrganizationResponsible.objects.get(
                organization=tender.organization, user=requesterUsername)
        except:
            return Response(
                {'error': 'Недостаточно прав для выполнения действия.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            bid = Bid.objects.get(tender=tender)
        except:
            return Response(
                {'error': 'Пользователь не делал предложений по указанному тендеру.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if authorUsername != bid.creator:
            return Response(
                {'error': 'Пользователь не существует или некорректен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class PingView(viewsets.ViewSet):
    """Вьюсет для обработки корневого эндпоинта /pind.
    Просто возвращает ок."""

    def list(self, request):
        return Response("ok")
