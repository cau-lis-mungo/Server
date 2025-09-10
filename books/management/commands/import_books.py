# 테스트
# python run_with_tunnel.py import_books --file book.csv --dry-run
# 실행
# python run_with_tunnel.py import_books --file book.csv

import csv
import re
from typing import Dict, List, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.utils import IntegrityError

from books.models import Book, Marc, TargetName, Target, Curation

# 구분자: 쉼표, 세미콜론, 줄바꿈 모두 지원
SPLIT_SEP = [",", ";", "\n"]


def split_multi(val: str) -> List[str]:
    if not val:
        return []
    s = str(val)
    for sep in SPLIT_SEP:
        s = s.replace(sep, "|")
    parts = [p.strip() for p in s.split("|")]
    return [p for p in parts if p]


# MARC 파싱
_SUBFIELD_RE = re.compile(r"\$([0-9a-zA-Z])")  # $a, $b, $d 등

def _parse_marc_subfields(raw: str) -> Dict[str, List[str]]:
    if not raw:
        return {}

    s = str(raw)
    results: Dict[str, List[str]] = {}

    matches: List[Tuple[str, int]] = [(m.group(1), m.start()) for m in _SUBFIELD_RE.finditer(s)]
    if not matches:
        return {}

    for i, (code, start_idx) in enumerate(matches):
        value_start = start_idx + 2
        value_end = matches[i + 1][1] if i + 1 < len(matches) else len(s)
        value = s[value_start:value_end]

        cleaned = value.strip().strip(" ,;:/")
        if cleaned:
            results.setdefault(code.lower(), []).append(cleaned)

    return results


def _first_subfield(raw: str, code: str) -> str | None:
    mp = _parse_marc_subfields(raw)
    vals = mp.get(code.lower())
    return vals[0] if vals else None


def _clean_isbn(isbn: str | None) -> str | None:
    if not isbn:
        return None
    isbn = re.split(r"[\s\(\)]", isbn)[0]
    cleaned = re.sub(r"[^0-9Xx]", "", isbn)
    return cleaned or None


def _clean_issn(issn: str | None) -> str | None:
    if not issn:
        return None
    m = re.search(r'(\d{4})[- ]?(\d{3}[\dXx])', issn)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2).upper()}"


