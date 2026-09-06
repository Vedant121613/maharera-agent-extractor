"""
Fetches general registration details for an agent.
"""

from api.api_client import APIClient
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GeneralAPI(APIClient):
    """
    Retrieves general details (name, registration number, validity, etc.)
    for a given MahaRERA agent ID.
    """

    _PATH_TEMPLATE = "/en/api/agent/{agent_id}/general"

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    async def fetch(self, agent_id: str) -> dict:
        """
        Fetch and normalise general details for `agent_id`.

        Returns:
            A flat dict with keys: name, registration_number,
            registration_date, valid_upto, status, agent_type.
        """
        path = self._PATH_TEMPLATE.format(agent_id=agent_id)
        raw = await self.get(path)

        if isinstance(raw, dict):
            data = raw.get("data", raw)
        else:
            logger.warning(f"Unexpected general API response for {agent_id}")
            return {}

        return {
            "name": data.get("agentName") or data.get("name", ""),
            "registration_number": data.get("registrationNo", ""),
            "registration_date": data.get("registrationDate", ""),
            "valid_upto": data.get("validUpto", ""),
            "status": data.get("status", ""),
            "agent_type": data.get("agentType", ""),
        }
