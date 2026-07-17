"""Tests for the curated external course catalog."""

from pages.courses import CATALOG_URL, COURSES, Course, course_card_html


def test_catalog_contains_unique_official_course_links() -> None:
    urls = [course.url for course in COURSES]
    assert len(COURSES) == 6
    assert len(urls) == len(set(urls))
    assert all(url.startswith("https://kurs.alfabank.ru/courses/") for url in urls)
    assert CATALOG_URL == "https://kurs.alfabank.ru/courses/"


def test_course_card_is_clickable_safe_and_opens_new_tab() -> None:
    course = Course(
        title="Курс <для бизнеса>",
        category="Старт",
        details="1 урок",
        description="Описание",
        url="https://kurs.alfabank.ru/courses/example/?a=1&b=2",
    )
    rendered = course_card_html(course)
    assert 'target="_blank"' in rendered
    assert 'rel="noopener noreferrer"' in rendered
    assert "Курс &lt;для бизнеса&gt;" in rendered
    assert "?a=1&amp;b=2" in rendered
