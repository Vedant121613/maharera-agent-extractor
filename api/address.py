"""
Fetches address details for an agent.
"""

from api.api_client import APIClient
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AddressAPI(APIClient):
    """
    Retrieves address information for a MahaRERA agent.
    """

    _PATH_TEMPLATE = "/en/api/agent/{agent_id}/address"

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    async def fetch(self, agent_id: str) -> dict:
        """
        Fetch and normalise address details for `agent_id`.

        Returns:
            A flat dict with keys: address_line1, address_line2,
            city, district, state, pincode.
        """
        path = self._PATH_TEMPLATE.format(agent_id=agent_id)
        raw = await self.get(path)

        if isinstance(raw, dict):
            data = raw.get("data", raw)
        else:
            logger.warning(f"Unexpected address API response for {agent_id}")
            return {}

        return {
            "address_line1": data.get("addressLine1", ""),
            "address_line2": data.get("addressLine2", ""),
            "city": data.get("city", ""),
            "district": data.get("district", ""),
            "state": data.get("state", "Maharashtra"),
            "pincode": data.get("pincode", ""),
        }
