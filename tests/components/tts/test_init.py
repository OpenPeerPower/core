"""The tests for the TTS component."""
from unittest.mock import PropertyMock, patch

import pytest
import yarl

from openpeerpower.components.demo.tts import DemoProvider
from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    DOMAIN as DOMAIN_MP,
    MEDIA_TYPE_MUSIC,
    SERVICE_PLAY_MEDIA,
)
import openpeerpower.components.tts as tts
from openpeerpower.components.tts import _get_cache_files
from openpeerpower.config import async_process_op_core_config
from openpeerpower.const import HTTP_NOT_FOUND
from openpeerpower.setup import async_setup_component

from tests.common import assert_setup_component, async_mock_service


def relative_url(url):
    """Convert an absolute url to a relative one."""
    return str(yarl.URL(url).relative())


@pytest.fixture
def demo_provider():
    """Demo TTS provider."""
    return DemoProvider("en")


@pytest.fixture(autouse=True)
def mock_get_cache_files():
    """Mock the list TTS cache function."""
    with patch(
        "openpeerpower.components.tts._get_cache_files", return_value={}
    ) as mock_cache_files:
        yield mock_cache_files


@pytest.fixture(autouse=True)
def mock_init_cache_dir():
    """Mock the TTS cache dir in memory."""
    with patch(
        "openpeerpower.components.tts._init_tts_cache_dir",
        side_effect=lambda opp, cache_dir: opp.config.path(cache_dir),
    ) as mock_cache_dir:
        yield mock_cache_dir


@pytest.fixture
def empty_cache_dir(tmp_path, mock_init_cache_dir, mock_get_cache_files, request):
    """Mock the TTS cache dir with empty dir."""
    mock_init_cache_dir.side_effect = None
    mock_init_cache_dir.return_value = str(tmp_path)

    # Restore original get cache files behavior, we're working with a real dir.
    mock_get_cache_files.side_effect = _get_cache_files

    yield tmp_path

    if request.node.rep_call.passed:
        return

    # Print contents of dir if failed
    print("Content of dir for", request.node.nodeid)
    for fil in tmp_path.iterdir():
        print(fil.relative_to(tmp_path))

    # To show the log.
    assert False


@pytest.fixture()
def mutagen_mock():
    """Mock writing tags."""
    with patch(
        "openpeerpower.components.tts.SpeechManager.write_tags",
        side_effect=lambda *args: args[1],
    ):
        yield


@pytest.fixture(autouse=True)
async def internal_url_mock(opp):
    """Mock internal URL of the instance."""
    await async_process_op_core_config(
        opp,
        {"internal_url": "http://example.local:8123"},
    )


async def test_setup_component_demo(opp):
    """Set up the demo platform with defaults."""
    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    assert opp.services.has_service(tts.DOMAIN, "demo_say")
    assert opp.services.has_service(tts.DOMAIN, "clear_cache")
    assert f"{tts.DOMAIN}.demo" in opp.config.components


async def test_setup_component_demo_no_access_cache_folder(opp, mock_init_cache_dir):
    """Set up the demo platform with defaults."""
    config = {tts.DOMAIN: {"platform": "demo"}}

    mock_init_cache_dir.side_effect = OSError(2, "No access")
    assert not await async_setup_component(opp, tts.DOMAIN, config)

    assert not opp.services.has_service(tts.DOMAIN, "demo_say")
    assert not opp.services.has_service(tts.DOMAIN, "clear_cache")


async def test_setup_component_and_test_service(opp, empty_cache_dir):
    """Set up the demo platform and call service."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )

    assert len(calls) == 1
    assert calls[0].data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_MUSIC
    assert (
        calls[0].data[ATTR_MEDIA_CONTENT_ID]
        == "http://example.local:8123/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    )
    await opp.async_block_till_done()
    assert (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    ).is_file()


async def test_setup_component_and_test_service_with_config_language(
    opp, empty_cache_dir
):
    """Set up the demo platform and call service."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo", "language": "de"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )
    assert len(calls) == 1
    assert calls[0].data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_MUSIC
    assert (
        calls[0].data[ATTR_MEDIA_CONTENT_ID]
        == "http://example.local:8123/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_de_-_demo.mp3"
    )
    await opp.async_block_till_done()
    assert (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_de_-_demo.mp3"
    ).is_file()


