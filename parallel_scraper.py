#!/usr/bin/env python3
"""
Parallel MahaRERA Scraper - Multiple Browser Instances
======================================================
Runs multiple browser instances in parallel to speed up scraping.

Usage:
    python parallel_scraper.py --workers 3 --start-page 10 --pages 30
    python parallel_scraper.py --workers 5 --start-page 1 --pages 100
"""

import argparse
import sys
import time
import threading
from datetime import datetime
from colorama import Fore, Style, init as colorama_init

from config.config import Config
from browser.browser_manager import BrowserManager
from captcha.captcha_handler import CaptchaHandler
from scraper.search_pages import SearchPageScraper
from scraper.agent_details import AgentDetailsScraper
from database.database import Database
from exporter.excel import ExcelExporter
from utils.logger import setup_logger

colorama_init(autoreset=True)
logger = setup_logger("parallel_scraper")


class ParallelScraper:
    """
    Manages multiple browser instances scraping in parallel
    """
    
    def __init__(self, num_workers: int, db: Database, headless: bool = True):
        self.num_workers = num_workers
        self.db = db
        self.headless = headless
        self.stats = {
            "total_agents": 0,
            "collected": 0,
            "failed": 0,
            "skipped": 0
        }
        self.stats_lock = threading.Lock()
        
    def worker_scrape_pages(self, worker_id: int, page_range: range):
        """
        Worker function - each worker scrapes assigned pages
        """
        worker_logger = setup_logger(f"worker_{worker_id}")
        worker_logger.info(f"🚀 Worker {worker_id} starting - pages {page_range.start} to {page_range.stop-1}")
        
        local_stats = {"collected": 0, "failed": 0, "skipped": 0, "total": 0}
        captcha = CaptchaHandler()
        
        try:
            with BrowserManager(headless=self.headless) as bm:
                search_page = bm.new_page()
                detail_page = bm.new_page()
                
                # Navigate to search results
                bm.navigate(search_page, Config.AGENT_SEARCH_URL)
                captcha.handle_captcha(search_page)
                
                search_scraper = SearchPageScraper(search_page)
                
                # Process each assigned page
                for page_num in page_range:
                    worker_logger.info(f"📄 Worker {worker_id} - Page {page_num}")
                    
                    # Navigate to page
                    if page_num > 1:
                        ok = search_scraper.navigate_to_page(page_num)
                        if not ok:
                            worker_logger.error(f"Failed to navigate to page {page_num}")
                            continue
                        captcha.handle_captcha(search_page)
                    
                    # Extract agents on this page
                    agents = search_scraper.extract_agents()
                    if not agents:
                        worker_logger.warning(f"No agents found on page {page_num}")
                        continue
                    
                    worker_logger.info(f"Found {len(agents)} agents on page {page_num}")
                    local_stats["total"] += len(agents)
                    
                    # Process each agent
                    for idx, agent_data in enumerate(agents, 1):
                        agent_id = agent_data["agent_id"]
                        agent_name = agent_data["agent_name"]
                        
                        # Check if already collected
                        if self.db.agent_exists(agent_id):
                            existing = self.db._connect().execute(
                                "SELECT collection_status FROM agents WHERE agent_id=?", (agent_id,)
                            ).fetchone()
                            if existing and existing[0] == "collected":
                                worker_logger.debug(f"Agent {agent_id} already collected - skipping")
                                local_stats["skipped"] += 1
                                continue
                        
                        # Save basic info
                        self.db.upsert_agent({
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "certificate_no": agent_data.get("certificate_no", ""),
                            "collection_status": "pending",
                        })
                        
                        # Navigate to detail page
                        detail_url = Config.get_detail_url(agent_id)
                        try:
                            # Set up API response capture
                            api_responses = []
                            
                            def capture_response(response):
                                try:
                                    url = response.url
                                    if any(keyword in url for keyword in ['getAgent', 'Contact', 'Address', 'api/', '/en/api/']):
                                        try:
                                            body_bytes = response.body()
                                            api_responses.append({'url': url, 'body': body_bytes})
                                        except:
                                            pass
                                except:
                                    pass
                            
                            detail_page.on("response", capture_response)
                            bm.navigate(detail_page, detail_url)
                            
                            # Handle CAPTCHA
                            captcha_solved = captcha.handle_captcha(detail_page)
                            
                            if not captcha_solved:
                                self.db.mark_failed(agent_id, "CAPTCHA failed")
                                local_stats["failed"] += 1
                                worker_logger.warning(f"❌ Agent {agent_id} - CAPTCHA failed")
                                continue
                            
                            # Wait for API calls
                            detail_page.wait_for_load_state("networkidle", timeout=15000)
                            detail_page.wait_for_timeout(2000)
                            
                            # Parse API responses
                            contact_data = {}
                            address_data = {}
                            import json as json_lib
                            
                            for resp in api_responses:
                                try:
                                    body_text = resp['body'].decode('utf-8')
                                    json_data = json_lib.loads(body_text)
                                    resp_obj = json_data.get('responseObject', json_data.get('data', {}))
                                    
                                    if not resp_obj or not isinstance(resp_obj, dict):
                                        continue
                                    
                                    # Extract contact
                                    mobile = resp_obj.get('mobileNumber') or resp_obj.get('mobile')
                                    if mobile and 'X' not in str(mobile):
                                        contact_data['mobile'] = str(mobile).strip()
                                    
                                    alternate_mobile = resp_obj.get('alternateMobileNo')
                                    if alternate_mobile and 'X' not in str(alternate_mobile):
                                        contact_data['alternate_mobile'] = str(alternate_mobile).strip()
                                    
                                    office = resp_obj.get('officeNumber')
                                    if office and 'X' not in str(office):
                                        contact_data['office_phone'] = str(office).strip()
                                    
                                    email = (resp_obj.get('alternateEmailId') or 
                                           resp_obj.get('emailId') or 
                                           resp_obj.get('email'))
                                    if email and 'X' not in str(email):
                                        contact_data['email'] = str(email).strip()
                                    
                                    website = resp_obj.get('websiteUrl')
                                    if website:
                                        contact_data['website'] = str(website).strip()
                                    
                                    # Extract address
                                    if resp_obj.get('buildingName'):
                                        address_data['building_name'] = str(resp_obj.get('buildingName', '')).strip()
                                    if resp_obj.get('streetName'):
                                        address_data['street_name'] = str(resp_obj.get('streetName', '')).strip()
                                    if resp_obj.get('locality'):
                                        address_data['locality'] = str(resp_obj.get('locality', '')).strip()
                                    if resp_obj.get('villageName'):
                                        address_data['city'] = str(resp_obj.get('villageName', '')).strip()
                                    if resp_obj.get('districtName'):
                                        address_data['district'] = str(resp_obj.get('districtName', '')).strip()
                                    if resp_obj.get('pinCode'):
                                        address_data['pincode'] = str(resp_obj.get('pinCode', '')).strip()
                                    
                                except:
                                    pass
                            
                            # Extract from HTML
                            detail_scraper = AgentDetailsScraper(detail_page)
                            details = detail_scraper.extract_details() or {}
                            
                            # Merge API data
                            if contact_data:
                                details.update(contact_data)
                            if address_data:
                                details.update(address_data)
                            
                            if details:
                                details["agent_id"] = agent_id
                                self.db.upsert_agent(details)
                                self.db.mark_collected(agent_id)
                                local_stats["collected"] += 1
                                
                                mobile = details.get("mobile", "—")
                                email = details.get("email", "—")
                                worker_logger.info(f"✅ Agent {agent_id} - {mobile} | {email[:30]}")
                            else:
                                self.db.mark_failed(agent_id, "no details")
                                local_stats["failed"] += 1
                                worker_logger.warning(f"❌ Agent {agent_id} - no data")
                            
                            time.sleep(Config.get_random_delay())
                            
                        except Exception as exc:
                            self.db.mark_failed(agent_id, str(exc)[:500])
                            local_stats["failed"] += 1
                            worker_logger.error(f"❌ Agent {agent_id} - {type(exc).__name__}: {exc}")
        
        except Exception as exc:
            worker_logger.error(f"Worker {worker_id} fatal error: {exc}", exc_info=True)
        
        finally:
            # Update global stats
            with self.stats_lock:
                self.stats["total_agents"] += local_stats["total"]
                self.stats["collected"] += local_stats["collected"]
                self.stats["failed"] += local_stats["failed"]
                self.stats["skipped"] += local_stats["skipped"]
            
            worker_logger.info(f"🏁 Worker {worker_id} finished - Collected: {local_stats['collected']}, Failed: {local_stats['failed']}")
    
    def run(self, start_page: int, total_pages: int):
        """
        Distribute pages across workers and start parallel scraping
        """
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║  🚀 PARALLEL SCRAPER - {self.num_workers} WORKERS                        ║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
        print(f"  Pages: {start_page} to {start_page + total_pages - 1}")
        print(f"  Workers: {self.num_workers}")
        print(f"  Mode: {'Headless' if self.headless else 'Visible'}\n")
        
        # Distribute pages across workers
        pages_per_worker = total_pages // self.num_workers
        remaining = total_pages % self.num_workers
        
        threads = []
        current_page = start_page
        
        for i in range(self.num_workers):
            # Give extra pages to first workers if there's a remainder
            worker_pages = pages_per_worker + (1 if i < remaining else 0)
            page_range = range(current_page, current_page + worker_pages)
            current_page += worker_pages
            
            thread = threading.Thread(
                target=self.worker_scrape_pages,
                args=(i + 1, page_range),
                daemon=False
            )
            threads.append(thread)
            thread.start()
            time.sleep(2)  # Stagger worker starts
        
        # Wait for all workers to complete
        for thread in threads:
            thread.join()
        
        # Final summary
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║  ✅ PARALLEL SCRAPING COMPLETE!                              ║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"  Total agents found : {self.stats['total_agents']}")
        print(f"  Collected          : {self.stats['collected']} {Fore.GREEN}✓{Style.RESET_ALL}")
        print(f"  Failed             : {self.stats['failed']} {Fore.RED}✗{Style.RESET_ALL}")
        print(f"  Skipped (existing) : {self.stats['skipped']}\n")
        
        return self.stats


