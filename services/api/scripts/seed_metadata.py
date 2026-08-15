import asyncio
import os
import sys

# Add the app directory to the path so we can import dependencies
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.dependencies.database import AsyncSessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_metadata():
    logger.info("Seeding Source Metadata (Phase 5)...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Ensure the 4 primary sources exist
            sources_data = [
                ("Sun News", "sunnews.in", "DRAVIDIAN_ORIENTED", 0.95, "Owned by Sun Group (Maran family, DMK affiliated)"),
                ("Puthiya Thalaimurai", "puthiyathalaimurai.com", "OTHER_UNKNOWN", 0.70, "Owned by SRM Group"),
                ("Thanthi TV", "thanthitv.com", "CONSERVATIVE_VARIABLE", 0.60, "Owned by Daily Thanthi group, variable leanings"),
                ("Dinakaran", "dinakaran.com", "DRAVIDIAN_ORIENTED", 0.90, "Owned by Sun Group")
            ]
            
            for s_name, s_domain, s_orient, s_conf, s_ev in sources_data:
                await db.execute(text("""
                    INSERT INTO sources (name, domain, orientation, orientation_confidence, orientation_evidence)
                    VALUES (:name, :domain, :orientation, :conf, :ev)
                    ON CONFLICT DO NOTHING
                """), {"name": s_name, "domain": s_domain, "orientation": s_orient, "conf": s_conf, "ev": s_ev})
            
            # 2. Get the Source IDs
            result = await db.execute(text("SELECT id, name FROM sources"))
            source_map = {row.name: str(row.id) for row in result.fetchall()}
            
            # 3. Insert Ownership Data
            ownership_data = [
                (source_map.get("Sun News"), "Sun TV Network Ltd", "Sun Group", "Kalanithi Maran", "Strong direct affiliation with DMK leadership"),
                (source_map.get("Dinakaran"), "Kal Publications", "Sun Group", "Kalanithi Maran", "Strong direct affiliation with DMK leadership"),
                (source_map.get("Puthiya Thalaimurai"), "New Generation Media", "SRM Group", "T. R. Pachamuthu", "Independent educational conglomerate"),
                (source_map.get("Thanthi TV"), "Metronation Chennai Television", "Daily Thanthi", "S. Balasubramanian Adityan", "Legacy print media group")
            ]
            
            for o_sid, o_name, o_parent, o_owner, o_affil in ownership_data:
                if not o_sid: continue
                await db.execute(text("""
                    INSERT INTO ownership_entities (source_id, name, parent_company, owner, political_or_affiliate_links)
                    VALUES (:sid, :name, :parent, :owner, :affil)
                    ON CONFLICT DO NOTHING
                """), {"sid": o_sid, "name": o_name, "parent": o_parent, "owner": o_owner, "affil": o_affil})
                
            # 4. Insert Reliability Data
            reliability_data = [
                (source_map.get("Sun News"), "LOW", "Generally factual reporting, but strong selection bias."),
                (source_map.get("Puthiya Thalaimurai"), "HIGH", "High editorial independence and factuality."),
                (source_map.get("Thanthi TV"), "MEDIUM", "Occasional sensationalism."),
            ]
            
            for r_sid, r_level, r_notes in reliability_data:
                if not r_sid: continue
                await db.execute(text("""
                    INSERT INTO source_reliability (source_id, reliability_level, historical_notes)
                    VALUES (:sid, :level, :notes)
                    ON CONFLICT DO NOTHING
                """), {"sid": r_sid, "level": r_level, "notes": r_notes})
                
            await db.commit()
            logger.info("Metadata seeding complete!")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error seeding metadata: {e}")

if __name__ == "__main__":
    asyncio.run(seed_metadata())