async def test_setup_component_and_test_service_with_config_language_special(
    opp, empty_cache_dir
):
    """Set up the demo platform and call service with extend language."""
    import openpeerpower.components.demo.tts as demo_tts

    demo_tts.SUPPORT_LANGUAGES.append("en_US")
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo", "language": "en_US"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )
    assert len(calls) == 1
    assert calls[0].data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_MUSIC
    assert (
        calls[0].data[ATTR_MEDIA_CONTENT_ID]
        == "http://example.local:8123/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_en-us_-_demo.mp3"
    )
    await opp.async_block_till_done()
    assert (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_en-us_-_demo.mp3"
    ).is_file()


async def test_setup_component_and_test_service_with_wrong_conf_language(opp):
    """Set up the demo platform and call service with wrong config."""
    config = {tts.DOMAIN: {"platform": "demo", "language": "ru"}}

    with assert_setup_component(0, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)


async def test_setup_component_and_test_service_with_service_language(
    opp, empty_cache_dir
):
    """Set up the demo platform and call service."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
            tts.ATTR_LANGUAGE: "de",
        },
        blocking=True,
    )
    assert len(calls) == 1
    assert calls[0].data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_MUSIC
    assert (
        calls[0].data[ATTR_MEDIA_CONTENT_ID]
        == "http://example.local:8123/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_de_-_demo.mp3"
    )
    await opp.async_block_till_done()
    assert (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_de_-_demo.mp3"
    ).is_file()


async def test_setup_component_test_service_with_wrong_service_language(
    opp, empty_cache_dir
):
    """Set up the demo platform and call service."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
            tts.ATTR_LANGUAGE: "lang",
        },
        blocking=True,
    )
    assert len(calls) == 0
    await opp.async_block_till_done()
    assert not (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_lang_-_demo.mp3"
    ).is_file()


async def test_setup_component_and_test_service_with_service_options(
    opp, empty_cache_dir
):
    """Set up the demo platform and call service with options."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
            tts.ATTR_LANGUAGE: "de",
            tts.ATTR_OPTIONS: {"voice": "alex", "age": 5},
        },
        blocking=True,
    )
    opt_hash = tts._hash_options({"voice": "alex", "age": 5})

    assert len(calls) == 1
    assert calls[0].data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_MUSIC
    assert (
        calls[0].data[ATTR_MEDIA_CONTENT_ID]
        == f"http://example.local:8123/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_de_{opt_hash}_demo.mp3"
    )
    await opp.async_block_till_done()
    assert (
        empty_cache_dir
        / f"42f18378fd4393d18c8dd11d03fa9563c1e54491_de_{opt_hash}_demo.mp3"
    ).is_file()


async def test_setup_component_and_test_with_service_options_def(opp, empty_cache_dir):
    """Set up the demo platform and call service with default options."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN), patch(
        "openpeerpower.components.demo.tts.DemoProvider.default_options",
        new_callable=PropertyMock(return_value={"voice": "alex"}),
    ):
        assert await async_setup_component(opp, tts.DOMAIN, config)

        await opp.services.async_call(
            tts.DOMAIN,
            "demo_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "There is someone at the door.",
                tts.ATTR_LANGUAGE: "de",
            },
            blocking=True,
        )
        opt_hash = tts._hash_options({"voice": "alex"})

        assert len(calls) == 1
        assert calls[0].data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_MUSIC
        assert (
            calls[0].data[ATTR_MEDIA_CONTENT_ID]
            == f"http://example.local:8123/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_de_{opt_hash}_demo.mp3"
        )
        await opp.async_block_till_done()
        assert (
            empty_cache_dir
            / f"42f18378fd4393d18c8dd11d03fa9563c1e54491_de_{opt_hash}_demo.mp3"
        ).is_file()


