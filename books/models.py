# 유효성 통과 확인
## python run_with_tunnel.py import_books --file ./book.csv --dry-run
# 실제 반영
## python run_with_tunnel.py import_books --file ./book.csv

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings

# Create your models here.
class Book(models.Model):
    BOOK_STATUS_CHOICES = [
        ('AVAILABLE', '대출가능'),
        ('RENTED', '대출중'),
        ('RESERVED', '예약중'),
        ('UNAVAILABLE', '대출불가'),
    ]

    book_code = models.CharField(max_length=30, unique=True) # 장서등록번호
    title = models.CharField(max_length=200, null=True, blank=True) # 표제
    author = models.CharField(max_length=200, null=True, blank=True) # 저자사항
    publisher = models.CharField(max_length=200, blank=True, null=True) # 출판사
    isbn = models.CharField(max_length=20, null=True, blank=True) # ISBN
    callnumber = models.CharField(max_length=200, null=True, blank=True) # 청구기호
    location = models.CharField(max_length=20, blank=True, null=True) # 위치
    edition = models.CharField(max_length=100, null=True, blank=True) # 판사항
    desc = models.TextField(null=True, blank=True) # 총서사항
    book_status = models.CharField(max_length=20, choices=BOOK_STATUS_CHOICES, default='AVAILABLE')  # 도서 상태
    # image = models.ImageField(upload_to='book_images/', null=True, blank=True)  # 표지 이미지
    image_url = models.URLField(null=True, blank=True)

    liked_users = models.ManyToManyField( # 좋아요
        settings.AUTH_USER_MODEL,
        related_name='liked_books',
        blank=True
    )

    def __str__(self):
        return f"{self.title} ({self.book_code})"

class Marc(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='marc')
    data = models.JSONField("MARC JSON", default=dict, blank=True, encoder=DjangoJSONEncoder)


    field_020        = models.TextField("020", null=True, blank=True)
    field_020_set    = models.TextField("020(세트)", null=True, blank=True)
    field_022        = models.TextField("022", null=True, blank=True)
    field_052        = models.TextField("052", null=True, blank=True)
    field_056        = models.TextField("056", null=True, blank=True)
    field_090        = models.TextField("090", null=True, blank=True)

    field_245        = models.TextField("245", null=True, blank=True)
    field_246_same   = models.TextField("246(대등표제)", null=True, blank=True)
    field_246_origin = models.TextField("246(원표제)", null=True, blank=True)
    field_250        = models.TextField("250", null=True, blank=True)

    field_260        = models.TextField("260", null=True, blank=True)
    field_300        = models.TextField("300", null=True, blank=True)
    field_310        = models.TextField("310", null=True, blank=True)
    field_362        = models.TextField("362", null=True, blank=True)

    field_490        = models.TextField("490", null=True, blank=True)

    field_500        = models.TextField("500", null=True, blank=True)
    field_502        = models.TextField("502", null=True, blank=True)
    field_504        = models.TextField("504", null=True, blank=True)
    field_541        = models.TextField("541", null=True, blank=True)
    field_546        = models.TextField("546", null=True, blank=True)
    field_586        = models.TextField("586", null=True, blank=True)
    field_590        = models.TextField("590", null=True, blank=True)

    field_600        = models.TextField("600", null=True, blank=True)
    field_610        = models.TextField("610", null=True, blank=True)
    field_647        = models.TextField("647", null=True, blank=True)
    field_650        = models.TextField("650", null=True, blank=True)
    field_653        = models.TextField("653", null=True, blank=True)
    field_655        = models.TextField("655", null=True, blank=True)

    field_700        = models.TextField("700", null=True, blank=True)
    field_710        = models.TextField("710", null=True, blank=True)
    field_720        = models.TextField("720", null=True, blank=True)
    field_730        = models.TextField("730", null=True, blank=True)

    field_856        = models.TextField("856", null=True, blank=True)

    def __str__(self):
        return f"{self.book.title} ({self.book.book_code})"
    
    def build_json(self):
        j = {}

        def put(tag, key, val):
            if not val:
                return
            j.setdefault(tag, {})
            j[tag][key] = val

        # 020
        put("020", "a", self.field_020)
        put("020", "set", self.field_020_set)

        # 단일 텍스트/문자열 계열
        simple_map = {
            "022": self.field_022,
            "052": self.field_052,
            "056": self.field_056,
            "090": self.field_090,
            "245": self.field_245,
            "250": self.field_250,
            "260": self.field_260,
            "300": self.field_300,
            "310": self.field_310,
            "362": self.field_362,
            "490": self.field_490,
            "500": self.field_500,
            "502": self.field_502,
            "504": self.field_504,
            "541": self.field_541,
            "546": self.field_546,
            "586": self.field_586,
            "590": self.field_590,
            "600": self.field_600,
            "610": self.field_610,
            "647": self.field_647,
            "650": self.field_650,
            "653": self.field_653,
            "655": self.field_655,
            "700": self.field_700,
            "710": self.field_710,
            "720": self.field_720,
            "730": self.field_730,
            "856": self.field_856,
        }
        for tag, val in simple_map.items():
            put(tag, "a", val)

        # 246
        if self.field_246_same:
            put("246", "parallel_title", self.field_246_same)
        if self.field_246_origin:
            put("246", "original_title", self.field_246_origin)

        return j

    def save(self, *args, **kwargs):
        # save 시 JSON 동기화
        self.data = self.build_json()
        super().save(*args, **kwargs)

class TargetName(models.Model):
    name = models.CharField("이용자대상주기",  max_length=200, unique=True)

    class Meta:
        verbose_name = "TargetName"

    def __str__(self):
        return self.name

class Target(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="targets", null=True, blank=True)
    target = models.ForeignKey(TargetName, on_delete=models.PROTECT, related_name="book_targets")

    field_521 = models.CharField("521(이용자대상주기)", max_length=200, null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Target"
        # verbose_name_plural = "Target"
        # 같은 책에 같은 전거 중복 금지
        constraints = [
            models.UniqueConstraint(fields=["book", "target"], name="uq_target_book_authority")
        ]

    def save(self, *args, **kwargs):
        # 전거가 바뀌면 field_521 텍스트를 동기화
        self.field_521 = self.target.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title}"

class Curation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="curations")
    field_500_curation = models.TextField("500(큐레이션 주기)")

    class Meta:
        verbose_name = "Curation"
        # verbose_name_plural = "Curation"

    def __str__(self):
        return f"Curation[{self.book.title}]"