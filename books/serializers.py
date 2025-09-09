from rest_framework import serializers
from .models import Book
import re

class BookSerializer(serializers.ModelSerializer):
    # like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    # book_status = serializers.CharField(source='get_book_status_display', read_only=True)

    
    class Meta:
        model = Book
        fields = [
            'id',
            'book_code',
            'title',
            'author',
            'publisher',
            'callnumber',
            'location',
            'image_url',
            # 'liked_count', # 좋아요 개수
            'is_liked', # 좋아요 여부
            'book_status'
        ]

    # def get_like_count(self, obj):
    #     return obj.liked_users.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # return request.user in obj.liked_users.all()
            return obj.liked_users.filter(pk=request.user.pk).exists()
        return False

# 상세 조회
class BookDetailSerializer(serializers.ModelSerializer):
    book_code = serializers.CharField(read_only=True) # 장서번호
    isbn = serializers.CharField(read_only=True) # isbn
    title = serializers.CharField(read_only=True) # 제목
    image_url = serializers.URLField(read_only=True) # 이미지
    author = serializers.CharField(read_only=True) # 저자
    publisher = serializers.CharField(read_only=True) # 출판사
    edition = serializers.CharField(read_only=True) # 판사항
    callnumber = serializers.CharField(read_only=True) # 청구기호

    # Marc
    # publication = serializers.CharField(source='marc.field_260', read_only=True) # 발행사항
    # physical = serializers.CharField(source='marc.field_300', read_only=True) # 형태사항
    # publication = serializers.SerializerMethodField() # 출판사
    physical = serializers.SerializerMethodField() # 페이지, 판형
    marc = serializers.JSONField(source='marc.data', read_only=True) # 전체 MARC

    class Meta:
        model = Book
        fields = [
            'id', 'book_code', 'isbn',
            'title', 'image_url', 'author', 'edition',
            'publisher', 'physical',
            'callnumber', 'marc',
        ]

    # _re_pub_b = re.compile(r"\$b\s*([^$:;,]+)")
    # _re_phy_a = re.compile(r"\$a\s*([\d.,\s]+)\s*p", re.IGNORECASE)
    _re_phy_a = re.compile(
        r"\$a\s*([0-9IVXLCDMivxlcdm.,\s\-–—]+)\s*p",
        re.IGNORECASE
    )
    _re_phy_c = re.compile(r"\$c\s*([\d.,\s]+)\s*cm", re.IGNORECASE)

    def _get_marc_field(self, obj, name: str) -> str:
        marc = getattr(obj, 'marc', None)
        if not marc:
            return ""
        val = getattr(marc, name, "")
        if isinstance(val, (list, tuple)):
            val = " ".join(v for v in val if isinstance(v, str))
        return val or ""

    # def get_publication(self, obj) -> str | None:
    #     raw = self._get_marc_field(obj, 'field_260')
    #     if not raw:
    #         return None
    #     m = self._re_pub_b.search(raw)
    #     if not m:
    #         return None
    #     return m.group(1).strip(" ,;:/")

    def get_physical(self, obj) -> str | None:
        raw = self._get_marc_field(obj, 'field_300')
        if not raw:
            return None

        page, size = None, None
        m_page = self._re_phy_a.search(raw)
        if m_page:
            # num = m_page.group(1).replace(" ", "").replace(",", "")
            num = m_page.group(1)
            num = (num.replace(" ", "")
                    .replace(",", "")
                    .replace("–", "-")
                    .replace("—", "-")
                    .rstrip("."))
            if num:
                page = f"{num}p"

        m_size = self._re_phy_c.search(raw)
        if m_size:
            num = m_size.group(1).replace(" ", "").replace(",", "")
            if num:
                size = f"{num}cm"

        if page and size:
            return f"{page}, {size}"
        return page or size