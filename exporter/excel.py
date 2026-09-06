"""
Export collected agent data to a formatted Excel workbook (.xlsx).
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from database.database import Database
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Column definitions: (header label, dict key from database row)
_COLUMNS = [
    ("Agent ID",           "agent_id"),
    ("Full Name",          "agent_name"),
    ("First Name",         "first_name"),
    ("Middle Name",        "middle_name"),
    ("Last Name",          "last_name"),
    ("Father Name",        "father_name"),
    ("Certificate No.",    "certificate_no"),
    ("Reg. Date",          "registration_date"),
    ("Valid Upto",         "validity_end_date"),
    ("Status",             "status"),
    ("Mobile",             "mobile"),
    ("Email",              "email"),
    ("Address",            "address"),
    ("City",               "city"),
    ("District",           "district"),
    ("State",              "state"),
    ("Pincode",            "pincode"),
    ("Collected At",       "collected_at"),
]

_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_ALT_FILL    = PatternFill("solid", fgColor="D9E1F2")
_THIN        = Side(style="thin")
_BORDER      = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)


class ExcelExporter:
    def __init__(self, db: Database) -> None:
        self._db = db

    def export(self, output_path: str | Path | None = None) -> Path:
        """
        Write all collected agents to an Excel file.

        Args:
            output_path: Full file path including .xlsx extension.
                         Defaults to <OUTPUT_DIR>/maharera_agents.xlsx
        """
        from config.config import Config
        from utils.helpers import timestamp_filename

        if output_path is None:
            fname = timestamp_filename("maharera_agents", ".xlsx")
            output_path = Path(Config.OUTPUT_DIR) / fname

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        agents = self._db.get_all_agents()

        wb = Workbook()
        ws = wb.active
        ws.title = "MahaRERA Agents"
        ws.row_dimensions[1].height = 20

        # ── Header ────────────────────────────────────────────────────────────
        for col_idx, (header, _) in enumerate(_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font      = Font(bold=True, color="FFFFFF", size=11)
            cell.fill      = _HEADER_FILL
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border    = _BORDER

        # ── Data rows ─────────────────────────────────────────────────────────
        for row_idx, agent in enumerate(agents, start=2):
            fill = _ALT_FILL if row_idx % 2 == 0 else PatternFill()
            for col_idx, (_, key) in enumerate(_COLUMNS, start=1):
                cell = ws.cell(row=row_idx, column=col_idx,
                               value=agent.get(key) or "")
                cell.fill      = fill
                cell.border    = _BORDER
                cell.alignment = Alignment(vertical="center", wrap_text=False)

        # ── Column widths ─────────────────────────────────────────────────────
        for col_idx in range(1, len(_COLUMNS) + 1):
            max_len = max(
                (len(str(ws.cell(row=r, column=col_idx).value or ""))
                 for r in range(1, ws.max_row + 1)),
                default=10,
            )
            ws.column_dimensions[get_column_letter(col_idx)].width = min(
                max_len + 4, 50
            )

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        wb.save(path)
        logger.info(f"Excel saved → {path}  ({len(agents)} rows)")
        return path
