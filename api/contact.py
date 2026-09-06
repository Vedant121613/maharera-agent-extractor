"""
Fetches contact details for an agent.
"""

from api.api_client import APIClient
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ContactAPI(APIClient):
    """
    Retrieves contact information (phone, email, website) for a MahaRERA agent.
    """

    _PATH_TEMPLATE = "/en/api/agent/{agent_id}/contact"

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    async def fetch(self, agent_id: str) -> dict:
        """
        Fetch and normalise contact details for `agent_id`.

        Returns:
            A flat dict with keys: phone, mobile, email, website.
        """
        path = self._PATH_TEMPLATE.format(agent_id=agent_id)
        raw = await self.get(path)

        if isinstance(raw, dict):
            data = raw.get("data", raw)
        else:
            logger.warning(f"Unexpected contact API response for {agent_id}")
            return {}

        return {
            "phone": data.get("phone", ""),
            "mobile": data.get("mobile", ""),
            "email": data.get("email", ""),
            "website": data.get("website", ""),
        }
