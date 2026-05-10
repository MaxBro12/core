import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict, AsyncGenerator

import aiohttp

class MockClientResponse:
    """Mock class to simulate aiohttp.ClientResponse."""
    def __init__(self, url: str, status: int, headers: Dict[str, str], json_data: Any = None, content_type: str = 'application/json'):
        self.url = url
        self.status = status
        self.headers = headers
        self._json_data = json_data
        self._content_type = content_type

    async def json(self, content_type: str = None) -> Any:
        if content_type == 'json':
            return self._json_data
        # Simulate aiohttp's behavior for other content types or generic json() calls
        if self._content_type == 'text/html':
            # Simulate returning the raw response body as string if it's HTML, or JSON if json() was explicitly requested and data is present.
            return f"<mock_html_content_from_{self.url}>"

        if self._content_type == 'empty':
             # Simulate empty body response for some cases
            return {}

        return self._json_data if self._json_data is not None else ""

class MockClientSession:
    """Mock class to simulate aiohttp.ClientSession."""
    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.get('timeout', aiohttp.ClientTimeout(total=10))
        self.headers = {}
        self.params = {}
        self.mock_methods = {}

    async def __aenter__(self) -> 'MockClientSession':
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    def __await__(self) -> Any:
        # This is to handle calls like 'await session' which is not directly supported in this mock setup
        raise NotImplementedError("Use async methods.")

    async def __aenter__(self) -> 'MockClientSession':
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    async def __aenter__(self) -> 'MockClientSession':
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    async def __aenter__(self) -> 'MockClientSession':
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass


    async def request(self, method: str, url: str, **kwargs) -> MockClientResponse:
        """Simulates the top-level request method."""
        if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']:
            raise NotImplementedError(f"Mock session does not support method: {method}")

        # This is a placeholder; the actual calls are usually made to methods like .get(), .post(), etc., on the session object.
        raise NotImplementedError(f"Mock session request method {method} not implemented directly on session.")

    async def get(self, url: str, **kwargs) -> MockClientResponse:
        """Simulates aiohttp.ClientSession.get()."""
        if url not in self.mock_methods:
            self.mock_methods[url] = MagicMock()

        # Simulate the response object
        mock_response = MockClientResponse(
            url=url,
            status=200,
            headers={'Content-Type': 'application/json'},
            json_data={"result": "mocked_data"}
        )
        return mock_response

    async def post(self, url: str, **kwargs) -> MockClientResponse:
        """Simulates aiohttp.ClientSession.post()."""
        if url not in self.mock_methods:
            self.mock_methods[url] = MagicMock()

        mock_response = MockClientResponse(
            url=url,
            status=201,
            headers={'Content-Type': 'application/json'},
            json_data={"status": "created"}
        )
        return mock_response

    async def put(self, url: str, **kwargs) -> MockClientResponse:
        """Simulates aiohttp.ClientSession.put()."""
        if url not in self.mock_methods:
            self.mock_methods[url] = MagicMock()

        mock_response = MockClientResponse(
            url=url,
            status=200,
            headers={'Content-Type': 'application/json'},
            json_data={"status": "updated"}
        )
        return mock_response

    async def delete(self, url: str, **kwargs) -> MockClientResponse:
        """Simulates aiohttp.ClientSession.delete()."""
        if url not in self.mock_methods:
            self.mock_methods[url] = MagicMock()

        mock_response = MockClientResponse(
            url=url,
            status=204,
            headers={},
            json_data=None
        )
        return mock_response

    async def head(self, url: str, **kwargs) -> MockClientResponse:
        """Simulates aiohttp.ClientSession.head()."""
        if url not in self.mock_methods:
            self.mock_methods[url] = MagicMock()

        mock_response = MockClientResponse(
            url=url,
            status=200,
            headers={'Content-Type': 'application/json'},
            json_data={"ok": True}
        )
        return mock_response

    async def __aenter__(self) -> 'MockClientSession':
        # In a real mock, you'd need to manage context if session operations are tied to it.
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

# To make it behave like an async context manager for the usage in HttpMakerAsync.__execute
class AsyncClientSessionMock(MockClientSession):
    """Context manager wrapper for the mock session."""
    async def __aenter__(self) -> MockClientSession:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

# Example of how to use the mock for testing (conceptual):
# async def test_http_request():
#     mock_session = AsyncClientSessionMock()
#     result = await HttpMakerAsync(timeout_in_sec=1, parse_method=lambda r: MockClientResponse(r.url, r.status, r.headers, {"data": "test"}).json()).__execute(
#         url="http://test.com/api",
#         method=Method.GET,
#         try_wait_if_error=False
#     )
#     assert result.json == {"data": "test"}
#     assert result.status == 200
