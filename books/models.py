from django.db import models
from django.conf import settings

# Create your models here.
class Book(models.Model):
    BOOK_STATUS_CHOICES = [
        ('대출가능', '대출가능'),
        ('대출중', '대출중'),
        ('예약중', '예약중'),
        ('대출불가', '대출불가'),
    ]

    book_code = models.CharField(max_length=30, unique=True) # 장서등록번호
    title = models.CharField(max_length=200, null=True, blank=True) # 표제
    author = models.CharField(max_length=200, null=True, blank=True) # 저자사항
    publisher = models.CharField(max_length=200, blank=True, null=True) # 출판사
    isbn = models.CharField(max_length=20, null=True, blank=True) # ISBN
    callnumber = models.CharField(max_length=50, null=True, blank=True) # 청구기호
    location = models.CharField(max_length=200, blank=True, null=True) # 위치
    edition = models.CharField(max_length=100, null=True, blank=True) # 판사항
    desc = models.TextField(null=True, blank=True) # 총서사항
    book_status = models.CharField(max_length=20, choices=BOOK_STATUS_CHOICES, default='대출가능')  # 도서 상태
    image = models.ImageField(upload_to='book_images/', null=True, blank=True)  # 표지 이미지

    liked_users = models.ManyToManyField( # 좋아요
        settings.AUTH_USER_MODEL,
        related_name='liked_books',
        blank=True
    )

    def __str__(self):
        return f"{self.title} ({self.book_code})"

class Marc(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='marc')

    field_020        = models.CharField("020", max_length=32, null=True, blank=True)
    field_020_set    = models.CharField("020(세트)", max_length=32, null=True, blank=True)
    field_022        = models.CharField("022", max_length=32, null=True, blank=True)
    field_052        = models.CharField("052", max_length=32, null=True, blank=True)
    field_090        = models.CharField("090", max_length=64, null=True, blank=True)

    field_245        = models.TextField("245", null=True, blank=True)
    field_246_same   = models.TextField("246(대등표제)", null=True, blank=True)
    field_246_origin = models.TextField("246(원표제)", null=True, blank=True)
    field_250        = models.CharField("250", max_length=200, null=True, blank=True)

    field_260        = models.TextField("260", null=True, blank=True)
    field_300        = models.TextField("300", null=True, blank=True)
    field_310        = models.CharField("310", max_length=200, null=True, blank=True)
    field_342        = models.TextField("342", null=True, blank=True)

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
        return f"{self.book.title}"

class TargetName(models.Model):
    name = models.CharField("이용자 대상 주기 전거표", max_length=200, unique=True)

    class Meta:
        verbose_name = "521 전거"

    def __str__(self):
        return self.name

class Target(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="targets", null=True, blank=True)
    target = models.ForeignKey(TargetName, on_delete=models.PROTECT, related_name="book_targets")

    field_521 = models.CharField("521(이용자대상주기)", max_length=200, null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Target"
        verbose_name_plural = "Target"
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
        verbose_name_plural = "Curation"

    def __str__(self):
        return f"Curation[{self.book.title}]"