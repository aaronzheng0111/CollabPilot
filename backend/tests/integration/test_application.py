async def test_mock_chat_persists_session(application) -> None:
    first = await application.chat("你好", provider_name="mock")
    second = await application.chat(
        "现在几点？",
        session_id=first.session_id,
        provider_name="mock",
    )

    assert first.session_id == second.session_id
    assert second.tool_calls == 1
    messages = application.store.list_messages(first.session_id)
    assert [message.role for message in messages] == [
        "user",
        "assistant",
        "user",
        "tool",
        "assistant",
    ]
