#!/usr/bin/env python3
"""
MahaRERA Agent Data Extractor
==============================
Single entry point. Run with --help to see all options.

Examples:
    python main.py --scrape
    python main.py --scrape --pages 10 --no-headless
    python main.py --export excel
    python main.py --export csv
"""

import argparse
import sys
import time
from datetime import datetime

from colorama import Fore, Style, init as colorama_init

from config.config import Config
from browser.browser_manager import BrowserManager
from captcha.captcha_handler import CaptchaHandler
from scraper.search_pages import SearchPageScraper
from scraper.agent_details import AgentDetailsScraper
from database.database import Database
from exporter.excel import ExcelExporter
from exporter.csv_exporter import CSVExporter
from utils.logger import setup_logger

colorama_init(autoreset=True)
logger = setup_logger("main")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MahaRERA Agent Data Extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--scrape",  action="store_true",
                        help="Run the scraper to collect agent data")
    parser.add_argument("--pages",   type=int, default=None,
                        help="Max search pages to scrape (default: all)")
    parser.add_argument("--start-page", type=int, default=1,
                        help="Start from this page number (default: 1)")
    parser.add_argument("--export",  choices=["excel", "csv", "both"],
                        help="Export collected data")
    parser.add_argument("--output",  type=str, default=None,
                        help="Output file base path (without extension)")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run browser headless (default: True)")
    parser.add_argument("--no-headless", dest="headless", action="store_false",
                        help="Show browser window")
    return parser.parse_args()


# ── Banner ────────────────────────────────────────────────────────────────────

def print_banner() -> None:
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║       MahaRERA Agent Data Extractor                          ║
║       Automated · CAPTCHA-aware · SQLite-backed              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
  Headless  : {Config.HEADLESS}
  DB        : {Config.DB_PATH}
  CAPTCHA   : {Config.CAPTCHA_SOLVER_TYPE}
  Output    : {Config.OUTPUT_DIR}
