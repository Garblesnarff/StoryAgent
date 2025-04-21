"""Empathic Voice Interface client."""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, ClassVar, List, Optional

from hume._common.api_type import ApiType
from hume._common.client_base import ClientBase
from hume._common.config_utils import deserialize_configs
from hume._voice.voice_socket import VoiceSocket
from hume.error.hume_client_exception import HumeClientException
from hume.models.config.model_config_base import ModelConfigBase

try:
    import websockets

    HAS_WEBSOCKETS = True
except ModuleNotFoundError:
    HAS_WEBSOCKETS = False


class HumeVoiceClient(ClientBase):
    """Empathic Voice Interface client.

    Example:
        ```python
        import asyncio

        from hume import HumeVoiceClient

        async def main():
            client = HumeVoiceClient("<your-api-key>")
            async with client.connect() as socket:
                # TODO: Update this

        asyncio.run(main())
        ```
    """

    API_BASE_PATH: ClassVar[str] = "v0/assistant"
    API_BASE_HOST: ClassVar[str] = f"api.hume.ai/{API_BASE_PATH}"
    API_BASE_HTTP_URL: ClassVar[str] = f"https://{API_BASE_HOST}"
    API_BASE_WSS_URL: ClassVar[str] = f"wss://{API_BASE_HOST}"
    API_CHAT_PATH: ClassVar[str] = "chat"
    API_CHAT_URL: ClassVar[str] = f"{API_BASE_WSS_URL}/{API_CHAT_PATH}"

    def __init__(
        self,
        api_key: str,
        *args: Any,
        open_timeout: Optional[int] = 10,
        close_timeout: Optional[int] = 10,
        **kwargs: Any,
    ):
        """Construct a HumeVoiceClient.

        Args:
            api_key (str): Hume API key.
            open_timeout (Optional[int]): Time in seconds before canceling socket open operation.
            close_timeout (Optional[int]): Time in seconds before canceling socket close operation.
        """
        if not HAS_WEBSOCKETS:
            raise HumeClientException(
                "The websockets package is required to use HumeVoiceClient. "
                'Run `pip install "hume[stream]"` to install a version compatible with the'
                "Hume Python SDK."
            )

        self._open_timeout = open_timeout
        self._close_timeout = close_timeout
        super().__init__(api_key, *args, **kwargs)

    @classmethod
    def get_api_type(cls) -> ApiType:
        """Get the ApiType of the client.

        Returns:
            ApiType: API type of the client.
        """
        return ApiType.VOICE

    @asynccontextmanager
    async def connect(
        self,
        configs: List[ModelConfigBase],
        stream_window_ms: Optional[int] = None,
    ) -> AsyncIterator[VoiceSocket]:
        """Connect to the voice API.

        Note: Only one config per model type should be passed.
            If more than one config is passed for a given model type, only the last config will be used.

        Args:
            configs (List[ModelConfigBase]): List of job configs.
            stream_window_ms (Optional[int]): Length of the sliding window in milliseconds to use when
                aggregating media across WebSocket payloads within one WebSocket connection.
        """
        endpoint = self._construct_endpoint("models")
        try:
            # pylint: disable=no-member
            async with websockets.connect(  # type: ignore[attr-defined]
                endpoint,
                extra_headers=self._get_client_headers(),
                close_timeout=self._close_timeout,
                open_timeout=self._open_timeout,
            ) as protocol:
                yield VoiceSocket(protocol, configs, stream_window_ms=stream_window_ms)
        except websockets.exceptions.InvalidStatusCode as exc:
            status_code: int = exc.status_code
            if status_code == 401:  # Unauthorized
                message = "HumeVoiceClient initialized with invalid API key."
                raise HumeClientException(message) from exc
            raise HumeClientException("Unexpected error when creating voice API connection") from exc

    @asynccontextmanager
    async def _connect_with_configs_dict(self, configs_dict: Any) -> AsyncIterator[VoiceSocket]:
        """Connect to the voice API with a single models configuration dict.

        Args:
            configs_dict (Any): Models configurations dict. This should be a dict from model name
                to model configuration dict. An empty dict uses the default configuration.
        """
        configs = deserialize_configs(configs_dict)
        async with self.connect(configs) as websocket:
            yield websocket