class Command(BaseCommand):
    help = "Import/Upsert Books+Marc(+Target/Curation) from a CSV exported from Google Sheets."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="CSV file path (UTF-8/UTF-8-SIG)")
        parser.add_argument("--dry-run", action="store_true", help="Validate only; no DB writes")

    def handle(self, *args, **opts):
        path = opts["file"]
        dry = opts["dry_run"]

        # 통계 카운터
        created_books = updated_books = 0
        created_marc = updated_marc = 0
        created_targets = 0
        created_targetnames = 0
        created_curations = 0

        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                # 필수 헤더 검증
                required_cols = ["등록번호"]
                for rc in required_cols:
                    if rc not in reader.fieldnames:
                        raise CommandError(f"CSV header missing required column: {rc}")

                # 열 이름 매핑
                COL = lambda k: k if k in reader.fieldnames else None
                col = {name: COL(name) for name in reader.fieldnames}

                # 셀 값 접근자
                def val(row, key, default: str = "") -> str:
                    ck = col.get(key)
                    if not ck:
                        return default
                    return (row.get(ck) or "").strip()

                # 파일 전체 트랜잭션
                with transaction.atomic():
                    for idx, row in enumerate(reader, start=2):
                        # --- Book 업서트 ---
                        book_code = val(row, "등록번호")
                        if not book_code:
                            raise CommandError(f"[line {idx}] '등록번호' is required.")

                        f020 = val(row, "020") # ISBN
                        f020_set  = val(row, "020(세트)") # ISBN(세트)
                        f022 = val(row, "022") # ISSN
                        f245 = val(row, "245") # 저자
                        f260 = val(row, "260") # 출판사

                        # ISBN
                        isbn_raw = _first_subfield(f020, "a") # 020 $a
                        if not isbn_raw and f020_set:
                            isbn_raw = _first_subfield(f020_set, "a") or f020_set
                        isbn = _clean_isbn(isbn_raw)
                        # ISSN
                        issn_raw = _first_subfield(f022, "a") if f022 else None
                        issn = None
                        if issn_raw:
                            issn = _clean_issn(issn_raw)
                        elif f022:
                            for piece in split_multi(f022):
                                cand = _first_subfield(piece, "a") or piece
                                issn = _clean_issn(cand)
                                if issn:
                                    break
                        # 저자
                        author = _first_subfield(f245, "d") # 245 $d
                        # 출판사
                        publisher = _first_subfield(f260, "b") # 260 $b


                        book_defaults = {
                            "title": val(row, "서명") or None,
                            "image_url": val(row, "책표지이미지") or None,
                            "callnumber": val(row, "090(분류번호)") or None,
                            "author": author or None,
                            "publisher": publisher or None,
                            "isbn": isbn or None,
                            "issn": issn or None,
                            "location": "문헌정보학과 과실",
                        }

                        try:
                            book, b_created = Book.objects.update_or_create(
                                book_code=book_code, defaults=book_defaults
                            )
                        except IntegrityError as e:
                            raise CommandError(f"[line {idx}] Book upsert failed: {e}")

                        created_books += int(b_created)
                        updated_books += int(not b_created)

                        marc_map = {
                            "field_020":        f020 or None,
                            "field_020_set":    f020_set or None,
                            "field_022":        f022 or None,
                            # "field_020_set":    val(row, "020(세트)") or None,
                            # "field_022":        val(row, "022") or None,
                            "field_052":        val(row, "052") or None,
                            "field_056":        val(row,"056") or None,
                            "field_090":        val(row, "090") or None,
                            "field_245":        f245 or None,
                            "field_246_same":   val(row, "246(대등표제)") or None,
                            "field_246_origin": val(row, "246(원표제)") or None,
                            "field_250":        val(row, "250") or None,
                            "field_260":        f260 or None,
                            "field_300":        val(row, "300") or None,
                            "field_310":        val(row, "310") or None,
                            "field_362":        val(row, "362") or None,
                            "field_490":        val(row, "490") or None,
                            "field_500":        val(row, "500") or None,
                            "field_502":        val(row, "502") or None,
                            "field_504":        val(row, "504") or None,
                            "field_541":        val(row, "541") or None,
                            "field_546":        val(row, "546") or None,
                            "field_586":        val(row, "586") or None,
                            "field_590":        val(row, "590") or None,
                            "field_600":        val(row, "600") or None,
                            "field_610":        val(row, "610") or None,
                            "field_647":        val(row, "647") or None,
                            "field_650":        val(row, "650") or None,
                            "field_653":        val(row, "653") or None,
                            "field_655":        val(row, "655") or None,
                            "field_700":        val(row, "700") or None,
                            "field_710":        val(row, "710") or None,
                            "field_720":        val(row, "720") or None,
                            "field_730":        val(row, "730") or None,
                            "field_856":        val(row, "856") or None,
                        }

                        marc, m_created = Marc.objects.update_or_create(
                            book=book, defaults=marc_map
                        )
                        created_marc += int(m_created)
                        updated_marc += int(not m_created)

                        # Target(521)
                        targets_texts = split_multi(val(row, "521"))
                        for tname in targets_texts:
                            tn, tn_created = TargetName.objects.get_or_create(name=tname)
                            created_targetnames += int(tn_created)
                            _, t_created = Target.objects.get_or_create(book=book, target=tn)
                            created_targets += int(t_created)

                        # Curation(500 큐레이션 주기) 처리
                        curations = split_multi(val(row, "500(큐레이션 주기)"))
                        for text in curations:
                            _, c_created = Curation.objects.get_or_create(
                                book=book, field_500_curation=text
                            )
                            created_curations += int(c_created)

                    # 드라이런: 실제 DB 쓰기 없이 전체 롤백
                    if dry:
                        transaction.set_rollback(True)

        except FileNotFoundError:
            raise CommandError(f"CSV not found: {path}")

        # 드라이런 안내
        if dry:
            self.stdout.write(self.style.WARNING("[DRY-RUN] No changes applied."))

        # 요약 출력
        self.stdout.write(self.style.SUCCESS(
            f"Books C/U: {created_books}/{updated_books} | "
            f"Marc C/U: {created_marc}/{updated_marc} | "
            f"TargetNames+: {created_targetnames} Targets+: {created_targets} | "
            f"Curation+: {created_curations}"
        ))
