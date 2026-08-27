from providers.finished.overchat import MODELS, OverchatProviderAdapter
from providers.finished.overchat.streaming import collect_text


class _Transport:
    def get(self, *args, **kwargs):  # pragma: no cover - not called
        raise AssertionError

    patch = post = get


def test_finished_package_imports_without_working_tree():
    adapter = OverchatProviderAdapter(_Transport())
    assert adapter.provider_id == "overchat"
    assert len(MODELS) == 3
    assert collect_text(
        [
            b'data: {"event":"response.output_text.delta","data":{"delta":"ok"}}',
            b"data: [DONE]",
        ]
    ) == "ok"
