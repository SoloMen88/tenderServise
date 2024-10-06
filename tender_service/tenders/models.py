import uuid
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Organization(models.Model):
    """Класс моделей организаций.
    Настроен для исползования уже существующей таблицы в БД 'organization'
    с соответствующими полями."""

    ORGANIZATION_TYPE_CHOICES = [
        ('IE', 'IE'),
        ('LLC', 'LLC'),
        ('JSC', 'JSC'),
    ]
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=3, choices=ORGANIZATION_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization'
        # managed = False

    def __str__(self):
        return self.name


class Employee(models.Model):
    """Класс моделей пользователей.
    Настроен для исползования уже существующей таблицы в БД 'employee'
    с соответствующими полями."""

    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee'
        # managed = False

    def __str__(self):
        return self.username


class OrganizationResponsible(models.Model):
    """Класс моделей сотрудников организаций.
    Настроен для исползования уже существующей таблицы в БД
    'organization_responsible' с соответствующими полями."""

    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(Employee, on_delete=models.CASCADE)

    class Meta:
        db_table = 'organization_responsible'
        # managed = False


class Tender(models.Model):
    """Класс моделей тендеров."""

    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('Published', 'Published'),
        ('Closed', 'Closed'),
    ]
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    service_type = models.CharField(verbose_name='serviceType', max_length=50)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    creator = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='created_tenders')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ('name',)


class TenderArhive(models.Model):
    """Класс архивных моделей тендеров.
    Добавлено поле 'tender_id' для поиска тендера."""

    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('Published', 'Published'),
        ('Closed', 'Closed'),
    ]
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    service_type = models.CharField(verbose_name='serviceType', max_length=50)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='organization_rar')
    creator = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='created_tenders_rar')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)
    tender_id = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)


class Bid(models.Model):
    """Класс моделей предложений."""

    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('Published', 'Published'),
        ('Canceled', 'Canceled'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    AUTHOR_TYPE_CHOICES = [
        ('Organization', 'Organization'),
        ('User', 'User'),
    ]
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    tender = models.ForeignKey(
        Tender, on_delete=models.CASCADE, related_name='bids')
    organization = models.ForeignKey(
        Organization, on_delete=models.SET_NULL, blank=True, null=True)
    creator = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='created_bids')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)
    authorType = models.CharField(max_length=15, choices=AUTHOR_TYPE_CHOICES)
    quorum = models.PositiveIntegerField(default=0)
    approved_list = ArrayField(
        models.UUIDField(), blank=True, default=list)


class BidArhive(models.Model):
    """Класс архивных моделей предложений.
    Добавлено поле 'bid_id' для поиска предложения."""

    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('Published', 'Published'),
        ('Canceled', 'Canceled'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    AUTHOR_TYPE_CHOICES = [
        ('Organization', 'Organization'),
        ('User', 'User'),
    ]
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    tender = models.ForeignKey(
        Tender, on_delete=models.CASCADE, related_name='bids_rar')
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        related_name='organization_bid_rar',
        blank=True,
        null=True)
    creator = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='created_bids_rar')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)
    bid_id = models.CharField(max_length=100)
    authorType = models.CharField(max_length=15, choices=AUTHOR_TYPE_CHOICES)


class Review(models.Model):
    """Класс моделей отзывов.
    'author_feedback' это автор отзыва, 'user' это автор предложения."""

    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False)
    bid = models.ForeignKey(Bid, related_name='reviews',
                            on_delete=models.CASCADE)
    author_feedback = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='review_author_feedback')
    description = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Employee, on_delete=models.CASCADE)
