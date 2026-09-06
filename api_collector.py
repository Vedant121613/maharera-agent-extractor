#!/usr/bin/env python3
"""
MahaRERA Agent Data Extractor - Direct API Version
===================================================
NO CAPTCHA REQUIRED - Uses public APIs directly

This bypasses CAPTCHA entirely by calling the same APIs
the website uses internally.
"""

import requests
import time
import re
from datetime import datetime
from typing import Optional, Dict, List
from bs4 import BeautifulSoup

from config.config import Config
from database.database import Database
from exporter.excel import ExcelExporter
from utils.logger import setup_logger
from colorama import Fore, Style

logger = setup_logger("api_collector")


class APICollector:
    """
    Collects agent data using direct API calls - NO BROWSER, NO CAPTCHA
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://maharerait.maharashtra.gov.in/'
        })
        self.db = Database(Config.DB_PATH)
        
        logger.info("✅ APICollector initialized - NO CAPTCHA required")
    
    def get_agent_ids_from_page(self, page_num: int = 1) -> List[Dict]:
        """
        Extract agent IDs from search results page via HTML scraping
        
        Returns:
            List of dicts with: agent_id, agent_name, certificate_no
        """
        url = f"https://maharera.maharashtra.gov.in/agents-search-result?page={page_num}"
        
        try:
            logger.debug(f"Fetching page {page_num}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            agents = []
            
            table = soup.find('table')
            if not table:
                logger.warning(f"No table found on page {page_num}")
                return agents
            
            rows = table.find_all('tr')
            logger.debug(f"Found {len(rows)} rows in table")
            
            for row in rows[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue
                
                try:
                    agent_name = cols[1].get_text(strip=True)
                    cert_no = cols[2].get_text(strip=True)
                    
                    # Extract agent ID from view link
                    view_link = cols[3].find('a')
                    if view_link and view_link.get('href'):
                        match = re.search(r'/agent/view/(\d+)', view_link['href'])
                        if match:
                            agent_id = int(match.group(1))
                            agents.append({
                                'agent_id': agent_id,
                                'agent_name': agent_name,
                                'certificate_no': cert_no
                            })
                            logger.debug(f"  Found agent {agent_id}: {agent_name}")
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Page {page_num}: Found {len(agents)} agents")
            return agents
            
        except Exception as e:
            logger.error(f"Error fetching page {page_num}: {e}")
            return []
    
    def get_total_count(self) -> tuple[int, int]:
        """
        Get total agent count and page count from first page
        
        Returns:
            (total_agents, total_pages)
        """
        try:
            response = self.session.get("https://maharera.maharashtra.gov.in/agents-search-result")
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # Look for "Showing Final X Result"
            match = re.search(r'Showing Final (\d+) Result', text)
            if match:
                total_agents = int(match.group(1))
            else:
                # Fallback
                total_agents = 58488
            
            total_pages = (total_agents // 10) + (1 if total_agents % 10 > 0 else 0)
            
            logger.info(f"📊 Total: {total_agents} agents across {total_pages} pages")
            return total_agents, total_pages
            
        except Exception as e:
            logger.error(f"Error getting total count: {e}")
            return 58488, 5849  # Fallback
    
    def get_agent_details_via_api(self, agent_id: int) -> Optional[Dict]:
        """
        Get agent details DIRECTLY from public APIs - NO CAPTCHA NEEDED
        
        These endpoints are the same ones the website uses after CAPTCHA,
        but they're accessible without CAPTCHA when called directly.
        
        Returns:
            Dict with all agent data or None on failure
        """
        try:
            # API endpoints (all public, no auth required)
            base = "https://maharerait.maharashtra.gov.in/api/maha-rera-agent-management-service"
            
            general_url = f"{base}/agent/general/{agent_id}"
            contact_url = f"{base}/agent/contact/{agent_id}"
            address_url = f"{base}/agent/address/{agent_id}"
            
            logger.debug(f"Fetching API data for agent {agent_id}")
            
            # Make all API calls
            general_resp = self.session.get(general_url, timeout=30)
            contact_resp = self.session.get(contact_url, timeout=30)
            address_resp = self.session.get(address_url, timeout=30)
            
            # Parse JSON
            general = general_resp.json() if general_resp.status_code == 200 else {}
            contact = contact_resp.json() if contact_resp.status_code == 200 else {}
            address = address_resp.json() if address_resp.status_code == 200 else {}
            
            logger.debug(f"  General API: {general_resp.status_code}")
            logger.debug(f"  Contact API: {contact_resp.status_code}")
            logger.debug(f"  Address API: {address_resp.status_code}")
            
            # Extract data from responseObject
            gen_data = general.get('responseObject', {})
            con_data = contact.get('responseObject', {})
            add_data = address.get('responseObject', {})
            
            # Build unified data dict
            data = {
                'agent_id': agent_id,
                # General info
                'first_name': gen_data.get('firstName'),
                'middle_name': gen_data.get('middleName'),
                'last_name': gen_data.get('lastName'),
                'father_name': gen_data.get('fatherFullName'),
                'certificate_no': gen_data.get('reraRegistrationNumber'),
                'registration_date': gen_data.get('reraRegistrationDate'),
                'validity_end_date': gen_data.get('reraRegistrationEndDate'),
                'status': gen_data.get('agentCurrentStatus'),
                # Contact info
                'mobile': con_data.get('mobileNo') or con_data.get('mobileNumber'),
                'email': con_data.get('emailId') or con_data.get('alternateEmailId'),
                'alternate_mobile': con_data.get('alternateMobileNo'),
                'office_phone': con_data.get('officeNumber'),
                'website': con_data.get('websiteUrl'),
                # Address info
                'unit_number': add_data.get('unitNumber'),
                'building_name': add_data.get('buildingName'),
                'street_name': add_data.get('streetName'),
                'locality': add_data.get('locality'),
                'landmark': add_data.get('landmark'),
                'city': add_data.get('villageName') or add_data.get('city'),
                'taluka': add_data.get('talukaName'),
                'district': add_data.get('districtName'),
                'state': add_data.get('stateName') or 'Maharashtra',
                'pincode': add_data.get('pinCode'),
            }
            
            # Build full address
            addr_parts = [
                data.get('unit_number'),
                data.get('building_name'),
                data.get('street_name'),
                data.get('locality'),
            ]
            full_addr = ', '.join(str(p) for p in addr_parts if p)
            if full_addr:
                data['address'] = full_addr
            
            # Log extracted data
            if data.get('mobile'):
                logger.info(f"  📞 Mobile: {data['mobile']}")
            if data.get('email'):
                logger.info(f"  ✉️  Email: {data['email']}")
            if data.get('building_name'):
                logger.info(f"  🏢 Building: {data['building_name']}")
            
            return data
            
        except Exception as e:
            logger.error(f"API error for agent {agent_id}: {e}")
            return None
    
    def collect_all_agents(self, max_pages: Optional[int] = None, max_agents: Optional[int] = None):
        """
        Main collection function - scrapes ALL agents without CAPTCHA
        
        Args:
            max_pages: Limit to N pages (default: all)
            max_agents: Limit to N agents (default: all)
        """
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║  🚀 STARTING API COLLECTION - NO CAPTCHA REQUIRED           ║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
        
        # Phase 1: Get total count
        total_agents_count, total_pages = self.get_total_count()
        
        if max_pages:
            total_pages = min(total_pages, max_pages)
        
        print(f"  📊 Target: {total_pages} pages")
        print(f"  💾 Database: {Config.DB_PATH}\n")
        
        # Phase 2: Collect agent IDs from search pages
        print(f"{Fore.YELLOW}── PHASE 1: Collecting Agent IDs ──────────────────────────{Style.RESET_ALL}\n")
        
        all_agents = []
        for page in range(1, total_pages + 1):
            print(f"  Page {page:>4}/{total_pages}...", end=' ')
            agents = self.get_agent_ids_from_page(page)
            all_agents.extend(agents)
            print(f"{Fore.GREEN}✓ {len(agents)} agents{Style.RESET_ALL}")
            time.sleep(1)  # Rate limiting
        
        print(f"\n{Fore.GREEN}✅ Total agent IDs collected: {len(all_agents)}{Style.RESET_ALL}\n")
        
        # Phase 3: Get details via API (NO CAPTCHA)
        print(f"{Fore.YELLOW}── PHASE 2: Fetching Agent Details (NO CAPTCHA) ───────────{Style.RESET_ALL}\n")
        
        collected = 0
        failed = 0
        skipped = 0
        
        for idx, agent in enumerate(all_agents, 1):
            if max_agents and idx > max_agents:
                break
            
            agent_id = agent['agent_id']
            agent_name = agent['agent_name']
            cert_no = agent['certificate_no']
            
            # Check if already collected
            if self.db.agent_exists(agent_id):
                existing = self.db._connect().execute(
                    "SELECT collection_status FROM agents WHERE agent_id=?", (agent_id,)
                ).fetchone()
                if existing and existing[0] == "collected":
                    print(f"  [{idx:>4}/{len(all_agents)}] {agent_id} {agent_name[:35]:35} {Fore.CYAN}— already collected ✓{Style.RESET_ALL}")
                    skipped += 1
                    continue
            
            print(f"  [{idx:>4}/{len(all_agents)}] {agent_id} {agent_name[:35]:35} ", end='')
            
            # Get details from API
            details = self.get_agent_details_via_api(agent_id)
            
            if details and (details.get('mobile') or details.get('email')):
                # Save to database
                details['agent_name'] = agent_name
                details['certificate_no'] = cert_no
                self.db.upsert_agent(details)
                self.db.mark_collected(agent_id)
                
                collected += 1
                mobile = details.get('mobile', '—')
                email = details.get('email', '—')[:30]
                print(f"{Fore.GREEN}✓ 📱 {mobile} ✉ {email}{Style.RESET_ALL}")
            else:
                self.db.mark_failed(agent_id, "No data from API")
                failed += 1
                print(f"{Fore.RED}✗ No data{Style.RESET_ALL}")
            
            time.sleep(1)  # Rate limiting
        
        # Final summary
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║  ✅ COLLECTION COMPLETE!                                     ║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"  Total processed    : {len(all_agents)}")
        print(f"  ✅ Collected        : {collected}")
        print(f"  ✗ Failed           : {failed}")
        print(f"  ⊚ Skipped (exists) : {skipped}")
        print(f"  💾 Database        : {Config.DB_PATH}\n")
        
        # Export to Excel if we collected any
        if collected > 0:
            print(f"{Fore.YELLOW}📊 Exporting to Excel...{Style.RESET_ALL}")
            filename = ExcelExporter(self.db).export()
            print(f"{Fore.GREEN}✅ Exported to: {filename}{Style.RESET_ALL}\n")
        
        return {
            'total': len(all_agents),
            'collected': collected,
            'failed': failed,
            'skipped': skipped
        }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    from colorama import init as colorama_init
    
    colorama_init(autoreset=True)
    
    parser = argparse.ArgumentParser(
        description="MahaRERA Agent Extractor - Direct API (NO CAPTCHA)"
    )
    parser.add_argument("--pages", type=int, default=None,
                        help="Max pages to scrape (default: all)")
    parser.add_argument("--agents", type=int, default=None,
                        help="Max agents to collect (default: all)")
    parser.add_argument("--test", action="store_true",
                        help="Test mode: collect first 10 agents only")
    
    args = parser.parse_args()
    
    collector = APICollector()
    
    if args.test:
        print(f"\n{Fore.YELLOW}🔧 TEST MODE: Collecting first 10 agents{Style.RESET_ALL}")
        collector.collect_all_agents(max_pages=1, max_agents=10)
    else:
        collector.collect_all_agents(max_pages=args.pages, max_agents=args.agents)
