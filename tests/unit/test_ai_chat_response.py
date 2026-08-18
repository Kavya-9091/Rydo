import uuid

from app.api.v1.endpoints.ai import _extract_chat_tool_metadata


def test_extract_chat_tool_metadata_reads_tool_and_ride_id() -> None:
    ride_id = uuid.uuid4()
    metadata = {
        "tool_results": [
            {
                "tool": "book_ride",
                "result": {
                    "success": True,
                    "data": {"ride_id": str(ride_id)},
                },
            }
        ]
    }

    tool_name, extracted_ride_id = _extract_chat_tool_metadata(metadata)

    assert tool_name == "book_ride"
    assert extracted_ride_id == ride_id


def test_extract_chat_tool_metadata_handles_missing_tool_results() -> None:
    tool_name, ride_id = _extract_chat_tool_metadata({"provider": "local_fallback"})

    assert tool_name is None
    assert ride_id is None