async def test_setup_component_and_test_service_with_service_options_wrong(
    opp, empty_cache_dir
):
    """Set up the demo platform and call service with wrong options."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
            tts.ATTR_LANGUAGE: "de",
            tts.ATTR_OPTIONS: {"speed": 1},
        },
        blocking=True,
    )
    opt_hash = tts._hash_options({"speed": 1})

    assert len(calls) == 0
    await opp.async_block_till_done()
    assert not (
        empty_cache_dir
        / f"42f18378fd4393d18c8dd11d03fa9563c1e54491_de_{opt_hash}_demo.mp3"
    ).is_file()


async def test_setup_component_and_test_service_with_base_url_set(opp):
    """Set up the demo platform with ``base_url`` set and call service."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo", "base_url": "http://fnord"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )
    assert len(calls) == 1
    assert calls[0].data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_MUSIC
    assert (
        calls[0].data[ATTR_MEDIA_CONTENT_ID] == "http://fnord"
        "/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491"
        "_en_-_demo.mp3"
    )


async def test_setup_component_and_test_service_clear_cache(opp, empty_cache_dir):
    """Set up the demo platform and call service clear cache."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )
    # To make sure the file is persisted
    await opp.async_block_till_done()
    assert len(calls) == 1
    await opp.async_block_till_done()
    assert (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    ).is_file()

    await opp.services.async_call(
        tts.DOMAIN, tts.SERVICE_CLEAR_CACHE, {}, blocking=True
    )

    await opp.async_block_till_done()
    assert not (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    ).is_file()


async def test_setup_component_and_test_service_with_receive_voice(
    opp, demo_provider, opp_client
):
    """Set up the demo platform and call service and receive voice."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    client = await opp_client()

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )
    assert len(calls) == 1

    req = await client.get(relative_url(calls[0].data[ATTR_MEDIA_CONTENT_ID]))
    _, demo_data = demo_provider.get_tts_audio("bla", "en")
    demo_data = tts.SpeechManager.write_tags(
        "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3",
        demo_data,
        demo_provider,
        "There is someone at the door.",
        "en",
        None,
    )
    assert req.status == 200
    assert await req.read() == demo_data


async def test_setup_component_and_test_service_with_receive_voice_german(
    opp, demo_provider, opp_client
):
    """Set up the demo platform and call service and receive voice."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo", "language": "de"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    client = await opp_client()

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )
    assert len(calls) == 1
    req = await client.get(relative_url(calls[0].data[ATTR_MEDIA_CONTENT_ID]))
    _, demo_data = demo_provider.get_tts_audio("bla", "de")
    demo_data = tts.SpeechManager.write_tags(
        "42f18378fd4393d18c8dd11d03fa9563c1e54491_de_-_demo.mp3",
        demo_data,
        demo_provider,
        "There is someone at the door.",
        "de",
        None,
    )
    assert req.status == 200
    assert await req.read() == demo_data


async def test_setup_component_and_web_view_wrong_file(opp, opp_client):
    """Set up the demo platform and receive wrong file from web."""
    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    client = await opp_client()

    url = "/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"

    req = await client.get(url)
    assert req.status == HTTP_NOT_FOUND


async def test_setup_component_and_web_view_wrong_filename(opp, opp_client):
    """Set up the demo platform and receive wrong filename from web."""
    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    client = await opp_client()

    url = "/api/tts_proxy/265944dsk32c1b2a621be5930510bb2cd_en_-_demo.mp3"

    req = await client.get(url)
    assert req.status == HTTP_NOT_FOUND


async def test_setup_component_test_without_cache(opp, empty_cache_dir):
    """Set up demo platform without cache."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo", "cache": False}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )
    assert len(calls) == 1
    await opp.async_block_till_done()
    assert not (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    ).is_file()


