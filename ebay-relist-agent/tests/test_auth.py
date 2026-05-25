import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_get_access_token_returns_cached_token():
    from auth import get_access_token
    cfg = {"app_id": "app", "cert_id": "cert", "dev_id": "dev", "ru_name": "ru"}
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    tokens = {"access_token": "cached_token", "expires_at": future, "refresh_token": "rt"}
    with patch("auth.load_tokens", return_value=tokens):
        result = get_access_token(cfg)
    assert result == "cached_token"


def test_get_access_token_refreshes_when_expired():
    from auth import get_access_token
    cfg = {"app_id": "app", "cert_id": "cert", "dev_id": "dev", "ru_name": "ru"}
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    tokens = {"access_token": "old", "expires_at": past, "refresh_token": "rt"}
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "new_token", "expires_in": 7200}
    mock_resp.raise_for_status = MagicMock()
    with patch("auth.load_tokens", return_value=tokens), \
         patch("auth.save_tokens") as mock_save, \
         patch("requests.post", return_value=mock_resp):
        result = get_access_token(cfg)
    assert result == "new_token"
    mock_save.assert_called_once()


def test_get_access_token_raises_without_refresh_token():
    from auth import get_access_token
    cfg = {"app_id": "app", "cert_id": "cert", "dev_id": "dev", "ru_name": "ru"}
    with patch("auth.load_tokens", return_value={}):
        with pytest.raises(RuntimeError, match="No refresh token"):
            get_access_token(cfg)
