from unittest.mock import Mock
import subprocess
import pytest
from server import Settings, create_app

TOKEN = "fictional-test-token-not-for-deployment"


@pytest.fixture
def context():
    runner = Mock()
    app = create_app(Settings("02:00:00:00:00:01", TOKEN), runner)
    return app.test_client(), runner


def test_health_does_not_send_packet(context):
    client, runner = context
    assert client.get("/health").json == {"status": "ok"}
    runner.assert_not_called()


@pytest.mark.parametrize("header", [None, "Bearer wrong", "Basic invalid", "Bearer \u2603"])
def test_authentication_required(context, header):
    client, runner = context
    assert client.post("/wol", headers={"Authorization": header} if header else {}).status_code == 401
    runner.assert_not_called()


def test_get_has_no_side_effect(context):
    client, runner = context
    assert client.get("/wol").status_code == 405
    runner.assert_not_called()


def test_success_uses_fixed_arguments(context):
    client, runner = context
    response = client.post("/wol", headers={"Authorization": "Bearer " + TOKEN})
    assert response.status_code == 200
    assert response.json["status"] == "sent"
    runner.assert_called_once_with(["wakeonlan", "-i", "255.255.255.255", "02:00:00:00:00:01"],
                                  check=True, capture_output=True, timeout=5)


@pytest.mark.parametrize("failure,status", [(FileNotFoundError(), 503),
    (subprocess.TimeoutExpired("wakeonlan", 5), 504), (subprocess.CalledProcessError(1, "wakeonlan"), 502)])
def test_command_failure_is_not_reported_as_success(context, failure, status):
    client, runner = context
    runner.side_effect = failure
    assert client.post("/wol", headers={"Authorization": "Bearer " + TOKEN}).status_code == status


@pytest.mark.parametrize("values", [dict(target_mac="invalid", token=TOKEN),
    dict(target_mac="02:00:00:00:00:01", token="short"),
    dict(target_mac="02:00:00:00:00:01", token=TOKEN, broadcast="not-an-ip"),
    dict(target_mac="02:00:00:00:00:01", token=TOKEN, port=70000)])
def test_invalid_configuration_fails_early(values):
    with pytest.raises(ValueError):
        Settings(**values)