async def test_setup_component_test_with_cache_call_service_without_cache(
    opp, empty_cache_dir
):
    """Set up demo platform with cache and call service without cache."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "demo", "cache": True}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    await opp.services.async_call(
        tts.DOMAIN,
        "demo_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
            tts.ATTR_CACHE: False,
        },
        blocking=True,
    )
    assert len(calls) == 1
    await opp.async_block_till_done()
    assert not (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    ).is_file()


async def test_setup_component_test_with_cache_dir(
    opp, empty_cache_dir, demo_provider
):
    """Set up demo platform with cache and call service without cache."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    _, demo_data = demo_provider.get_tts_audio("bla", "en")
    cache_file = (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    )

    with open(cache_file, "wb") as voice_file:
        voice_file.write(demo_data)

    config = {tts.DOMAIN: {"platform": "demo", "cache": True}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    with patch(
        "openpeerpower.components.demo.tts.DemoProvider.get_tts_audio",
        return_value=(None, None),
    ):
        await opp.services.async_call(
            tts.DOMAIN,
            "demo_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "There is someone at the door.",
            },
            blocking=True,
        )
    assert len(calls) == 1
    assert (
        calls[0].data[ATTR_MEDIA_CONTENT_ID]
        == "http://example.local:8123/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    )


async def test_setup_component_test_with_error_on_get_tts(opp):
    """Set up demo platform with wrong get_tts_audio."""
    config = {tts.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, tts.DOMAIN), patch(
        "openpeerpower.components.demo.tts.DemoProvider.get_tts_audio",
        return_value=(None, None),
    ):
        assert await async_setup_component(opp, tts.DOMAIN, config)


async def test_setup_component_load_cache_retrieve_without_mem_cache(
    opp, demo_provider, empty_cache_dir, opp_client
):
    """Set up component and load cache and get without mem cache."""
    _, demo_data = demo_provider.get_tts_audio("bla", "en")
    cache_file = (
        empty_cache_dir / "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"
    )

    with open(cache_file, "wb") as voice_file:
        voice_file.write(demo_data)

    config = {tts.DOMAIN: {"platform": "demo", "cache": True}}

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    client = await opp_client()

    url = "/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3"

    req = await client.get(url)
    assert req.status == 200
    assert await req.read() == demo_data


async def test_setup_component_and_web_get_url(opp, opp_client):
    """Set up the demo platform and receive file from web."""
    config = {tts.DOMAIN: {"platform": "demo"}}

    await async_setup_component(opp, tts.DOMAIN, config)

    client = await opp_client()

    url = "/api/tts_get_url"
    data = {"platform": "demo", "message": "There is someone at the door."}

    req = await client.post(url, json=data)
    assert req.status == 200
    response = await req.json()
    assert response == {
        "url": "http://example.local:8123/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3",
        "path": "/api/tts_proxy/42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.mp3",
    }


async def test_setup_component_and_web_get_url_bad_config(opp, opp_client):
    """Set up the demo platform and receive wrong file from web."""
    config = {tts.DOMAIN: {"platform": "demo"}}

    await async_setup_component(opp, tts.DOMAIN, config)

    client = await opp_client()

    url = "/api/tts_get_url"
    data = {"message": "There is someone at the door."}

    req = await client.post(url, json=data)
    assert req.status == 400


async def test_tags_with_wave(opp, demo_provider):
    """Set up the demo platform and call service and receive voice."""

    # below data represents an empty wav file
    demo_data = bytes.fromhex(
        "52 49 46 46 24 00 00 00 57 41 56 45 66 6d 74 20 10 00 00 00 01 00 02 00"
        + "22 56 00 00 88 58 01 00 04 00 10 00 64 61 74 61 00 00 00 00"
    )

    tagged_data = tts.SpeechManager.write_tags(
        "42f18378fd4393d18c8dd11d03fa9563c1e54491_en_-_demo.wav",
        demo_data,
        demo_provider,
        "AI person is in front of your door.",
        "en",
        None,
    )

    assert tagged_data != demo_data