def parse_args():
    parser = argparse.ArgumentParser(description="Parallel MahaRERA Agent Scraper")
    parser.add_argument("--workers", type=int, default=3,
                        help="Number of parallel browser instances (default: 3)")
    parser.add_argument("--start-page", type=int, default=1,
                        help="Start from this page (default: 1)")
    parser.add_argument("--pages", type=int, required=True,
                        help="Total pages to scrape across all workers")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run browsers in headless mode (default)")
    parser.add_argument("--no-headless", dest="headless", action="store_false",
                        help="Show browser windows")
    parser.add_argument("--export", action="store_true",
                        help="Export to Excel after completion")
    return parser.parse_args()


def main():
    args = parse_args()
    
    if args.workers < 1 or args.workers > 10:
        print(f"{Fore.RED}Error: Workers must be between 1 and 10{Style.RESET_ALL}")
        sys.exit(1)
    
    if args.pages < args.workers:
        print(f"{Fore.RED}Error: Pages must be >= workers{Style.RESET_ALL}")
        sys.exit(1)
    
    start_time = time.time()
    db = Database(Config.DB_PATH)
    
    try:
        scraper = ParallelScraper(
            num_workers=args.workers,
            db=db,
            headless=args.headless
        )
        
        stats = scraper.run(
            start_page=args.start_page,
            total_pages=args.pages
        )
        
        if args.export and stats["collected"] > 0:
            print(f"\n{Fore.YELLOW}📊 Exporting to Excel...{Style.RESET_ALL}")
            filename = ExcelExporter(db).export()
            print(f"{Fore.GREEN}✅ Exported to: {filename}{Style.RESET_ALL}\n")
        
        elapsed = time.time() - start_time
        db_stats = db.get_stats()
        
        print(f"{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║  Database Summary                                            ║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"  Total in DB : {db_stats['total']}")
        print(f"  Collected   : {db_stats['collected']}")
        print(f"  Pending     : {db_stats['pending']}")
        print(f"  Failed      : {db_stats['failed']}")
        print(f"  \n  Time elapsed: {elapsed/60:.1f} minutes\n")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
