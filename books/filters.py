from rest_framework.filters import SearchFilter
from rest_framework.exceptions import ValidationError

class MinLengthSearchFilter(SearchFilter):
    min_length = 2 # 최소 글자 수

    def filter_queryset(self, request, queryset, view):
        # search 파라미터가 아예 없는 경우
        if self.search_param not in request.query_params:
            return queryset

        raw = request.query_params.get(self.search_param, "")
        term = raw.strip()

        # search 파라미터는 있지만 비어 있거나 공백뿐인 경우
        if term == "":
            return queryset

        # search 파라미터가 있고, 2글자 미만
        if len(term) < self.min_length:
            raise ValidationError({
                self.search_param: f"검색어는 최소 {self.min_length}글자 이상 입력해야 합니다."
            })

        # 2글자 이상
        return super().filter_queryset(request, queryset, view)