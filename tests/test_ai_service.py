"""Tests for GigaChat integration without network access."""

from types import SimpleNamespace

import pytest

from services.ai_service import AIServiceError, GigaChatAIService, MAX_HISTORY_MESSAGES


class FakeChat:
    """Collect SDK requests and return a configured response."""

    def __init__(self, response: object | None = None, error: Exception | None = None) -> None:
        self.response = response or make_response("Понятный ответ")
        self.error = error
        self.requests: list[object] = []

    def create(self, request: object) -> object:
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    """Minimal injected client compatible with the GigaChat SDK surface."""

    def __init__(self, chat: FakeChat) -> None:
        self.chat = chat


def make_response(text: object) -> object:
    return SimpleNamespace(messages=[SimpleNamespace(content=[SimpleNamespace(text=text)])])


def configured_service(chat: FakeChat | None = None) -> GigaChatAIService:
    return GigaChatAIService(
        credentials="test-credential",
        scope="GIGACHAT_API_PERS",
        model="GigaChat-2",
        max_tokens=321,
        temperature=0.1,
        client=FakeClient(chat or FakeChat()),
    )


def financial_context(service: GigaChatAIService) -> str:
    return service.build_financial_context(
        metrics={
            "period": "Июль 2026",
            "revenue": 175_000,
            "expenses": 72_000,
            "profit": 95_900,
            "card_number": "1111 2222 3333 4444",
            "email": "private@example.test",
        },
        alerts=[
            {
                "severity": "warning",
                "title": "Рост рекламных расходов",
                "description": "Расходы на рекламу выросли",
                "phone": "+70000000000",
            }
        ],
    )


def test_mock_mode_does_not_call_client() -> None:
    chat = FakeChat()
    service = GigaChatAIService(None, "GIGACHAT_API_PERS", "GigaChat-2", client=FakeClient(chat))
    context = financial_context(service)
    answer = service.ask("Почему изменилась прибыль?", context)
    assert "демонстрационном режиме" in answer
    assert "175 000 ₽" in answer
    assert chat.requests == []


def test_context_keeps_russian_and_drops_private_fields() -> None:
    context = financial_context(configured_service())
    assert "Июль 2026" in context
    assert "\\u0418" not in context
    assert "card_number" not in context
    assert "private@example.test" not in context
    assert "+70000000000" not in context


def test_context_limits_alerts_to_five() -> None:
    service = configured_service()
    context = service.build_financial_context(
        metrics={"revenue": 1},
        alerts=[{"title": f"Сигнал {index}", "description": "x"} for index in range(10)],
    )
    assert context.count("Сигнал") == 5


def test_context_allows_only_aggregated_cashflow_fields() -> None:
    service = configured_service()
    context = service.build_financial_context(
        metrics={"revenue": 1},
        cashflow={
            "horizon_days": 30,
            "first_gap_date": "2026-07-20",
            "maximum_shortage": 5000,
            "payment_title": "Секретный поставщик",
        },
    )
    assert "2026-07-20" in context
    assert "maximum_shortage" in context
    assert "Секретный поставщик" not in context


def test_empty_question_is_rejected() -> None:
    with pytest.raises(ValueError, match="Вопрос не может быть пустым"):
        configured_service().ask("   ", financial_context(configured_service()))


def test_request_has_system_message_history_limit_and_settings() -> None:
    chat = FakeChat()
    service = configured_service(chat)
    history = [{"role": "user", "content": f"Вопрос {index}"} for index in range(8)]
    service.ask("Текущий вопрос", financial_context(service), history)
    request = chat.requests[0]
    assert request.model == "GigaChat-2"
    assert request.temperature == 0.1
    assert request.max_tokens == 321
    assert request.messages[0].role == "system"
    assert len(request.messages) == 2 + MAX_HISTORY_MESSAGES
    assert service.scope == "GIGACHAT_API_PERS"


def test_extracts_string_and_text_block_responses() -> None:
    service = configured_service()
    assert service.extract_response_text(SimpleNamespace(messages=[SimpleNamespace(content="Строковый ответ")])) == "Строковый ответ"
    assert service.extract_response_text(make_response("Текст из блока")) == "Текст из блока"


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(messages=[]),
        SimpleNamespace(messages=[SimpleNamespace(content=[])]),
        SimpleNamespace(messages=[SimpleNamespace(content=[SimpleNamespace(text=None)])]),
    ],
)
def test_rejects_empty_sdk_responses(response: object) -> None:
    with pytest.raises(AIServiceError, match="пустой ответ"):
        configured_service().extract_response_text(response)


def test_fake_client_error_is_safe() -> None:
    chat = FakeChat(error=RuntimeError("network connection failed: test-credential"))
    service = configured_service(chat)
    with pytest.raises(AIServiceError) as error:
        service.ask("Что с расходами?", financial_context(service))
    assert "test-credential" not in str(error.value)
    assert "подключиться" in str(error.value)
