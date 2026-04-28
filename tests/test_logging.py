"""Tests for request-id logging."""


async def test_request_id_is_in_response_header_and_log_output(async_client, caplog):
    response = await async_client.get("/health")
    request_id = response.headers["x-request-id"]
    record = next(item for item in caplog.records if item.getMessage() == "health.check")
    assert record.request_id == request_id