""")


# ── Unified Scraping: Search page → immediately collect each agent's details ──

def scrape_agents(db: Database, headless: bool, max_pages: int | None, start_page: int = 1) -> dict:
    """
    Scrape search pages and immediately collect full details for each agent.
    
    Returns:
        Stats dict with 'total_agents', 'collected', 'failed'
    """
    print(f"\n{Fore.CYAN}── Scraping Agent Data ─────────────────────────────────────{Style.RESET_ALL}")
    
    stats = {"total_agents": 0, "collected": 0, "failed": 0, "skipped": 0}
    captcha = CaptchaHandler()

    with BrowserManager(headless=headless) as bm:
        search_page = bm.new_page()
        detail_page = bm.new_page()  # Keep a separate page for details
        
        # Navigate to search results
        bm.navigate(search_page, Config.AGENT_SEARCH_URL)
        captcha.handle_captcha(search_page)
        
        search_scraper = SearchPageScraper(search_page)
        total_pages = search_scraper.get_total_pages()
        
        if max_pages:
            total_pages = min(total_pages, start_page + max_pages - 1)
        
        print(f"  Starting from page: {start_page}")
        print(f"  Ending at page: {total_pages}\n")
        
        # Navigate to start page if not page 1
        if start_page > 1:
            print(f"  Navigating to page {start_page}...")
            ok = search_scraper.navigate_to_page(start_page)
            if not ok:
                print(f"{Fore.RED}Failed to navigate to start page {start_page}{Style.RESET_ALL}")
                return stats
            captcha.handle_captcha(search_page)
        
        # Process each search result page
        for page_num in range(start_page, total_pages + 1):
            print(f"{Fore.YELLOW}┌─ Page {page_num}/{total_pages} ───────────────────────────────────────────{Style.RESET_ALL}")
            
            if page_num > start_page:
                ok = search_scraper.navigate_to_page(page_num)
                if not ok:
                    print(f"{Fore.RED}│  Navigation failed — skipping page{Style.RESET_ALL}")
                    continue
                captcha.handle_captcha(search_page)
            
            # Extract all agent IDs from this search page
            agents = search_scraper.extract_agents()
            if not agents:
                print(f"{Fore.RED}│  No agents found on page — stopping{Style.RESET_ALL}")
                break
            
            print(f"{Fore.GREEN}│  Found {len(agents)} agents on search page{Style.RESET_ALL}")
            stats["total_agents"] += len(agents)
            
            # Process each agent immediately
            for idx, agent_data in enumerate(agents, start=1):
                agent_id = agent_data["agent_id"]
                agent_name = agent_data["agent_name"]
                
                # Check if already collected
                if db.agent_exists(agent_id):
                    existing = db._connect().execute(
                        "SELECT collection_status FROM agents WHERE agent_id=?", (agent_id,)
                    ).fetchone()
                    if existing and existing[0] == "collected":
                        print(f"{Fore.CYAN}│  [{idx:>2}/{len(agents)}] {agent_id} {agent_name[:30]:30} — already collected ✓{Style.RESET_ALL}")
                        stats["skipped"] += 1
                        continue
                
                # Save basic info first
                db.upsert_agent({
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "certificate_no": agent_data.get("certificate_no", ""),
                    "collection_status": "pending",
                })
                
                print(f"{Fore.YELLOW}│  [{idx:>2}/{len(agents)}] {agent_id} {agent_name[:30]:30}{Style.RESET_ALL}", end=" ")
                
                # Navigate to detail page
                detail_url = Config.get_detail_url(agent_id)
                try:
                    logger.debug(f"=== Starting agent {agent_id} ===")
                    
                    # Set up API response capture BEFORE navigation
                    api_responses = []
                    
                    def capture_response(response):
                        """Capture all API responses"""
                        try:
                            url = response.url
                            # Capture responses containing agent data
                            if any(keyword in url for keyword in ['getAgent', 'Contact', 'Address', 'api/', '/en/api/']):
                                try:
                                    body_bytes = response.body()
                                    api_responses.append({
                                        'url': url,
                                        'body': body_bytes
                                    })
                                    logger.debug(f"📡 Captured: {url.split('/')[-1][:50]}")
                                except Exception as e:
                                    logger.debug(f"Could not read body: {e}")
                        except Exception:
                            pass
                    
                    # Attach listener BEFORE navigating
                    detail_page.on("response", capture_response)
                    logger.debug("Network listener active BEFORE navigation")
                    
                    bm.navigate(detail_page, detail_url)
                    logger.debug(f"Loaded: {detail_page.title()}")
                    
                    # Handle CAPTCHA on detail page
                    logger.debug(f"About to call handle_captcha for {agent_id}")
                    captcha_solved = captcha.handle_captcha(detail_page)
                    logger.debug(f"handle_captcha returned: {captcha_solved} for {agent_id}")
                    
                    if not captcha_solved:
                        logger.warning(f"CAPTCHA failed for {agent_id}")
                        db.mark_failed(agent_id, "CAPTCHA failed")
                        stats["failed"] += 1
                        print(f"{Fore.RED}✗ CAPTCHA failed{Style.RESET_ALL}")
                        continue
                    
                    logger.debug(f"CAPTCHA solved! Waiting for API calls for {agent_id}")
                    
                    # Wait for additional API calls after CAPTCHA
                    detail_page.wait_for_load_state("networkidle", timeout=15000)
                    detail_page.wait_for_timeout(3000)
                    
                    logger.info(f"📊 Total API responses captured: {len(api_responses)}")
                    
                    # Parse captured API responses
                    contact_data = {}
                    address_data = {}
                    import json as json_lib
                    
                    for resp in api_responses:
                        try:
                            body_text = resp['body'].decode('utf-8')
                            json_data = json_lib.loads(body_text)
                            url = resp['url']
                            
                            logger.debug(f"Parsing: {url.split('/')[-1][:50]}")
                            
                            # Look for responseObject in the JSON
                            resp_obj = json_data.get('responseObject', json_data.get('data', {}))
                            
                            if not resp_obj or not isinstance(resp_obj, dict):
                                continue
                            
                            # Extract CONTACT details
                            mobile = (resp_obj.get('mobileNumber') or 
                                    resp_obj.get('mobile'))
                            alternate_mobile = resp_obj.get('alternateMobileNo')
                            office = resp_obj.get('officeNumber')
                            email = (resp_obj.get('alternateEmailId') or 
                                   resp_obj.get('emailId') or 
                                   resp_obj.get('email'))
                            website = resp_obj.get('websiteUrl')
                            
                            if mobile and 'X' not in str(mobile):
                                contact_data['mobile'] = str(mobile).strip()
                                logger.info(f"📞 Mobile: {contact_data['mobile']}")
                            
                            if alternate_mobile and 'X' not in str(alternate_mobile):
                                contact_data['alternate_mobile'] = str(alternate_mobile).strip()
                            
                            if office and 'X' not in str(office):
                                contact_data['office_phone'] = str(office).strip()
                                logger.info(f"☎️  Office: {contact_data['office_phone']}")
                            
                            if email and 'X' not in str(email):
                                contact_data['email'] = str(email).strip()
                                logger.info(f"✉️  Email: {contact_data['email']}")
                            
                            if website:
                                contact_data['website'] = str(website).strip()
                            
                            # Extract ADDRESS details
                            if resp_obj.get('unitNumber'):
                                address_data['unit_number'] = str(resp_obj.get('unitNumber', '')).strip()
                            if resp_obj.get('buildingName'):
                                address_data['building_name'] = str(resp_obj.get('buildingName', '')).strip()
                                logger.info(f"🏢 Building: {address_data['building_name']}")
                            if resp_obj.get('streetName'):
                                address_data['street_name'] = str(resp_obj.get('streetName', '')).strip()
                            if resp_obj.get('locality'):
                                address_data['locality'] = str(resp_obj.get('locality', '')).strip()
                            if resp_obj.get('landmark'):
                                address_data['landmark'] = str(resp_obj.get('landmark', '')).strip()
                            if resp_obj.get('villageName'):
                                address_data['city'] = str(resp_obj.get('villageName', '')).strip()
                            if resp_obj.get('talukaName'):
                                address_data['taluka'] = str(resp_obj.get('talukaName', '')).strip()
                            if resp_obj.get('districtName'):
                                address_data['district'] = str(resp_obj.get('districtName', '')).strip()
                                logger.info(f"📍 District: {address_data['district']}")
                            if resp_obj.get('stateName'):
                                address_data['state'] = str(resp_obj.get('stateName', '')).strip()
                            if resp_obj.get('pinCode'):
                                address_data['pincode'] = str(resp_obj.get('pinCode', '')).strip()
                            
                            # Build full address
                            if address_data:
                                addr_parts = [
                                    address_data.get('unit_number'),
                                    address_data.get('building_name'),
                                    address_data.get('street_name'),
                                    address_data.get('locality'),
                                ]
                                full_addr = ', '.join(p for p in addr_parts if p)
                                if full_addr:
                                    address_data['address'] = full_addr
                                    logger.info(f"📮 Address: {full_addr[:50]}...")
                        
                        except Exception as e:
                            logger.debug(f"Parse error: {e}")
                    
                    # Extract basic details from HTML
                    detail_scraper = AgentDetailsScraper(detail_page)
                    details = detail_scraper.extract_details() or {}
                    
                    # Merge API data (API data takes priority)
                    if contact_data:
                        details.update(contact_data)
                        logger.info(f"✅ Merged contact data")
                    
                    if address_data:
                        details.update(address_data)
                        logger.info(f"✅ Merged address data")
                    
                    if details:
                        logger.info(f"📱 Final Mobile: {details.get('mobile', 'NOT FOUND')}")
                        logger.info(f"✉️  Final Email: {details.get('email', 'NOT FOUND')}")
                    
                    if details:
                        details["agent_id"] = agent_id
                        db.upsert_agent(details)
                        db.mark_collected(agent_id)
                        stats["collected"] += 1
                        
                        mobile = details.get("mobile", "—")
                        email = details.get("email", "—")
                        print(f"{Fore.GREEN}✓ 📱 {mobile} ✉ {email}{Style.RESET_ALL}")
                    else:
                        db.mark_failed(agent_id, "no details extracted")
                        stats["failed"] += 1
                        print(f"{Fore.RED}✗ no data{Style.RESET_ALL}")
                    
                    time.sleep(Config.get_random_delay())
                
                except Exception as exc:
                    db.mark_failed(agent_id, str(exc)[:500])
                    stats["failed"] += 1
                    print(f"{Fore.RED}✗ {exc}{Style.RESET_ALL}")
                    logger.error(f"Agent {agent_id} failed with exception type {type(exc).__name__}: {exc}", exc_info=True)
                    logger.error(f"Exception repr: {repr(exc)}")
                    logger.error(f"Exception str: {str(exc)}")
            
            print(f"{Fore.YELLOW}└{'─' * 62}{Style.RESET_ALL}\n")
    
    return stats


# ── Export ────────────────────────────────────────────────────────────────────

def run_export(db: Database, fmt: str, output_base: str | None) -> None:
    print(f"\n{Fore.CYAN}── Export ───────────────────────────────────────────────────{Style.RESET_ALL}")

    if fmt in ("excel", "both"):
        path = (f"{output_base}.xlsx" if output_base else None)
        out = ExcelExporter(db).export(path)
        print(f"  {Fore.GREEN}Excel → {out}{Style.RESET_ALL}")

    if fmt in ("csv", "both"):
        path = (f"{output_base}.csv" if output_base else None)
        out = CSVExporter(db).export(path)
        print(f"  {Fore.GREEN}CSV   → {out}{Style.RESET_ALL}")


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    if not args.scrape and not args.export:
        print("Nothing to do. Use --scrape, --export, or both.")
        print("Run  python main.py --help  for usage.")
        sys.exit(1)

    print_banner()
    start = time.time()

    db = Database(Config.DB_PATH)

    try:
        if args.scrape:
            stats = scrape_agents(db, args.headless, args.pages, args.start_page)
            
            print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║  Scraping Complete                                           ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
  Total agents found : {stats['total_agents']}
  Collected          : {stats['collected']} {Fore.GREEN}✓{Style.RESET_ALL}
  Failed             : {stats['failed']} {Fore.RED}✗{Style.RESET_ALL}
  Skipped (existing) : {stats['skipped']}
""")

        if args.export:
            run_export(db, args.export, args.output)

        db_stats = db.get_stats()
        elapsed = time.time() - start
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║  Database Summary                                            ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
  Total in DB : {db_stats['total']}
  Collected   : {db_stats['collected']}
  Pending     : {db_stats['pending']}
  Failed      : {db_stats['failed']}
  
  Time elapsed: {elapsed:.1f}s
""")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
