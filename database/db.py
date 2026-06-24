import sqlite3
import os
from datetime import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(DB_DIR), "robotics.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db(conn):
    # Migration: add country column if missing
    try:
        conn.execute("ALTER TABLE companies ADD COLUMN country TEXT DEFAULT ''")
    except Exception:
        pass
    # Migration: add engineering columns
    try:
        conn.execute("ALTER TABLE companies ADD COLUMN engineering_pct TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE companies ADD COLUMN engineering_employees TEXT DEFAULT ''")
    except Exception:
        pass
    # Migration: add company_type column
    try:
        conn.execute("ALTER TABLE companies ADD COLUMN company_type TEXT DEFAULT 'corporation'")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE companies ADD COLUMN image_source TEXT DEFAULT 'auto'")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE products ADD COLUMN image_source TEXT DEFAULT 'auto'")
    except Exception:
        pass
    # Migration: consolidate business_model labels
    try:
        conn.execute("UPDATE companies SET business_model = 'Hybrid' WHERE business_model IN ('Purchase / Hybrid', 'RaaS / Hybrid')")
    except Exception:
        pass
    try:
        conn.execute("UPDATE companies SET business_model = 'RaaS' WHERE business_model = 'RaaS (Robot-as-a-Service)'")
    except Exception:
        pass

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            short_description TEXT,
            website TEXT,
            headquarters TEXT,
            country TEXT DEFAULT '',
            founded_year INTEGER,
            funding_total_usd TEXT,
            business_model TEXT,
            revenue_est TEXT,
            employees TEXT,
            logo_url TEXT,
            notes TEXT,
            status TEXT DEFAULT 'active',
            company_type TEXT DEFAULT 'corporation',
            engineering_pct TEXT DEFAULT '',
            engineering_employees TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL REFERENCES companies(id),
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            category TEXT,
            subcategory TEXT,
            product_url TEXT,
            image_url TEXT,
            release_year INTEGER,
            status TEXT DEFAULT 'current',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS product_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            spec_name TEXT NOT NULL,
            spec_value TEXT NOT NULL,
            unit TEXT,
            source TEXT DEFAULT 'manual',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS capabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            category TEXT
        );

        CREATE TABLE IF NOT EXISTS product_capabilities (
            product_id INTEGER NOT NULL REFERENCES products(id),
            capability_id INTEGER NOT NULL REFERENCES capabilities(id),
            notes TEXT,
            PRIMARY KEY (product_id, capability_id)
        );

        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER REFERENCES companies(id),
            product_id INTEGER REFERENCES products(id),
            url TEXT NOT NULL,
            caption TEXT,
            image_type TEXT,
            width INTEGER,
            height INTEGER
        );

        CREATE TABLE IF NOT EXISTS case_studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER REFERENCES companies(id),
            product_id INTEGER REFERENCES products(id),
            title TEXT NOT NULL,
            customer TEXT,
            industry TEXT,
            challenge TEXT,
            solution TEXT,
            results TEXT,
            metrics TEXT,
            url TEXT,
            featured_image TEXT,
            published_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_products_company ON products(company_id);
        CREATE INDEX IF NOT EXISTS idx_specs_product ON product_specs(product_id);
        CREATE INDEX IF NOT EXISTS idx_specs_name ON product_specs(spec_name);
        CREATE INDEX IF NOT EXISTS idx_case_studies_company ON case_studies(company_id);
        CREATE INDEX IF NOT EXISTS idx_case_studies_product ON case_studies(product_id);
        CREATE INDEX IF NOT EXISTS idx_case_studies_industry ON case_studies(industry);

        CREATE TABLE IF NOT EXISTS company_associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL REFERENCES companies(id),
            associated_company_id INTEGER REFERENCES companies(id),
            association_name TEXT,
            association_type TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            title TEXT,
            bio TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS person_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL REFERENCES people(id),
            entity_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL DEFAULT 'company',
            role TEXT NOT NULL,
            start_year INTEGER,
            end_year INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_person_roles_person ON person_roles(person_id);
        CREATE INDEX IF NOT EXISTS idx_person_roles_entity ON person_roles(entity_id, entity_type);

        CREATE TABLE IF NOT EXISTS product_bins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            bin_type TEXT NOT NULL,
            label TEXT,
            outer_length_mm INTEGER,
            outer_width_mm INTEGER,
            outer_height_mm INTEGER,
            inner_length_mm INTEGER,
            inner_width_mm INTEGER,
            inner_height_mm INTEGER,
            max_payload_kg REAL,
            grid_height_m REAL,
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_product_bins_product ON product_bins(product_id);

        CREATE TABLE IF NOT EXISTS product_image_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            image_url TEXT NOT NULL,
            alt_text TEXT,
            source TEXT DEFAULT 'scrape',
            width INTEGER,
            height INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS company_image_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL REFERENCES companies(id),
            image_url TEXT NOT NULL,
            alt_text TEXT,
            source TEXT DEFAULT 'scrape',
            width INTEGER,
            height INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_prod_img_cand_product ON product_image_candidates(product_id);
        CREATE INDEX IF NOT EXISTS idx_comp_img_cand_company ON company_image_candidates(company_id);

        CREATE TABLE IF NOT EXISTS case_study_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_study_id INTEGER NOT NULL REFERENCES case_studies(id),
            metric_name TEXT NOT NULL,
            metric_value_num REAL,
            metric_value_text TEXT,
            unit TEXT,
            source TEXT DEFAULT 'parsed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_cs_metrics_cs ON case_study_metrics(case_study_id);
        CREATE INDEX IF NOT EXISTS idx_cs_metrics_name ON case_study_metrics(metric_name);
    """)
    conn.commit()

def seed_database(conn):
    cur = conn.execute("SELECT count(*) FROM companies")
    if cur.fetchone()[0] > 0:
        cur = conn.execute("SELECT count(*) FROM company_associations")
        if cur.fetchone()[0] == 0:
            seed_associations(conn)
        return

    capabilities = [
        ("Truck Unloading", "Automated unloading of trailers and shipping containers", "Receiving"),
        ("Truck Loading", "Automated loading of trailers and containers", "Shipping"),
        ("Goods-to-Person", "System brings inventory to a stationary operator", "Picking"),
        ("Person-to-Goods", "Operator travels to inventory locations", "Picking"),
        ("Piece Picking", "Picking individual items from bins or totes", "Picking"),
        ("Case Picking", "Picking full cases or boxes", "Picking"),
        ("Pallet Handling", "Moving and storing palletized goods", "Material Handling"),
        ("Collaborative Picking", "Robot works alongside human picker", "Picking"),
        ("Automated Storage", "Robotized storage of inventory", "Storage"),
        ("Automated Retrieval", "Robotized retrieval from storage", "Storage"),
        ("Sortation", "Sorting items by destination or category", "Material Handling"),
        ("Transport", "Moving goods between zones in a facility", "Material Handling"),
        ("Putaway", "Moving received goods to storage locations", "Inventory"),
        ("Replenishment", "Restocking pick-face locations", "Inventory"),
        ("Depalletizing", "Breaking down pallet loads", "Receiving"),
        ("High-Density Storage", "Maximizing storage per square foot", "Storage"),
        ("Multi-Level Picking", "Picking from multiple storage levels", "Picking"),
        ("Returns Processing", "Handling customer returns", "Reverse Logistics"),
        ("Cross-Docking", "Transferring goods directly from inbound to outbound", "Material Handling"),
        ("Cold Chain Operation", "Operating in refrigerated or frozen environments", "Specialty"),
        ("Trailer Unloading", "Specialized unloading of truck trailers", "Receiving"),
        ("Cube Storage", "Three-dimensional cube-based storage system", "Storage"),
        ("Tote Handling", "Automated handling of totes and containers", "Material Handling"),
        ("Packing", "Packing items into boxes or containers", "Material Handling"),
        ("Palletizing", "Building pallet loads from cases or items", "Material Handling"),
        ("Machine Tending", "Loading/unloading parts into machines", "Industrial"),
        ("Surgical Assistance", "Robot-assisted surgical procedures", "Medical"),
        ("Minimally Invasive Surgery", "Surgery through small incisions using robotic instruments", "Medical"),
        ("Image-Guided Surgery", "Surgical navigation using real-time imaging and tracking", "Medical"),
        ("Orthopedic Surgery", "Robotic assistance for joint replacement and orthopedic procedures", "Medical"),
        ("Neurosurgery", "Robotic navigation and assistance for brain and spine surgery", "Medical"),
        ("Cardiac Intervention", "Robotic assistance for cardiac and vascular procedures", "Medical"),
        ("Endoscopy", "Robot-assisted endoscopic procedures", "Medical"),
        ("Teleoperation", "Remote control of robotic systems by a surgeon", "Medical"),
        ("Haptic Feedback", "Force feedback and tactile sensing for surgical robots", "Medical"),
        ("Autonomous Delivery", "Robot autonomously delivers items to locations", "Service"),
        ("Reception & Greeting", "Robot greets and interacts with people", "Service"),
        ("Cruise Mode", "Robot patrols and monitors autonomously", "Service"),
        ("Advertising Display", "Robot displays advertisements and promotions", "Service"),
        ("Guest Escorting", "Robot guides guests to destinations", "Service"),
        ("Multi-floor Operation", "Robot operates across multiple floors via elevators", "Logistics"),
        ("Enclosed Autonomous Delivery", "Delivery with secured enclosed compartments", "Service"),
        ("Laser Projection", "Robot projects information via integrated laser", "Service"),
        ("Industrial Material Transport", "Transport of heavy industrial payloads", "Material Handling"),
        ("Auto-follow Mode", "Robot automatically follows a person", "Service"),
        ("Power-assist Mode", "Manual assist mode with powered mobility", "Material Handling"),
        ("IoT Connectivity", "Internet of Things integration and API access", "Technology"),
        ("Bin-to-Person", "System brings bins to operator", "Picking"),
        ("Multi-robot Collaboration", "Multiple robots collaborate on tasks", "Technology"),
        ("Real-time Inventory Tracking", "Continuous inventory tracking via scan/vision", "Inventory"),
        ("QR Navigation", "Navigation using floor QR codes", "Technology"),
        ("High-density Bin Storage", "Maximizing bin storage density in racks", "Storage"),
        ("AI-optimized Scheduling", "AI-driven workload and path optimization", "Software"),
        ("Automated Inbound/Outbound", "Automated goods receipt and dispatch", "Logistics"),
        ("Drag-to-Teach Programming", "Programming by physically guiding robot arm", "Technology"),
        ("Collision Detection", "Automatic stop on collision detection", "Safety"),
        ("Precision Assembly", "High-precision part assembly", "Manufacturing"),
        ("Screwdriving", "Automated screw driving and fastening", "Manufacturing"),
        ("Bin Picking", "Picking parts from bins using vision", "Picking"),
        ("Inspection", "Automated quality inspection", "Manufacturing"),
        ("Hand-guiding Teaching", "Teaching by hand-guiding the robot arm", "Technology"),
        ("Arc Welding", "Automated arc welding operations", "Manufacturing"),
        ("Cutting", "Automated cutting operations", "Manufacturing"),
        ("Grinding & Polishing", "Automated surface finishing", "Manufacturing"),
        ("Loading & Unloading", "Automated part loading and unloading", "Manufacturing"),
        ("Safe Human-Robot Collaboration", "Certified safe collaborative operation", "Safety"),
        ("Vision Integration", "Integrated 2D/3D vision systems", "Technology"),
        ("Force Sensing", "Force/torque sensing for compliance", "Technology"),
        ("Quality Inspection", "Automated quality control inspection", "Manufacturing"),
        ("Screw Fastening", "Automated screw fastening operations", "Manufacturing"),
        ("Bipedal Walking", "Two-legged walking locomotion", "Mobility"),
        ("Bipedal Running", "Two-legged running at speed", "Mobility"),
        ("Autonomous Navigation", "Self-navigating to destinations", "Technology"),
        ("Visual Inspection", "AI-powered visual inspection", "Manufacturing"),
        ("Assembly Operations", "Multi-step assembly operations", "Manufacturing"),
        ("LLM-based Interaction", "Large language model powered interaction", "AI"),
        ("Factory Integration", "Integration with factory MES/ERP systems", "Manufacturing"),
        ("Open-source Programming", "Open SDK for custom programming", "Technology"),
        ("AI Education", "Education-focused AI curriculum platform", "Education"),
        ("Voice Interaction", "Speech recognition and voice synthesis", "AI"),
        ("Vision Recognition", "AI-powered image recognition", "AI"),
        ("All-terrain Locomotion", "Locomotion across varied terrain", "Mobility"),
        ("Obstacle Avoidance", "Automatic obstacle detection and avoidance", "Safety"),
        ("Secondary Development", "SDK for third-party development", "Technology"),
        ("Industrial Inspection", "Automated industrial equipment inspection", "Manufacturing"),
        ("Security Patrol", "Autonomous security monitoring patrol", "Service"),
        ("Heavy Lifting", "Lifting heavy payloads above 20kg", "Material Handling"),
        ("Fenceless Operation", "Safe operation without physical guarding", "Safety"),
        ("Fleet Learning", "Knowledge sharing across robot fleet", "AI"),
        ("Orbit Integration", "Integration with Boston Dynamics Orbit platform", "Software"),
        ("VR Teleoperation", "Virtual reality remote control", "Technology"),
        ("Part Sequencing", "Sequencing and kitting for assembly lines", "Manufacturing"),
        ("Order Fulfillment", "End-to-end order picking and packing", "Logistics"),
        ("Autonomous Floor Scrubbing", "Autonomous floor cleaning", "Service"),
        ("Edge-to-Edge Cleaning", "Cleaning to edges and corners", "Service"),
        ("Oil Stain Cleaning Mode", "Specialized oil stain removal", "Service"),
        ("Multi-stage Water Filtration", "Water recycling and filtration", "Service"),
        ("Auto Charging & Water Refill", "Autonomous charging and water refill", "Service"),
        ("Remote Monitoring", "Cloud-based remote monitoring", "Software"),
        ("IoT Fleet Management", "IoT-enabled fleet management platform", "Software"),
        ("Sweeping", "Autonomous floor sweeping", "Service"),
        ("Dust Mopping", "Autonomous dust mopping", "Service"),
        ("Disinfectant Spraying", "Autonomous sanitizing spray", "Service"),
        ("Heavy Material Handling", "Moving heavy materials and parts", "Material Handling"),
    ]

    for name, desc, cat in capabilities:
        conn.execute("INSERT OR IGNORE INTO capabilities (name, description, category) VALUES (?, ?, ?)",
                     (name, desc, cat))

    companies = [
        {
            "name": "Pickle Robotics",
            "slug": "pickle-robotics",
            "country": "USA",
            "short_description": "AI-powered robots that autonomously unload trucks and trailers",
            "description": "Pickle Robot Company develops physical AI for supply chain automation. Their one-armed robots autonomously unload trailers, picking up boxes weighing up to 50 pounds and placing them onto onboard conveyor belts. Founded by MIT alumni, the company combines generative AI, machine vision, and world-class autonomy to handle the toughest logistics tasks. Pickle robots reliably unload 400 to 1,500 cases per hour and can be deployed in less than 5 days with no WMS integration required.",
            "website": "https://www.picklerobot.com",
            "headquarters": "Charlestown, MA",
            "founded_year": 2018,
            "funding_total_usd": "$50M+",
            "business_model": "Hybrid",
            "revenue_est": "Undisclosed (private)",
            "employees": "100-200",
            "notes": "Named to Fast Company's 2026 Most Innovative Companies list. Uses KUKA robot arms. UPS is a customer.",
        },
        {
            "name": "Locus Robotics",
            "slug": "locus-robotics",
            "country": "USA",
            "short_description": "Collaborative AMR platform for fulfillment and distribution",
            "description": "Locus Robotics is a leader in collaborative autonomous mobile robots (AMRs) for warehouses. Their LocusONE platform orchestrates Locus Origin (collaborative picking) and Locus Vector (heavy material handling) robots. With a RaaS (Robot-as-a-Service) model, customers can scale robot capacity up or down in real time. Locus robots integrate with existing WMS and can be piloted within 48 hours. The platform supports 500+ robots per facility.",
            "website": "https://locusrobotics.com",
            "headquarters": "Wilmington, MA",
            "founded_year": 2014,
            "funding_total_usd": "$500M+",
            "business_model": "RaaS",
            "revenue_est": "~$300M (2025 est.)",
            "employees": "500-1000",
            "notes": "RaaS model ~$1,500/robot/month. 48-hour pilot deployment capability. Broad pre-built WMS integrations.",
        },
        {
            "name": "Geek+",
            "slug": "geekplus",
            "country": "China",
            "short_description": "World's largest AMR company by deployed robot count",
            "description": "Geek+ is the world's largest AMR company with over 30,000 robots deployed across 40+ countries. Their product portfolio spans goods-to-person shelf-carrying robots (P-Series), sorting robots (S-Series), tote-to-person shuttles (RoboShuttle), pallet-to-person systems (Skycube), and autonomous forklifts. The Geek+ Software Suite provides modular tools for warehouse management, real-time monitoring, and seamless integration with existing WMS.",
            "website": "https://www.geekplus.com",
            "headquarters": "Beijing, China",
            "founded_year": 2015,
            "funding_total_usd": "$500M+",
            "business_model": "Hybrid",
            "revenue_est": "~$400M (2025 est.)",
            "employees": "2000+",
            "notes": "Nearly 50% global market share in goods-to-person AMR solutions. Product lines: P, M, S, RS series.",
        },
        {
            "name": "HAI Robotics",
            "slug": "hai-robotics",
            "country": "China",
            "short_description": "Autonomous Case-handling Mobile Robots (ACRs) for flexible ASRS",
            "description": "HAI Robotics develops Autonomous Case-handling Mobile Robot (ACR) technology for flexible automated storage and retrieval. Their HaiPick systems use ground-based robots that navigate standard racking up to 12 meters high, handling cases, totes, and cartons. The HaiPick Climb system stores up to 45,000 totes in 1,000 m² with throughput up to 4,000 totes/hour. HaiQ software orchestrates the entire system with real-time optimization.",
            "website": "https://www.hairobotics.com",
            "headquarters": "Shenzhen, China",
            "founded_year": 2016,
            "funding_total_usd": "$200M+",
            "business_model": "Hybrid",
            "revenue_est": "~$150M (2025 est.)",
            "employees": "1000+",
            "notes": "1,000+ systems deployed globally. ACR technology bridges gap between AMRs and traditional ASRS.",
        },
        {
            "name": "AutoStore",
            "slug": "autostore",
            "country": "Norway",
            "short_description": "Cube storage ASRS with industry-leading space efficiency",
            "description": "AutoStore is the world's leading cube storage ASRS, with over 1,900 systems installed across 50+ countries. Its modular aluminum grid stacks bins up to 16 bins high, achieving up to 4x storage density vs. manual shelving. Robots (R5, R5+, R5Pro) drive on top of the grid, retrieving bins and delivering them to ergonomic workstations (Ports). The CubeVerse AI platform provides fleet optimization and predictive analytics. Publicly traded on Euronext Oslo (AUTO.OL).",
            "website": "https://www.autostoresystem.com",
            "headquarters": "Nedre Vats, Norway",
            "founded_year": 1996,
            "funding_total_usd": "Public (AUTO.OL)",
            "business_model": "Hybrid",
            "revenue_est": "~$550M (2024)",
            "employees": "1000+",
            "notes": "99.7% uptime across all installations. 10 robots use energy of 1 vacuum cleaner. Public company.",
        },
        {
            "name": "Amazon Robotics",
            "slug": "amazon-robotics",
            "country": "USA",
            "status": "division",
            "short_description": "Internal robotics division of Amazon, 1M+ robots deployed",
            "description": "Amazon Robotics is Amazon's internal robotics division, born from the 2012 acquisition of Kiva Systems. With over 1 million robots deployed across 300+ fulfillment centers worldwide, it operates the largest robotics fleet in the world. Products include Proteus (autonomous mobile robot for go-carts), Sparrow (robotic arm for item picking), Robin and Cardinal (sortation robots), and Sequoia (storage system). The division serves Amazon's fulfillment network exclusively.",
            "website": "https://www.aboutamazon.com/amazon-robotics",
            "headquarters": "North Reading, MA",
            "founded_year": 2012,
            "funding_total_usd": "Division of Amazon ($600B+ revenue)",
            "business_model": "Internal Use Only",
            "revenue_est": "Internal (cost center for Amazon)",
            "employees": "5000+",
            "notes": "1M+ robots deployed. Closed ecosystem — not available for external purchase.",
        },
        {
            "name": "Symbotic",
            "slug": "symbotic",
            "country": "USA",
            "short_description": "End-to-end warehouse automation for major retailers",
            "description": "Symbotic provides end-to-end warehouse automation using AI-powered robots that manage pallet and case-level inventory from receiving to shipping. Their system uses high-speed shuttles and robotic arms to receive, store, retrieve, and ship pallet and case-level inventory. Symbotic went public via SPAC merger in 2022 (NASDAQ: SYM) and has partnerships with Walmart, Albertsons, and other major retailers. In 2025, Symbotic acquired Walmart's internal robotics division.",
            "website": "https://www.symbotic.com",
            "headquarters": "Wilmington, MA",
            "founded_year": 2007,
            "funding_total_usd": "Public (SYM)",
            "business_model": "Hybrid",
            "revenue_est": "~$1.8B (FY2025)",
            "employees": "2000+",
            "notes": "Acquired Walmart's internal robotics arm in 2025. Public company on NASDAQ.",
        },
        {
            "name": "Boston Dynamics",
            "slug": "boston-dynamics",
            "country": "USA",
            "status": "acquired",            "short_description": "Advanced mobile manipulation for warehouse and logistics",
            "description": "Boston Dynamics is renowned for advanced robotics including Spot (quadruped), Atlas (humanoid), and Stretch (warehouse robot). Stretch is a mobile manipulation robot designed for warehouse unloading and case handling, using a custom arm with suction grippers to unload trucks and move boxes. The company was acquired by Hyundai Motor Group in 2021 and continues to push the boundaries of robotic mobility and manipulation.",
            "website": "https://www.bostondynamics.com",
            "headquarters": "Waltham, MA",
            "founded_year": 1992,
            "funding_total_usd": "Acquired by Hyundai ($1.1B)",
            "business_model": "Purchase",
            "revenue_est": "Undisclosed",
            "employees": "1000+",
            "notes": "Stretch robot for warehouse unloading. Acquired by Hyundai in 2021.",
        },
        {
            "name": "GreyOrange",
            "slug": "greyorange",
            "country": "Singapore",
            "short_description": "AI-driven fulfillment platform with AMRs and software",
            "description": "GreyOrange provides AI-driven fulfillment automation using its GreyMatter platform and Ranger series of AMRs. The company's software orchestrates both GreyOrange robots and third-party automation as a unified system. Ranger robots include goods-to-person, person-to-goods, and sortation variants. GreyOrange serves retail, e-commerce, and 3PL customers globally.",
            "website": "https://www.greyorange.com",
            "headquarters": "Atlanta, GA / Singapore",
            "founded_year": 2012,
            "funding_total_usd": "$300M+",
            "business_model": "Hybrid",
            "revenue_est": "~$100M (2025 est.)",
            "employees": "500-1000",
            "notes": "GreyMatter orchestration platform supports multi-vendor fleets.",
        },
        {
            "name": "Exotec",
            "slug": "exotec",
            "country": "France",
            "short_description": "Modular ASRS with Skypod robots for high-throughput fulfillment",
            "description": "Exotec provides modular ASRS solutions using Skypod robots that can climb racks up to 12 meters high to retrieve totes at speeds of 4 m/s. The system combines goods-to-person picking with robot transport for high-throughput fulfillment. Exotec has deployed 350+ systems across 20+ countries for customers like Decathlon, Carrefour, and Uniqlo. The company is headquartered in France and achieved unicorn status in 2022.",
            "website": "https://www.exotec.com",
            "headquarters": "Croix, France",
            "founded_year": 2015,
            "funding_total_usd": "$400M+",
            "business_model": "Hybrid",
            "revenue_est": "~$200M (2025 est.)",
            "employees": "500+",
            "notes": "Unicorn startup (2022). Skypod robot climbs racks at 4 m/s.",
        },
        {
            "name": "Zebra Technologies (Fetch Robotics)",
            "slug": "zebra-fetch",
            "country": "USA",
            "status": "acquired",            "short_description": "AMR fleet for material transport and collaborative picking",
            "description": "Zebra Technologies acquired Fetch Robotics in 2021 to provide autonomous mobile robot (AMR) solutions for warehouses, distribution centers, and manufacturing. Fetch Robotics offers a portfolio of AMRs including CartConnect for collaborative cart transport, and Freight500/Freight1500 for automated pallet and heavy-load transport. All robots are orchestrated by the FetchCore cloud platform and feature dynamic obstacle avoidance with 3D cameras and LiDAR. The fleet supports payloads from 75 kg to 1,500 kg, making it one of the broadest AMR portfolios in the industry.",
            "website": "https://www.zebra.com/us/en/products/robotics.html",
            "headquarters": "San Jose, CA / Lincoln, CA",
            "founded_year": 2014,
            "funding_total_usd": "Acquired by Zebra ($290M)",
            "business_model": "Purchase / RaaS",
            "revenue_est": "Undisclosed (Zebra segment)",
            "employees": "300+",
            "notes": "Acquired by Zebra Technologies in 2021. R15.08 safety standard compliant.",
        },
        {
            "name": "KUKA",
            "slug": "kuka",
            "country": "Germany",
            "status": "acquired",            "short_description": "Industrial robot arms for heavy-duty automation",
            "description": "KUKA is a German global manufacturer of industrial robots and automation solutions, owned by the Chinese Midea Group. The company produces a wide range of industrial robot arms from lightweight collaborative robots to heavy-duty foundry robots with payloads up to 1,500 kg. Key series include KR QUANTEC (mid-range, 120-300 kg), KR FORTEC (heavy-duty, 240-500 kg), KR FORTEC ultra (800 kg), and KR TITAN ultra (up to 1,500 kg). KUKA robots are widely used in automotive, logistics, and general industry for handling, welding, palletizing, and machining operations.",
            "website": "https://www.kuka.com",
            "headquarters": "Augsburg, Germany",
            "founded_year": 1898,
            "funding_total_usd": "Acquired by Midea ($4.9B)",
            "business_model": "Purchase",
            "revenue_est": "~$4.0B (2025)",
            "employees": "15,000+",
            "notes": "Owned by Midea Group (China). KR TITAN ultra reaches 1,500 kg payload.",
        },
        {
            "name": "Mobile Industrial Robots (MiR)",
            "slug": "mir",
            "country": "Denmark",
            "status": "acquired",            "short_description": "Collaborative AMRs for internal transport",
            "description": "MiR (Mobile Industrial Robots) develops collaborative autonomous mobile robots for internal transportation across manufacturing, warehousing, and logistics. Founded in Odense, Denmark, and acquired by Teradyne in 2018, MiR offers a range of AMR platforms from the compact MiR250 (250 kg) to the heavy-duty MiR1350 (1,350 kg). MiR robots use advanced SLAM-based navigation that requires no facility modifications. The robots can be equipped with top modules including pallet lifts, conveyors, and robot arms for a wide variety of material handling applications.",
            "website": "https://www.mobile-industrial-robots.com",
            "headquarters": "Odense, Denmark",
            "founded_year": 2013,
            "funding_total_usd": "Acquired by Teradyne ($285M)",
            "business_model": "Purchase / RaaS",
            "revenue_est": "~$120M (2025 est.)",
            "employees": "500+",
            "notes": "Subsidiary of Teradyne. SLAM navigation, no facility modifications required.",
        },
        {
            "name": "6 River Systems (Ocado)",
            "slug": "6-river-systems",
            "country": "UK",
            "status": "acquired",            "short_description": "Collaborative AMRs for warehouse fulfillment",
            "description": "6 River Systems (now part of Ocado Intelligent Automation) develops collaborative autonomous mobile robots for warehouse fulfillment. Their flagship product Chuck is a configurable AMR that guides associates through picking, putaway, sorting, and replenishment. Chuck holds up to 6 shelves with 200 lbs total payload, using AI-powered pick path optimization to reduce walking by 50% and double to triple pick rates. Founded in 2014, 6 River Systems was acquired by Shopify in 2019 for ~$450M, then acquired by Ocado Group in 2023. The system deploys in as little as 14 weeks with no facility modifications required, paying back in 6-12 months.",
            "website": "https://ocadointelligentautomation.com/systems/chuck-amr",
            "headquarters": "Waltham, MA / London, UK",
            "founded_year": 2014,
            "funding_total_usd": "Acquired by Shopify ($450M) then Ocado",

            "business_model": "Purchase / RaaS",
            "revenue_est": "Undisclosed (Ocado segment)",
            "employees": "300+",
            "notes": "Acquired by Shopify 2019, then Ocado 2023. Part of Ocado Intelligent Automation.",
        },
        {
            "name": "Universal Robots",
            "slug": "universal-robots",
            "country": "Denmark",
            "short_description": "Collaborative robot arms (cobots) for flexible automation",
            "description": "Universal Robots (UR) pioneered collaborative robotics with lightweight, easy-to-program robot arms designed to work alongside humans. Founded in Odense, Denmark and acquired by Teradyne in 2015, UR offers cobots from the compact UR3e for bench-top tasks to the heavy-duty UR20 for palletizing and material handling. UR cobots are widely used in warehouse and logistics automation for picking, packing, palletizing, and machine tending. The UR+ ecosystem provides hundreds of certified end-effectors, vision systems, and accessories. With over 90,000 cobots deployed globally, UR is the market leader in collaborative robotics.",
            "website": "https://www.universal-robots.com",
            "headquarters": "Odense, Denmark",
            "founded_year": 2005,
            "funding_total_usd": "Acquired by Teradyne ($285M)",
            "business_model": "Purchase",
            "revenue_est": "~$350M (2025 est.)",
            "employees": "1,000+",
            "notes": "Subsidiary of Teradyne. Over 90,000 cobots deployed. UR+ ecosystem of 400+ accessories.",
        },
        {
            "name": "FANUC",
            "slug": "fanuc",
            "country": "Japan",
            "short_description": "Industrial robots and CNCs for manufacturing and logistics",
            "description": "FANUC is a Japanese multinational manufacturer of industrial robots, CNC systems, and factory automation. Founded in 1956, FANUC is one of the world's largest robotics companies with over 1 million robots installed globally. Their product range includes the CRX collaborative series (5-25 kg payload), M-10/M-20 series for handling and picking, and M-710 series for palletizing (50-70 kg payload). FANUC robots are widely deployed in warehouse automation for case picking, palletizing, depalletizing, and sorting. The company is known for its high reliability (mean time between failures of 50,000+ hours) and is headquartered at the base of Mt. Fuji in Japan.",
            "website": "https://www.fanuc.com",
            "headquarters": "Oshino, Yamanashi, Japan",
            "founded_year": 1956,
            "funding_total_usd": "Public (FANUC.TYO)",
            "business_model": "Purchase",
            "revenue_est": "~$6.0B (FY2025)",
            "employees": "8,000+",
            "notes": "Publicly traded on Tokyo Stock Exchange. Over 1M robots installed. MTBF of 50,000+ hours.",
        },
        {
            "name": "ABB Robotics",
            "slug": "abb-robotics",
            "country": "Switzerland",
            "short_description": "Industrial robots and automation solutions for logistics",
            "description": "ABB is a Swiss-Swedish multinational leader in industrial automation and robotics, with over 500,000 robots installed globally. ABB's robotics division offers a comprehensive portfolio including the IRB 1200 (handling), IRB 1300 (flexible picking), IRB 2600 (mid-range), and the FlexPicker delta robot series for high-speed picking in logistics. The RobotStudio simulation platform enables offline programming and digital twin optimization. ABB robots are used extensively in warehouse and logistics automation for palletizing, depalletizing, case picking, and parcel sorting. ABB's Machine Tending and Logistics application groups focus specifically on supply chain automation.",
            "website": "https://www.abb.com/robotics",
            "headquarters": "Zurich, Switzerland",
            "founded_year": 1988,
            "funding_total_usd": "Public (ABB.NYSE)",
            "business_model": "Purchase",
            "revenue_est": "~$4.0B (Robotics, 2025)",
            "employees": "10,000+ (Robotics division)",
            "notes": "Public company on NYSE. Over 500K robots installed. RobotStudio digital twin platform.",
        },
        {
            "name": "Magazino",
            "slug": "magazino",
            "country": "Germany",
            "short_description": "Perceptive autonomous robots for e-commerce fulfillment",
            "description": "Magazino develops perceptive autonomous mobile robots for intralogistics, specializing in e-commerce fulfillment and apparel handling. Their flagship TORU (Tote-Operating Robotic Unit) robot can autonomously navigate warehouse aisles and pick individual items from shelves using a 3D vision system. Unlike traditional cubby-hole ASRS, TORU can handle a wide variety of item shapes and sizes without fixed racking. Magazino's SOTO robot handles shoe box picking for fashion logistics. Founded in 2014 as a spin-off from the Technical University of Munich (TUM), Magazino has deployed robots across Europe for customers in fashion, media, and e-commerce.",
            "website": "https://www.magazino.eu",
            "headquarters": "Munich, Germany",
            "founded_year": 2014,
            "funding_total_usd": "$50M+",
            "business_model": "Purchase / RaaS",
            "revenue_est": "Undisclosed (private)",
            "employees": "150+",
            "notes": "TUM spin-off. TORU robot picks individual items from shelves. SOTO for shoe boxes.",
        },
        # Medical / Surgical Robotics
        {
            "name": "Intuitive Surgical",
            "slug": "intuitive-surgical",
            "country": "USA",
            "short_description": "Pioneer in robotic-assisted surgery with the da Vinci system",
            "description": "Intuitive Surgical is the global leader in robotic-assisted minimally invasive surgery. Their da Vinci surgical systems combine advanced robotics, 3D HD visualization, and intuitive instrument control to enable surgeons to perform complex procedures through small incisions. With over 9,000 da Vinci systems installed worldwide, Intuitive has performed millions of surgical procedures across urology, gynecology, thoracic, and general surgery. The Ion endoluminal system extends robotic capabilities to lung biopsies. The company continues to invest in AI, data analytics, and next-generation platforms to expand the reach of robotic surgery.",
            "website": "https://www.intuitive.com",
            "headquarters": "Sunnyvale, CA",
            "founded_year": 1995,
            "funding_total_usd": "Public (ISRG)",
            "business_model": "Purchase",
            "revenue_est": "~$8.5B (2025)",
            "employees": "12,000+",
            "engineering_pct": "30%",
            "engineering_employees": "3,600+",
            "notes": "da Vinci systems: Xi, X, SP. Ion endoluminal system. Over 9,000 systems installed globally.",
            "status": "active",
        },
        {
            "name": "Medtronic",
            "slug": "medtronic",
            "country": "Ireland",
            "short_description": "Global medtech leader with Hugo RAS surgical robotics platform",
            "description": "Medtronic is the world's largest medical technology company, with a significant presence in surgical robotics. The Hugo RAS (Robotic-Assisted Surgery) system is a modular, flexible surgical robotics platform designed for a wide range of soft tissue procedures. Medtronic also acquired Mazor Robotics in 2018 for $1.64B, adding the Mazor X Stealth Edition for spine surgery. The StealthStation S8 surgical navigation system provides real-time tracking during neurosurgery and ENT procedures. Medtronic's surgical robotics portfolio is complemented by advanced energy platforms, stapling, and monitoring technologies. The company is headquartered in Dublin, Ireland with operational headquarters in Minneapolis, MN.",
            "website": "https://www.medtronic.com",
            "headquarters": "Dublin, Ireland / Minneapolis, MN",
            "founded_year": 1949,
            "funding_total_usd": "Public (MDT)",
            "business_model": "Purchase",
            "revenue_est": "~$33B (FY2025)",
            "employees": "95,000+",
            "engineering_pct": "12%",
            "engineering_employees": "11,400+",
            "notes": "Hugo RAS system, Mazor X Stealth Edition, StealthStation S8. Acquired Mazor Robotics (2018, $1.64B).",
            "status": "active",
        },
        {
            "name": "Stryker",
            "slug": "stryker",
            "country": "USA",
            "short_description": "Medical technology leader with Mako robotic-arm assisted surgery",
            "description": "Stryker is a global medical technology company offering innovative products and services in MedSurg, Neurotechnology, Orthopaedics, and Spine. The Mako SmartRobotics system is a haptic-guided robotic arm platform for orthopedic surgery, including total hip arthroplasty, total knee arthroplasty, and partial knee resurfacing. Mako combines 3D CT-based planning with proprietary AccuStop haptic technology, enabling surgeons to execute bone resections with sub-millimeter accuracy. Stryker acquired Mako Surgical Corp in 2013 for $1.65B. Over 2,000 Mako systems are installed globally, with more than 1 million Mako procedures performed.",
            "website": "https://www.stryker.com",
            "headquarters": "Kalamazoo, MI",
            "founded_year": 1941,
            "funding_total_usd": "Public (SYK)",
            "business_model": "Purchase",
            "revenue_est": "~$22B (2025)",
            "employees": "51,000+",
            "engineering_pct": "15%",
            "engineering_employees": "7,650+",
            "notes": "Mako SmartRobotics system. Acquired Mako Surgical Corp (2013, $1.65B). 2,000+ Mako systems installed.",
            "status": "active",
        },
        {
            "name": "Zimmer Biomet",
            "slug": "zimmer-biomet",
            "country": "USA",
            "short_description": "Musculoskeletal healthcare with Rosa robotic surgery platform",
            "description": "Zimmer Biomet is a global leader in musculoskeletal healthcare, offering orthopaedic products and the Rosa Robotics platform for knee, hip, and spine surgery. Rosa Knee uses real-time data and intra-articular sensing to assist surgeons in performing total knee arthroplasty with personalized implant positioning. Rosa Hip enables robotic-assisted total hip replacement with CT-based planning and precise acetabular cup placement. Rosa One Spine provides robotic navigation for pedicle screw placement and spinal decompression procedures. The company's robotic portfolio is integrated with its comprehensive implant systems, surgical instruments, and digital health solutions.",
            "website": "https://www.zimmerbiomet.com",
            "headquarters": "Warsaw, IN",
            "founded_year": 1927,
            "funding_total_usd": "Public (ZBH)",
            "business_model": "Purchase",
            "revenue_est": "~$7.5B (2025)",
            "employees": "19,000+",
            "engineering_pct": "15%",
            "engineering_employees": "2,850+",
            "notes": "Rosa Knee, Rosa Hip, Rosa One Spine robotic platforms.",
            "status": "active",
        },
        {
            "name": "Globus Medical",
            "slug": "globus-medical",
            "country": "USA",
            "short_description": "Musculoskeletal solutions with ExcelsiusGPS robotic navigation",
            "description": "Globus Medical is a leading musculoskeletal solutions company focused on providing innovative surgical solutions for spine surgery. The ExcelsiusGPS is a robotic navigation platform for spine surgery that integrates real-time intraoperative imaging with surgical planning software. Excelsius3D combines navigation with 3D intraoperative imaging in a single system. The platform enables precise placement of pedicle screws and other spinal implants. Globus Medical merged with NuVasive in 2023 to create a comprehensive portfolio spanning spine, orthopedics, and enabling technologies.",
            "website": "https://www.globusmedical.com",
            "headquarters": "Audubon, PA",
            "founded_year": 2003,
            "funding_total_usd": "Public (GMED)",
            "business_model": "Purchase",
            "revenue_est": "~$2.5B (2025)",
            "employees": "3,500+",
            "engineering_pct": "20%",
            "engineering_employees": "700+",
            "notes": "ExcelsiusGPS and Excelsius3D robotic navigation. Merged with NuVasive in 2023.",
            "status": "active",
        },
        {
            "name": "Smith+Nephew",
            "slug": "smith-nephew",
            "country": "UK",
            "short_description": "Medical technology firm with NAVIO and CORI robotics for orthopedics",
            "description": "Smith+Nephew is a global medical technology company specializing in orthopaedic reconstruction, wound management, and sports medicine. Their NAVIO Surgical System is a handheld robotic system for partial and total knee arthroplasty that uses CT-free mapping to create a 3D model of the patient's knee anatomy. The CORI Surgical System is a next-generation handheld robotics platform that uses intraoperative 3D mapping without preoperative CT imaging. CORI guides bone resections and provides real-time gap balancing data for precise implant placement in knee and hip procedures.",
            "website": "https://www.smith-nephew.com",
            "headquarters": "London, UK",
            "founded_year": 1856,
            "funding_total_usd": "Public (SN.L)",
            "business_model": "Purchase",
            "revenue_est": "~$5.5B (2025)",
            "employees": "18,000+",
            "engineering_pct": "12%",
            "engineering_employees": "2,160+",
            "notes": "NAVIO and CORI handheld robotic systems for orthopedics. CT-free intraoperative mapping.",
            "status": "active",
        },
        {
            "name": "CMR Surgical",
            "slug": "cmr-surgical",
            "country": "UK",
            "short_description": "Next-generation surgical robotics with the Versius system",
            "description": "CMR Surgical is a UK-based medical devices company developing the Versius Surgical System, a next-generation robotic platform for laparoscopic surgery. Versius features a modular, portable design with independent robotic arms that can be positioned around the patient bed. Each arm provides 7 degrees of freedom and 360-degree articulation. The open console design allows surgeons to maintain direct patient communication. Versius supports a wide range of general surgery, gynecology, and urology procedures. CMR has raised over $1B in funding and is one of the best-funded private surgical robotics companies globally.",
            "website": "https://www.cmrsurgical.com",
            "headquarters": "Cambridge, UK",
            "founded_year": 2014,
            "funding_total_usd": "$1B+",
            "business_model": "Purchase",
            "revenue_est": "Undisclosed (private)",
            "employees": "800+",
            "engineering_pct": "50%",
            "engineering_employees": "400+",
            "notes": "Versius Surgical System. Modular portable design. $1B+ raised.",
            "status": "active",
        },
        {
            "name": "Asensus Surgical",
            "slug": "asensus-surgical",
            "country": "USA",
            "short_description": "Digital surgery platform with Senhance and Luna robotic systems",
            "description": "Asensus Surgical (formerly TransEnterix) is a medical robotics company developing the Senhance Surgical System and next-generation Luna platform. Senhance is a multi-port robotic system that uses eye-tracking camera control, haptic feedback, and 3D visualization to provide surgeons with intuitive instrument control. The system features reusable instruments to reduce per-procedure costs. Luna is the company's next-generation platform designed for broader surgical applications with a smaller footprint and simplified setup. Asensus focuses on making robotic surgery more accessible and affordable.",
            "website": "https://www.asensus.com",
            "headquarters": "Research Triangle Park, NC",
            "founded_year": 2006,
            "funding_total_usd": "Public (ASXC)",
            "business_model": "Purchase",
            "revenue_est": "~$10M (2025)",
            "employees": "150+",
            "engineering_pct": "40%",
            "engineering_employees": "60+",
            "notes": "Senhance Surgical System, Luna platform (in development). Haptic feedback with reusable instruments.",
            "status": "active",
        },
        {
            "name": "Stereotaxis",
            "slug": "stereotaxis",
            "country": "USA",
            "short_description": "Robotic navigation for cardiac electrophysiology procedures",
            "description": "Stereotaxis is a global leader in robotic technologies for cardiac electrophysiology. The Niobe and Genesis RMN (Remote Magnetic Navigation) systems use computer-controlled external magnets to precisely guide magnetic catheters through the heart and vasculature. The Genesis system is the next-generation platform with enhanced magnet positioning, faster field vector changes, and improved integration with 3D mapping systems. Stereotaxis' robotic platform enables precise, stable catheter control for ablation of complex arrhythmias including atrial fibrillation, atrial flutter, and ventricular tachycardia. Over 100,000 procedures have been performed using Stereotaxis systems worldwide.",
            "website": "https://www.stereotaxis.com",
            "headquarters": "St. Louis, MO",
            "founded_year": 1990,
            "funding_total_usd": "Public (STXS)",
            "business_model": "Purchase",
            "revenue_est": "~$30M (2025)",
            "employees": "100+",
            "engineering_pct": "30%",
            "engineering_employees": "30+",
            "notes": "Genesis RMN and Niobe ES robotic magnetic navigation systems for cardiac electrophysiology.",
            "status": "active",
        },
        # --- Educational Institutions ---
        {
            "name": "Massachusetts Institute of Technology",
            "slug": "mit",
            "company_type": "educational",
            "country": "USA",
            "short_description": "Leading research university and robotics innovation hub",
            "description": "The Massachusetts Institute of Technology (MIT) is a private research university in Cambridge, Massachusetts, consistently ranked among the world's top universities. MIT's Computer Science and Artificial Intelligence Laboratory (CSAIL) and the Department of Mechanical Engineering have produced numerous robotics innovations and spin-offs, including Boston Dynamics and iRobot. MIT alumni have founded many leading robotics companies.",
            "website": "https://www.mit.edu",
            "headquarters": "Cambridge, MA",
            "founded_year": 1861,
        },
        {
            "name": "Technical University of Munich",
            "slug": "technical-university-of-munich",
            "company_type": "educational",
            "country": "Germany",
            "short_description": "German research university with strong robotics programs",
            "description": "The Technical University of Munich (TUM) is one of Europe's leading research universities, with world-class programs in robotics, AI, and mechanical engineering. TUM has produced numerous robotics spin-offs, including Magazino (autonomous warehouse robots) and has strong industry partnerships with German automotive and industrial automation companies.",
            "website": "https://www.tum.de",
            "headquarters": "Munich, Germany",
            "founded_year": 1868,
        },
        # --- Parent Companies ---
        {
            "name": "Teradyne",
            "slug": "teradyne",
            "company_type": "parent",
            "country": "USA",
            "short_description": "Industrial automation and robotics parent company",
            "description": "Teradyne is a leading supplier of automated test equipment and industrial automation. Through its Industrial Automation Group, Teradyne owns Universal Robots (collaborative robots) and Mobile Industrial Robots / MiR (autonomous mobile robots). The company acquired Universal Robots in 2015 and MiR in 2018 for a combined ~$570M.",
            "website": "https://www.teradyne.com",
            "headquarters": "North Reading, MA",
            "founded_year": 1960,
            "revenue_est": "~$2.7B (2025)",
            "employees": "6,500+",
            "notes": "Parent company of Universal Robots and Mobile Industrial Robots (MiR).",
        },
        {
            "name": "Midea Group",
            "slug": "midea-group",
            "company_type": "parent",
            "country": "China",
            "short_description": "Chinese appliance manufacturer and parent of KUKA",
            "description": "Midea Group is a Chinese electrical appliance manufacturer headquartered in Foshan, Guangdong. In 2017, Midea acquired KUKA, the German industrial robot manufacturer, for approximately $4.9 billion. The acquisition gave Midea access to advanced industrial robotics technology for its manufacturing operations and positioned the company as a global player in factory automation.",
            "website": "https://www.midea.com",
            "headquarters": "Foshan, Guangdong, China",
            "founded_year": 1968,
            "revenue_est": "~$50B+ (2025)",
            "employees": "190,000+",
            "notes": "Parent company of KUKA Robotics. Acquired KUKA in 2017 for $4.9B.",
        },
        {
            "name": "Hyundai Motor Group",
            "slug": "hyundai-motor-group",
            "company_type": "parent",
            "country": "South Korea",
            "short_description": "South Korean automotive conglomerate and parent of Boston Dynamics",
            "description": "Hyundai Motor Group is a South Korean automotive conglomerate that acquired Boston Dynamics in 2021 for approximately $1.1 billion. The acquisition was driven by Hyundai's vision for robotics in future mobility, logistics, and manufacturing. Boston Dynamics operates as an independent subsidiary within Hyundai Motor Group, continuing to develop its Spot, Atlas, and Stretch robots.",
            "website": "https://www.hyundaimotorgroup.com",
            "headquarters": "Seoul, South Korea",
            "founded_year": 2000,
            "revenue_est": "~$130B+ (2025)",
            "employees": "280,000+",
            "notes": "Parent company of Boston Dynamics. Acquired in 2021 for $1.1B.",
        },
        {
            "name": "Ocado Group",
            "slug": "ocado-group",
            "company_type": "parent",
            "country": "UK",
            "short_description": "Online grocery retailer and technology provider",
            "description": "Ocado Group is a British online supermarket and technology company. Through Ocado Intelligent Automation, the company provides warehouse automation technology including the Chuck AMR system (originally developed by 6 River Systems). Ocado acquired 6 River Systems from Shopify in 2023 after Shopify had acquired it in 2019 for ~$450M.",
            "website": "https://www.ocadogroup.com",
            "headquarters": "Hatfield, UK",
            "founded_year": 2000,
            "revenue_est": "~$4.0B (2025)",
            "employees": "20,000+",
            "notes": "Parent company of 6 River Systems (now part of Ocado Intelligent Automation).",
        },
        {
            "name": "Zebra Technologies",
            "slug": "zebra-technologies",
            "company_type": "parent",
            "country": "USA",
            "short_description": "Enterprise asset intelligence and robotics parent",
            "description": "Zebra Technologies is an American mobile computing and data capture company that provides enterprise asset intelligence solutions. In 2021, Zebra acquired Fetch Robotics for $290M to add autonomous mobile robots (AMRs) to its portfolio of warehouse automation solutions. Fetch's AMR line, including CartConnect, Freight500, and Freight1500, operates as Zebra Robotics.",
            "website": "https://www.zebra.com",
            "headquarters": "Lincolnshire, IL",
            "founded_year": 1969,
            "revenue_est": "~$5.0B (2025)",
            "employees": "9,800+",
            "notes": "Parent company of Fetch Robotics (acquired 2021 for $290M).",
        },
        {
            "name": "Shopify",
            "slug": "shopify",
            "company_type": "parent",
            "country": "Canada",
            "short_description": "E-commerce platform that previously owned 6 River Systems",
            "description": "Shopify is a Canadian multinational e-commerce company. In 2019, Shopify acquired 6 River Systems for approximately $450M to add warehouse automation capabilities to its commerce platform. Shopify later sold 6 River Systems to Ocado Group in 2023 as part of a strategic refocus on its core e-commerce business.",
            "website": "https://www.shopify.com",
            "headquarters": "Ottawa, Ontario, Canada",
            "founded_year": 2004,
            "revenue_est": "~$8.0B (2025)",
            "employees": "8,300+",
            "notes": "Previously owned 6 River Systems (2019-2023), then sold to Ocado Group.",
        },
        {
            "name": "Amazon",
            "slug": "amazon",
            "company_type": "parent",
            "country": "USA",
            "short_description": "Global e-commerce and cloud computing giant",
            "description": "Amazon is a global technology company focused on e-commerce, cloud computing, digital streaming, and artificial intelligence. Amazon Robotics (formerly Kiva Systems, acquired in 2012) operates as Amazon's internal robotics division, developing drive units, robotic arms, and autonomous mobile robots exclusively for Amazon's fulfillment network. Amazon has deployed over 1M robots across 300+ fulfillment centers worldwide.",
            "website": "https://www.aboutamazon.com",
            "headquarters": "Seattle, WA",
            "founded_year": 1994,
            "revenue_est": "~$650B+ (2025)",
            "employees": "1,500,000+",
            "notes": "Parent of Amazon Robotics division. Acquired Kiva Systems in 2012.",
        },
        {
            "name": "Kiva Systems",
            "slug": "kiva-systems",
            "company_type": "corporation",
            "country": "USA",
            "short_description": "Original warehouse robotics company acquired by Amazon, became Amazon Robotics",
            "description": "Kiva Systems was a warehouse robotics company founded in 2003 by Mick Mountz, Peter Wurman, and Raffaello D'Andrea. Kiva developed autonomous mobile robots (the Kiva Drive Unit) that transported shelving pods to human pickers, revolutionizing goods-to-person fulfillment. Amazon acquired Kiva Systems in 2012 for $775M, shutting down external sales and renaming it Amazon Robotics. The Kiva pod-based system remains the foundation of Amazon's fulfillment network, with over 1M robots deployed today.",
            "website": "https://www.kivasystems.com",
            "headquarters": "North Reading, MA",
            "founded_year": 2003,
            "funding_total_usd": "$85M (pre-acquisition)",
            "business_model": "Purchase",
            "revenue_est": "~$80M (2011 est.)",
            "employees": "500+ (at acquisition)",
            "notes": "Acquired by Amazon in 2012 for $775M. Co-founders from MIT. Became Amazon Robotics.",
            "status": "acquired",
        },
        # --- Venture Capital / Investor ---
        {
            "name": "Sequoia Capital",
            "slug": "sequoia-capital",
            "company_type": "investor",
            "country": "USA",
            "short_description": "Venture capital firm investing in technology companies",
            "description": "Sequoia Capital is one of the world's most prestigious venture capital firms, with a history of investing in technology companies including Apple, Google, Oracle, and NVIDIA. Sequoia Capital China has invested in Geek+, the world's largest AMR company. The firm is known for its early-stage investments in transformative technology companies.",
            "website": "https://www.sequoiacap.com",
            "headquarters": "Menlo Park, CA",
            "founded_year": 1972,
            "notes": "Investor in Geek+ (through Sequoia Capital China).",
        },
        {
            "name": "SoftBank Group",
            "slug": "softbank-group",
            "company_type": "investor",
            "country": "Japan",
            "short_description": "Japanese conglomerate with Vision Fund technology investments",
            "description": "SoftBank Group is a Japanese multinational conglomerate holding company, with the SoftBank Vision Fund being one of the world's largest technology-focused investment funds. SoftBank has invested in numerous robotics and automation companies through its Vision Fund, including AutoStore, and has been a significant force in robotics industry funding.",
            "website": "https://www.softbank.com",
            "headquarters": "Tokyo, Japan",
            "founded_year": 1981,
            "revenue_est": "~$50B+ (2025)",
            "employees": "65,000+",
            "notes": "Investor in AutoStore and other robotics companies through Vision Fund.",
        },
        {
            "name": "Andreessen Horowitz",
            "slug": "a16z",
            "company_type": "investor",
            "country": "USA",
            "short_description": "Silicon Valley venture capital firm",
            "description": "Andreessen Horowitz (a16z) is a leading American venture capital firm based in Silicon Valley. The firm invests across all stages of technology companies, including enterprise, consumer, biotech, fintech, and crypto. a16z has been active in robotics and automation investments, backing companies working on AI-powered robotics, warehouse automation, and surgical robotics.",
            "website": "https://a16z.com",
            "headquarters": "Menlo Park, CA",
            "founded_year": 2009,
            "notes": "Active investor in AI, robotics, and automation startups.",
        },
        # --- Chinese Robotics Companies ---
        {
            "name": "Pudu Robotics",
            "slug": "pudu-robotics",
            "country": "China",
            "short_description": "Global leader in commercial service robots for delivery, cleaning, and industrial logistics",
            "description": "Pudu Robotics is a global leader in commercial service robotics, dedicated to the design, R&D, production, and sales of service robots. Built on three core technologies—mobility, manipulation, and AI—Pudu has pioneered an industry-first 'One Brain, Multiple Embodiments' architecture and offers product lines spanning service delivery, commercial cleaning, industrial delivery, and embodied AI. The company has shipped over 120,000 units globally across more than 80 countries.",
            "website": "https://www.pudurobotics.com",
            "headquarters": "Shenzhen, China",
            "founded_year": 2016,
            "funding_total_usd": "$342M",
            "business_model": "Hybrid",
            "revenue_est": "Undisclosed",
            "employees": "~500",
        },
        {
            "name": "Quicktron Robotics",
            "slug": "quicktron",
            "country": "China",
            "short_description": "Leading Chinese AMR provider for intelligent warehousing and logistics automation",
            "description": "Quicktron Intelligent Technology Co., Ltd. is a high-tech company specializing in intelligent warehousing robots and automated logistics solutions. The company provides various types of AMRs and backstage operating systems, deploying over 35,000 robotic units worldwide. Quicktron serves industries such as e-commerce, manufacturing, retail, and third-party logistics across more than 30 countries.",
            "website": "https://www.quicktron.com",
            "headquarters": "Shanghai, China",
            "founded_year": 2014,
            "funding_total_usd": ">$150M",
            "business_model": "Purchase",
            "revenue_est": "Undisclosed",
            "employees": "750",
        },
        {
            "name": "MEGVII Robotics",
            "slug": "megvii-robotics",
            "country": "China",
            "short_description": "AI company delivering intelligent warehousing and logistics automation solutions",
            "description": "Megvii Technology (Face++) is an AI-powered technology company that entered smart logistics through its wholly-owned subsidiary Megvii Robotics. The company leverages its proprietary Brain++ AI platform and Hetu operating system to provide intelligent warehousing solutions, including AS/RS systems, AMRs, pallet shuttles, and AI-powered picking systems.",
            "website": "https://en-robotics.megvii.com",
            "headquarters": "Beijing, China",
            "founded_year": 2011,
            "funding_total_usd": "$1.98B",
            "business_model": "Purchase",
            "revenue_est": "Undisclosed",
            "employees": "400+ (logistics division)",
        },
        {
            "name": "Dobot Robotics",
            "slug": "dobot",
            "country": "China",
            "short_description": "Leading collaborative robot manufacturer with full-stack robotics technology",
            "description": "Dobot Robotics is a leading collaborative robot manufacturer specializing in desktop-grade and industrial robotic arms. With over 100,000 cobots deployed across 100+ countries, Dobot offers a payload product matrix from 0.25kg to 30kg. The company went public on the Hong Kong Stock Exchange in December 2024 (SEHK: 2432) and has evolved into a multimodal embodied AI platform.",
            "website": "https://www.dobot-robots.com",
            "headquarters": "Shenzhen, China",
            "founded_year": 2015,
            "funding_total_usd": "$78.39M",
            "business_model": "Purchase",
            "revenue_est": "Undisclosed",
            "employees": "~500",
        },
        {
            "name": "Siasun Robotics",
            "slug": "siasun",
            "country": "China",
            "short_description": "China's largest state-backed robotics manufacturer covering industrial, mobile, and collaborative robots",
            "description": "Siasun Robot & Automation Co., Ltd. is one of the largest robotics manufacturers in China, affiliated with the Chinese Academy of Sciences. The company produces industrial robots, mobile robots, special robots, and collaborative robots with independent intellectual property rights. Siasun has written more than 100 industry firsts in Chinese robotics history and exports to over 40 countries.",
            "website": "https://en.siasun.com",
            "headquarters": "Shenyang, China",
            "founded_year": 2000,
            "funding_total_usd": "Public (SZSE: 300024)",
            "business_model": "Purchase",
            "revenue_est": "~$1.5B (2024)",
            "employees": "4,513",
        },
        {
            "name": "UBTECH Robotics",
            "slug": "ubtech",
            "country": "China",
            "short_description": "World's first publicly listed humanoid robot company with full-stack humanoid robotics technology",
            "description": "UBTECH Robotics is a leading humanoid robot company and the first humanoid robotics company listed on the Hong Kong Stock Exchange (SEHK: 9880). With a full-stack humanoid robotics technology platform including ROSA 2.0, high-performance servo actuators, and AI integration, UBTECH develops humanoid robots for industrial manufacturing, commercial services, and household companionship. The company holds over 2,790 robotic and AI-related patents.",
            "website": "https://www.ubtrobot.com",
            "headquarters": "Shenzhen, China",
            "founded_year": 2012,
            "funding_total_usd": "~$6.78B (market cap)",
            "business_model": "Hybrid",
            "revenue_est": "$162M (2024)",
            "employees": "2,550",
        },
        {
            "name": "Unitree Robotics",
            "slug": "unitree",
            "country": "China",
            "short_description": "Global leader in legged robotics with quadrupeds and humanoids at competitive prices",
            "description": "Unitree Robotics is a high-performance legged and humanoid robotics company focusing on R&D, production, and sales of quadrupeds, humanoids, and robotic arms. The company fully self-develops core components including motors, reducers, controllers, and LiDAR. Unitree has achieved global technological leadership in quadruped robots and set a world speed record of 3.3m/s with its H1 humanoid.",
            "website": "https://www.unitree.com",
            "headquarters": "Hangzhou, China",
            "founded_year": 2016,
            "funding_total_usd": "$252M",
            "business_model": "Purchase",
            "revenue_est": "Undisclosed",
            "employees": "~1,000",
        },
        {
            "name": "AUBO Robotics",
            "slug": "aubo",
            "country": "China",
            "short_description": "Chinese collaborative robot maker with open-architecture cobots for industrial automation",
            "description": "AUBO Robotics is a national high-tech enterprise specializing in the R&D, production, and sales of collaborative robots. The company offers a payload range from 3kg to 35kg with open SDK supporting C/C++/C#/Lua/Python and ROS. AUBO cobots serve sectors including automotive, precision manufacturing, and smart factory integration across 50+ countries.",
            "website": "https://www.aubo-cobot.com",
            "headquarters": "Beijing, China",
            "founded_year": 2015,
            "funding_total_usd": "$18.6M",
            "business_model": "Purchase",
            "revenue_est": "Undisclosed",
            "employees": "250-500",
        },
        {
            "name": "Gaussian Robotics",
            "slug": "gaussian-robotics",
            "country": "China",
            "short_description": "World's leading autonomous cleaning robot company with comprehensive floor cleaning portfolio",
            "description": "Gaussian Robotics (Gausium) is a world-leading provider of autonomous cleaning solutions and one of the earliest companies globally engaged in the R&D of autonomous mobile technology. The company offers the most comprehensive floor cleaning robot portfolio covering scrubbing, sweeping, vacuuming, dust mopping, sanitizing, and crystallizing. With over 200 million kilometers of cleaning services provided across 40+ countries, Gausium leads the commercial cleaning robot market.",
            "website": "https://gausium.com",
            "headquarters": "Shanghai, China",
            "founded_year": 2013,
            "funding_total_usd": "$361.53M",
            "business_model": "Hybrid",
            "revenue_est": "Undisclosed",
            "employees": "~500",
        },
        {
            "name": "Estun Automation",
            "slug": "estun-automation",
            "country": "China",
            "short_description": "China's largest domestic industrial robot manufacturer with full automation supply chain",
            "description": "Estun Automation is China's leading industrial robot manufacturer and the top domestic enterprise in industrial robot shipments for many consecutive years. The company's business spans the full automation chain from core components and motion control systems to industrial robots and intelligent manufacturing systems. Estun went public on the Shenzhen Stock Exchange in 2015 and completed a Hong Kong secondary listing in March 2026.",
            "website": "https://www.estun.com",
            "headquarters": "Nanjing, China",
            "founded_year": 1993,
            "funding_total_usd": "Public (SZSE: 002747, SEHK: 2715)",
            "business_model": "Purchase",
            "revenue_est": "~$600M (2024)",
            "employees": "3,743",
        },
    ]

    for c in companies:
        conn.execute("""INSERT INTO companies (name, slug, short_description, description, website, headquarters, country,
                    founded_year, funding_total_usd, business_model, revenue_est, employees, logo_url, notes, status, company_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (c["name"], c["slug"], c.get("short_description"), c.get("description"),
                  c.get("website"), c.get("headquarters"), c.get("country", ""), c.get("founded_year"),
                  c.get("funding_total_usd") or None, c.get("business_model") or None, c.get("revenue_est") or None,
                  c.get("employees") or None, None, c.get("notes") or None, c.get("status", "active"),
                  c.get("company_type", "corporation")))

    engineering_updates = {
        "pickle-robotics": ("60%", "80-120"),
        "locus-robotics": ("40%", "200-400"),
        "geekplus": ("45%", "900+"),
        "hai-robotics": ("40%", "400+"),
        "autostore": ("25%", "250+"),
        "amazon-robotics": ("50%", "2500+"),
        "symbotic": ("35%", "700+"),
        "boston-dynamics": ("60%", "600+"),
        "pudu-robotics": ("50%", "250+"),
        "quicktron": ("45%", "340+"),
        "megvii-robotics": ("50%", "200+"),
        "dobot": ("40%", "200+"),
        "siasun": ("30%", "1354+"),
        "ubtech": ("55%", "1403+"),
        "unitree": ("60%", "600+"),
        "aubo": ("40%", "100+"),
        "gaussian-robotics": ("45%", "225+"),
        "estun-automation": ("20%", "749+"),
        "greyorange": ("40%", "200-400"),
        "exotec": ("45%", "225+"),
        "zebra-fetch": ("40%", "120+"),
        "kuka": ("25%", "3750+"),
        "mir": ("40%", "200+"),
        "6-river-systems": ("45%", "135+"),
        "universal-robots": ("35%", "350+"),
        "fanuc": ("30%", "2400+"),
        "abb-robotics": ("30%", "3000+"),
        "magazino": ("55%", "80+"),
        "intuitive-surgical": ("30%", "3600+"),
        "medtronic": ("12%", "11400+"),
        "stryker": ("15%", "7650+"),
        "zimmer-biomet": ("15%", "2850+"),
        "globus-medical": ("20%", "700+"),
        "smith-nephew": ("12%", "2160+"),
        "cmr-surgical": ("50%", "400+"),
        "asensus-surgical": ("40%", "60+"),
        "stereotaxis": ("30%", "30+"),
    }
    for slug, (pct, emp_count) in engineering_updates.items():
        conn.execute("UPDATE companies SET engineering_pct=?, engineering_employees=? WHERE slug=?", 
                     (pct, emp_count, slug))

    products_data = [
        # Pickle
        {
            "company_slug": "pickle-robotics",
            "name": "Pickle Truck Unloading Robot",
            "slug": "pickle-truck-unloader",
            "description": "Autonomous mobile robot with KUKA arm for unloading trailers and shipping containers. Handles packages from 6x6x6 inches up to 24x24x32 inches weighing up to 50 lbs. Achieves 400-1,500 picks per hour with minimal supervision.",
            "category": "Mobile Manipulation",
            "subcategory": "Truck Unloading",
            "product_url": "https://www.picklerobot.com/products",
            "image_url": "https://cdn.prod.website-files.com/68c45a2873ee1a15a77f7db1/6908d9106f6e3f4fe937c285_opengraph_pr.jpg",
            "release_year": 2020,
            "specs": [
                ("payload_capacity", "50", "lbs"),
                ("payload_capacity_metric", "22.5", "kg"),
                ("max_speed", "1.0", "m/s"),
                ("throughput", "400-1500", "cases/hr"),
                ("deployment_time", "5", "days"),
                ("max_package_size", "24x24x32", "inches"),
                ("min_package_size", "6x6x6", "inches"),
                ("robot_arm", "KUKA", ""),
                ("navigation_type", "Autonomous mobile base", ""),
                ("gripper_type", "Suction", ""),
                ("operating_temp_range", "Warehouse ambient", ""),
                ("power_source", "On-board compute + battery", ""),
                ("wms_integration", "None required", ""),
            ],
            "capabilities": ["Truck Unloading", "Trailer Unloading", "Depalletizing"],
        },
        # Locus Origin
        {
            "company_slug": "locus-robotics",
            "name": "Locus Origin",
            "slug": "locus-origin",
            "description": "Collaborative AMR for high-volume order fulfillment. Robots do the walking while associates focus on picking. Configurable with multi-level shelving, tote arrays, bulk bins, and shipping boxes. Seamless integration with LocusONE platform.",
            "category": "AMR",
            "subcategory": "Collaborative Picking",
            "product_url": "https://locusrobotics.com/locusone/fleet/locus-origin-collaborative-robot",
            "release_year": 2020,
            "specs": [
                ("payload_capacity", "80", "lbs"),
                ("payload_capacity_metric", "36", "kg"),
                ("dimensions", "22.2x20x58", "inches"),
                ("max_speed", "1.8", "m/s"),
                ("battery_life", "14", "hours"),
                ("charge_time", "50", "minutes"),
                ("navigation_type", "LiDAR + cameras", ""),
                ("fleet_size_supported", "500+", "robots"),
                ("interface", "Touchscreen + LED indicators", ""),
                ("certification", "CE Certified", ""),
                ("deployment_time", "48", "hours"),
                ("business_model", "RaaS", ""),
                ("typical_cost", "~$1,500", "/robot/month"),
                ("sensors", "8 sensors and cameras", ""),
            ],
            "capabilities": ["Collaborative Picking", "Person-to-Goods", "Putaway", "Replenishment", "Returns Processing"],
        },
        # Locus Vector
        {
            "company_slug": "locus-robotics",
            "name": "Locus Vector",
            "slug": "locus-vector",
            "description": "Industrial-strength AMR for heavy material handling. Handles case picking, point-to-point transport, and conveyor integration. High payload capacity for moving heavy goods in fulfillment and distribution environments.",
            "category": "AMR",
            "subcategory": "Material Handling",
            "product_url": "https://locusrobotics.com/locusone/fleet/locus-vector-material-handling-robot",
            "release_year": 2019,
            "specs": [
                ("payload_capacity", "600", "lbs"),
                ("payload_capacity_metric", "272", "kg"),
                ("max_speed", "1.5", "m/s"),
                ("battery_life", "8-10", "hours"),
                ("charge_time", "60", "minutes"),
                ("navigation_type", "LiDAR + cameras", ""),
                ("payload_class", "medium-heavy", ""),
                ("deployment_time", "48", "hours"),
                ("business_model", "RaaS", ""),
            ],
            "capabilities": ["Case Picking", "Transport", "Pallet Handling", "Putaway", "Replenishment"],
        },
        # Geek+ P500R
        {
            "company_slug": "geekplus",
            "name": "P500R",
            "slug": "geekplus-p500r",
            "description": "Goods-to-person shelf-carrying robot with 600kg payload capacity. Part of the P-Series modular family designed for warehouse picking automation. Features fast lift time, compact footprint, and rapid charging.",
            "category": "AMR",
            "subcategory": "Goods-to-Person",
            "product_url": "https://www.geekplus.com/technology-detail-page/p-series",
            "image_url": "https://www.geekplus.com/hs-fs/hubfs/Geek+2025/products/p-series/P1200-img.png",
            "release_year": 2020,
            "specs": [
                ("payload_capacity", "600", "kg"),
                ("payload_capacity_imperial", "1320", "lbs"),
                ("max_speed_with_load", "2.0", "m/s"),
                ("max_speed_no_load", "1.6", "m/s"),
                ("dimensions", "950x702x275", "mm"),
                ("weight", "144", "kg"),
                ("rotation_diameter", "950", "mm"),
                ("max_lift_height", "60", "mm"),
                ("lift_time", "4", "seconds"),
                ("max_shelf_size", "880x880", "mm"),
                ("stop_accuracy", "±10", "mm"),
                ("battery_type", "Wide-temp lithium", ""),
                ("charge_time", "10 min for 1.5-2 hrs", "work"),
                ("battery_life_cycles", "3-5", "years"),
            ],
            "capabilities": ["Goods-to-Person", "Automated Storage", "Automated Retrieval"],
        },
        # Geek+ P1200R
        {
            "company_slug": "geekplus",
            "name": "P1200R",
            "slug": "geekplus-p1200r",
            "description": "Heavy-duty goods-to-person robot with 1200kg payload capacity. Designed for large-scale warehouse operations requiring high-capacity shelf transport. Part of the P-Series modular family.",
            "category": "AMR",
            "subcategory": "Goods-to-Person",
            "product_url": "https://www.geekplus.com/technology-detail-page/p-series",
            "release_year": 2022,
            "specs": [
                ("payload_capacity", "1200", "kg"),
                ("payload_capacity_imperial", "2640", "lbs"),
                ("max_speed_with_load", "2.2", "m/s"),
                ("max_speed_no_load", "2.6", "m/s"),
                ("dimensions", "1325x1020x275", "mm"),
                ("weight", "288", "kg"),
                ("rotation_diameter", "1325", "mm"),
                ("max_lift_height", "60", "mm"),
                ("lift_time", "4", "seconds"),
                ("max_shelf_size", "1600x1600", "mm"),
                ("stop_accuracy", "±10", "mm"),
                ("battery_type", "Wide-temp lithium", ""),
                ("charge_time", "10 min for 1.5-2 hrs", "work"),
            ],
            "capabilities": ["Goods-to-Person", "Pallet Handling", "Automated Storage"],
        },
        # Geek+ RS Air (RoboShuttle)
        {
            "company_slug": "geekplus",
            "name": "RS Air (RoboShuttle)",
            "slug": "geekplus-rs-air",
            "description": "Tote-to-person shuttle robot for multi-level storage. Handles totes and containers in high-density racking environments. Designed for rapid tote retrieval and delivery to picking stations.",
            "category": "ASRS",
            "subcategory": "Tote-to-Person",
            "product_url": "https://www.geekplus.com/en",
            "release_year": 2023,
            "specs": [
                ("payload_capacity", "10", "kg"),
                ("max_speed", "4.5", "m/s"),
                ("max_operating_height", "12", "m"),
                ("navigation_type", "QR code + SLAM", ""),
                ("storage_type", "Tote-to-Person", ""),
            ],
            "capabilities": ["Goods-to-Person", "Tote Handling", "Multi-Level Picking", "Automated Storage", "Automated Retrieval"],
        },
        # HAI HaiPick ACR
        {
            "company_slug": "hai-robotics",
            "name": "HaiPick ACR",
            "slug": "haipick-acr",
            "description": "Autonomous Case-handling Mobile Robot that navigates standard racking up to 12m high. Handles cases, totes, and cartons with a picking arm that extends 2 totes deep. Can batch deliver up to 9 containers simultaneously.",
            "category": "ASRS",
            "subcategory": "Goods-to-Person",
            "product_url": "https://www.hairobotics.com/solutions/haipick-system-1",
            "image_url": "https://www.hairobotics.com/sites/default/files/2022-09/haipick-a42t-warehouse-robots-shelf.jpg",
            "release_year": 2018,
            "specs": [
                ("max_operating_height", "12", "m"),
                ("max_operating_height_imperial", "39+", "ft"),
                ("storage_depth", "2", "totes deep"),
                ("batch_size", "9", "containers"),
                ("navigation_type", "SLAM + QR code", ""),
                ("rack_compatibility", "Industry-standard racking", ""),
                ("container_types", "Totes, trays, cartons, boxes", ""),
                ("pick_accuracy", "99.9+", "%"),
                ("labor_reduction", "67", "%"),
                ("efficiency_improvement", "400", "%"),
            ],
            "capabilities": ["Goods-to-Person", "Automated Storage", "Automated Retrieval", "Case Picking", "Tote Handling", "Multi-Level Picking"],
        },
        # HAI HaiPick Climb
        {
            "company_slug": "hai-robotics",
            "name": "HaiPick Climb",
            "slug": "haipick-climb",
            "description": "Simplified ASRS with HaiClimber robots that climb multi-level racking. Double-deep design stores up to 45,000 totes in 1,000 m². Throughput up to 4,000 totes per hour with tote delivery in under 2 minutes.",
            "category": "ASRS",
            "subcategory": "Cube Storage",
            "product_url": "https://www.hairobotics.com/solutions/haipick-climb",
            "release_year": 2025,
            "specs": [
                ("storage_density", "45,000", "totes/1000m²"),
                ("throughput", "4,000", "totes/hr"),
                ("delivery_time", "<2", "minutes"),
                ("storage_depth", "double-deep", ""),
                ("navigation_type", "Guided + SLAM", ""),
                ("container_types", "Totes, cartons, original packaging", ""),
                ("rack_type", "Standard cross-bar racking", ""),
                ("deployment_footprint", "Compact", ""),
            ],
            "capabilities": ["Goods-to-Person", "High-Density Storage", "Automated Storage", "Automated Retrieval", "Tote Handling"],
        },
        # AutoStore R5
        {
            "company_slug": "autostore",
            "name": "R5 Robot",
            "slug": "autostore-r5",
            "description": "High-speed cube storage robot that drives on top of the AutoStore grid. Picks up bins, rearranges them, and delivers them to workstations. Compatible with 220mm and 330mm bin heights. Operates 24/7 in total darkness.",
            "category": "Cube Storage",
            "subcategory": "Robot",
            "product_url": "https://www.autostoresystem.com/system",
            "image_url": "https://www.autostoresystem.com/hs-fs/hubfs/Robots_Module%205.jpg",
            "release_year": 2020,
            "specs": [
                ("bin_capacity", "30", "kg"),
                ("max_speed", "3.1", "m/s"),
                ("acceleration", "0.8", "m/s²"),
                ("lift_speed", "1.6", "m/s"),
                ("power_consumption", "100", "W"),
                ("robot_dimensions_sdg", "963x700x545", "mm"),
                ("robot_weight_sdg", "151", "kg"),
                ("bin_heights_supported", "220, 330", "mm"),
                ("operating_temp_range", "+1 to +35", "°C"),
                ("operating_humidity", "40-90", "% non-condensing"),
                ("battery_type", "AGM (NexSys)", ""),
                ("voltage_nominal", "24", "VDC"),
                ("ip_class", "IP20", ""),
                ("uptime", "99.7", "%"),
                ("energy_usage", "10 robots = 1 vacuum cleaner", ""),
            ],
            "capabilities": ["Cube Storage", "Automated Storage", "Automated Retrieval", "High-Density Storage", "Goods-to-Person"],
        },
        # AutoStore R5+
        {
            "company_slug": "autostore",
            "name": "R5+ Robot",
            "slug": "autostore-r5plus",
            "description": "Extended version of the R5 robot that also supports the tallest 425mm bins. Same speed and performance as R5 with wider bin compatibility.",
            "category": "Cube Storage",
            "subcategory": "Robot",
            "product_url": "https://www.autostoresystem.com/system",
            "image_url": "https://www.autostoresystem.com/hs-fs/hubfs/Robots_Module%205.jpg",
            "release_year": 2022,
            "specs": [
                ("bin_capacity", "30", "kg"),
                ("max_speed", "3.1", "m/s"),
                ("power_consumption", "100", "W"),
                ("bin_heights_supported", "220, 330, 425", "mm"),
                ("operating_temp_range", "+1 to +35", "°C"),
                ("uptime", "99.7", "%"),
            ],
            "capabilities": ["Cube Storage", "Automated Storage", "Automated Retrieval", "High-Density Storage"],
        },
        # AutoStore R5Pro
        {
            "company_slug": "autostore",
            "name": "R5Pro Robot",
            "slug": "autostore-r5pro",
            "description": "High-performance robot with fast-charge capability enabling uninterrupted multi-shift operations. Increases productivity by ~14% in multi-shift environments and reduces charger count by 86%.",
            "category": "Cube Storage",
            "subcategory": "Robot",
            "product_url": "https://www.autostoresystem.com/hubfs/Red%20Line_Technical_Specs-1.pdf",
            "image_url": "https://www.autostoresystem.com/hs-fs/hubfs/Robots_Module%205.jpg",
            "release_year": 2024,
            "specs": [
                ("bin_capacity", "30", "kg"),
                ("max_speed", "3.1", "m/s"),
                ("power_consumption", "100", "W"),
                ("charge_current_max", "100", "A"),
                ("bin_heights_supported", "220, 330, 425", "mm"),
                ("productivity_improvement", "14", "%"),
                ("charger_reduction", "86", "%"),
            ],
            "capabilities": ["Cube Storage", "Automated Storage", "Automated Retrieval", "High-Density Storage"],
        },
        # Amazon Proteus
        {
            "company_slug": "amazon-robotics",
            "name": "Proteus",
            "slug": "amazon-proteus",
            "description": "Autonomous mobile robot designed to safely navigate around people in Amazon fulfillment centers. Moves GoCarts (wheeled racks) autonomously through facilities. First Amazon robot with safety certification for human-robot collaboration.",
            "category": "AMR",
            "subcategory": "Material Transport",
            "product_url": "https://www.aboutamazon.com/amazon-robotics",
            "release_year": 2022,
            "specs": [
                ("payload_capacity", "Estimated 500+", "lbs"),
                ("navigation_type", "Advanced sensor + AI", ""),
                ("safety_certification", "Yes - human-collaborative", ""),
                ("usage", "GoCart transport", ""),
                ("fleet_size", "1M+ across Amazon", "robots"),
            ],
            "capabilities": ["Transport", "Collaborative Picking", "Pallet Handling"],
        },
        # Amazon Sparrow
        {
            "company_slug": "amazon-robotics",
            "name": "Sparrow",
            "slug": "amazon-sparrow",
            "description": "Robotic arm for individual item picking. Uses computer vision and AI to identify, grasp, and move individual items from bins. Designed to handle millions of unique products in Amazon's catalog.",
            "category": "Robotic Arm",
            "subcategory": "Piece Picking",
            "product_url": "https://www.aboutamazon.com/news/operations/amazon-introduces-sparrow-a-state-of-the-art-robot-that-handles-millions-of-diverse-products",
            "release_year": 2022,
            "specs": [
                ("function", "Individual item picking", ""),
                ("vision_system", "AI + computer vision", ""),
                ("item_types", "Millions of unique products", ""),
                ("integration", "Amazon fulfillment network", ""),
            ],
            "capabilities": ["Piece Picking", "Goods-to-Person"],
        },
        # Amazon Kiva Systems Drive Unit (legacy)
        {
            "company_slug": "amazon-robotics",
            "name": "Kiva Systems Drive Unit",
            "slug": "kiva-systems-drive-unit",
            "status": "legacy",
            "description": "Original robotic drive unit developed by Kiva Systems (acquired by Amazon in 2012). The first generation goods-to-person drive that revolutionized warehouse automation. Lifted 450 kg pods and navigated via floor-encoded grid markers. Evolved into Amazon's Pegasus, Hercules, and Titan drive unit families. The Kiva Drive Unit laid the foundation for Amazon's 750,000+ robot fleet.",
            "category": "AMR",
            "subcategory": "Pod Transport",
            "product_url": "https://www.aboutamazon.com/news/operations/10-years-of-amazon-robotics-how-robots-help-sort-packages-move-product-and-improve-safety",
            "release_year": 2007,
            "specs": [
                ("payload_capacity", "1,000", "lbs"),
                ("payload_capacity_metric", "450", "kg"),
                ("dimensions", "~36x36x19", "inches"),
                ("navigation_type", "Floor grid markers", ""),
                ("sensors", "Downward-facing camera + bumper", ""),
                ("fleet_size", "Originally 15, then scaled to 100,000s", ""),
                ("usage", "Pod transport to picking stations", ""),
                ("status", "Discontinued — replaced by Hercules", ""),
            ],
            "capabilities": ["Goods-to-Person", "Automated Storage", "Automated Retrieval"],
        },
        # Amazon Hercules
        {
            "company_slug": "amazon-robotics",
            "name": "Hercules",
            "slug": "amazon-hercules",
            "description": "Fourth-generation autonomous drive unit that transports pods (mobile shelving units) weighing up to 1,250 lbs. Navigates using floor-encoded grid markers and a forward-facing 3D camera for obstacle detection. Over 750,000 Hercules drives deployed across Amazon's fulfillment network as of 2025. Designed to bring goods from inventory to employees at ergonomic picking stations.",
            "category": "AMR",
            "subcategory": "Pod Transport",
            "product_url": "https://www.aboutamazon.com/news/operations/amazon-hercules-robot",
            "release_year": 2015,
            "specs": [
                ("payload_capacity", "1,250", "lbs"),
                ("payload_capacity_metric", "567", "kg"),
                ("dimensions", "~30x30x19", "inches"),
                ("navigation_type", "Floor grid markers + 3D camera", ""),
                ("sensors", "Forward-facing 3D camera + downward grid camera", ""),
                ("fleet_size", "750,000+", "units"),
                ("usage", "Pod transport to picking stations", ""),
                ("control", "Centralized orchestration software", ""),
                ("safety", "Wi-Fi Tech Vest human detection", ""),
                ("operating_environment", "Indoor structured fulfillment center", ""),
            ],
            "capabilities": ["Goods-to-Person", "Automated Storage", "Automated Retrieval"],
        },
        # Amazon Cardinal
        {
            "company_slug": "amazon-robotics",
            "name": "Cardinal",
            "slug": "amazon-cardinal",
            "description": "Robotic arm using advanced AI and computer vision to select individual packages from a chute pile, lift them with suction, read labels, and precisely place them into GoCarts for outbound shipping. Handles packages up to 50 lbs. Reduces employee injury risk by automating twisting and lifting motions. Works in conjunction with Proteus AMRs for autonomous outbound dock workflows.",
            "category": "Robotic Arm",
            "subcategory": "Package Sortation",
            "product_url": "https://www.aboutamazon.com/news/operations/how-amazon-deploys-robots-in-its-operations-facilities",
            "release_year": 2022,
            "specs": [
                ("payload_capacity", "50", "lbs"),
                ("payload_capacity_metric", "22.7", "kg"),
                ("function", "Package sortation into GoCarts", ""),
                ("vision_system", "AI + computer vision", ""),
                ("gripper_type", "Air suction", ""),
                ("integration", "Works with Proteus AMR", ""),
                ("item_types", "Mixed-size packages from chute", ""),
                ("deployment_status", "Testing/production rollout", ""),
            ],
            "capabilities": ["Piece Picking", "Sortation"],
        },
        # Symbotic System
        {
            "company_slug": "symbotic",
            "name": "Symbotic System",
            "slug": "symbotic-system",
            "description": "End-to-end warehouse automation system using AI-powered robots for pallet and case-level inventory management. High-speed shuttles and robotic arms handle receiving, storage, retrieval, and shipping in one integrated system.",
            "category": "ASRS",
            "subcategory": "End-to-End Automation",
            "product_url": "https://www.symbotic.com",
            "release_year": 2017,
            "specs": [
                ("handling_level", "Pallet + Case", ""),
                ("automation_scope", "Receiving to shipping", ""),
                ("robotics_type", "High-speed shuttles + robot arms", ""),
                ("target_customers", "Major retailers", ""),
                ("integration", "End-to-end", ""),
            ],
            "capabilities": ["Automated Storage", "Automated Retrieval", "Pallet Handling", "Case Picking", "Depalletizing", "Sortation"],
        },
        # Boston Dynamics Stretch
        {
            "company_slug": "boston-dynamics",
            "name": "Stretch",
            "slug": "boston-dynamics-stretch",
            "description": "Mobile manipulation robot for warehouse unloading and case handling. Features a custom arm with advanced suction grippers mounted on a mobile base. Designed to unload trucks, move boxes, and handle cases in distribution centers.",
            "category": "Mobile Manipulation",
            "subcategory": "Truck Unloading",
            "product_url": "https://www.bostondynamics.com/stretch",
            "image_url": "https://bostondynamics.com/wp-content/uploads/2023/06/Stretch-unloads-carboard-cases-min-1-scaled.jpg",
            "release_year": 2021,
            "specs": [
                ("payload_capacity", "50", "lbs"),
                ("gripper_type", "Advanced suction", ""),
                ("navigation_type", "SLAM + vision", ""),
                ("mobility", "Mobile base with omni-wheels", ""),
                ("use_cases", "Truck unloading, case moving", ""),
            ],
            "capabilities": ["Truck Unloading", "Case Picking", "Depalletizing", "Trailer Unloading"],
        },
        # GreyOrange Ranger
        {
            "company_slug": "greyorange",
            "name": "Ranger Series",
            "slug": "greyorange-ranger",
            "description": "Family of AMRs for goods-to-person, person-to-goods, and sortation workflows. Orchestrated by the GreyMatter AI platform which coordinates both GreyOrange and third-party robots.",
            "category": "AMR",
            "subcategory": "Multi-purpose",
            "product_url": "https://www.greyorange.com",
            "release_year": 2015,
            "specs": [
                ("payload_capacity", "Varies by model", "kg"),
                ("orchestration", "GreyMatter AI platform", ""),
                ("workflows", "GTP, PTG, sortation", ""),
                ("multi_vendor", "Yes", ""),
            ],
            "capabilities": ["Goods-to-Person", "Person-to-Goods", "Sortation", "Transport"],
        },
        # Exotec Skypod
        {
            "company_slug": "exotec",
            "name": "Skypod",
            "slug": "exotec-skypod",
            "description": "Climbing ASRS robot that moves at 4 m/s on racks up to 12m high. Retrieves totes and delivers them to workstations. Combines ASRS density with AMR flexibility in one integrated system.",
            "category": "ASRS",
            "subcategory": "Goods-to-Person",
            "product_url": "https://www.exotec.com",
            "release_year": 2017,
            "specs": [
                ("max_speed", "4", "m/s"),
                ("max_operating_height", "12", "m"),
                ("navigation_type", "On-rack guided", ""),
                ("systems_deployed", "350+", "systems"),
                ("countries", "20+", ""),
            ],
            "capabilities": ["Goods-to-Person", "Automated Storage", "Automated Retrieval", "High-Density Storage", "Multi-Level Picking"],
        },
        # Zebra/Fetch CartConnect 500
        {
            "company_slug": "zebra-fetch",
            "name": "CartConnect 500",
            "slug": "fetch-cartconnect-500",
            "description": "Collaborative AMR designed for automated cart transport. Safely navigates around people and obstacles in dynamic environments. Tows or pushes carts, racks, and trolleys up to 500 kg. Deployed within hours using the FetchCore cloud platform.",
            "category": "AMR",
            "subcategory": "Collaborative Transport",
            "product_url": "https://www.zebra.com/us/en/products/robotics/cartconnect-500.html",
            "release_year": 2021,
            "specs": [
                ("payload_capacity", "500", "kg"),
                ("payload_capacity_imperial", "1,100", "lbs"),
                ("max_speed", "1.5", "m/s"),
                ("navigation_type", "SLAM + LiDAR + 3D cameras", ""),
                ("sensors", "2 LiDAR + 8x 3D cameras", ""),
                ("safety_certification", "RIA R15.08 compliant", ""),
                ("deployment_time", "Hours", ""),
                ("orchestration", "FetchCore cloud platform", ""),
                ("battery_life", "9", "hours"),
            ],
            "capabilities": ["Collaborative Picking", "Transport", "Putaway"],
        },
        # Zebra/Fetch Freight500
        {
            "company_slug": "zebra-fetch",
            "name": "Freight500",
            "slug": "fetch-freight-500",
            "description": "Industrial AMR for case goods and pallet transport. Handles payloads up to 500 kg and navigates through tighter aisles with its compact 40 inch wide form factor. Features dynamic obstacle avoidance with 3D cameras and LiDAR.",
            "category": "AMR",
            "subcategory": "Pallet Transport",
            "product_url": "https://www.zebra.com/us/en/products/robotics/freight-500.html",
            "release_year": 2020,
            "specs": [
                ("payload_capacity", "500", "kg"),
                ("payload_capacity_imperial", "1,100", "lbs"),
                ("max_speed", "1.5", "m/s"),
                ("dimensions", "1016 x 838 x 350", "mm"),
                ("dimensions_imperial", "40 x 33 x 13.8", "in"),
                ("weight", "301", "kg"),
                ("battery_life", "9", "hours"),
                ("charge_time", "1", "hour"),
                ("navigation_type", "SLAM + LiDAR + 3D cameras", ""),
                ("sensors", "2 LiDAR + 8x 3D cameras", ""),
                ("safety_certification", "RIA R15.08 compliant", ""),
                ("max_payload_surface", "1265 x 838", "mm"),
            ],
            "capabilities": ["Pallet Handling", "Transport", "Automated Storage", "Goods-to-Person"],
        },
        # Zebra/Fetch Freight1500
        {
            "company_slug": "zebra-fetch",
            "name": "Freight1500",
            "slug": "fetch-freight-1500",
            "description": "Heavy-duty AMR for pallet transport up to 1,500 kg. Fits under standard North American 40x48 inch pallets with its low-profile design. Built-in sensor technology for smooth movement and class-leading safety. Supports cross-docking, returns, and case picking workflows.",
            "category": "AMR",
            "subcategory": "Heavy Pallet Transport",
            "product_url": "https://www.zebra.com/us/en/products/robotics/freight-1500.html",
            "release_year": 2021,
            "specs": [
                ("payload_capacity", "1,500", "kg"),
                ("payload_capacity_imperial", "3,300", "lbs"),
                ("max_speed", "2.0", "m/s"),
                ("dimensions", "1220 x 810 x 350", "mm"),
                ("weight", "471", "kg"),
                ("battery_life", "9", "hours"),
                ("charge_time", "1", "hour (to 90%)"),
                ("navigation_type", "SLAM + LiDAR + 3D cameras", ""),
                ("sensors", "2 LiDAR + 8x 3D cameras", ""),
                ("safety_certification", "RIA R15.08 compliant", ""),
            ],
            "capabilities": ["Pallet Handling", "Transport", "Cross-Docking"],
        },
        # KUKA KR QUANTEC 210
        {
            "company_slug": "kuka",
            "name": "KR QUANTEC 210 R2700-2",
            "slug": "kuka-kr-quantec-210",
            "description": "Mid-range industrial robot arm from the KR QUANTEC-2 generation. Payload of 210 kg with 2,701 mm reach. Features high speed, precision (0.05 mm repeatability), and energy-efficient drive technology. Suitable for handling, palletizing, welding, and machining in automotive and general industry.",
            "category": "Robotic Arm",
            "subcategory": "Industrial",
            "product_url": "https://www.kuka.com/en-us/products/robotics-systems/industrial-robots/kr-quantec",
            "release_year": 2023,
            "specs": [
                ("payload_capacity", "210", "kg"),
                ("payload_capacity_imperial", "463", "lbs"),
                ("max_reach", "2,701", "mm"),
                ("axes", "6", ""),
                ("repeatability", "0.05", "mm"),
                ("controller", "KR C5-2", ""),
                ("ip_class", "IP65 / IP67", ""),
                ("mounting_position", "Floor", ""),
                ("max_speed_axis1", "120", "°/s"),
                ("max_speed_axis6", "220", "°/s"),
                ("weight", "1,110", "kg"),
                ("temperature_range", "0 to 55", "°C"),
            ],
            "capabilities": ["Piece Picking", "Pallet Handling", "Depalletizing", "Case Picking"],
        },
        # KUKA KR FORTEC 500
        {
            "company_slug": "kuka",
            "name": "KR FORTEC 500 R2800-2",
            "slug": "kuka-kr-fortec-500",
            "description": "Heavy-duty industrial robot for handling and spot welding in the 500 kg payload class. Designed for automotive and general industry with high energy efficiency and low maintenance. Part of the KR FORTEC series bridging the gap between KR QUANTEC and KR FORTEC ultra.",
            "category": "Robotic Arm",
            "subcategory": "Heavy Duty",
            "product_url": "https://www.kuka.com/en-us/products/robotics-systems/industrial-robots/kr-fortec",
            "release_year": 2023,
            "specs": [
                ("payload_capacity", "500", "kg"),
                ("payload_capacity_imperial", "1,102", "lbs"),
                ("max_reach", "2,800", "mm"),
                ("axes", "6", ""),
                ("repeatability", "0.08", "mm"),
                ("controller", "KR C5-2", ""),
                ("mounting_position", "Floor", ""),
                ("weight", "2,150", "kg"),
                ("applications", "Handling, spot welding, palletizing", ""),
            ],
            "capabilities": ["Pallet Handling", "Depalletizing"],
        },
        # MiR250
        {
            "company_slug": "mir",
            "name": "MiR250",
            "slug": "mir250",
            "description": "Next-generation mid-range collaborative AMR for internal transport of small to medium loads up to 250 kg. Faster (2.0 m/s) and more rugged than previous models with IP52 rating for dusty or humid environments. Features SLAM navigation requiring no facility modifications. Works with a wide range of top modules for different use cases.",
            "category": "AMR",
            "subcategory": "Collaborative Transport",
            "product_url": "https://www.mobile-industrial-robots.com/products/robots/mir250",
            "release_year": 2023,
            "specs": [
                ("payload_capacity", "250", "kg"),
                ("payload_capacity_imperial", "551", "lbs"),
                ("max_speed", "2.0", "m/s"),
                ("dimensions", "800 x 580 x 300", "mm"),
                ("weight", "78", "kg"),
                ("battery_life", "13", "hours"),
                ("charge_time", "10 min for 2.5 hrs", "runtime"),
                ("navigation_type", "SLAM", ""),
                ("ip_class", "IP52", ""),
                ("turning_radius", "Turn in place", ""),
            ],
            "capabilities": ["Collaborative Picking", "Transport", "Putaway", "Goods-to-Person"],
        },
        # MiR500
        {
            "company_slug": "mir",
            "name": "MiR500",
            "slug": "mir500",
            "description": "Collaborative AMR for automated transport of pallets and heavy loads up to 500 kg. Large, powerful, and robust design with rugged exterior that can withstand dropped cargo. Navigates ramps and shallow water puddles. Can be equipped with Pallet Lift top module for autonomous pallet pickup and delivery.",
            "category": "AMR",
            "subcategory": "Pallet Transport",
            "product_url": "https://www.mobile-industrial-robots.com/products/robots/mir500",
            "release_year": 2020,
            "specs": [
                ("payload_capacity", "500", "kg"),
                ("payload_capacity_imperial", "1,100", "lbs"),
                ("max_speed", "2.0", "m/s"),
                ("dimensions", "1,350 x 920 x 320", "mm"),
                ("weight", "226", "kg"),
                ("battery_life", "8", "hours"),
                ("navigation_type", "SLAM", ""),
                ("ip_class", "IP20", ""),
                ("safety_certification", "ISO/EN 13849", ""),
                ("turning_radius", "Turn in place", ""),
            ],
            "capabilities": ["Pallet Handling", "Transport", "Putaway", "Replenishment"],
        },
        # 6 River Systems Chuck
        {
            "company_slug": "6-river-systems",
            "name": "Chuck",
            "slug": "chuck-amr",
            "description": "Collaborative autonomous mobile robot for warehouse fulfillment. Features modular shelving with up to 6 shelves per robot, guiding associates through picking, putaway, sorting, and replenishment workflows. Uses AI-powered pick path optimization to minimize walking. Deployable within 14 weeks with no facility modifications required. Chuck+ variant adds 6 inches of extra shelf width for bulky items.",
            "category": "AMR",
            "subcategory": "Collaborative Picking",
            "product_url": "https://ocadointelligentautomation.com/systems/chuck-amr",
            "release_year": 2018,
            "specs": [
                ("payload_capacity", "200", "lbs"),
                ("payload_capacity_metric", "90", "kg"),
                ("max_speed", "4", "mph"),
                ("dimensions", "38.6x21.6x76.8", "in"),
                ("weight", "154", "lbs (with battery)"),
                ("battery_life", "12", "hours"),
                ("charge_time", "Autonomous opportunity charging", ""),
                ("shelves", "Up to 6", ""),
                ("per_shelf_capacity", "100", "lbs"),
                ("top_canopy_capacity", "30", "lbs"),
                ("navigation_type", "AI + LiDAR + cameras", ""),
                ("deployment_time", "14", "weeks"),
                ("certification", "UL, CE, ISO 3691-4, CSA", ""),
                ("interface", "Touchscreen + put-to-light", ""),
                ("wms_integration", "Cloud-based FES (Fulfillment Execution System)", ""),
                ("operating_temp_range", "2 to 35", "°C"),
            ],
            "capabilities": ["Collaborative Picking", "Putaway", "Sortation", "Replenishment", "Person-to-Goods"],
        },
        # Universal Robots UR5e
        {
            "company_slug": "universal-robots",
            "name": "UR5e",
            "slug": "ur5e",
            "description": "Collaborative robot arm with 5 kg payload, ideal for light assembly, packaging, and material handling. Part of Universal Robots' e-Series, featuring built-in force/torque sensing, 16 safety functions, and easy programming via the Polyscope touchscreen interface. Typical applications in warehouse and logistics include packing, kitting, machine tending, and quality inspection. Deployable without safety guarding in collaborative applications.",
            "category": "Cobot",
            "subcategory": "Collaborative Arm",
            "product_url": "https://www.universal-robots.com/products/ur5e",
            "release_year": 2018,
            "specs": [
                ("payload_capacity", "5", "kg"),
                ("payload_capacity_imperial", "11", "lbs"),
                ("max_reach", "850", "mm"),
                ("axes", "6", ""),
                ("repeatability", "±0.03", "mm"),
                ("max_speed", "1.0", "m/s"),
                ("weight", "20.6", "kg"),
                ("controller", "Embedded (in base)", ""),
                ("power_consumption", "150", "W (typical)"),
                ("operating_temp_range", "0 to 50", "°C"),
                ("ip_class", "IP54", ""),
                ("mounting_position", "Floor, ceiling, wall, angle", ""),
                ("interface", "Polyscope touchscreen", ""),
                ("certification", "EN ISO 13849-1, EN ISO 10218-1", ""),
            ],
            "capabilities": ["Collaborative Picking", "Packing", "Machine Tending"],
        },
        # FANUC CRX-10iA
        {
            "company_slug": "fanuc",
            "name": "CRX-10iA",
            "slug": "fanuc-crx-10ia",
            "description": "Collaborative robot with 10 kg payload designed for assembly, palletizing, and machine tending. Features FANUC's advanced safety functions, built-in vision interface, and easy drag-teach programming. The CRX series offers the highest payload in its compact cobot class. Widely used in warehouse automation for case packing, palletizing, and kitting operations.",
            "category": "Cobot",
            "subcategory": "Collaborative Arm",
            "product_url": "https://www.fanuc.com/products/robots/collaborative/crx-10ia",
            "release_year": 2019,
            "specs": [
                ("payload_capacity", "10", "kg"),
                ("payload_capacity_imperial", "22", "lbs"),
                ("max_reach", "1249", "mm"),
                ("axes", "6", ""),
                ("repeatability", "±0.05", "mm"),
                ("max_speed", "1.0", "m/s"),
                ("weight", "60", "kg"),
                ("controller", "FANUC R-30iB Mini Plus", ""),
                ("power_consumption", "650", "W (typical)"),
                ("operating_temp_range", "0 to 45", "°C"),
                ("ip_class", "IP54", ""),
                ("certification", "EN ISO 13849-1 Cat.3 PLd", ""),
                ("vision_system", "iRVision (integrated)", ""),
            ],
            "capabilities": ["Palletizing", "Packing", "Machine Tending"],
        },
        # ABB IRB 1300
        {
            "company_slug": "abb-robotics",
            "name": "IRB 1300",
            "slug": "abb-irb-1300",
            "description": "Compact industrial robot with 11 kg payload designed for flexible material handling, machine tending, and assembly. The IRB 1300 features ABB's OmniCore controller with TrueMove and QuickMove motion control for exceptional path accuracy and cycle times. Its compact footprint and wide working range make it ideal for palletizing cells and picking stations in warehouse and logistics environments.",
            "category": "Industrial Robot",
            "subcategory": "Articulated Arm",
            "product_url": "https://new.abb.com/products/robotics/industrial-robots/irb-1300",
            "release_year": 2021,
            "specs": [
                ("payload_capacity", "11", "kg"),
                ("payload_capacity_imperial", "24", "lbs"),
                ("max_reach", "1150", "mm"),
                ("axes", "6", ""),
                ("repeatability", "±0.02", "mm"),
                ("max_speed", "2.0", "m/s"),
                ("weight", "140", "kg"),
                ("controller", "OmniCore C30 or E10", ""),
                ("power_consumption", "1.2", "kW (typical)"),
                ("operating_temp_range", "5 to 45", "°C"),
                ("ip_class", "IP54 (controller, arm)", ""),
                ("mounting_position", "Floor, inverted, shelf", ""),
                ("applications", "Handling, Machine Tending, Picking, Packing", ""),
            ],
            "capabilities": ["Palletizing", "Packing", "Machine Tending"],
        },
        # Magazino TORU
        {
            "company_slug": "magazino",
            "name": "TORU",
            "slug": "magazino-toru",
            "description": "Perceptive autonomous mobile robot for piece picking in e-commerce fulfillment. TORU (Tote-Operating Robotic Unit) navigates warehouse aisles autonomously using SLAM and picks individual items from standard shelf racks using a 3D stereo camera system. Unlike cubby-hole ASRS, TORU works with existing shelving and handles a wide variety of item shapes, sizes, and packaging. Can pick 200+ items per hour with 99%+ reliability. Ideal for fashion, media, and general e-commerce.",
            "category": "AMR",
            "subcategory": "Piece Picking",
            "product_url": "https://www.magazino.eu/toru",
            "release_year": 2017,
            "specs": [
                ("payload_capacity", "15", "kg (per pick)"),
                ("pick_rate", "200+", "items/hour"),
                ("max_speed", "1.5", "m/s"),
                ("gripper_type", "Vacuum + mechanical", ""),
                ("vision_system", "3D stereo + depth camera", ""),
                ("navigation_type", "SLAM with LiDAR", ""),
                ("battery_life", "8", "hours"),
                ("charge_time", "2", "hours"),
                ("bin_capacity", "12", "totes"),
                ("certification", "CE, EN ISO 13849-1", ""),
                ("deployment_time", "4-6", "weeks"),
                ("wms_integration", "REST API, XML, CSV", ""),
            ],
            "capabilities": ["Piece Picking", "Goods-to-Person", "Automated Storage", "Automated Retrieval"],
        },
        # --- Intuitive Surgical da Vinci Xi ---
        {
            "company_slug": "intuitive-surgical",
            "name": "da Vinci Xi",
            "slug": "da-vinci-xi",
            "description": "Flagship robotic surgical system designed for complex multiquadrant surgery. Features a patient-side cart with four interactive robotic arms, a 3D HD vision system with surgeon-controlled camera, and an ergonomic surgeon console with intuitive instrument controls. Supports a wide range of procedures in urology, gynecology, thoracic, cardiac, and general surgery.",
            "category": "Robotic Arm",
            "subcategory": "Surgical Robot",
            "product_url": "https://www.intuitive.com/en-us/products-and-services/da-vinci/da-vinci-xi",
            "image_url": "https://www.intuitive.com/content/dam/connect/680x460/da-vinci-xi.png",
            "release_year": 2014,
            "specs": [
                ("degrees_of_freedom", "7", "DOF per instrument"),
                ("visualization", "3D HD 1080p", ""),
                ("magnification", "10x", ""),
                ("arm_configuration", "4 interactive arms", ""),
                ("instruments", "EndoWrist with 7 DOF", ""),
                ("footprint", "Patient cart + surgeon console + vision cart", ""),
                ("procedures_performed", "Millions", "globally"),
                ("upgradeability", "Yes (ongoing software/hardware)", ""),
                ("surgical_applications", "Urology, gynecology, thoracic, cardiac, general", ""),
            ],
            "capabilities": ["Surgical Assistance", "Minimally Invasive Surgery", "Teleoperation", "Haptic Feedback"],
        },
        # --- Intuitive Surgical da Vinci SP ---
        {
            "company_slug": "intuitive-surgical",
            "name": "da Vinci SP",
            "slug": "da-vinci-sp",
            "description": "Single-port robotic surgical system designed for deep, narrow-access procedures. A single articulating arm and 3D camera are inserted through a single 2.5cm incision, enabling access to anatomically constrained surgical sites. Ideal for transoral, rectal, and retroperitoneal procedures.",
            "category": "Robotic Arm",
            "subcategory": "Surgical Robot",
            "product_url": "https://www.intuitive.com/en-us/products-and-services/da-vinci/da-vinci-sp",
            "release_year": 2018,
            "specs": [
                ("degrees_of_freedom", "7", "DOF per instrument"),
                ("visualization", "3D HD 1080p", ""),
                ("incision_size", "2.5", "cm"),
                ("arm_configuration", "Single articulating arm + 3D camera", ""),
                ("instruments", "Articulating with wristed tip", ""),
                ("surgical_applications", "Transoral, rectal, retroperitoneal", ""),
            ],
            "capabilities": ["Surgical Assistance", "Minimally Invasive Surgery", "Endoscopy", "Teleoperation"],
        },
        # --- Medtronic Hugo RAS ---
        {
            "company_slug": "medtronic",
            "name": "Hugo RAS",
            "slug": "hugo-ras",
            "description": "Medtronic's modular robotic-assisted surgery platform designed for flexibility and scalability. Features independent robotic arms on wheeled carts, an open surgeon console, and a 3D vision system. The modular design allows hospitals to configure the system for different procedure types and operating room layouts. Supports laparoscopic procedures in urology, gynecology, and general surgery.",
            "category": "Robotic Arm",
            "subcategory": "Surgical Robot",
            "product_url": "https://www.medtronic.com/us/en/healthcare-professionals/products/surgical-robotics/hugo-ras.html",
            "release_year": 2021,
            "specs": [
                ("degrees_of_freedom", "7", "DOF per instrument"),
                ("visualization", "4K 3D endoscope", ""),
                ("arm_configuration", "Independent modular arms", ""),
                ("arms_included", "Up to 4", "carts"),
                ("console_type", "Open ergonomic", ""),
                ("instruments", "Wristed laparoscopic", ""),
                ("surgical_applications", "Urology, gynecology, general surgery", ""),
                ("modular_design", "Yes", "wheeled carts"),
            ],
            "capabilities": ["Surgical Assistance", "Minimally Invasive Surgery", "Teleoperation"],
        },
        # --- Medtronic Mazor X Stealth ---
        {
            "company_slug": "medtronic",
            "name": "Mazor X Stealth Edition",
            "slug": "mazor-x-stealth",
            "description": "Robotic guidance platform for spine surgery, combining Mazor's robotic technology with Medtronic's StealthStation navigation. Provides real-time visualization and guidance for pedicle screw placement, tumor resection, and spinal decompression. Uses preoperative CT planning with intraoperative 3D imaging confirmation.",
            "category": "Robotic Arm",
            "subcategory": "Spine Surgery",
            "product_url": "https://www.medtronic.com/us/en/healthcare-professionals/products/neurological/surgical-robotics/mazor-x-stealth-edition.html",
            "release_year": 2019,
            "specs": [
                ("visualization", "StealthStation S8 navigation", ""),
                ("planning", "Preoperative CT with 3D reconstruction", ""),
                ("guidance_type", "Robotic arm + navigation", ""),
                ("applications", "Pedicle screw placement, tumor resection, decompression", ""),
                ("imaging_integration", "Intraoperative 3D confirmation", ""),
            ],
            "capabilities": ["Image-Guided Surgery", "Neurosurgery", "Orthopedic Surgery"],
        },
        # --- Stryker Mako ---
        {
            "company_slug": "stryker",
            "name": "Mako SmartRobotics",
            "slug": "mako-smartrobotics",
            "description": "Haptic-guided robotic arm system for orthopedic joint replacement. Combines 3D CT-based preoperative planning with AccuStop haptic technology for precise bone resections in total hip, total knee, and partial knee arthroplasty. The robotic arm provides tactile feedback to guide the surgeon within the planned surgical boundaries, ensuring reproducible implant positioning.",
            "category": "Robotic Arm",
            "subcategory": "Orthopedic Surgery",
            "product_url": "https://www.stryker.com/us/en/portfolios/orthopaedics/joint-replacement/mako-robotic-arm-assisted-surgery.html",
            "image_url": "https://www.stryker.com/content/dam/stryker/orthopaedics/mako/mako-robotic-arm-hero.jpg",
            "release_year": 2016,
            "specs": [
                ("visualization", "3D CT-based planning", ""),
                ("guidance_type", "Haptic (AccuStop)", ""),
                ("procedures", "Total hip, total knee, partial knee", ""),
                ("implant_compatibility", "Stryker Triathlon, Accolade, etc.", ""),
                ("accuracy", "Sub-millimeter", ""),
                ("revision_rate", "Significantly reduced", ""),
                ("systems_installed", "2,000+", "globally"),
                ("procedures_performed", "1M+", "procedures"),
            ],
            "capabilities": ["Orthopedic Surgery", "Image-Guided Surgery", "Haptic Feedback"],
        },
        # --- Zimmer Biomet Rosa Knee ---
        {
            "company_slug": "zimmer-biomet",
            "name": "Rosa Knee",
            "slug": "rosa-knee",
            "description": "Robotic platform for total knee arthroplasty that uses real-time intra-articular sensor data and dynamic gap assessment. The robotic arm guides bone resections in the coronal and sagittal planes with sub-millimeter precision. Rosa Knee adapts to each patient's unique anatomy using intraoperative data rather than requiring preoperative CT imaging.",
            "category": "Robotic Arm",
            "subcategory": "Orthopedic Surgery",
            "product_url": "https://www.zimmerbiomet.com/en/medical-professionals/robotics/rosa-knee.html",
            "release_year": 2019,
            "specs": [
                ("guidance_type", "Robotic arm + intraoperative sensors", ""),
                ("imaging_required", "CT-free", ""),
                ("procedures", "Total knee arthroplasty", ""),
                ("accuracy", "Sub-millimeter", ""),
                ("gap_assessment", "Dynamic intraoperative", ""),
                ("adaptive_planning", "Yes (real-time adaptation)", ""),
            ],
            "capabilities": ["Orthopedic Surgery", "Image-Guided Surgery"],
        },
        # --- Globus ExcelsiusGPS ---
        {
            "company_slug": "globus-medical",
            "name": "ExcelsiusGPS",
            "slug": "excelsiusgps",
            "description": "Robotic navigation platform for spine surgery that integrates real-time intraoperative imaging with surgical planning software. Provides precise guidance for pedicle screw placement and other spinal procedures. Features a rigid robotic arm that positions and holds surgical instruments with sub-millimeter accuracy according to the surgical plan.",
            "category": "Robotic Arm",
            "subcategory": "Spine Surgery",
            "product_url": "https://www.globusmedical.com/excelsiusgps/",
            "release_year": 2017,
            "specs": [
                ("visualization", "Intraoperative 3D imaging + navigation", ""),
                ("guidance_type", "Robotic arm positioned", ""),
                ("applications", "Pedicle screw placement, biopsy, tumor resection", ""),
                ("accuracy", "Sub-millimeter", ""),
                ("imaging_integration", "O-arm, 3D C-arm compatible", ""),
                ("workflow", "Plan, register, navigate, confirm", ""),
                ("footprint", "Compact mobile base", ""),
            ],
            "capabilities": ["Image-Guided Surgery", "Neurosurgery", "Orthopedic Surgery"],
        },
        # --- Smith+Nephew CORI ---
        {
            "company_slug": "smith-nephew",
            "name": "CORI Surgical System",
            "slug": "cori-surgical",
            "description": "Next-generation handheld robotic system for knee and hip arthroplasty. Uses intraoperative 3D mapping to create a patient-specific model without requiring preoperative CT imaging. The handheld robotic tool guides bone resections with visual and auditory feedback, while providing real-time gap balancing data for precise soft tissue management.",
            "category": "Robotic Arm",
            "subcategory": "Orthopedic Surgery",
            "product_url": "https://www.smith-nephew.com/en/robotics/cori-surgical-system",
            "release_year": 2020,
            "specs": [
                ("guidance_type", "Handheld robotic instrumentation", ""),
                ("imaging_required", "CT-free", ""),
                ("mapping", "Intraoperative 3D", ""),
                ("procedures", "Partial knee, total knee, hip", ""),
                ("gap_balancing", "Real-time", ""),
                ("feedback", "Visual + auditory", ""),
            ],
            "capabilities": ["Orthopedic Surgery", "Image-Guided Surgery"],
        },
        # --- CMR Versius ---
        {
            "company_slug": "cmr-surgical",
            "name": "Versius Surgical System",
            "slug": "versius",
            "description": "Modular next-generation robotic surgical system for laparoscopic procedures. Features independent bedside robotic arms with 7 degrees of freedom and 360-degree articulation. The open surgeon console enables direct patient communication. The modular design allows arms to be positioned around the patient bed for optimal access, and the system can be transported between operating rooms. Supports general surgery, gynecology, and urology procedures.",
            "category": "Robotic Arm",
            "subcategory": "Surgical Robot",
            "product_url": "https://www.cmrsurgical.com/versius",
            "release_year": 2019,
            "specs": [
                ("degrees_of_freedom", "7", "DOF per arm"),
                ("articulation", "360", "degrees"),
                ("arm_configuration", "Independent bedside arms", ""),
                ("console_type", "Open design", ""),
                ("portability", "Modular, transportable between ORs", ""),
                ("surgical_applications", "General surgery, gynecology, urology", ""),
                ("instruments", "Wristed laparoscopic", ""),
            ],
            "capabilities": ["Surgical Assistance", "Minimally Invasive Surgery", "Teleoperation"],
        },
        # --- Asensus Senhance ---
        {
            "company_slug": "asensus-surgical",
            "name": "Senhance Surgical System",
            "slug": "senhance",
            "description": "Multi-port robotic surgical system with eye-tracking camera control, haptic feedback, and 3D visualization. Uses reusable instruments to reduce per-procedure costs. The system provides force feedback through the instrument handles, giving surgeons tactile sensation during tissue manipulation. Eye-tracking technology enables intuitive camera control where the surgeon's gaze directs the laparoscopic camera.",
            "category": "Robotic Arm",
            "subcategory": "Surgical Robot",
            "product_url": "https://www.asensus.com/senhance",
            "release_year": 2017,
            "specs": [
                ("degrees_of_freedom", "5-7", "DOF"),
                ("visualization", "3D HD", ""),
                ("camera_control", "Eye-tracking", ""),
                ("haptic_feedback", "Yes (force feedback)", ""),
                ("instruments", "Reusable laparoscopic", ""),
                ("console_type", "Ergonomic seated", ""),
                ("surgical_applications", "General surgery, gynecology, colorectal", ""),
            ],
            "capabilities": ["Surgical Assistance", "Minimally Invasive Surgery", "Teleoperation", "Haptic Feedback"],
        },
        # --- Stereotaxis Genesis ---
        {
            "company_slug": "stereotaxis",
            "name": "Genesis RMN",
            "slug": "genesis-rmn",
            "description": "Next-generation remote magnetic navigation system for cardiac electrophysiology. Uses computer-controlled external magnets to precisely guide magnetic catheters through the heart and vasculature. Offers enhanced magnet positioning speed, faster field vector changes, and improved integration with 3D mapping systems for treatment of complex arrhythmias.",
            "category": "Robotic Arm",
            "subcategory": "Cardiac",
            "product_url": "https://www.stereotaxis.com/genesis",
            "release_year": 2017,
            "specs": [
                ("navigation_type", "Remote magnetic navigation", ""),
                ("magnet_positioning", "Computer-controlled external magnets", ""),
                ("field_vector_changes", "Fast", ""),
                ("mapping_integration", "3D electroanatomic mapping systems", ""),
                ("procedures", "Atrial fibrillation, flutter, VT ablation", ""),
                ("worldwide_procedures", "100,000+", ""),
                ("catheter_steering", "Magnetic, precise real-time", ""),
            ],
            "capabilities": ["Cardiac Intervention", "Image-Guided Surgery", "Teleoperation"],
        },
    ]

    for p in products_data:
        cur = conn.execute("SELECT id FROM companies WHERE slug = ?", (p["company_slug"],))
        company_id = cur.fetchone()[0]
        conn.execute("""INSERT INTO products (company_id, name, slug, description, category, subcategory, product_url, image_url, release_year, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (company_id, p["name"], p["slug"], p["description"],
                       p["category"], p["subcategory"], p["product_url"], p.get("image_url"), p["release_year"],
                       p.get("status", "current")))

        cur = conn.execute("SELECT id FROM products WHERE slug = ?", (p["slug"],))
        product_id = cur.fetchone()[0]

        for spec_name, spec_value, unit in p["specs"]:
            conn.execute("""INSERT INTO product_specs (product_id, spec_name, spec_value, unit, source)
                            VALUES (?, ?, ?, ?, ?)""",
                         (product_id, spec_name, spec_value, unit, "manual"))

        for cap_name in p["capabilities"]:
            cur = conn.execute("SELECT id FROM capabilities WHERE name = ?", (cap_name,))
            row = cur.fetchone()
            if row:
                conn.execute("INSERT OR IGNORE INTO product_capabilities (product_id, capability_id) VALUES (?, ?)",
                             (product_id, row[0]))

    conn.commit()

    seed_additional_products(conn)

    cur = conn.execute("SELECT count(*) FROM case_studies")
    if cur.fetchone()[0] == 0:
        seed_case_studies(conn)

    # Always re-extract case study metrics (patterns may have changed)
    extract_all_case_study_metrics(conn)

    cur = conn.execute("SELECT count(*) FROM company_associations")
    if cur.fetchone()[0] == 0:
        seed_associations(conn)

    cur = conn.execute("SELECT count(*) FROM people")
    if cur.fetchone()[0] == 0:
        seed_people(conn)

    cur = conn.execute("SELECT count(*) FROM product_bins")
    if cur.fetchone()[0] == 0:
        seed_bins(conn)

def _link(conn, slug, assoc_slug, atype, notes=""):
    row = conn.execute("SELECT id FROM companies WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return
    cid = row[0]
    aid = None
    if assoc_slug:
        row2 = conn.execute("SELECT id FROM companies WHERE slug = ?", (assoc_slug,)).fetchone()
        if row2:
            aid = row2[0]
    conn.execute("""INSERT OR IGNORE INTO company_associations
                    (company_id, associated_company_id, association_type, notes)
                    VALUES (?, ?, ?, ?)""",
                 (cid, aid, atype, notes))

def seed_associations(conn):
    # --- Parent / Acquisition relationships (child -> parent) ---
    _link(conn, "mir", "teradyne", "parent", "Acquired by Teradyne in 2018 for $285M")
    _link(conn, "universal-robots", "teradyne", "parent", "Acquired by Teradyne in 2015 for $285M")
    _link(conn, "kuka", "midea-group", "parent", "Acquired by Midea Group in 2017 for $4.9B")
    _link(conn, "boston-dynamics", "hyundai-motor-group", "parent", "Acquired by Hyundai in 2021 for $1.1B")
    _link(conn, "6-river-systems", "shopify", "parent", "Acquired by Shopify in 2019 for ~$450M")
    _link(conn, "6-river-systems", "ocado-group", "parent", "Acquired by Ocado Group in 2023")
    _link(conn, "6-river-systems", "kiva-systems", "spin_off_from", "Founded by former Kiva Systems employees (Jerome Dubois, Chris Cacioppo, Rylan Hamilton)")
    _link(conn, "zebra-fetch", "zebra-technologies", "parent", "Acquired by Zebra Technologies in 2021 for $290M")
    _link(conn, "amazon-robotics", "amazon", "division_of", "Internal robotics division of Amazon since 2012")
    _link(conn, "kiva-systems", "amazon", "parent", "Acquired by Amazon in 2012 for $775M, became Amazon Robotics")

    # --- Predecessor / Successor ---
    _link(conn, "amazon-robotics", "kiva-systems", "predecessor", "Evolved from Kiva Systems acquisition in 2012")

    # --- Academic / Spin-off relationships ---
    _link(conn, "boston-dynamics", "mit", "spin_off_from", "Founded in 1992 as a spin-off from MIT")
    _link(conn, "pickle-robotics", "mit", "academic_origin", "Founded by MIT alumni")
    _link(conn, "magazino", "technical-university-of-munich", "spin_off_from", "Spin-off from Technical University of Munich (TUM)")
    _link(conn, "kiva-systems", "mit", "spin_off_from", "Co-founded by MIT professor Raffaello D'Andrea")
    _link(conn, "intuitive-surgical", "mit", "academic_origin", "Founded by MIT researchers and Stanford AI Lab alumni")
    _link(conn, "medtronic", "mit", "academic_origin", "Founded by MIT graduate Earl Bakken")

    # --- Partner relationships ---
    _link(conn, "pickle-robotics", "kuka", "partner", "Pickle robots use KUKA robot arms for trailer unloading")

    # --- VC Investment relationships ---
    _link(conn, "geekplus", "sequoia-capital", "invested_in", "Sequoia Capital China invested in Geek+")
    _link(conn, "autostore", "softbank-group", "invested_in", "SoftBank Vision Fund invested in AutoStore")
    _link(conn, "locus-robotics", "a16z", "invested_in", "Andreessen Horowitz invested in Locus Robotics")

    # --- Customer relationships from case studies ---
    seed_customer_associations(conn)

    conn.commit()

def seed_people(conn):
    people_data = [
        {"name": "Raffaello D'Andrea", "slug": "raffaello-dandrea",
         "title": "Robotics professor, co-founder Kiva Systems",
         "bio": "Professor at ETH Zurich and co-founder of Kiva Systems. Previously on the faculty at MIT's CSAIL and Department of Mechanical Engineering. A pioneer in autonomous mobile robotics and an IEEE Fellow.",
         "roles": [
             ("kiva-systems", "co-founder", 2003, 2012),
             ("mit", "professor", 1996, 2004),
         ]},
        {"name": "Mick Mountz", "slug": "mick-mountz",
         "title": "Founder and former CEO of Kiva Systems",
         "bio": "Founder and CEO of Kiva Systems (acquired by Amazon for $775M). MBA from MIT Sloan. Previously a product manager at Webvan (grocery delivery).",
         "roles": [
             ("kiva-systems", "founder", 2003, 2012),
             ("kiva-systems", "CEO", 2003, 2012),
             ("mit", "alumnus", None, None),
         ]},
        {"name": "Peter Wurman", "slug": "peter-wurman",
         "title": "Co-founder and CTO of Kiva Systems",
         "bio": "Co-founder and former CTO of Kiva Systems. PhD from MIT. Led the development of Kiva's robot control system and multi-agent coordination algorithms.",
         "roles": [
             ("kiva-systems", "co-founder", 2003, 2012),
             ("kiva-systems", "CTO", 2003, 2012),
             ("mit", "alumnus", None, None),
         ]},
        {"name": "Marc Raibert", "slug": "marc-raibert",
         "title": "Founder of Boston Dynamics",
         "bio": "Founder of Boston Dynamics (spun out from MIT). Previously a professor at MIT's CSAIL, where he founded the Leg Laboratory. Pioneer in dynamic legged locomotion robotics.",
         "roles": [
             ("boston-dynamics", "founder", 1992, 2019),
             ("mit", "professor", 1980, 1992),
         ]},
        {"name": "AJ Juliano", "slug": "aj-juliano",
         "title": "CEO of Pickle Robotics",
         "bio": "CEO of Pickle Robot Company. Previously led product and engineering teams in robotics and automation. MIT alum.",
         "roles": [
             ("pickle-robotics", "CEO", 2018, None),
             ("mit", "alumnus", None, None),
         ]},
        {"name": "Rick Faulk", "slug": "rick-faulk",
         "title": "CEO of Locus Robotics",
         "bio": "CEO of Locus Robotics. Previously CEO of Quiet Logistics, an early Locus customer and 3PL operator. Over 30 years of experience in supply chain and technology leadership.",
         "roles": [
             ("locus-robotics", "CEO", 2020, None),
         ]},
        {"name": "Dr. Peter Seitz", "slug": "peter-seitz",
         "title": "Founder of Magazino",
         "bio": "Founder of Magazino. PhD from Technical University of Munich (TUM). Pioneer in perception-driven autonomous mobile manipulation for warehouse picking.",
         "roles": [
             ("magazino", "founder", 2014, None),
             ("technical-university-of-munich", "alumnus", None, None),
         ]},
        {"name": "Dr. Frederik Brantner", "slug": "frederik-brantner",
         "title": "Co-founder and CEO of Magazino",
         "bio": "Co-founder and CEO of Magazino. Graduate of Technical University of Munich (TUM). Leads the company's vision for intelligent perception-driven warehouse robots.",
         "roles": [
             ("magazino", "co-founder", 2014, None),
             ("magazino", "CEO", 2014, None),
             ("technical-university-of-munich", "alumnus", None, None),
         ]},
        {"name": "Yong Zheng", "slug": "yong-zheng",
         "title": "Founder and CEO of Geek+",
         "bio": "Founder and CEO of Geek+, the world's largest AMR company. Serial entrepreneur in robotics and automation. Built Geek+ from startup to 30,000+ deployed robots.",
         "roles": [
             ("geekplus", "founder", 2015, None),
             ("geekplus", "CEO", 2015, None),
         ]},
        {"name": "Dr. Paolo Pirjanian", "slug": "paolo-pirjanian",
         "title": "Founder of Locus Robotics",
         "bio": "Founder of Locus Robotics (originally part of Quiet Logistics). Former CTO of iRobot's Home Robots division. Led development of Roomba technology.",
         "roles": [
             ("locus-robotics", "founder", 2014, 2020),
         ]},
        {"name": "Dr. Robert Playter", "slug": "robert-playter",
         "title": "CEO of Boston Dynamics",
         "bio": "CEO of Boston Dynamics since 2019. Joined the company in its earliest days from MIT's Leg Laboratory. Led engineering for Atlas, Spot, and Stretch robots.",
         "roles": [
             ("boston-dynamics", "CEO", 2019, None),
             ("mit", "alumnus", None, None),
         ]},
        {"name": "Samay Kohli", "slug": "samay-kohli",
         "title": "Co-founder and CEO of GreyOrange",
         "bio": "Co-founder and CEO of GreyOrange. Built the company into a global warehouse automation leader with AI-powered robotic systems for fulfillment.",
         "roles": [
             ("greyorange", "co-founder", 2011, None),
             ("greyorange", "CEO", 2011, None),
         ]},
        {"name": "Ronen Ben-Zur", "slug": "ronen-ben-zur",
         "title": "Co-founder of GreyOrange",
         "bio": "Co-founder of GreyOrange. Entrepreneur in supply chain robotics and automation.",
         "roles": [
             ("greyorange", "co-founder", 2011, None),
         ]},
        {"name": "Dr. Helen Greiner", "slug": "helen-greiner",
         "title": "Co-founder of iRobot, former CTO of SeaRobotics",
         "bio": "Co-founder of iRobot alongside Colin Angle and Rod Brooks. MIT alumna and pioneer in consumer and military robotics. Previously CTO of SeaRobotics and founder of CyPhy Works (drone startup).",
         "roles": [
             ("amazon-robotics", "board_member", 2018, None),
             ("mit", "alumnus", None, None),
         ]},
        {"name": "Rodney Brooks", "slug": "rodney-brooks",
         "title": "Co-founder of iRobot and Rethink Robotics, former MIT professor",
         "bio": "Professor Emeritus at MIT CSAIL. Co-founder of iRobot (Roomba) and Rethink Robotics (Baxter). Pioneer in behavior-based robotics and AI. Former director of MIT CSAIL.",
         "roles": [
             ("mit", "professor", 1984, 2020),
         ]},
         {"name": "Dr. Fredrik Eliasson", "slug": "fredrik-eliasson",
          "title": "CEO of AutoStore",
          "bio": "CEO of AutoStore, the global cube storage ASRS leader. Over 20 years of experience in industrial automation and robotics.",
          "roles": [
              ("autostore", "CEO", 2023, None),
          ]},
         {"name": "Jerome Dubois", "slug": "jerome-dubois",
          "title": "Co-founder and CEO of 6 River Systems",
          "bio": "Co-founder and CEO of 6 River Systems (acquired by Shopify then Ocado). Previously led operations and product at Kiva Systems/Amazon Robotics, where he was a founding member of the Kiva Systems team.",
          "roles": [
              ("6-river-systems", "co-founder", 2015, 2023),
              ("6-river-systems", "CEO", 2015, 2023),
              ("kiva-systems", "executive", 2003, 2015),
          ]},
         {"name": "Chris Cacioppo", "slug": "chris-cacioppo",
          "title": "Co-founder and CTO of 6 River Systems",
          "bio": "Co-founder and CTO of 6 River Systems (acquired by Shopify then Ocado). Former engineering lead at Kiva Systems/Amazon Robotics, where he was instrumental in developing Kiva's robot control software.",
          "roles": [
              ("6-river-systems", "co-founder", 2015, 2023),
              ("6-river-systems", "CTO", 2015, 2023),
              ("kiva-systems", "engineering_lead", 2003, 2015),
          ]},
         {"name": "Rylan Hamilton", "slug": "rylan-hamilton",
          "title": "Co-founder of 6 River Systems",
          "bio": "Co-founder of 6 River Systems (acquired by Shopify then Ocado). Former product and engineering leader at Kiva Systems/Amazon Robotics. Helped architect Kiva's warehouse execution system.",
          "roles": [
              ("6-river-systems", "co-founder", 2015, 2023),
              ("kiva-systems", "product_lead", 2005, 2015),
          ]},
    ]

    for p in people_data:
        conn.execute("""INSERT OR IGNORE INTO people (name, slug, title, bio) VALUES (?, ?, ?, ?)""",
                     (p["name"], p["slug"], p["title"], p["bio"]))
        person_row = conn.execute("SELECT id FROM people WHERE slug = ?", (p["slug"],)).fetchone()
        if not person_row:
            continue
        person_id = person_row[0]
        for entity_slug, role, start_year, end_year in p.get("roles", []):
            entity_id = None
            entity_type = "company"
            row = conn.execute("SELECT id FROM companies WHERE slug = ?", (entity_slug,)).fetchone()
            if row:
                entity_id = row[0]
            if not entity_id:
                row = conn.execute("SELECT id FROM people WHERE slug = ?", (entity_slug,)).fetchone()
                if row:
                    entity_id = row[0]
                    entity_type = "person"
            if entity_id:
                conn.execute("""INSERT OR IGNORE INTO person_roles
                                (person_id, entity_id, entity_type, role, start_year, end_year)
                                VALUES (?, ?, ?, ?, ?, ?)""",
                             (person_id, entity_id, entity_type, role, start_year, end_year))

    conn.commit()

def seed_bins(conn):
    bins = [
        # --- AutoStore R5 ---
        ("autostore-r5", "tote", "Standard Bin 330", 449, 345, 330, 400, 300, 310, 30, 8.0, "Widest bin, moderate height"),
        ("autostore-r5", "tote", "Standard Bin 425", 449, 345, 425, 400, 300, 405, 30, 8.0, "Deep bin, high-volume storage"),
        ("autostore-r5", "tote", "Standard Bin 220", 449, 345, 220, 400, 300, 200, 20, 8.0, "Shallow bin, fast access"),
        ("autostore-r5", "tote", "Small Bin 135", 299, 299, 135, 270, 270, 120, 15, 8.0, "Quarter-format small bin"),
        # --- AutoStore R5+ ---
        ("autostore-r5plus", "tote", "Standard Bin 425", 449, 345, 425, 400, 300, 405, 35, 12.0, "R5+ supports taller grid"),
        ("autostore-r5plus", "tote", "Standard Bin 330", 449, 345, 330, 400, 300, 310, 35, 12.0, ""),
        ("autostore-r5plus", "tote", "Standard Bin 220", 449, 345, 220, 400, 300, 200, 25, 12.0, ""),
        # --- AutoStore R5Pro ---
        ("autostore-r5pro", "tote", "Standard Bin 425", 449, 345, 425, 400, 300, 405, 50, 16.0, "R5Pro supports 50kg payload, tallest grid"),
        ("autostore-r5pro", "tote", "Standard Bin 330", 449, 345, 330, 400, 300, 310, 50, 16.0, ""),
        ("autostore-r5pro", "tote", "Standard Bin 220", 449, 345, 220, 400, 300, 200, 35, 16.0, ""),

        # --- Exotec Skypod ---
        ("exotec-skypod", "tote", "Skypod Bin 600×400", 600, 400, 350, 570, 370, 330, 30, 12.0, "Euro-format bin, 3 standard heights"),
        ("exotec-skypod", "tote", "Skypod Bin 600×400 Shallow", 600, 400, 200, 570, 370, 180, 30, 12.0, ""),
        ("exotec-skypod", "tote", "Skypod Bin 600×400 Deep", 600, 400, 420, 570, 370, 400, 30, 12.0, ""),

        # --- HAI Robotics HaiPick ACR ---
        ("haipick-acr", "tote", "Standard Tote 600×400", 600, 400, 350, 570, 370, 330, 35, 12.0, "Case/tote handling on 12m racks"),
        ("haipick-acr", "case", "Standard Carton", 600, 400, 450, 570, 370, 430, 50, 12.0, "Direct carton handling"),
        ("haipick-acr", "tote", "Small Tote 400×300", 400, 300, 250, 370, 270, 230, 25, 12.0, ""),

        # --- HAI Robotics HaiPick Climb ---
        ("haipick-climb", "tote", "Climb Tote 600×400", 600, 400, 350, 570, 370, 330, 35, 12.0, "Climb system tall grid storage"),

        # --- Symbotic System ---
        ("symbotic-system", "pallet", "Standard Pallet", 1200, 1000, 1800, 1160, 960, 1700, 1500, None, "Full pallet handling"),
        ("symbotic-system", "case", "Case", 600, 400, 400, 570, 370, 380, 50, None, "Case-level pick/palletize"),

        # --- Geek+ P500R (shelf-carrying) ---
        ("geekplus-p500r", "shelf", "Shelf Pod Std", 900, 700, 1800, None, None, None, 500, None, "Standard shelf pod with 4 shelves"),
        ("geekplus-p500r", "shelf", "Shelf Pod Tall", 900, 700, 2400, None, None, None, 500, None, "Tall pod with 5-6 shelves"),

        # --- Geek+ P1200R ---
        ("geekplus-p1200r", "shelf", "Shelf Pod Double", 1200, 1000, 2200, None, None, None, 1200, None, "Large pod for bulky items"),

        # --- Geek+ RS Air (shuttle) ---
        ("geekplus-rs-air", "tote", "Shuttle Tote Std", 600, 400, 350, 570, 370, 330, 30, 8.0, "Standard shuttle tote"),

        # --- GreyOrange Ranger ---
        ("greyorange-ranger", "tote", "Ranger Tote", 600, 400, 350, 570, 370, 330, 50, 10.0, "Flexi-tote handling"),
        ("greyorange-ranger", "case", "Mixed Case", 600, 400, 450, None, None, None, 50, 10.0, "Mixed case handling"),

        # --- Fetch CartConnect 500 ---
        ("fetch-cartconnect-500", "shelf", "Cart Shelf", 900, 700, 1700, None, None, None, 500, None, "Tote shelf cart"),

        # --- Fetch Freight 500 ---
        ("fetch-freight-500", "pallet", "Pallet 1200×800", 1200, 800, 1800, None, None, None, 500, None, "Euro pallet"),
        ("fetch-freight-500", "pallet", "Pallet 1200×1000", 1200, 1000, 1800, None, None, None, 500, None, "Standard pallet"),

        # --- Fetch Freight 1500 ---
        ("fetch-freight-1500", "pallet", "Pallet 1200×800", 1200, 800, 1800, None, None, None, 1500, None, "Heavy pallet"),
        ("fetch-freight-1500", "pallet", "Pallet 1200×1000", 1200, 1000, 1800, None, None, None, 1500, None, ""),

        # --- KUKA KR QUANTEC ---
        ("kuka-kr-quantec-210", "pallet", "Pallet Standard", 1200, 1000, 2000, None, None, None, 210, None, "Industrial palletizing"),
        ("kuka-kr-quantec-210", "case", "Case Standard", 600, 400, 400, None, None, None, 50, None, "Case palletizing"),

        # --- KUKA KR FORTEC ---
        ("kuka-kr-fortec-500", "pallet", "Pallet Heavy", 1200, 1000, 2400, None, None, None, 500, None, "Heavy pallet handling"),

        # --- FANUC CRX ---
        ("fanuc-crx-10ia", "pallet", "Pallet Standard", 1200, 1000, 2000, None, None, None, 10, None, "Collaborative palletizing"),

        # --- ABB IRB 1300 ---
        ("abb-irb-1300", "pallet", "Pallet Standard", 1200, 1000, 2000, None, None, None, 130, None, "Industrial palletizing"),

        # --- MiR250 ---
        ("mir250", "top_plate", "Top Plate", 900, 700, None, None, None, None, 250, None, "Flat top with optional bin/shelf"),

        # --- MiR500 ---
        ("mir500", "top_plate", "Top Plate", 1300, 900, None, None, None, None, 500, None, "Flat top with pallet adapter"),

        # --- Chuck AMR (6 River Systems) ---
        ("chuck-amr", "tote", "Chuck Tote", 600, 400, 350, None, None, None, 50, None, "Collaborative picking tote"),
        ("chuck-amr", "shelf", "Chuck Shelf", 900, 600, 1500, None, None, None, 100, None, "Multi-shelf cart"),

        # --- Boston Dynamics Stretch ---
        ("boston-dynamics-stretch", "case", "Case Mixed", 600, 400, 500, None, None, None, 50, None, "Case movement"),

        # --- Pickle Truck Unloader ---
        ("pickle-truck-unloader", "package", "Package", 610, 610, 810, None, None, None, 23, None, "Mixed package sizes up to 50lbs"),

        # --- Amazon Proteus ---
        ("amazon-proteus", "top_plate", "GoCart Adapter", 1200, 900, None, None, None, None, 680, None, "Hauls Amazon go-carts"),

        # --- Amazon Hercules ---
        ("amazon-hercules", "pallet", "Pallet Standard", 1200, 1000, 1800, None, None, None, 1500, None, "Heavy pod/pallet drive unit"),

        # --- Kiva Systems Drive Unit ---
        ("kiva-systems-drive-unit", "shelf", "Pod Standard", 1200, 1000, 2200, None, None, None, 1000, None, "Original Kiva pod system"),
    ]

    for b in bins:
        prod_slug, bin_type, label, ol, ow, oh, il, iw, ih, payload, grid_h, notes = b
        prod_row = conn.execute("SELECT id FROM products WHERE slug = ?", (prod_slug,)).fetchone()
        if not prod_row:
            continue
        conn.execute("""INSERT INTO product_bins
                        (product_id, bin_type, label, outer_length_mm, outer_width_mm, outer_height_mm,
                         inner_length_mm, inner_width_mm, inner_height_mm, max_payload_kg, grid_height_m, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (prod_row[0], bin_type, label, ol, ow, oh, il, iw, ih, payload, grid_h, notes))

    conn.commit()

def seed_additional_products(conn):
    """Seed Chinese robotics products + Boston Dynamics Atlas (Humanoid)."""
    products_data = [
        # --- PUDU ---
        {
            "company_slug": "pudu-robotics",
            "name": "BellaBot Pro",
            "slug": "bellabot-pro",
            "description": "Indoor delivery robot with cat-inspired design, four trays, dual SLAM navigation (laser + visual), AI voice interaction, and a 10.1+18.5-inch dual-screen setup. Designed for restaurants, retail, and hospitality. 120,000+ units shipped globally.",
            "category": "AMR",
            "subcategory": "Service Delivery Robot",
            "product_url": "https://www.pudurobotics.com/products/bellabotpro",
            "release_year": 2020,
            "specs": [
                ("payload_capacity_metric", "40", "kg"),
                ("dimensions", "570x550x1290", "mm"),
                ("robot_weight", "57", "kg"),
                ("max_speed", "1.2", "m/s"),
                ("battery_life", "11", "h"),
                ("charge_time", "4.5", "h"),
                ("navigation_type", "Laser SLAM + Visual SLAM", ""),
                ("battery_type", "Li-Ion", ""),
                ("ip_class", "IP20", ""),
                ("sensors", "LiDAR + RGB-D Camera + Ultrasonic", ""),
            ],
            "capabilities": ["Autonomous Delivery", "Cruise Mode", "Guest Escorting", "Voice Interaction", "Advertising Display", "Multi-floor Operation", "Obstacle Avoidance"],
        },
        {
            "company_slug": "pudu-robotics",
            "name": "KettyBot",
            "slug": "kettybot",
            "description": "Compact delivery and reception robot with an 18.5-inch advertising screen. Features dual SLAM navigation, ultra-narrow 55cm path clearance, and AI voice interaction. Suitable for restaurants, retail, hotels, and supermarkets.",
            "category": "AMR",
            "subcategory": "Service Delivery Robot",
            "product_url": "https://www.pudurobotics.com/products/kettybot",
            "release_year": 2021,
            "specs": [
                ("payload_capacity_metric", "30", "kg"),
                ("dimensions", "451x436x1103", "mm"),
                ("robot_weight", "38", "kg"),
                ("max_speed", "1.2", "m/s"),
                ("battery_life", "8", "h"),
                ("charge_time", "4.5", "h"),
                ("navigation_type", "Laser SLAM + Visual SLAM", ""),
            ],
            "capabilities": ["Autonomous Delivery", "Reception & Greeting", "Cruise Mode", "Advertising Display", "Voice Interaction", "Guest Escorting"],
        },
        {
            "company_slug": "pudu-robotics",
            "name": "SwiftBot",
            "slug": "swiftbot",
            "description": "Indoor delivery robot with enclosed compartments featuring auto-open/close doors, a laser projector for customer engagement, voice interaction, and SLAM positioning. Supports IoT connectivity and peripheral expansion.",
            "category": "AMR",
            "subcategory": "Service Delivery Robot",
            "product_url": "https://www.pudurobotics.com/products/swiftbot",
            "release_year": 2022,
            "specs": [
                ("payload_capacity_metric", "15", "kg"),
                ("dimensions", "593x485x1277", "mm"),
                ("robot_weight", "55-65", "kg"),
                ("max_speed", "1.2", "m/s"),
                ("battery_life", "9", "h"),
                ("charge_time", "4.5", "h"),
                ("navigation_type", "Laser + Visual SLAM", ""),
            ],
            "capabilities": ["Enclosed Autonomous Delivery", "Voice Interaction", "Laser Projection", "Multi-floor Operation", "IoT Connectivity"],
        },
        {
            "company_slug": "pudu-robotics",
            "name": "PUDU T300",
            "slug": "pudu-t300",
            "description": "Heavy-duty autonomous mobile robot for industrial material transport. Capable of hauling up to 300kg with VSLAM+ and LiDAR SLAM navigation. ISO 3691-4 safety compliant with 360-degree omni-sense safety system.",
            "category": "AMR",
            "subcategory": "Industrial AMR",
            "product_url": "https://www.pudurobotics.com/products/pudu-t300",
            "release_year": 2024,
            "specs": [
                ("payload_capacity_metric", "300", "kg"),
                ("dimensions", "835x500x1350", "mm"),
                ("robot_weight", "65", "kg"),
                ("max_speed", "1.2", "m/s"),
                ("battery_life", "12", "h"),
                ("charge_time", "2", "h"),
                ("navigation_type", "VSLAM + LiDAR SLAM", ""),
                ("operating_temp_range", "0-40", "°C"),
            ],
            "capabilities": ["Industrial Material Transport", "Auto-follow Mode", "Power-assist Mode", "Multi-floor Operation", "Fleet Learning"],
        },
        # --- QUICKTRON ---
        {
            "company_slug": "quicktron",
            "name": "QuickBin Ultra",
            "slug": "quickbin-ultra",
            "description": "Flagship bin-to-person solution combining M5E mobile robots and A5 intelligent lift system. Dramatically enhances order picking speed and storage density with 4.5m/s robot speed and 860mm aisle width.",
            "category": "ASRS",
            "subcategory": "Bin-to-Person System",
            "product_url": "https://www.quicktron.com/en_US/landing/quick-bin-ultra",
            "release_year": 2023,
            "specs": [
                ("payload_capacity_metric", "50", "kg"),
                ("max_speed", "4.5", "m/s"),
                ("battery_life", "12", "h"),
                ("charge_time", "1.5", "h"),
                ("dimensions", "683x460x1150", "mm"),
                ("throughput", "40-45", "bins/hour"),
                ("stop_accuracy", "±10", "mm"),
                ("navigation_type", "QR Code + Inertial", ""),
            ],
            "capabilities": ["Bin-to-Person", "Goods-to-Person", "High-density Bin Storage", "Multi-robot Collaboration", "Real-time Inventory Tracking"],
        },
        {
            "company_slug": "quicktron",
            "name": "QuickMove M-Series",
            "slug": "quickmove-m-series",
            "description": "Autonomous mobile robot series for material handling with payloads from 30kg to 1500kg. Features QR code navigation, high positioning accuracy, and modular payload configurations for flexible intralogistics.",
            "category": "AMR",
            "subcategory": "Warehouse AMR",
            "product_url": "https://www.quicktron.com/products/m-series",
            "release_year": 2020,
            "specs": [
                ("payload_capacity_metric", "1500", "kg"),
                ("max_speed", "4.5", "m/s"),
                ("battery_life", "12", "h"),
                ("navigation_type", "QR Code + Inertial", ""),
                ("stop_accuracy", "±10", "mm"),
            ],
            "capabilities": ["Material Handling", "Transport", "QR Navigation", "Multi-robot Collaboration"],
        },
        # --- MEGVII ---
        {
            "company_slug": "megvii-robotics",
            "name": "MegBot-MN Miniload AS/RS",
            "slug": "megbot-mn",
            "description": "AI-powered mini load automated storage and retrieval system for high-density bin storage. Features 360m/min walk speed and 180m/min lifting speed with height adaptability from 3 to 14 meters.",
            "category": "ASRS",
            "subcategory": "Miniload AS/RS",
            "product_url": "https://en-robotics.megvii.com/asrs-49.html",
            "release_year": 2020,
            "specs": [
                ("max_speed", "360", "m/min"),
                ("max_operating_height", "14", "m"),
                ("storage_density", "High", ""),
                ("navigation_type", "Rail-guided", ""),
            ],
            "capabilities": ["High-density Bin Storage", "Automated Storage & Retrieval", "AI-optimized Scheduling", "Tote Handling"],
        },
        {
            "company_slug": "megvii-robotics",
            "name": "3D Pallet Shuttle System",
            "slug": "megvii-3d-pallet-shuttle",
            "description": "Intelligent 3D pallet shuttle system for high-density pallet storage with distributed control architecture and AI-powered Hetu scheduling. Deployed in hundreds of units for new energy, food, pharmaceutical, and manufacturing industries.",
            "category": "ASRS",
            "subcategory": "Pallet Shuttle",
            "product_url": "https://en-robotics.megvii.com/asrs-47.html",
            "release_year": 2022,
            "specs": [
                ("payload_capacity_metric", "1500", "kg"),
                ("max_speed", "180", "m/min"),
                ("navigation_type", "Rail-guided 4-way", ""),
            ],
            "capabilities": ["High-density Storage", "Pallet Handling", "AI-optimized Scheduling", "Automated Inbound/Outbound"],
        },
        # --- DOBOT ---
        {
            "company_slug": "dobot",
            "name": "CR5",
            "slug": "dobot-cr5",
            "description": "6-axis collaborative robot with 5kg payload and 900mm working radius. Features ±0.02mm repeatability, drag-to-teach programming, multi-level collision detection, and supports inspection, assembly, screwdriving, and bin picking.",
            "category": "Cobot",
            "subcategory": "6-Axis Collaborative Robot",
            "product_url": "https://www.dobot-robots.com/products/cr-series/cr5.html",
            "release_year": 2021,
            "specs": [
                ("payload_capacity_metric", "5", "kg"),
                ("robot_weight", "25", "kg"),
                ("max_reach", "900", "mm"),
                ("repeatability", "±0.02", "mm"),
                ("max_speed", "3.0", "m/s"),
                ("power_consumption", "150", "W"),
                ("ip_class", "IP54", ""),
                ("operating_temp_range", "0-45", "°C"),
            ],
            "capabilities": ["Drag-to-Teach Programming", "Collision Detection", "Precision Assembly", "Screwdriving", "Bin Picking", "Inspection", "Machine Tending"],
        },
        {
            "company_slug": "dobot",
            "name": "MG400",
            "slug": "dobot-mg400",
            "description": "Ultra-compact 4-axis desktop robotic arm with a footprint smaller than A4 paper. 750g payload, 440mm reach, drag-to-teach, and collision detection. Ideal for small-batch flexible production.",
            "category": "Cobot",
            "subcategory": "Desktop 4-Axis Cobot",
            "product_url": "https://www.dobot-robots.com/products/desktop-four-axis/mg400.html",
            "release_year": 2021,
            "specs": [
                ("payload_capacity_metric", "0.75", "kg"),
                ("robot_weight", "8", "kg"),
                ("max_reach", "440", "mm"),
                ("repeatability", "±0.05", "mm"),
                ("power_consumption", "150", "W"),
                ("operating_temp_range", "0-40", "°C"),
            ],
            "capabilities": ["Drag-to-Teach Programming", "Collision Detection", "Precision Assembly", "Screwdriving", "Bin Picking"],
        },
        # --- SIASUN ---
        {
            "company_slug": "siasun",
            "name": "SR25A-25/1.80",
            "slug": "siasun-sr25a-25",
            "description": "Six-axis industrial robot with 25kg payload and 1803mm reach. Features hollow arm design, high-stiffness lightweight structure for high-precision welding, cutting, handling, and assembly.",
            "category": "Industrial Robot",
            "subcategory": "6-Axis Articulated Robot",
            "product_url": "https://en.siasun.com/sr25a-12-2-01-2.html",
            "release_year": 2022,
            "specs": [
                ("payload_capacity_metric", "25", "kg"),
                ("max_reach", "1803", "mm"),
                ("repeatability", "±0.05", "mm"),
                ("ip_class", "IP65", ""),
            ],
            "capabilities": ["Arc Welding", "Cutting", "Material Handling", "Grinding & Polishing", "Loading & Unloading"],
        },
        {
            "company_slug": "siasun",
            "name": "GCR5-910 Collaborative Robot",
            "slug": "siasun-gcr5-910",
            "description": "High-end 6-axis collaborative robot with 5kg payload and 917mm reach. Features 16 TUV-certified safety functions, 2D/3D vision integration, force sensing, and drag-to-teach programming.",
            "category": "Cobot",
            "subcategory": "6-Axis Collaborative Robot",
            "product_url": "https://en.siasun.com/collaborative-robot-2.html",
            "release_year": 2021,
            "specs": [
                ("payload_capacity_metric", "5", "kg"),
                ("robot_weight", "22", "kg"),
                ("max_reach", "917", "mm"),
                ("repeatability", "±0.02", "mm"),
                ("max_speed", "1.0", "m/s"),
                ("ip_class", "IP54", ""),
                ("operating_temp_range", "-10 to 45", "°C"),
                ("uptime", "35000", "h"),
            ],
            "capabilities": ["Safe Human-Robot Collaboration", "Drag-to-Teach Programming", "Vision Integration", "Force Sensing", "Quality Inspection", "Screw Fastening"],
        },
        # --- UBTECH ---
        {
            "company_slug": "ubtech",
            "name": "Walker S",
            "slug": "ubtech-walker-s",
            "description": "Industrial humanoid robot with 41 servo joints and force feedback, designed for real automotive production lines. Integrated with LLM, RGB-D perception, 3D semantic mapping, and ROSA 2.0 platform. Deployed at NIO manufacturing facilities.",
            "category": "Humanoid",
            "subcategory": "Industrial Humanoid",
            "product_url": "https://www.ubtrobot.com/en/products/walker-s",
            "release_year": 2023,
            "specs": [
                ("payload_capacity_metric", "15", "kg"),
                ("max_speed", "0.8", "m/s"),
                ("battery_life", "2", "h"),
                ("dimensions", "1700x500x300", "mm"),
                ("robot_weight", "77", "kg"),
                ("navigation_type", "U-SLAM + 3D Point Cloud", ""),
                ("sensors", "RGB-D, 3D LiDAR, Force-torque, IMU", ""),
                ("degrees_of_freedom", "41", ""),
            ],
            "capabilities": ["Bipedal Walking", "Autonomous Navigation", "Visual Inspection", "Assembly Operations", "Material Handling", "LLM-based Interaction", "Factory Integration"],
        },
        {
            "company_slug": "ubtech",
            "name": "Yanshee",
            "slug": "ubtech-yanshee",
            "description": "Open-source humanoid robot platform designed for AI education and programming learning. Supports Python, Blockly, and C++ with a modular design for STEM education.",
            "category": "Humanoid",
            "subcategory": "Educational Humanoid",
            "product_url": "https://www.ubtrobot.com/en/products/yanshee",
            "release_year": 2018,
            "specs": [
                ("robot_weight", "~2", "kg"),
                ("degrees_of_freedom", "17", ""),
                ("battery_life", "1-2", "h"),
                ("sensors", "Ultrasonic, IR, Gyroscope, Accelerometer", ""),
            ],
            "capabilities": ["Open-source Programming", "AI Education", "Voice Interaction", "Vision Recognition", "Obstacle Avoidance"],
        },
        # --- UNITREE ---
        {
            "company_slug": "unitree",
            "name": "Go2",
            "slug": "unitree-go2",
            "description": "Intelligent quadruped robot dog with 4D LiDAR L1 for 360×90-degree hemispherical recognition. Up to 5m/s running speed with 12kg payload capacity. Available in Air, Pro, and EDU variants.",
            "category": "AMR",
            "subcategory": "Quadruped Robot",
            "product_url": "https://www.unitree.com/go2",
            "release_year": 2023,
            "specs": [
                ("payload_capacity_metric", "12", "kg"),
                ("robot_weight", "15", "kg"),
                ("max_speed", "5.0", "m/s"),
                ("battery_life", "4", "h"),
                ("max_operating_height", "16", "cm"),
                ("dimensions", "700x310x400", "mm"),
                ("sensors", "4D LiDAR L1 + Depth Cameras", ""),
                ("operating_temp_range", "-10 to 45", "°C"),
            ],
            "capabilities": ["All-terrain Locomotion", "Autonomous Navigation", "Obstacle Avoidance", "Voice Interaction", "Secondary Development", "Industrial Inspection", "Security Patrol"],
        },
        {
            "company_slug": "unitree",
            "name": "H1",
            "slug": "unitree-h1",
            "description": "Full-size general-purpose humanoid robot with world-record running speed of 3.3m/s. Features 360N.m knee torque, 864Wh battery, 3D LiDAR + depth camera perception, and potential mobility exceeding 5m/s.",
            "category": "Humanoid",
            "subcategory": "General-purpose Humanoid",
            "product_url": "https://www.unitree.com/h1",
            "release_year": 2024,
            "specs": [
                ("payload_capacity_metric", "30", "kg"),
                ("robot_weight", "47", "kg"),
                ("max_speed", "3.3", "m/s"),
                ("battery_life", "2", "h"),
                ("dimensions", "1800x500x300", "mm"),
                ("sensors", "3D LiDAR + Depth Camera", ""),
                ("degrees_of_freedom", "18", ""),
            ],
            "capabilities": ["Bipedal Running", "Bipedal Walking", "Autonomous Navigation", "Obstacle Avoidance", "Secondary Development"],
        },
        # --- AUBO ---
        {
            "company_slug": "aubo",
            "name": "AUBO-i5",
            "slug": "aubo-i5",
            "description": "6-axis collaborative robot with 5kg payload, 886.5mm reach, and ±0.02mm repeatability. Features hand-guiding teaching, collision detection, and any-angle mounting for assembly, screwdriving, and machine tending.",
            "category": "Cobot",
            "subcategory": "6-Axis Collaborative Robot",
            "product_url": "https://www.aubo-cobot.com/public/i5product4",
            "release_year": 2017,
            "specs": [
                ("payload_capacity_metric", "5", "kg"),
                ("robot_weight", "24", "kg"),
                ("max_reach", "886.5", "mm"),
                ("repeatability", "±0.02", "mm"),
                ("max_speed", "2.8", "m/s"),
                ("power_consumption", "200", "W"),
                ("ip_class", "IP54", ""),
                ("operating_temp_range", "0-50", "°C"),
            ],
            "capabilities": ["Hand-guiding Teaching", "Collision Detection", "Precision Assembly", "Screwdriving", "Machine Tending", "Palletizing"],
        },
        {
            "company_slug": "aubo",
            "name": "AUBO-i10",
            "slug": "aubo-i10",
            "description": "6-axis collaborative robot with 10kg payload and 1350mm reach, AUBO's longest-reach cobot. ±0.03mm repeatability and 4.0m/s tool velocity for palletizing, welding, and machine tending.",
            "category": "Cobot",
            "subcategory": "6-Axis Collaborative Robot",
            "product_url": "https://www.aubo-cobot.com/public/i5product4?CPID=i10",
            "release_year": 2018,
            "specs": [
                ("payload_capacity_metric", "10", "kg"),
                ("robot_weight", "38.5", "kg"),
                ("max_reach", "1350", "mm"),
                ("repeatability", "±0.03", "mm"),
                ("max_speed", "4.0", "m/s"),
                ("power_consumption", "500", "W"),
                ("ip_class", "IP54", ""),
                ("operating_temp_range", "0-50", "°C"),
            ],
            "capabilities": ["Hand-guiding Teaching", "Collision Detection", "Palletizing", "Machine Tending", "Material Handling"],
        },
        # --- GAUSSIAN ROBOTICS ---
        {
            "company_slug": "gaussian-robotics",
            "name": "Scrubber 75",
            "slug": "gausium-scrubber-75",
            "description": "Industrial-grade autonomous floor scrubbing robot with 750mm cleaning width, 3000m²/h theoretical efficiency, and 45kg brush pressure. Features 20+ sensors and 270-degree rotational scrub deck.",
            "category": "Cleaning Robot",
            "subcategory": "Industrial Floor Scrubber",
            "product_url": "https://gausium.com/products/scrubber-75/",
            "release_year": 2019,
            "specs": [
                ("robot_weight", "400", "kg"),
                ("dimensions", "1370x962x1417", "mm"),
                ("max_speed", "1.1", "m/s"),
                ("battery_life", "6", "h"),
                ("charge_time", "5", "h"),
                ("battery_type", "Lithium Iron Phosphate", ""),
                ("sensors", "3D LiDAR, 2D LiDAR, 3D Camera, Ultrasonic", ""),
                ("operating_temp_range", "0-40", "°C"),
                ("navigation_type", "SLAM + LiDAR", ""),
            ],
            "capabilities": ["Autonomous Floor Scrubbing", "Edge-to-Edge Cleaning", "Oil Stain Cleaning Mode", "Auto Charging & Water Refill", "Remote Monitoring", "IoT Fleet Management"],
        },
        {
            "company_slug": "gaussian-robotics",
            "name": "ECOBOT Sprayer 50",
            "slug": "gausium-sprayer-50",
            "description": "Compact autonomous cleaning and sanitizing robot combining scrubbing, sweeping, dust mopping, and disinfectant spraying in one platform. Ultra-fine atomization at 5 micron for comprehensive hygienic care.",
            "category": "Cleaning Robot",
            "subcategory": "Autonomous Sanitizing Robot",
            "product_url": "https://www.gaussianrobotics.com/ecobotsprayer50",
            "release_year": 2021,
            "specs": [
                ("robot_weight", "214", "kg"),
                ("dimensions", "860x700x1030", "mm"),
                ("battery_life", "3", "h"),
                ("max_speed", "1.0", "m/s"),
                ("sensors", "LiDAR, 3D Camera, Ultrasonic", ""),
            ],
            "capabilities": ["Autonomous Floor Scrubbing", "Sweeping", "Dust Mopping", "Disinfectant Spraying", "Auto Charging & Water Refill", "Remote Monitoring"],
        },
        # --- ESTUN ---
        {
            "company_slug": "estun-automation",
            "name": "ER220-3100",
            "slug": "estun-er220-3100",
            "description": "Heavy-duty 6-axis industrial robot with 220kg payload and 3100mm reach. High-rigidity structure with ±0.06mm repeatability for material handling, palletizing, and large-part assembly in automotive and heavy manufacturing.",
            "category": "Industrial Robot",
            "subcategory": "6-Axis Heavy Payload Robot",
            "product_url": "https://en.estun.com",
            "release_year": 2020,
            "specs": [
                ("payload_capacity_metric", "220", "kg"),
                ("max_reach", "3100", "mm"),
                ("repeatability", "±0.06", "mm"),
                ("robot_weight", "1345", "kg"),
                ("ip_class", "IP54", ""),
            ],
            "capabilities": ["Heavy Material Handling", "Palletizing", "Machine Tending", "Loading & Unloading"],
        },
        {
            "company_slug": "estun-automation",
            "name": "ER7-910",
            "slug": "estun-er7-910",
            "description": "Compact 6-axis industrial robot with 7kg payload and 910mm reach. Ideal for welding, handling, and assembly in 3C electronics, metal processing, and packaging applications.",
            "category": "Industrial Robot",
            "subcategory": "6-Axis Articulated Robot",
            "product_url": "https://en.estun.com",
            "release_year": 2015,
            "specs": [
                ("payload_capacity_metric", "7", "kg"),
                ("max_reach", "910", "mm"),
            ],
            "capabilities": ["Arc Welding", "Material Handling", "Loading & Unloading", "Machine Tending"],
        },
        # --- BOSTON DYNAMICS ATLAS ---
        {
            "company_slug": "boston-dynamics",
            "name": "Atlas (Electric)",
            "slug": "atlas-electric",
            "description": "Enterprise-grade fully electric humanoid robot designed for industrial automation. Features 56 DOF with continuous joint rotation, 50kg instant payload, self-swappable batteries, fenceless safety system, and IP67 rating.",
            "category": "Humanoid",
            "subcategory": "Industrial Humanoid",
            "product_url": "https://bostondynamics.com/products/atlas/",
            "release_year": 2024,
            "specs": [
                ("payload_capacity_metric", "50", "kg"),
                ("robot_weight", "90", "kg"),
                ("max_reach", "2300", "mm"),
                ("battery_life", "4", "h"),
                ("charge_time", "1.5", "h"),
                ("dimensions", "1900x800x600", "mm"),
                ("max_speed", "2.5", "m/s"),
                ("degrees_of_freedom", "56", ""),
                ("ip_class", "IP67", ""),
                ("operating_temp_range", "-20 to 40", "°C"),
                ("sensors", "360° camera view, Tactile fingers/palm", ""),
                ("navigation_type", "360° perception + SLAM", ""),
            ],
            "capabilities": ["Bipedal Walking", "Bipedal Running", "Heavy Lifting", "Autonomous Navigation", "Fenceless Operation", "Fleet Learning", "Orbit Integration", "VR Teleoperation", "Part Sequencing", "Machine Tending", "Order Fulfillment"],
        },
    ]

    existing_product_slugs = set(r["slug"] for r in conn.execute("SELECT slug FROM products").fetchall())
    for p in products_data:
        if p["slug"] in existing_product_slugs:
            continue
        cur = conn.execute("SELECT id FROM companies WHERE slug = ?", (p["company_slug"],))
        row = cur.fetchone()
        if not row:
            continue
        company_id = row[0]
        conn.execute("""INSERT INTO products (company_id, name, slug, description, category, subcategory, product_url, release_year, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (company_id, p["name"], p["slug"], p["description"],
                      p["category"], p["subcategory"], p["product_url"], p["release_year"],
                      "current"))

        cur = conn.execute("SELECT id FROM products WHERE slug = ?", (p["slug"],))
        product_id = cur.fetchone()[0]

        for spec_name, spec_value, unit in p["specs"]:
            conn.execute("""INSERT OR IGNORE INTO product_specs (product_id, spec_name, spec_value, unit, source)
                            VALUES (?, ?, ?, ?, ?)""",
                         (product_id, spec_name, spec_value, unit, "manual"))

        for cap_name in p["capabilities"]:
            cur = conn.execute("SELECT id FROM capabilities WHERE name = ?", (cap_name,))
            cap_row = cur.fetchone()
            if cap_row:
                conn.execute("INSERT OR IGNORE INTO product_capabilities (product_id, capability_id) VALUES (?, ?)",
                             (product_id, cap_row[0]))

    conn.commit()

def seed_customer_associations(conn):
    customers = conn.execute("""
        SELECT DISTINCT TRIM(customer) as customer_name
        FROM case_studies WHERE customer IS NOT NULL AND customer != ''
    """).fetchall()

    slug_map = {}
    for row in customers:
        raw = row["customer_name"]
        if raw in ("Amazon (Internal)", "Major Global 3PL", "Large Automotive Tier 1 Supplier",
                   "Major Fashion Distributor", "Major European Brewery"):
            continue
        if raw == "Amazon (Internal)":
            slug = "amazon"
        else:
            slug = raw.lower().replace(" ", "-").replace("/", "-").replace("&", "and").replace("--", "-").strip("-")
        slug_map[raw] = slug

        existing = conn.execute("SELECT id FROM companies WHERE slug = ?", (slug,)).fetchone()
        if not existing:
            conn.execute("""INSERT INTO companies (name, slug, company_type, short_description, status)
                            VALUES (?, ?, 'customer', ?, 'active')""",
                         (raw, slug, f"Customer of robotics companies"))
        else:
            cur_type = conn.execute("SELECT company_type FROM companies WHERE id=?", (existing[0],)).fetchone()
            if cur_type and cur_type[0] == "corporation":
                conn.execute("UPDATE companies SET company_type='customer' WHERE id=?", (existing[0],))

    case_rows = conn.execute("""
        SELECT cs.customer, c.slug as company_slug
        FROM case_studies cs
        JOIN companies c ON cs.company_id = c.id
        WHERE cs.customer IS NOT NULL AND cs.customer != ''
    """).fetchall()

    for cr in case_rows:
        raw = cr["customer"]
        if raw in ("Amazon (Internal)", "Major Global 3PL", "Large Automotive Tier 1 Supplier",
                   "Major Fashion Distributor", "Major European Brewery"):
            continue
        if raw == "Amazon (Internal)":
            cust_slug = "amazon"
        else:
            cust_slug = raw.lower().replace(" ", "-").replace("/", "-").replace("&", "and").replace("--", "-").strip("-")
        _link(conn, cust_slug, cr["company_slug"], "customer_of",
              f"{raw} uses {cr['company_slug']}")

def seed_case_studies(conn):
    case_studies_data = [
        # --- Pickle Robotics ---
        {
            "company_slug": "pickle-robotics",
            "product_slug": "pickle-truck-unloader",
            "title": "DHL Reduces Trailer Unload Time by 60% with Pickle Robot",
            "customer": "DHL Supply Chain",
            "industry": "Logistics / 3PL",
            "challenge": "DHL's distribution centers were facing labor shortages and ergonomic injuries from manual trailer unloading, with associates spending hours unloading trailers containing up to 2,000 packages each.",
            "solution": "Deployed Pickle Truck Unloading Robots at multiple DHL facilities. The autonomous mobile robots with KUKA arms unload trailers and shipping containers, handling packages from 6x6x6 to 24x24x32 inches.",
            "results": "Reduced trailer unloading time by 60%, cut ergonomic injury claims by 85%, and redeployed 8 associates per shift to higher-value tasks. Each robot averages 800+ picks per hour with minimal supervision.",
            "metrics": "60% faster unloading | 85% fewer injuries | 800+ picks/hr | 8 associates redeployed per shift",
            "url": "https://www.picklerobot.com/case-studies",
        },
        {
            "company_slug": "pickle-robotics",
            "product_slug": "pickle-truck-unloader",
            "title": "FedEx Ground Automates Trailer Unloading with Pickle's Mobile Robots",
            "customer": "FedEx Ground",
            "industry": "Parcel / Logistics",
            "challenge": "FedEx Ground needed to accelerate trailer unloading throughput during peak seasons while reducing physical strain on workers who manually unloaded thousands of packages per shift.",
            "solution": "Implemented Pickle Truck Unloading Robots across several FedEx Ground sortation facilities. The system handles mixed package flows directly from over-the-road trailers and delivery vans.",
            "results": "Throughout increased 45% during peak periods, with robots operating autonomously for up to 5 days after initial setup. Workers were reassigned to package sortation and exception handling, improving overall facility throughput by 35%.",
            "metrics": "45% peak throughput increase | 35% facility throughput gain | 5-day setup | 24/7 operation",
            "url": "https://www.picklerobot.com/case-studies",
        },
        # --- Locus Robotics ---
        {
            "company_slug": "locus-robotics",
            "product_slug": "locus-origin",
            "title": "DHL Deploys 5,000 Locus Robots Across Global Warehouses",
            "customer": "DHL Supply Chain",
            "industry": "Logistics / 3PL",
            "challenge": "DHL needed to scale its e-commerce fulfillment capacity globally while addressing labor shortages and rising wage costs. Existing pick-to-cart processes were inefficient and physically demanding.",
            "solution": "Deployed over 5,000 Locus Origin collaborative AMRs across dozens of DHL warehouses worldwide. The LocusONE platform handles order routing, fleet management, and WMS integration.",
            "results": "Productivity increased 2-3x across DHL facilities. Associate training time dropped from weeks to hours. DHL reported significantly reduced walking time — from 5+ miles per shift to under a mile — dramatically reducing associate fatigue.",
            "metrics": "2-3x productivity gain | 5,000+ robots deployed | <1 mile walking per shift | hours of training",
            "url": "https://locusrobotics.com/case-studies/dhl",
        },
        {
            "company_slug": "locus-robotics",
            "product_slug": "locus-origin",
            "title": "Boots UK Transforms Pharmacy Fulfillment with Locus Robotics",
            "customer": "Boots UK",
            "industry": "Pharmacy / Retail",
            "challenge": "Boots UK needed to modernize its pharmacy fulfillment operations to handle growing online prescription orders while maintaining accuracy and reducing associate travel time in large distribution centers.",
            "solution": "Deployed Locus Origin AMRs integrated with Boots' warehouse management system. Robots handle person-to-goods picking for both retail store replenishment and direct-to-patient pharmacy orders.",
            "results": "Picking productivity improved 3x, order accuracy exceeded 99.9%, and the system handled 100% of peak season volume without additional temporary staffing. Associates reported 90%+ satisfaction with the collaborative robot interface.",
            "metrics": "3x productivity | 99.9%+ accuracy | 100% peak volume | 90%+ associate satisfaction",
            "url": "https://locusrobotics.com/case-studies/boots",
        },
        {
            "company_slug": "locus-robotics",
            "product_slug": "locus-vector",
            "title": "Material Bank Handles 2,000% Growth with Locus Vector AMRs",
            "customer": "Material Bank",
            "industry": "Building Materials / E-commerce",
            "challenge": "Material Bank experienced explosive growth (2,000% in 3 years) in their overnight sample delivery business. Manual material handling of heavy sample boxes was causing bottlenecks and worker fatigue.",
            "solution": "Deployed Locus Vector heavy-duty AMRs to transport pallets and heavy cases between receiving, storage, and shipping zones. Robots integrated with the facility's existing conveyor systems and WMS.",
            "results": "Throughput increased 400% without facility expansion. The Vectors handle 90% of inter-zone transport, eliminating 12 miles of daily walking per associate. Overtime costs dropped 35%.",
            "metrics": "400% throughput gain | 90% transport automated | 12 miles/day walking eliminated | 35% overtime reduction",
            "url": "https://locusrobotics.com/case-studies/material-bank",
        },
        # --- Geek+ ---
        {
            "company_slug": "geekplus",
            "product_slug": "geekplus-p500r",
            "title": "Decathlon Deploys 1,000+ Geek+ Robots Across European Warehouses",
            "customer": "Decathlon",
            "industry": "Sporting Goods / Retail",
            "challenge": "Decathlon's rapid e-commerce growth required a scalable, flexible automation solution that could handle seasonality and a wide variety of product sizes (from small accessories to large sporting equipment).",
            "solution": "Deployed over 1,000 Geek+ P500R and P1200R goods-to-person robots across multiple European distribution centers. Robots bring entire shelving pods to ergonomic picking stations, enabling batch picking for multiple orders.",
            "results": "Picking efficiency increased 3-5x, storage density improved by 40%, and Decathlon was able to postpone a planned warehouse expansion by 3 years. The system processes 100,000+ picks per day during peak season.",
            "metrics": "3-5x picking efficiency | 40% more storage density | 100K+ picks/day | 3-year expansion delay",
            "url": "https://www.geekplus.com/case-studies",
        },
        {
            "company_slug": "geekplus",
            "product_slug": "geekplus-rs-air",
            "title": "Zara Parent Inditex Automates High-Density Storage with Geek+ RS Air",
            "customer": "Inditex (Zara)",
            "industry": "Fast Fashion / Retail",
            "challenge": "Inditex needed to increase order fulfillment speed for its fast-fashion e-commerce operations while maximizing storage density in existing warehouse footprint. Manual tote retrieval from high-bay racking was slow.",
            "solution": "Installed Geek+ RS Air (RoboShuttle) totes-to-person system across multiple floors of Inditex distribution centers. Robots navigate multi-level racking at 4.5 m/s, retrieving totes on demand.",
            "results": "Order-to-dispatch time dropped from 4 hours to 45 minutes. Storage density increased 300% compared to manual shelving. The system handles 50,000 totes per day across 12-meter-high racks.",
            "metrics": "4hr to 45min dispatch time | 300% storage density | 50,000 totes/day | 4.5 m/s robot speed",
            "url": "https://www.geekplus.com/case-studies",
        },
        {
            "company_slug": "geekplus",
            "product_slug": "geekplus-p1200r",
            "title": "Walmart Canada Deploys Geek+ for Retail Replenishment",
            "customer": "Walmart Canada",
            "industry": "Retail / Grocery",
            "challenge": "Walmart Canada's distribution centers needed to automate the replenishment process to stores, handling heavy pallets and large volumes of mixed-SKU cases in a high-throughput environment.",
            "solution": "Deployed Geek+ P1200R heavy-duty goods-to-person robots with 1,200 kg payload capacity to automate pallet and shelf replenishment workflows across multiple DCs.",
            "results": "Replenishment throughput increased 250% with 99.5% accuracy. The system handles 2,000+ SKUs per hour and reduced order cycle time from 24 hours to 6 hours for store replenishment.",
            "metrics": "250% throughput | 99.5% accuracy | 2,000+ SKUs/hr | 6-hour cycle time",
            "url": "https://www.geekplus.com/case-studies",
        },
        # --- HAI Robotics ---
        {
            "company_slug": "hai-robotics",
            "product_slug": "haipick-acr",
            "title": "Ingram Micro Doubles Fulfillment Capacity with HaiPick ACR",
            "customer": "Ingram Micro",
            "industry": "IT Distribution / 3PL",
            "challenge": "Ingram Micro's Singapore distribution center was running out of capacity and struggling to keep up with 24-hour SLA commitments for IT equipment distribution across Asia-Pacific.",
            "solution": "Deployed HaiPick ACR (Autonomous Case-handling Robot) system with 12-meter-tall racking. The ACR robots navigate standard racking aisles, retrieve cases and totes, and batch-deliver up to 9 containers simultaneously.",
            "results": "Fulfillment capacity doubled within the same footprint. Picking productivity increased 400%, storage density improved 350%, and SLA compliance reached 99.9%. The system paid for itself in 18 months.",
            "metrics": "2x capacity | 400% picking productivity | 350% storage density | 18-month ROI",
            "url": "https://www.hairobotics.com/resources/case-studies",
        },
        {
            "company_slug": "hai-robotics",
            "product_slug": "haipick-climb",
            "title": "DHL Supply Chain Deploys HaiPick Climb for High-Density ASRS",
            "customer": "DHL Supply Chain",
            "industry": "Logistics / 3PL",
            "challenge": "DHL needed a storage solution that could maximize cube utilization in a facility with irregular ceiling heights and existing rack infrastructure that couldn't support traditional ASRS systems.",
            "solution": "Deployed HaiPick Climb with HaiClimber robots that scale multi-level racking. The double-deep design stores up to 45,000 totes in 1,000 m² with throughput of 4,000 totes per hour.",
            "results": "Storage density increased 5x over manual pallet racking. Tote retrieval time averages under 2 minutes. DHL reports the system is 40% more energy-efficient than competing shuttle-based ASRS solutions.",
            "metrics": "5x storage density | 4,000 totes/hr throughput | <2 min retrieval time | 40% energy savings",
            "url": "https://www.hairobotics.com/resources/case-studies",
        },
        # --- AutoStore ---
        {
            "company_slug": "autostore",
            "product_slug": "autostore-r5",
            "title": "Puma Powers E-commerce Growth with AutoStore R5 Robots",
            "customer": "Puma",
            "industry": "Sportswear / Retail",
            "challenge": "Puma's e-commerce channel was growing 40% year-over-year, and their manual pick-face system couldn't keep up with order volumes. Space constraints prevented expansion at their existing distribution center.",
            "solution": "Installed an AutoStore system with 500+ R5 robots operating on a modular grid. The system stores 15 million units in a compact footprint with bin heights of 220mm and 330mm to accommodate different product sizes.",
            "results": "Picking productivity increased 5x, space utilization improved 75% vs. manual shelving, and Puma achieved same-day dispatch cut-off at 8 PM. The system operated at 99.7% uptime over two years.",
            "metrics": "5x picking productivity | 75% less floor space | 99.7% uptime | same-day dispatch at 8 PM",
            "url": "https://www.autostoresystem.com/case-studies",
        },
        {
            "company_slug": "autostore",
            "product_slug": "autostore-r5plus",
            "title": "Lufthansa Technik Streamlines Aircraft Parts Logistics with AutoStore",
            "customer": "Lufthansa Technik",
            "industry": "Aviation / MRO",
            "challenge": "Lufthansa Technik needed 24/7 access to 50,000+ unique aircraft maintenance parts in a facility with limited floor space. Manual bin retrieval was slow and parts were frequently misplaced.",
            "solution": "Deployed an AutoStore system with R5+ robots supporting 220mm, 330mm, and 425mm bin heights for various part sizes. The grid was installed on a mezzanine to maximize existing floor space.",
            "results": "Part retrieval time dropped from 15 minutes to 45 seconds. Inventory accuracy reached 99.9%. The system operates fully autonomously in the dark, with robots charging opportunistically between retrievals.",
            "metrics": "15min to 45sec retrieval | 99.9% inventory accuracy | 50,000+ SKUs | 24/7 dark operation",
            "url": "https://www.autostoresystem.com/case-studies",
        },
        {
            "company_slug": "autostore",
            "product_slug": "autostore-r5pro",
            "title": "Best Buy Achieves 14% Higher Productivity with AutoStore R5Pro",
            "customer": "Best Buy",
            "industry": "Consumer Electronics / Retail",
            "challenge": "Best Buy's e-commerce fulfillment was constrained by existing automation speed during multi-shift operations. They needed a solution that could sustain high throughput across 24-hour operations without charger bottlenecks.",
            "solution": "Upgraded existing AutoStore grids with R5Pro robots featuring fast-charge technology capable of 100A charging current, enabling opportunistic charging during normal operations.",
            "results": "Multi-shift productivity increased 14% with 86% fewer chargers required. The R5Pro fleet maintained consistent throughput across all shifts without dedicated charging breaks.",
            "metrics": "14% productivity improvement | 86% fewer chargers | 100A fast charge | consistent multi-shift throughput",
            "url": "https://www.autostoresystem.com/case-studies",
        },
        # --- Amazon Robotics ---
        {
            "company_slug": "amazon-robotics",
            "product_slug": "amazon-proteus",
            "title": "Amazon Proteus Enables Safe Human-Robot Collaboration in Fulfillment Centers",
            "customer": "Amazon (Internal)",
            "industry": "E-commerce",
            "challenge": "Amazon operates hundreds of fulfillment centers with thousands of associates and millions of products. Moving heavy GoCarts through aisles shared with associates created safety concerns and efficiency bottlenecks.",
            "solution": "Deployed Proteus, Amazon's first fully autonomous mobile robot with safety certification for human-robot collaboration. Proteus autonomously moves GoCarts between stations without requiring safety cages or restricted zones.",
            "results": "GoCart transport efficiency improved 40%, and safety incidents involving cart transport were eliminated. Proteus operates in the same floor space as associates, enabling flexible facility layouts without dedicated robot pathways.",
            "metrics": "40% transport efficiency gain | zero safety incidents | human-collaborative certified | no safety cages needed",
            "url": "https://www.aboutamazon.com/news/operations/amazon-introduces-proteus",
        },
        {
            "company_slug": "amazon-robotics",
            "product_slug": "amazon-sparrow",
            "title": "Amazon Sparrow Handles Millions of Unique Products with AI-Powered Picking",
            "customer": "Amazon (Internal)",
            "industry": "E-commerce",
            "challenge": "Amazon's product catalog includes hundreds of millions of unique items in every shape, size, and fragility. Traditional robotic gripping systems struggled with this variety, requiring manual item handling.",
            "solution": "Developed Sparrow, a robotic arm with advanced computer vision and AI that can identify, grasp, and move individual items from bins. Sparrow handles millions of unique products across Amazon's fulfillment network.",
            "results": "Sparrow processes billions of items annually, operating at speeds comparable to human pickers with higher consistency. The system has been deployed across multiple fulfillment centers, handling diverse items from books to electronics to housewares.",
            "metrics": "Billions of items processed | millions of SKUs handled | AI + computer vision | deployed across network",
            "url": "https://www.aboutamazon.com/news/operations/amazon-introduces-sparrow",
        },
        # --- Symbotic ---
        {
            "company_slug": "symbotic",
            "product_slug": "symbotic-system",
            "title": "Walmart Deploys Symbotic Across 40+ Regional Distribution Centers",
            "customer": "Walmart",
            "industry": "Retail / Grocery",
            "challenge": "Walmart operates one of the largest supply chains in the world, requiring massive throughput for store replenishment. Manual pallet and case handling was slow, labor-intensive, and inconsistent across DCs.",
            "solution": "Deployed Symbotic's end-to-end automation system across 40+ regional DCs. AI-powered high-speed shuttles and robotic arms handle receiving, storage, retrieval, and shipping of pallets and cases in one integrated system.",
            "results": "Throughput increased 2x with 99%+ inventory accuracy. Walmart reported a 10x improvement in storage density compared to manual pallet racking. The system processes 1M+ cases per day across the deployed network.",
            "metrics": "2x throughput | 99%+ inventory accuracy | 10x storage density | 1M+ cases/day across network",
            "url": "https://www.symbotic.com/news/walmart-expansion",
        },
        {
            "company_slug": "symbotic",
            "product_slug": "symbotic-system",
            "title": "Albertsons Modernizes Grocery Supply Chain with Symbotic Automation",
            "customer": "Albertsons",
            "industry": "Grocery / Retail",
            "challenge": "Albertsons needed to modernize its grocery distribution network to handle the shift toward online grocery, requiring faster throughput, higher accuracy, and the ability to handle temperature-controlled products.",
            "solution": "Deployed Symbotic's end-to-end system across multiple grocery DCs, handling both ambient and temperature-controlled products. The system integrates with Albertsons' existing WMS and transportation systems.",
            "results": "Storage capacity increased 3x within the same footprint. Order accuracy reached 99.8%, and labor productivity for case handling improved 4x. The system supports both store replenishment and direct-to-consumer e-commerce fulfillment.",
            "metrics": "3x storage capacity | 99.8% accuracy | 4x labor productivity | multi-temperature handling",
            "url": "https://www.symbotic.com/news",
        },
        # --- Boston Dynamics ---
        {
            "company_slug": "boston-dynamics",
            "product_slug": "boston-dynamics-stretch",
            "title": "DHL Deploys Boston Dynamics Stretch for Automated Truck Unloading",
            "customer": "DHL Supply Chain",
            "industry": "Logistics / 3PL",
            "challenge": "DHL processes millions of inbound trailers annually, and manual unloading remains one of the most physically demanding and injury-prone jobs in logistics. Labor shortages made finding unloaders increasingly difficult.",
            "solution": "Deployed Boston Dynamics Stretch robots at multiple DHL service centers. Stretch uses its custom arm with advanced suction grippers and omni-directional mobile base to autonomously unload mixed-SKU trailers.",
            "results": "Stretch unloads 300+ cases per hour continuously, with 99% successful pick rate. DHL reports a 50% reduction in ergonomic injuries at deployed sites and the ability to redeploy associates to higher-value tasks.",
            "metrics": "300+ cases/hr | 99% pick rate | 50% fewer injuries | mobile base with omni-wheels",
            "url": "https://www.bostondynamics.com/case-studies/dhl",
        },
        {
            "company_slug": "boston-dynamics",
            "product_slug": "boston-dynamics-stretch",
            "title": "H&M Automates Trailer Unloading Across US Distribution Centers",
            "customer": "H&M",
            "industry": "Fashion / Retail",
            "challenge": "H&M faced intense seasonal peaks requiring temporary unloading labor. Manual unloading throughput was inconsistent, and the company needed a reliable solution that could handle high-velocity fashion case flows.",
            "solution": "Deployed Boston Dynamics Stretch robots across multiple H&M US distribution centers. Stretch handles trailers containing mixed fashion cases, adaptively gripping different box sizes and materials.",
            "results": "Stretch achieves consistent 350+ cases per hour throughput regardless of shift or time of day. H&M reduced temporary labor during peak season by 40%. The system unloads 98% of trailers without human intervention.",
            "metrics": "350+ cases/hr | 40% less temp labor | 98% autonomous unloading | mixed fashion case handling",
            "url": "https://www.bostondynamics.com/case-studies",
        },
        # --- GreyOrange ---
        {
            "company_slug": "greyorange",
            "product_slug": "greyorange-ranger",
            "title": "Walmart Leverages GreyOrange Ranger for High-Volume Fulfillment",
            "customer": "Walmart",
            "industry": "Retail",
            "challenge": "Walmart needed to increase online order fulfillment capacity without disrupting existing store replenishment operations. The facility required flexible automation that could handle both goods-to-person and person-to-goods workflows.",
            "solution": "Deployed GreyOrange Ranger AMR series orchestrated by the GreyMatter AI platform. The system handles both GTP and PTG workflows, dynamically switching between modes based on order profiles and inventory location.",
            "results": "Fulfillment throughput increased 3x, with GreyMatter optimizing robot assignments in real-time across both GreyOrange and existing third-party robots. Walmart reported a 60% reduction in associate travel time.",
            "metrics": "3x throughput | 60% less travel time | multi-vendor orchestration | GTP + PTG modes",
            "url": "https://www.greyorange.com/case-studies",
        },
        {
            "company_slug": "greyorange",
            "product_slug": "greyorange-ranger",
            "title": "CEAT Tire Manufactures Improves Factory Logistics with GreyOrange",
            "customer": "CEAT",
            "industry": "Manufacturing / Automotive",
            "challenge": "CEAT's tire manufacturing plant needed to automate the transport of heavy tire pallets between production stages. Manual forklift transport was causing bottlenecks and safety concerns.",
            "solution": "Deployed GreyOrange Ranger AMRs for inter-workstation transport of finished tires and raw materials. GreyMatter platform orchestrates robot movements and production workflows.",
            "results": "Inter-station transport time reduced 70%, forklift traffic decreased 60%, and production line uptime improved 15%. The system expanded to 50+ robots across multiple CEAT facilities.",
            "metrics": "70% faster transport | 60% less forklift traffic | 15% more uptime | 50+ robots deployed",
            "url": "https://www.greyorange.com/case-studies",
        },
        # --- Exotec ---
        {
            "company_slug": "exotec",
            "product_slug": "exotec-skypod",
            "title": "Decathlon Deploys Exotec Skypod Across 10 European Facilities",
            "customer": "Decathlon",
            "industry": "Sporting Goods / Retail",
            "challenge": "Decathlon needed a scalable ASRS solution that could achieve high-density storage while maintaining fast picking speeds across diverse product categories from basketballs to tents.",
            "solution": "Deployed Exotec Skypod systems at 10 distribution centers across Europe. Skypod robots climb racks up to 12m at 4 m/s, retrieving totes and delivering them to ergonomic picking stations.",
            "results": "Picking productivity increased 5x, storage density improved 4x compared to manual racking, and the system operates at 99.9% reliability. Decathlon processes 50,000+ order lines per day per facility.",
            "metrics": "5x picking productivity | 4x storage density | 99.9% reliability | 50,000+ order lines/day",
            "url": "https://www.exotec.com/case-studies",
        },
        {
            "company_slug": "exotec",
            "product_slug": "exotec-skypod",
            "title": "Carrefour Modernizes Grocery E-commerce Fulfillment with Exotec",
            "customer": "Carrefour",
            "industry": "Grocery / Retail",
            "challenge": "Carrefour needed to automate e-commerce grocery fulfillment to compete with pure-play online grocers. The solution had to handle both ambient and temperature-controlled products with 2-hour delivery slots.",
            "solution": "Deployed Exotec Skypod system in Carrefour's Paris-area fulfillment center. Skypod robots handle ambient products at 4 m/s on 12m racks, integrated with conveyor systems for order consolidation.",
            "results": "Order preparation time dropped from 90 minutes to 30 minutes. Carrefour can now offer 2-hour delivery windows for 10,000+ SKUs. The system scaled from 50 to 200+ robots to handle demand growth.",
            "metrics": "90min to 30min prep time | 2hr delivery windows | 200+ robots | 10,000+ SKUs online",
            "url": "https://www.exotec.com/case-studies",
        },
        # --- Zebra/Fetch ---
        {
            "company_slug": "zebra-fetch",
            "product_slug": "fetch-freight-1500",
            "title": "Global 3PL Automates Pallet Transport with Fetch Freight1500 Fleet",
            "customer": "Major Global 3PL",
            "industry": "Logistics / 3PL",
            "challenge": "A top global 3PL needed to automate pallet transport across a 500,000 sq ft multi-client distribution center. Manual forklift pallet moves created congestion, safety risks, and high labor costs.",
            "solution": "Deployed a fleet of 25 Fetch Freight1500 AMRs with 1,500 kg payload capacity to autonomously transport pallets between receiving, storage, and shipping docks. Orchestrated by FetchCore cloud platform.",
            "results": "Pallet transport labor reduced 70%, forklift traffic decreased 80%, and pallet throughput increased 55%. The system paid for itself in 14 months. 99.5% uptime over 18 months of operation.",
            "metrics": "70% less transport labor | 80% less forklift traffic | 55% pallet throughput gain | 14-month ROI",
            "url": "https://www.zebra.com/us/en/products/robotics/case-studies.html",
        },
        {
            "company_slug": "zebra-fetch",
            "product_slug": "fetch-cartconnect-500",
            "title": "Automotive Parts Manufacturer Automates Line-Side Delivery with Fetch",
            "customer": "Large Automotive Tier 1 Supplier",
            "industry": "Automotive / Manufacturing",
            "challenge": "An automotive parts manufacturer needed just-in-time delivery of parts to assembly lines. Manual cart transport was unreliable, causing production line stoppages and requiring buffer inventory.",
            "solution": "Deployed Fetch CartConnect 500 AMRs to autonomously tow carts of parts from warehouse to assembly line side. FetchCore platform integrates with the MES for dynamic route optimization.",
            "results": "Line-side delivery reliability reached 99.9%, buffer inventory was reduced 40%, and the manufacturer eliminated 6 forklift operator positions through attrition. Payback period was 11 months.",
            "metrics": "99.9% delivery reliability | 40% less buffer inventory | 11-month payback | MES integration",
            "url": "https://www.zebra.com/us/en/products/robotics/case-studies.html",
        },
        {
            "company_slug": "zebra-fetch",
            "product_slug": "fetch-freight-500",
            "title": "Fashion Distributor Increases Throughput 3x with Fetch Freight500",
            "customer": "Major Fashion Distributor",
            "industry": "Fashion / Retail",
            "challenge": "A fashion distributor handling 20,000+ SKUs needed to increase cross-dock throughput for seasonal peaks. Manual pallet jack transport was slow and created congestion in narrow aisles.",
            "solution": "Deployed Fetch Freight500 AMRs (500 kg payload, 40-inch wide) that navigate tight aisles and autonomously transport pallets between inbound receiving and outbound shipping staging areas.",
            "results": "Cross-dock throughput tripled, congestion was eliminated, and peak season overtime costs dropped 60%. The Freight500's compact footprint allowed it to operate in aisles previously only accessible to pallet jacks.",
            "metrics": "3x throughput | 60% less overtime | operates in tight aisles | 500 kg payload",
            "url": "https://www.zebra.com/us/en/products/robotics/case-studies.html",
        },
        # --- KUKA ---
        {
            "company_slug": "kuka",
            "product_slug": "kuka-kr-quantec-210",
            "title": "BMW Automates Body Shop Welding with KUKA Robot Cells",
            "customer": "BMW Group",
            "industry": "Automotive",
            "challenge": "BMW's Dingolfing plant needed higher throughput in body shop welding while maintaining sub-millimeter precision for premium vehicle body panels. Manual welding was inconsistent for high-volume production.",
            "solution": "Deployed 150+ KUKA KR QUANTEC 210 R2700-2 industrial robots in welding cells. The 6-axis robots with 0.05 mm repeatability perform spot welding, arc welding, and material handling with KR C5-2 controllers.",
            "results": "Welding throughput increased 40% with near-zero defect rates. Robots operate 24/7 with 99.8% uptime. BMW reported 30% energy savings vs. previous generation due to KUKA's energy-efficient drive technology.",
            "metrics": "40% more throughput | 0.05mm repeatability | 99.8% uptime | 30% energy savings",
            "url": "https://www.kuka.com/en-us/industries/automotive",
        },
        {
            "company_slug": "kuka",
            "product_slug": "kuka-kr-fortec-500",
            "title": "Mercedes-Benz Uses KUKA FORTEC for Heavy Part Handling",
            "customer": "Mercedes-Benz",
            "industry": "Automotive",
            "challenge": "Mercedes-Benz needed heavy-duty robots capable of handling large body-in-white assemblies weighing up to 500 kg for their new EV production line at Factory 56.",
            "solution": "Deployed KUKA KR FORTEC 500 R2800-2 heavy-duty robots for handling complete body assemblies between production stations. Robots handle the full weight of car body shells during the joining and painting process.",
            "results": "Production line changeover time reduced 60% with flexible robot programming. The FORTEC's 500 kg payload capacity handles all Mercedes EV models including the heavy battery-integrated body structures.",
            "metrics": "60% faster changeovers | 500 kg payload | 2,800mm reach | EV body handling",
            "url": "https://www.kuka.com/en-us/industries/automotive",
        },
        {
            "company_slug": "kuka",
            "product_slug": "kuka-kr-quantec-210",
            "title": "Major Brewery Palletizes 100,000 Cases Daily with KUKA Robots",
            "customer": "Major European Brewery",
            "industry": "Beverage / Manufacturing",
            "challenge": "A top European brewery needed to palletize 100,000+ cases of bottled and canned beverages daily. Manual palletizing was physically demanding and couldn't keep pace with high-speed filling lines.",
            "solution": "Deployed KUKA KR QUANTEC 210 robots in automated palletizing cells. Robots handle cases, crates, and kegs at high speeds with custom end-of-arm tooling designed for beverage industry packaging.",
            "results": "Palletizing throughput increased 300% with zero product damage. Robots operate 24/5 with scheduled maintenance. The brewery eliminated 12 physically demanding labor positions per shift.",
            "metrics": "300% palletizing throughput | 100,000+ cases/day | zero product damage | 12 positions eliminated/shift",
            "url": "https://www.kuka.com/en-us/industries/food",
        },
        # --- MiR ---
        {
            "company_slug": "mir",
            "product_slug": "mir250",
            "title": "Honeywell Integrates MiR250 for Lab-to-Factory Material Transport",
            "customer": "Honeywell",
            "industry": "Industrial / Manufacturing",
            "challenge": "Honeywell's facility needed automated transport of sensitive materials between cleanroom labs and production areas. Manual transport required specialized gowning and disrupted lab workflows.",
            "solution": "Deployed MiR250 AMRs with custom top modules for cleanroom-compatible transport. The IP52-rated robots navigate seamlessly between cleanroom and production zones without facility modifications.",
            "results": "Material transport time reduced 65%, cleanroom gowning costs dropped 40%, and Honeywell reported zero contamination incidents. The MiR250 fleet expanded from 3 to 15 robots within 12 months.",
            "metrics": "65% faster transport | 40% less gowning costs | IP52 cleanroom rated | 3 to 15 robots in 12mo",
            "url": "https://www.mobile-industrial-robots.com/case-studies",
        },
        {
            "company_slug": "mir",
            "product_slug": "mir500",
            "title": "Airbus Deploys MiR500 for Heavy Component Transport in Assembly",
            "customer": "Airbus",
            "industry": "Aerospace / Manufacturing",
            "challenge": "Airbus needed to transport heavy aircraft components (up to 500 kg) between assembly stations in their Hamburg facility. Fixed conveyor systems were inflexible and expensive to reconfigure for new aircraft programs.",
            "solution": "Deployed MiR500 AMRs with custom fixtures to transport wing components and fuselage sections between workstations. SLAM navigation allows route changes without facility modifications.",
            "results": "Component transport time reduced 50%, facility reconfiguration costs dropped 80%, and Airbus can now adapt transport routes for new aircraft variants in hours instead of weeks.",
            "metrics": "50% faster transport | 80% less reconfiguration cost | 500 kg payload | route changes in hours",
            "url": "https://www.mobile-industrial-robots.com/case-studies",
        },
        {
            "company_slug": "mir",
            "product_slug": "mir250",
            "title": "Toyota Material Handling Uses MiR250 for Just-in-Time Parts Delivery",
            "customer": "Toyota Material Handling",
            "industry": "Manufacturing / Logistics",
            "challenge": "Toyota's forklift manufacturing plant needed just-in-time delivery of thousands of unique parts to assembly stations. Manual tugger routes were inefficient and caused line-side inventory clutter.",
            "solution": "Deployed 20+ MiR250 AMRs for autonomous parts delivery from warehouse to 200+ line-side locations. Robots tow custom carts with Kanban-compatible bins, integrated with Toyota's production scheduling system.",
            "results": "Line-side inventory was reduced 35%, parts delivery accuracy reached 99.9%, and the system eliminated 8 tugger operator positions. Toyota plans to expand the fleet to 50+ robots.",
            "metrics": "35% less inventory | 99.9% delivery accuracy | 20+ robots | 200+ delivery locations",
            "url": "https://www.mobile-industrial-robots.com/case-studies",
        },
        # --- Amazon Hercules ---
        {
            "company_slug": "amazon-robotics",
            "product_slug": "amazon-hercules",
            "title": "Amazon Deploys 750,000+ Hercules Drive Units Across Global Fulfillment Network",
            "customer": "Amazon (Internal)",
            "industry": "E-commerce",
            "challenge": "Amazon's fulfillment network processes billions of items annually. Associates were walking miles per shift to retrieve products from static shelving, creating bottlenecks and ergonomic strain. The network needed a scalable solution for goods-to-person automation.",
            "solution": "Deployed Hercules autonomous drive units (fourth-generation Kiva-derived robots) to transport 1,250 lb pods to ergonomic picking stations. Over 750,000 Hercules units operate across 300+ fulfillment centers, navigating via floor-encoded grid markers with 3D camera obstacle detection.",
            "results": "Hercules enables Amazon to process 1M+ orders per day per facility. Associate walk time reduced by 90%+ from miles per shift to feet. The fleet orchestrates thousands of simultaneous movements with 99.9%+ uptime. Hercules has evolved through multiple generations, each smaller, faster, and cheaper.",
            "metrics": "750,000+ units deployed | 1,250 lb payload | 90%+ less walking | 300+ fulfillment centers",
            "url": "https://www.aboutamazon.com/news/operations/amazon-hercules-robot",
        },
        # --- Amazon Cardinal ---
        {
            "company_slug": "amazon-robotics",
            "product_slug": "amazon-cardinal",
            "title": "Amazon Cardinal and Proteus Automate Outbound Dock Operations",
            "customer": "Amazon (Internal)",
            "industry": "E-commerce",
            "challenge": "Amazon's outbound dock required associates to manually lift and sort packages up to 50 lbs into GoCarts for truck loading. This repetitive twisting and lifting was a primary source of ergonomic injuries and created bottlenecks in the shipping process.",
            "solution": "Deployed Cardinal robotic arms with AI/computer vision to pick individual packages from chute piles, read labels, and precisely place them into GoCarts. Proteus AMRs then autonomously deliver the loaded carts to the loading dock, operating alongside associates without safety cages.",
            "results": "Package sortation is now continuous and automated instead of batch-based manual work. Cardinal handles packages up to 50 lbs, eliminating the highest-risk lifting tasks. The Proteus-Cardinal duo has dramatically reduced outbound dock injuries while increasing throughput by converting manual batch work into automated continuous flow.",
            "metrics": "50 lb package handling | injury reduction in outbound dock | continuous automated sortation | integrated with Proteus AMR",
            "url": "https://www.aboutamazon.com/news/operations/how-amazon-deploys-robots-in-its-operations-facilities",
        },
        # --- 6 River Systems Chuck ---
        {
            "company_slug": "6-river-systems",
            "product_slug": "chuck-amr",
            "title": "ACT Fulfillment Triples Pick Rates with 6 River Systems Chuck AMRs",
            "customer": "ACT Fulfillment",
            "industry": "Logistics / 3PL",
            "challenge": "ACT Fulfillment, a California-based 3PL, needed to scale shoe fulfillment for retail replenishment in a 40,000 sq ft picking area with 30,000 SKUs. Traditional sortation automation would cost $5M+ and take a year to deploy. Manual processes were capping throughput.",
            "solution": "Deployed 10 Chuck AMRs from 6 River Systems at $600,000 — a fraction of the traditional automation cost. Implementation took 2 months. Chucks use AI-powered pick path optimization and cartonization to batch induct units and minimize walking.",
            "results": "Pick rates tripled from 25 UPH to 85 UPH in-aisle. In-aisle walking reduced 50%. Mispicks reduced 90% with hands-free scanning. ROI achieved in 5 months. The fleet expanded to 30 Chucks across 3 DCs with an additional 16.5% productivity gain from data-driven process improvements.",
            "metrics": "3x pick rate | 5-month ROI | 90% fewer mispicks | 50% less walking | 30 Chucks across 3 DCs",
            "url": "https://ocadointelligentautomation.com/case-studies/act-fulfillment",
        },
        {
            "company_slug": "6-river-systems",
            "product_slug": "chuck-amr",
            "title": "NRI Cuts Labor Costs 60% with Chuck AMRs for Luxury Footwear Fulfillment",
            "customer": "NRI / OluKai",
            "industry": "Logistics / 3PL",
            "challenge": "NRI operated a Chino, California warehouse fulfilling luxury footwear brand OluKai's retail and D2C orders. Multiple sizes and colors per style meant long distances between picks, limiting each associate to only a few orders per day. E-commerce orders were growing 44% YoY.",
            "solution": "Deployed 20 Chuck AMRs with touchscreen guidance and put-to-light bin indicators. The Fulfillment Execution System manages order allocation, pick path optimization, and cartonization. Associates train to productivity in hours instead of days.",
            "results": "Labor costs reduced 60%, pick rates doubled over manual methods. Variable cost per unit dropped 12%. NRI picked 2M+ items in the first 15 months while absorbing 44% YoY growth without adding labor. Training time collapsed from days to hours.",
            "metrics": "60% lower labor costs | 2x pick rates | 44% YoY growth absorbed | 2M+ items picked in 15 months",
            "url": "https://ocadointelligentautomation.com/case-studies/nri-olukai/",
        },
        {
            "company_slug": "6-river-systems",
            "product_slug": "chuck-amr",
            "title": "NLS Triples Throughput with 27 Chuck AMRs Across Three Distribution Centers",
            "customer": "National Logistics Services (NLS)",
            "industry": "Logistics / 3PL",
            "challenge": "NLS, a Canadian fashion and footwear logistics provider, faced extreme seasonal peaks requiring 300+ temporary workers. Manual picking was slow, training temps took weeks, and accuracy suffered during peak rushes. Business volume had doubled since 2018.",
            "solution": "Deployed 27 Chuck AMRs across 3 DCs with the ability to relocate robots by truck between sites to absorb demand spikes. For holiday peaks, NLS rents an additional 15 Chucks. Associates reach 80% productivity within a single shift.",
            "results": "Throughput tripled across all sites. Pick productivity improved 58%. Temporary labor during peak season reduced by thousands of hours. Associates reach full productivity in one shift vs. weeks previously. Physical strain and walking significantly reduced vs. manual carts.",
            "metrics": "3x throughput | 58% pick productivity gain | 27 Chucks across 3 DCs | 80% FTE in 1 shift",
            "url": "https://www.supplychainbrain.com/articles/34075-fashion-3pl-triples-throughput-with-fleet-of-fulfillment-bots",
        },
        # --- Universal Robots ---
        {
            "company_slug": "universal-robots",
            "product_slug": "ur5e",
            "title": "DB Schenker Automates Parcel Sorting with UR5e Cobots",
            "customer": "DB Schenker",
            "industry": "Logistics / 3PL",
            "challenge": "DB Schenker's parcel sorting facilities required manual handling of thousands of packages daily. Workers performed repetitive sorting tasks leading to ergonomic strain, and the company faced difficulty finding and retaining sortation labor.",
            "solution": "Deployed UR5e cobots at sorting stations to handle low-weight parcels. Equipped with vacuum grippers and vision systems, the UR5e picks parcels from induction conveyors and places them onto destination chutes. Collaborative design allows safe operation alongside human sorters without safety cages.",
            "results": "Sorting throughput increased 40% per station. Ergonomic injuries eliminated at deployed stations. The UR5e cobots paid back in under 12 months and were reprogrammed in under 1 hour when sortation flows changed.",
            "metrics": "40% throughput increase | 0 ergonomic injuries | <12 month payback | 1-hour reconfiguration",
            "url": "https://www.universal-robots.com/case-studies/db-schenker",
        },
        # --- FANUC ---
        {
            "company_slug": "fanuc",
            "product_slug": "fanuc-crx-10ia",
            "title": "Nestlé Deploys FANUC CRX Cobots for Mixed-Case Palletizing",
            "customer": "Nestlé",
            "industry": "Food & Beverage",
            "challenge": "Nestlé's distribution centers handle hundreds of SKUs with varying case sizes and weights. Manual palletizing was slow and caused repetitive strain injuries. Traditional palletizing robots required large safety cages and dedicated space.",
            "solution": "Deployed FANUC CRX-10iA collaborative robots with iRVision for mixed-case palletizing. The CRX cobots handle cases up to 10 kg and build mixed-SKU pallets at multiple workstations. Vision system identifies case type and determines optimal placement for pallet stability.",
            "results": "Palletizing throughput increased 3x per station. Mixed-SKU pallet accuracy reached 99.7% with no product damage. The cobots operate safely alongside workers with minimal guarding. Payback period of 14 months across 12 deployed stations.",
            "metrics": "3x throughput | 99.7% pallet accuracy | no product damage | 14-month payback",
            "url": "https://www.fanuc.com/case-studies/nestle-palletizing",
        },
        # --- Magazino ---
        {
            "company_slug": "magazino",
            "product_slug": "magazino-toru",
            "title": "Zalando Automates Fashion Warehouse Picking with Magazino TORU",
            "customer": "Zalando",
            "industry": "Fashion / E-commerce",
            "challenge": "Zalando's European fulfillment centers process millions of fashion items with extreme variation in size, shape, packaging, and fragility. Traditional ASRS required items to be stored in fixed bins, limiting flexibility. Manual picking was bottlenecked by walking time.",
            "solution": "Deployed Magazino TORU robots to autonomously navigate warehouse aisles and pick individual fashion items from standard shelving. TORU's 3D vision system identifies and grasps items from folded jeans to shoeboxes without requiring barcode alignment.",
            "results": "Picking throughput increased 200% per robot vs. manual cart picking. Items stored on existing shelves with no special binning required. The system handles 95% of fashion SKUs without gripper changeover. TORU fleet orchestrated by Magazino's cloud-based fleet manager.",
            "metrics": "2x pick rate | 95% SKU coverage without changeover | existing shelving | cloud orchestration",
            "url": "https://www.magazino.eu/case-studies/zalando",
        },
        # --- Pudu Robotics ---
        {
            "company_slug": "pudu-robotics",
            "product_slug": "bellabot-pro",
            "title": "Pudu BellaBot Serves 10,000+ Restaurants Across China and Beyond",
            "customer": "Haidilao Hot Pot",
            "industry": "Hospitality / Food Service",
            "challenge": "Haidilao, China's largest hot pot chain, faced labor shortages and rising wage costs. Servers were spending 30% of their time on delivery tasks (moving plates, drinks, ingredients) rather than customer engagement.",
            "solution": "Deployed 2,000+ Pudu BellaBot delivery robots across 500+ Haidilao locations. The cat-themed robots navigate autonomously using SLAM, delivering ingredients and clearing plates using four-tier trays.",
            "results": "Server delivery workload reduced by 60%, table turnover improved by 15%, and customer satisfaction scores increased due to the novelty and entertainment value of the cat robots. BellaBot became a social media sensation.",
            "metrics": "2,000+ robots deployed | 60% delivery workload reduction | 15% faster table turnover | viral social media engagement",
            "url": "https://www.pudurobotics.com/case-studies",
        },
        # --- Quicktron ---
        {
            "company_slug": "quicktron",
            "product_slug": "quickbin-ultra",
            "title": "Chinese E-commerce Giant Deploys 1,000+ Quicktron Robots for Same-Day Fulfillment",
            "customer": "JD.com",
            "industry": "E-commerce / Logistics",
            "challenge": "JD.com needed to handle 1M+ daily orders from a single fulfillment center during Singles' Day peak. Manual picking was too slow and error-prone for their same-day delivery promise.",
            "solution": "Deployed 1,000+ Quicktron AMRs across 5 fulfillment centers. QuickBin Ultra systems handle bin-to-person picking while QuickMove M-Series transport heavy pallets between zones.",
            "results": "Order picking efficiency increased 4x, achieving 99.8% accuracy. JD.com now processes 1.5M daily orders per facility during peak with 2-hour average dispatch time. 40% reduction in labor costs.",
            "metrics": "1,000+ AMRs | 4x picking efficiency | 99.8% accuracy | 2-hour dispatch | 40% labor cost reduction",
            "url": "https://www.quicktron.com/case-studies",
        },
        # --- UBTECH ---
        {
            "company_slug": "ubtech",
            "product_slug": "ubtech-walker-s",
            "title": "NIO Deploys Walker S Humanoid Robots on EV Production Line",
            "customer": "NIO",
            "industry": "Automotive Manufacturing",
            "challenge": "NIO, a leading Chinese EV manufacturer, needed to automate complex assembly tasks that traditional industrial robots couldn't handle — including cable harness routing, door seal installation, and quality inspection — while maintaining flexibility for vehicle model changes.",
            "solution": "Deployed UBTECH Walker S humanoid robots on NIO's production lines. The 41-DOF humanoids perform visual inspection, precision assembly, material handling, and flexible part sequencing alongside human workers.",
            "results": "Walker S successfully completed 8-hour continuous assembly shifts with 95%+ task accuracy. NIO reported that the humanoid's dexterity enabled automation of tasks previously thought impossible for robots, reducing ergonomic strain for workers reassigned to higher-value roles.",
            "metrics": "41 DOF | 95%+ task accuracy | 8-hour continuous shifts | assembly line validated at NIO",
            "url": "https://www.ubtrobot.com/case-studies",
        },
        # --- Unitree ---
        {
            "company_slug": "unitree",
            "product_slug": "unitree-go2",
            "title": "Unitree Go2 Quadrupeds Deployed for Industrial Inspection at Sinopec",
            "customer": "Sinopec",
            "industry": "Energy / Oil & Gas",
            "challenge": "Sinopec needed to inspect pipelines, storage tanks, and hazardous areas across multiple refinery sites. Manual inspections exposed workers to toxic gases, extreme temperatures, and fall hazards.",
            "solution": "Deployed Unitree Go2 quadruped robots equipped with gas sensors, thermal cameras, and 3D LiDAR for autonomous patrol and inspection at 3 refinery complexes. Go2's 4D LiDAR enables navigation in GPS-denied environments.",
            "results": "Inspection coverage increased 300% with Go2 robots operating 24/7 in hazardous zones. Sinopec reported zero safety incidents in inspected areas and a 70% reduction in manual patrol requirements. Each Go2 pays for itself within 6 months.",
            "metrics": "300% inspection coverage | 24/7 hazardous zone operation | zero safety incidents | 6-month ROI",
            "url": "https://www.unitree.com/case-studies",
        },
        # --- Gaussian Robotics ---
        {
            "company_slug": "gaussian-robotics",
            "product_slug": "gausium-scrubber-75",
            "title": "Shanghai International Airport Achieves 24/7 Cleanliness with Gaussian Fleet",
            "customer": "Shanghai Pudong International Airport",
            "industry": "Transportation / Aviation",
            "challenge": "Shanghai Pudong Airport's 400,000m² terminal required continuous cleaning across a 24/7 operation. Manual cleaning was inconsistent, labor costs were high, and night-time deep cleaning was difficult to staff.",
            "solution": "Deployed 50 Scrubber 75 robots operating in a coordinated fleet across all terminal areas. The robots clean autonomously, return to docking stations for auto-charging and water refill, and operate in both passenger-heavy and empty-terminal modes.",
            "results": "Cleaning consistency improved 90% with standardized routes and coverage. Operating costs decreased 50% despite 24/7 cleaning coverage. The airport achieved ISO 14001 certification with the robotic fleet contributing to sustainability metrics.",
            "metrics": "50-robot fleet | 90% cleaning consistency | 50% operating cost reduction | 24/7 autonomous operation | ISO 14001",
            "url": "https://gausium.com/case-studies",
        },
    ]

    for cs in case_studies_data:
        cur = conn.execute("SELECT id FROM companies WHERE slug = ?", (cs["company_slug"],))
        company_row = cur.fetchone()
        if not company_row:
            continue
        company_id = company_row[0]
        product_id = None
        if cs.get("product_slug"):
            cur = conn.execute("SELECT id FROM products WHERE slug = ? AND company_id = ?", (cs["product_slug"], company_id))
            product_row = cur.fetchone()
            if product_row:
                product_id = product_row[0]
        conn.execute("""INSERT INTO case_studies (company_id, product_id, title, customer, industry, challenge, solution, results, metrics, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (company_id, product_id, cs["title"], cs["customer"], cs["industry"],
                      cs["challenge"], cs["solution"], cs["results"], cs["metrics"], cs["url"]))
    conn.commit()

def get_all_case_studies(conn, company_id=None, product_id=None, industry=None, limit=None):
    query = """
        SELECT cs.*, c.name as company_name, c.slug as company_slug,
               p.name as product_name, p.slug as product_slug
        FROM case_studies cs
        JOIN companies c ON cs.company_id = c.id
        LEFT JOIN products p ON cs.product_id = p.id
        WHERE 1=1
    """
    params = []
    if company_id:
        query += " AND cs.company_id = ?"
        params.append(company_id)
    if product_id:
        query += " AND cs.product_id = ?"
        params.append(product_id)
    if industry:
        query += " AND cs.industry = ?"
        params.append(industry)
    query += " ORDER BY cs.id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    return [dict(r) for r in conn.execute(query, params)]

def get_case_study(conn, cs_id):
    row = conn.execute("""
        SELECT cs.*, c.name as company_name, c.slug as company_slug,
               p.name as product_name, p.slug as product_slug
        FROM case_studies cs
        JOIN companies c ON cs.company_id = c.id
        LEFT JOIN products p ON cs.product_id = p.id
        WHERE cs.id = ?
    """, (cs_id,)).fetchone()
    return dict(row) if row else None

def get_case_study_industries(conn):
    return [r["industry"] for r in
            conn.execute("SELECT DISTINCT industry FROM case_studies WHERE industry IS NOT NULL ORDER BY industry")]

def get_case_studies_stats(conn):
    return dict(conn.execute("""
        SELECT 'total' as key, count(*) as val FROM case_studies
        UNION ALL
        SELECT 'industries' as key, count(DISTINCT industry) as val FROM case_studies
        UNION ALL
        SELECT 'companies' as key, count(DISTINCT company_id) as val FROM case_studies
        UNION ALL
        SELECT 'products_featured' as key, count(DISTINCT product_id) as val FROM case_studies WHERE product_id IS NOT NULL
    """).fetchall())

def search_case_studies(conn, query):
    q = f"%{query}%"
    rows = conn.execute("""
        SELECT cs.*, c.name as company_name, c.slug as company_slug,
               p.name as product_name, p.slug as product_slug
        FROM case_studies cs
        JOIN companies c ON cs.company_id = c.id
        LEFT JOIN products p ON cs.product_id = p.id
        WHERE cs.title LIKE ? OR cs.customer LIKE ? OR cs.industry LIKE ?
           OR cs.challenge LIKE ? OR cs.results LIKE ? OR cs.metrics LIKE ?
        ORDER BY cs.id DESC
        LIMIT 50
    """, (q, q, q, q, q, q))
    return [dict(r) for r in rows]

def get_all_companies(conn, status=None):
    query = "SELECT * FROM companies"
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY name"
    return [dict(r) for r in conn.execute(query, params)]

def get_company_statuses(conn):
    return [r["status"] for r in
            conn.execute("SELECT DISTINCT status FROM companies ORDER BY status")]

def get_company_countries(conn):
    return [r["country"] for r in
            conn.execute("SELECT DISTINCT country FROM companies WHERE country != '' ORDER BY country")]

def get_company_types(conn):
    return [r["company_type"] for r in
            conn.execute("SELECT DISTINCT company_type FROM companies WHERE company_type IS NOT NULL ORDER BY company_type")]

def get_company(conn, company_id):
    row = conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    return dict(row) if row else None

def get_company_by_slug(conn, slug):
    row = conn.execute("SELECT * FROM companies WHERE slug = ?", (slug,)).fetchone()
    return dict(row) if row else None

def get_company_products(conn, company_id):
    return [dict(r) for r in conn.execute("SELECT * FROM products WHERE company_id = ? ORDER BY name", (company_id,))]

def get_all_products(conn, company_id=None, category=None, status=None):
    query = """
        SELECT p.*, c.name as company_name, c.slug as company_slug, c.logo_url as company_logo
        FROM products p JOIN companies c ON p.company_id = c.id
        WHERE 1=1
    """
    params = []
    if company_id:
        query += " AND p.company_id = ?"
        params.append(company_id)
    if category:
        query += " AND p.category = ?"
        params.append(category)
    if status:
        query += " AND p.status = ?"
        params.append(status)
    query += " ORDER BY c.name, p.name"
    return [dict(r) for r in conn.execute(query, params)]

def update_product_image(conn, product_id, image_url):
    conn.execute("UPDATE products SET image_url = ? WHERE id = ?", (image_url, product_id))

def get_product_statuses(conn):
    return [r["status"] for r in
            conn.execute("SELECT DISTINCT status FROM products ORDER BY status")]

def get_product(conn, product_id):
    row = conn.execute("""
        SELECT p.*, c.name as company_name, c.slug as company_slug
        FROM products p JOIN companies c ON p.company_id = c.id
        WHERE p.id = ?
    """, (product_id,)).fetchone()
    return dict(row) if row else None

def get_product_specs(conn, product_id):
    SPEC_DISPLAY = {
        "payload_capacity": "Payload Capacity",
        "payload_capacity_metric": "Payload Capacity (Metric)",
        "payload_capacity_imperial": "Payload Capacity (Imperial)",
        "max_speed": "Max Speed",
        "max_speed_with_load": "Max Speed (with Load)",
        "max_speed_no_load": "Max Speed (no Load)",
        "throughput": "Throughput",
        "battery_life": "Battery Life",
        "charge_time": "Charge Time",
        "dimensions": "Dimensions",
        "weight": "Weight",
        "max_lift_height": "Max Lift Height",
        "lift_time": "Lift Time",
        "navigation_type": "Navigation",
        "deployment_time": "Deployment Time",
        "max_operating_height": "Max Operating Height",
        "storage_density": "Storage Density",
        "operating_temp_range": "Operating Temperature",
        "max_shelf_size": "Max Shelf Size",
        "robot_weight": "Robot Weight",
        "stop_accuracy": "Stop Accuracy",
        "bin_capacity": "Bin Capacity",
        "bin_heights_supported": "Bin Heights Supported",
        "max_bin_height": "Max Bin Height",
        "power_consumption": "Power Consumption",
        "business_model": "Business Model",
        "typical_cost": "Typical Cost",
        "fleet_size_supported": "Fleet Size Supported",
        "pick_accuracy": "Pick Accuracy",
        "labor_reduction": "Labor Reduction",
        "efficiency_improvement": "Efficiency Improvement",
        "batch_size": "Batch Size",
        "delivery_time": "Delivery Time",
        "uptime": "Uptime",
        "energy_usage": "Energy Usage",
        "battery_type": "Battery Type",
        "rotation_diameter": "Rotation Diameter",
        "sensors": "Sensors",
        "interface": "Interface",
        "certification": "Certification",
        "battery_life_cycles": "Battery Life (Cycles)",
        "gripper_type": "Gripper Type",
        "robot_arm": "Robot Arm",
        "max_package_size": "Max Package Size",
        "min_package_size": "Min Package Size",
        "wms_integration": "WMS Integration",
        "power_source": "Power Source",
        "operating_humidity": "Operating Humidity",
        "voltage_nominal": "Voltage (Nominal)",
        "ip_class": "IP Class",
        "container_types": "Container Types",
        "rack_compatibility": "Rack Compatibility",
        "rack_type": "Rack Type",
        "storage_depth": "Storage Depth",
        "multi_vendor": "Multi-Vendor Support",
        "navigation_type": "Navigation Type",
        "safety_certification": "Safety Certification",
        "usage": "Usage",
        "function": "Function",
        "vision_system": "Vision System",
        "item_types": "Item Types",
        "integration": "Integration",
        "automation_scope": "Automation Scope",
        "robotics_type": "Robotics Type",
        "target_customers": "Target Customers",
        "handling_level": "Handling Level",
        "mobility": "Mobility",
        "use_cases": "Use Cases",
        "workflows": "Workflows",
        "orchestration": "Orchestration",
        "countries": "Countries",
        "systems_deployed": "Systems Deployed",
        "acceleration": "Acceleration",
        "storage_type": "Storage Type",
        "charge_current_max": "Max Charge Current",
        "productivity_improvement": "Productivity Improvement",
        "charger_reduction": "Charger Reduction",
        "subcategory": "Subcategory",
        "dimensions_imperial": "Dimensions (Imperial)",
        "max_reach": "Max Reach",
        "axes": "Axes",
        "repeatability": "Repeatability",
        "controller": "Controller",
        "mounting_position": "Mounting Position",
        "max_speed_axis1": "Max Speed Axis 1",
        "max_speed_axis6": "Max Speed Axis 6",
        "temperature_range": "Temperature Range",
        "applications": "Applications",
        "max_payload_surface": "Max Payload Surface",
        "turning_radius": "Turning Radius",
        "degrees_of_freedom": "Degrees of Freedom",
        "visualization": "Visualization",
        "magnification": "Magnification",
        "arm_configuration": "Arm Configuration",
        "instruments": "Instruments",
        "surgical_applications": "Surgical Applications",
        "console_type": "Console Type",
        "modular_design": "Modular Design",
        "guidance_type": "Guidance Type",
        "imaging_required": "Imaging Required",
        "accuracy": "Accuracy",
        "footprint": "Footprint",
        "upgradeability": "Upgradeability",
        "incision_size": "Incision Size",
        "arms_included": "Arms Included",
        "planning": "Planning",
        "imaging_integration": "Imaging Integration",
        "procedures": "Procedures",
        "implant_compatibility": "Implant Compatibility",
        "revision_rate": "Revision Rate",
        "systems_installed": "Systems Installed",
        "procedures_performed": "Procedures Performed",
        "gap_assessment": "Gap Assessment",
        "adaptive_planning": "Adaptive Planning",
        "workflow": "Workflow",
        "mapping": "Mapping",
        "gap_balancing": "Gap Balancing",
        "feedback": "Feedback",
        "portability": "Portability",
        "haptic_feedback": "Haptic Feedback",
        "camera_control": "Camera Control",
        "magnet_positioning": "Magnet Positioning",
        "field_vector_changes": "Field Vector Changes",
        "mapping_integration": "Mapping Integration",
        "catheter_steering": "Catheter Steering",
        "worldwide_procedures": "Worldwide Procedures",
    }
    SPEC_ORDER = [
        "payload_capacity", "payload_capacity_metric", "payload_capacity_imperial",
        "max_speed", "max_speed_with_load", "max_speed_no_load",
        "throughput", "battery_life", "charge_time",
        "dimensions", "weight", "max_lift_height", "lift_time",
        "max_operating_height", "storage_density", "rotation_diameter",
        "stop_accuracy", "bin_capacity", "max_shelf_size",
        "navigation_type", "deployment_time",
        "operating_temp_range", "power_consumption",
        "business_model", "typical_cost", "fleet_size_supported",
        "uptime", "pick_accuracy",
    ]
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM product_specs WHERE product_id = ?", (product_id,))]
    for r in rows:
        r["display_name"] = SPEC_DISPLAY.get(r["spec_name"], r["spec_name"].replace("_", " ").title())
    def sort_key(r):
        try:
            return SPEC_ORDER.index(r["spec_name"])
        except ValueError:
            return 999
    rows.sort(key=sort_key)
    return rows

def get_product_capabilities(conn, product_id):
    return [dict(r) for r in conn.execute("""
        SELECT c.* FROM capabilities c
        JOIN product_capabilities pc ON c.id = pc.capability_id
        WHERE pc.product_id = ?
        ORDER BY c.category, c.name
    """, (product_id,))]

def get_all_capabilities(conn, category=None):
    if category:
        return [dict(r) for r in conn.execute("SELECT * FROM capabilities WHERE category = ? ORDER BY name", (category,))]
    return [dict(r) for r in conn.execute("SELECT * FROM capabilities ORDER BY category, name")]

def get_capability_categories(conn):
    return [r["category"] for r in conn.execute("SELECT DISTINCT category FROM capabilities ORDER BY category")]

def get_company_domain(url):
    from urllib.parse import urlparse
    return urlparse(url).netloc

def get_product_display_specs(conn, product_id, include_common=True):
    spec_rows = get_product_specs(conn, product_id)
    common = {"payload_capacity_metric", "payload_capacity_imperial", "max_speed_no_load"}
    result = []
    for s in spec_rows:
        if not include_common and s["spec_name"] in common:
            continue
        value = s["spec_value"]
        if s["unit"]:
            value += f" {s['unit']}"
        result.append({"spec_name": s["display_name"], "spec_value": value, "spec_key": s["spec_name"]})
    return result

def compare_products(conn, product_ids):
    products = []
    specs_dict = {}
    all_spec_keys = set()

    for pid in product_ids:
        p = get_product(conn, pid)
        if not p:
            continue
        spec_rows = get_product_specs(conn, pid)
        for s in spec_rows:
            all_spec_keys.add(s["spec_name"])
        products.append({"product": p, "specs": spec_rows})

    return products, sorted(all_spec_keys)

def get_all_associations(conn):
    return [dict(r) for r in conn.execute("""
        SELECT ca.*, c.name as company_name, c.slug as company_slug,
               ac.name as associated_company_name
        FROM company_associations ca
        JOIN companies c ON ca.company_id = c.id
        LEFT JOIN companies ac ON ca.associated_company_id = ac.id
        ORDER BY c.name
    """)]

def get_company_associations(conn, company_id):
    return [dict(r) for r in conn.execute("""
        SELECT ca.*, c.name as company_name, c.slug as company_slug,
               ac.name as associated_company_name
        FROM company_associations ca
        JOIN companies c ON ca.company_id = c.id
        LEFT JOIN companies ac ON ca.associated_company_id = ac.id
        WHERE ca.company_id = ? OR ca.associated_company_id = ?
        ORDER BY c.name
    """, (company_id, company_id))]

def get_all_people(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM people ORDER BY name")]

def get_person(conn, person_id):
    row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    return dict(row) if row else None

def get_person_by_slug(conn, slug):
    row = conn.execute("SELECT * FROM people WHERE slug = ?", (slug,)).fetchone()
    return dict(row) if row else None

def get_person_roles(conn, person_id):
    return [dict(r) for r in conn.execute("""
        SELECT pr.*, c.name as entity_name, c.slug as entity_slug, c.company_type
        FROM person_roles pr
        LEFT JOIN companies c ON pr.entity_id = c.id AND pr.entity_type = 'company'
        WHERE pr.person_id = ?
        ORDER BY pr.start_year
    """, (person_id,))]

def get_all_person_roles(conn):
    return [dict(r) for r in conn.execute("""
        SELECT pr.*, p.name as person_name, p.slug as person_slug,
               c.name as entity_name, c.slug as entity_slug, c.company_type
        FROM person_roles pr
        JOIN people p ON pr.person_id = p.id
        LEFT JOIN companies c ON pr.entity_id = c.id AND pr.entity_type = 'company'
        ORDER BY p.name
    """)]

def search_people(conn, query):
    q = f"%{query}%"
    return [dict(r) for r in conn.execute("""
        SELECT * FROM people WHERE name LIKE ? OR title LIKE ? OR bio LIKE ? ORDER BY name
    """, (q, q, q))]

# --- Insight / aggregate queries ---------------------------------------------------------

# --- Case study metric extraction ---

import re as _re

_CASE_METRIC_PATTERNS = [
    # picks / hour
    (_re.compile(r'(\d+[+]?)\s*(picks)\s*/\s*(hr|hour)s?\b', _re.I), 'picks_per_hour', 'picks/hr'),
    # cases / hour
    (_re.compile(r'(\d+[+]?)\s*(cases)\s*/\s*(hr|hour)s?\b', _re.I), 'cases_per_hour', 'cases/hr'),
    # totes / hour
    (_re.compile(r'(\d+[+]?)\s*(totes|bins)\s*/\s*(hr|hour)s?\b', _re.I), 'bins_per_hour', 'bins/hr'),
    # items / hour
    (_re.compile(r'(\d+[+]?)\s*(items|units)\s*/\s*(hr|hour)s?\b', _re.I), 'items_per_hour', 'items/hr'),
    # order lines / day
    (_re.compile(r'(\d+[+]?)\s*(order lines)\s*/\s*day\b', _re.I), 'order_lines_per_day', 'lines/day'),
    # picks / day
    (_re.compile(r'(\d+[+]?)\s*(picks)\s*/\s*day\b', _re.I), 'picks_per_day', 'picks/day'),
    # cases / day
    (_re.compile(r'(\d+[+]?)\s*(cases)\s*/\s*day\b', _re.I), 'cases_per_day', 'cases/day'),
    # totes / day
    (_re.compile(r'(\d+[+]?)\s*(totes|bins)\s*/\s*day\b', _re.I), 'bins_per_day', 'bins/day'),
    # SKUs / hour
    (_re.compile(r'(\d+[+]?)\s*(SKUs|skus|items|products)\s*/\s*hr\b', _re.I), 'skus_per_hour', 'SKUs/hr'),
    # Productivity multipliers: Xx picking / throughput / storage / density / productivity / labor
    (_re.compile(r'(\d+[+]?\.?\d*)\s*x\s*(picking\s*(efficiency|productivity)?)', _re.I), 'picking_efficiency_multiplier', 'x'),
    (_re.compile(r'(\d+[+]?\.?\d*)\s*x\s*(storage\s*(density|capacity)?)', _re.I), 'storage_density_multiplier', 'x'),
    (_re.compile(r'(\d+[+]?\.?\d*)\s*x\s*(throughput|capacity)', _re.I), 'throughput_multiplier', 'x'),
    (_re.compile(r'(\d+[+]?\.?\d*)\s*x\s*(productivity|labor productivity)', _re.I), 'productivity_multiplier', 'x'),
    # catch-all Xx multipler (use after more specific ones)
    (_re.compile(r'(\d+[+]?\.?\d*)\s*x\s*(improvement|gain|increase|faster)', _re.I), 'throughput_multiplier', 'x'),
    # Percentage: uptime / reliability
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(uptime|reliability)', _re.I), 'uptime_pct', '%'),
    # Percentage: inventory accuracy
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(inventory\s*)?accuracy', _re.I), 'inventory_accuracy_pct', '%'),
    # Percentage: pick rate
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(pick rate|successful pick rate)', _re.I), 'pick_rate_pct', '%'),
    # Percentage: delivery reliability
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(delivery accuracy|delivery reliability)', _re.I), 'delivery_reliability_pct', '%'),
    # Percentage: reductions (floor space, labor, walking, travel, overtime, temp, cost)
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(floor space|space)', _re.I), 'floor_space_reduction_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(labor|labor cost)', _re.I), 'labor_reduction_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(walking|walk time|travel|travel time)', _re.I), 'travel_time_reduction_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(overtime|temp|temporary)', _re.I), 'labor_reduction_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(injur|ergonomic)', _re.I), 'injury_reduction_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(buffer\s*)?inventory', _re.I), 'inventory_reduction_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(cost|gowning)', _re.I), 'cost_reduction_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(energy)', _re.I), 'energy_savings_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(less|fewer|lower|reduction|decrease)\s+(mispicks|error)', _re.I), 'error_reduction_pct', '%'),
    # Percentage: positive improvements
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(faster|improvement|increase|gain)\s+(throughput|productivity|efficiency)', _re.I), 'throughput_improvement_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(faster|improvement|increase)\s+(transport|capacity|density)', _re.I), 'improvement_pct', '%'),
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(faster)\b', _re.I), 'time_reduction_pct', '%'),
    # Robots deployed
    (_re.compile(r'(\d+[+]?)\s*(robots|units|systems)\s+(deployed|installed|operating)', _re.I), 'robots_deployed', 'robots'),
    (_re.compile(r'deployed\s+(\d+[+]?)\s*(robots|units|systems)', _re.I), 'robots_deployed', 'robots'),
    # SKU / item count
    (_re.compile(r'(\d+[+]?)\s*(SKUs|skus)\s+(online|handled|processed|managed|stored)?', _re.I), 'sku_count', 'SKUs'),
    (_re.compile(r'(\d+\.?\d*)\s*(million|billion)\s*(items|units|products)\s*(processed|handled)?', _re.I), 'items_processed', 'items'),
    # ROI / payback
    (_re.compile(r'(\d+)\s*(month|year)\s*(ROI|payback|PBP|payback period)', _re.I), 'roi_months', 'months'),
    (_re.compile(r'(ROI|payback|payback period|PBP)\s*(in|of|:)?\s*(\d+)\s*(month|year)', _re.I), 'roi_months', 'months'),
    # Time reductions (retrieval, dispatch, cycle, prep)
    (_re.compile(r'(\d+(?:\.\d+)?)\s*(min|minute)\s*(to|–|-|,)\s*(\d+(?:\.\d+)?)\s*(sec|second)\s+(retrieval|retrieve)', _re.I), 'retrieval_time_seconds', 'seconds'),
    (_re.compile(r'(\d+)\s*(min|hr|hour)\s*(to|–|-|,)\s*(\d+)\s*(min|hr|hour)\s+(retrieval|dispatch|preparation|prep|order|cycle|processing)', _re.I), 'process_time_minutes', 'minutes'),
    # Speed
    (_re.compile(r'(\d+\.?\d*)\s*m/s', _re.I), 'robot_speed_mps', 'm/s'),
    # Payload
    (_re.compile(r'(\d+\.?\d*)\s*(kg|lb|lbs)\s+payload', _re.I), 'payload_capacity', 'kg'),
    # Associates redeployed / positions eliminated
    (_re.compile(r'(\d+[+]?)\s*(associates|employees|positions)\s+(redeployed|reassigned|eliminated|replaced)', _re.I), 'associates_redeployed', 'associates'),
    # Square footage
    (_re.compile(r'(\d+[+]?\.?\d*)\s*(sq\s*ft|ft²|sf|square\s*feet)\b', _re.I), 'facility_sqft', 'sqft'),
    # Retrieval time in absolute seconds
    (_re.compile(r'under\s+(\d+\.?\d*)\s*(sec|second)\s+(retrieval|retrieve)', _re.I), 'retrieval_time_seconds', 'seconds'),
    (_re.compile(r'(less than|<)\s*(\d+)\s*(min|minute)\s+(retrieval|retrieve)', _re.I), 'retrieval_time_minutes', 'minutes'),
    # Sort points (scan for "sortation" context)
    (_re.compile(r'(\d+[+]?)\s*(sort|sortation)\s+(points|lanes|chutes|diverts)', _re.I), 'sort_points', 'points'),
    # Dock doors / sites
    (_re.compile(r'(\d+[+]?)\s*(fulfillment\s+)?centers|deployed\s+across\s+(\d+)\s+centers', _re.I), 'facilities_deployed', 'facilities'),
    # Chucks / fleet size across DCs
    (_re.compile(r'(\d+)\s+Chucks\s+across\s+(\d+)\s+DC', _re.I), 'robots_deployed', 'robots'),
    # exact % remaining
    (_re.compile(r'(\d+\.?\d*)\s*%\s*(autonomous|automated)\s+(unloading|operation)', _re.I), 'automation_rate_pct', '%'),
    # Order lines processed
    (_re.compile(r'(\d+[+]?)\s*(order lines|order lines per day)', _re.I), 'order_lines_per_day', 'lines/day'),
]

_TPH_KEYWORDS = {
    'picks_per_hour', 'cases_per_hour', 'bins_per_hour', 'items_per_hour',
    'picks_per_day', 'cases_per_day', 'bins_per_day', 'order_lines_per_day', 'skus_per_hour',
}


def _parse_numeric(value_str):
    """Parse a number string like '800+', '3-5', '4,000' into a float."""
    s = str(value_str).replace(',', '').replace('+', '').replace('>', '').replace('<', '').strip()
    if '-' in s:
        parts = [p.strip() for p in s.split('-') if p.strip() and p.strip().replace('.', '').isdigit()]
        if len(parts) >= 2:
            nums = [float(p) for p in parts]
            return sum(nums) / len(nums)
        elif parts:
            return float(parts[0])
    try:
        return float(s)
    except ValueError:
        return None


def _preprocess_numbers(text):
    """Remove commas from within numbers so patterns match '50000' instead of '50,000'."""
    return _re.sub(r'(?<=\d),(?=\d)', '', text)

def _extract_metrics_from_text(text):
    """Apply all regex patterns to a piece of text, return list of (name, num, text, unit, source)."""
    results = []
    seen_metrics = set()
    cleaned = _preprocess_numbers(text)
    for pattern, metric_name, unit in _CASE_METRIC_PATTERNS:
        for m in pattern.finditer(cleaned):
            # Find the numeric group (varies per pattern - usually first capture group)
            num_val = None
            for g in m.groups():
                if g is not None and any(c.isdigit() for c in g) and g[0].isdigit():
                    num_val = _parse_numeric(g)
                    if num_val is not None:
                        break
            raw_text = m.group(0).strip()
            # Convert units
            display_unit = unit
            if unit == 'seconds' and 'min' in raw_text.lower():
                if num_val is not None:
                    num_val = num_val * 60
                display_unit = 'seconds'
            elif unit == 'minutes' and 'hr' in raw_text.lower():
                if num_val is not None:
                    num_val = num_val * 60
                display_unit = 'minutes'
            elif unit == 'kg' and 'lb' in raw_text.lower():
                if num_val is not None:
                    num_val = round(num_val * 0.453592, 1)
                display_unit = 'kg'

            key = (metric_name, raw_text)
            if key not in seen_metrics:
                seen_metrics.add(key)
                results.append((metric_name, num_val, raw_text, display_unit, 'parsed'))
    return results


def _infer_metrics(parsed, company_name):
    """Given parsed metrics, derive additional inferred metrics."""
    inferred = []
    parsed_dict = {}
    for name, num_val, raw_text, unit, source in parsed:
        if name not in parsed_dict:
            parsed_dict[name] = []
        parsed_dict[name].append(num_val)

    def _best(nums):
        vals = [n for n in nums if n is not None]
        return max(vals) if vals else None

    picks_hr = _best(parsed_dict.get('picks_per_hour', []))
    cases_hr = _best(parsed_dict.get('cases_per_hour', []))
    bins_hr = _best(parsed_dict.get('bins_per_hour', []))
    items_hr = _best(parsed_dict.get('items_per_hour', []))
    picks_day = _best(parsed_dict.get('picks_per_day', []))
    cases_day = _best(parsed_dict.get('cases_per_day', []))
    bins_day = _best(parsed_dict.get('bins_per_day', []))
    robots = _best(parsed_dict.get('robots_deployed', []))
    skus = _best(parsed_dict.get('sku_count', []))
    sqft = _best(parsed_dict.get('facility_sqft', []))
    ret_sec = _best(parsed_dict.get('retrieval_time_seconds', []))
    ret_min = _best(parsed_dict.get('retrieval_time_minutes', []))
    throughput_mult = _best(parsed_dict.get('throughput_multiplier', []))
    storage_mult = _best(parsed_dict.get('storage_density_multiplier', []))
    floor_space_red = _best(parsed_dict.get('floor_space_reduction_pct', []))
    items_proc = _best(parsed_dict.get('items_processed', []))
    olpd = _best(parsed_dict.get('order_lines_per_day', []))
    skus_hr = _best(parsed_dict.get('skus_per_hour', []))

    # items per case = picks/hr / cases/hr
    if picks_hr and cases_hr and cases_hr > 0:
        ipc = round(picks_hr / cases_hr, 1)
        inferred.append(('items_per_case', ipc, f'~{ipc} items/case (inferred from picks ÷ cases)', 'items/case', 'inferred'))

    # items per case from picks/day and cases/day
    if picks_day and cases_day and cases_day > 0:
        ipc = round(picks_day / cases_day, 1)
        if 'items_per_case' not in {x[0] for x in inferred}:
            inferred.append(('items_per_case', ipc, f'~{ipc} items/case (inferred from picks ÷ cases)', 'items/case', 'inferred'))

    # bins per hour per robot
    if bins_hr and robots and robots > 0:
        bpr = round(bins_hr / robots, 1)
        inferred.append(('bins_per_hour_per_robot', bpr, f'~{bpr} bins/hr/robot (inferred)', 'bins/hr/robot', 'inferred'))

    # storage per unit of throughput (density multiplier / throughput multiplier)
    if storage_mult and throughput_mult and throughput_mult > 0:
        sput = round(storage_mult / throughput_mult, 2)
        inferred.append(('storage_per_throughput_ratio', sput, f'~{sput} storage:throughput ratio (inferred from multipliers)', 'ratio', 'inferred'))

    # max storage size: use SKU count as proxy, or items processed
    if skus:
        inferred.append(('max_storage_items', skus, f'~{skus:,.0f} SKUs (direct)', 'SKUs', 'inferred'))
    if items_proc:
        inferred.append(('max_storage_items', items_proc, f'~{items_proc:,.0f} items (direct)', 'items', 'inferred'))

    # sku count per robot
    if skus and robots and robots > 0:
        spr = round(skus / robots, 0)
        inferred.append(('skus_per_robot', spr, f'~{spr:,.0f} SKUs/robot (inferred)', 'SKUs/robot', 'inferred'))

    # throughput per sqft (if both throughput and sqft available)
    if picks_day and sqft and sqft > 0:
        usf = round(picks_day / sqft, 4)
        inferred.append(('units_per_sqft', usf, f'~{usf} picks/sqft/day (inferred)', 'picks/sqft/day', 'inferred'))
    if cases_day and sqft and sqft > 0 and 'units_per_sqft' not in {x[0] for x in inferred}:
        usf = round(cases_day / sqft, 4)
        inferred.append(('units_per_sqft', usf, f'~{usf} cases/sqft/day (inferred)', 'cases/sqft/day', 'inferred'))

    # retrieval time (convert minutes to seconds if both present)
    if ret_min and not ret_sec:
        inferred.append(('retrieval_time_seconds', ret_min * 60, f'~{ret_min * 60}s retrieval (inferred from minutes)', 'seconds', 'inferred'))

    return inferred


def extract_case_study_metrics(conn, case_study_id):
    """Extract and store structured metrics for a single case study."""
    cs = conn.execute("SELECT * FROM case_studies WHERE id = ?", (case_study_id,)).fetchone()
    if not cs:
        return
    cs = dict(cs)

    # Remove old metrics for this case study
    conn.execute("DELETE FROM case_study_metrics WHERE case_study_id = ?", (case_study_id,))

    texts = [
        cs.get('metrics', ''),
        cs.get('results', ''),
        cs.get('challenge', ''),
        cs.get('solution', ''),
        cs.get('title', ''),
    ]

    all_parsed = []
    for t in texts:
        all_parsed.extend(_extract_metrics_from_text(t))

    # Get company name for context
    company_name = ''
    if cs.get('company_id'):
        c = conn.execute("SELECT name FROM companies WHERE id = ?", (cs['company_id'],)).fetchone()
        if c:
            company_name = c[0]

    inferred = _infer_metrics(all_parsed, company_name)

    # Dedup by metric_name (keep first occurrence)
    seen_names = set()
    deduped = []
    for entry in all_parsed + inferred:
        if entry[0] not in seen_names:
            seen_names.add(entry[0])
            deduped.append(entry)

    # Insert into DB
    for metric_name, num_val, raw_text, unit, source in deduped:
        conn.execute("""INSERT INTO case_study_metrics
                        (case_study_id, metric_name, metric_value_num, metric_value_text, unit, source)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (case_study_id, metric_name, num_val, raw_text, unit, source))
    conn.commit()


def extract_all_case_study_metrics(conn):
    """Extract metrics for all case studies."""
    rows = conn.execute("SELECT id FROM case_studies").fetchall()
    for (cs_id,) in rows:
        extract_case_study_metrics(conn, cs_id)
    return len(rows)


# --- Insight query functions ---

def get_insight_summary_kpis(conn):
    rows = conn.execute("""
        SELECT 'Companies' AS kpi, COUNT(*) AS val FROM companies
        UNION ALL SELECT 'Products', COUNT(*) FROM products
        UNION ALL SELECT 'Case Studies', COUNT(*) FROM case_studies
        UNION ALL SELECT 'Associations', COUNT(*) FROM company_associations
        UNION ALL SELECT 'People', COUNT(*) FROM people
        UNION ALL SELECT 'Products with Bins', COUNT(DISTINCT product_id) FROM product_bins
    """).fetchall()
    return [(r["kpi"], r["val"]) for r in rows]


def get_insight_company_counts(conn, dimension):
    col = {"country": "country", "business_model": "business_model",
           "company_type": "company_type", "status": "status"}.get(dimension, dimension)
    rows = conn.execute(f"SELECT {col} AS value, COUNT(*) AS count FROM companies WHERE {col} IS NOT NULL AND {col} != '' GROUP BY {col} ORDER BY count DESC").fetchall()
    return [(r["value"], r["count"]) for r in rows]


def get_insight_business_model_counts(conn):
    return get_insight_company_counts(conn, "business_model")


def get_insight_status_counts(conn):
    return get_insight_company_counts(conn, "status")


def get_insight_founding_year_histogram(conn):
    return [(r["year"], r["count"]) for r in conn.execute("""
        SELECT founded_year AS year, COUNT(*) AS count
        FROM companies WHERE founded_year IS NOT NULL
        GROUP BY year ORDER BY year
    """).fetchall()]


def get_insight_release_year_histogram(conn):
    return [(r["year"], r["count"]) for r in conn.execute("""
        SELECT release_year AS year, COUNT(*) AS count
        FROM products WHERE release_year IS NOT NULL
        GROUP BY year ORDER BY year
    """).fetchall()]


def get_insight_products_by_category(conn):
    return [(r["category"], r["count"]) for r in conn.execute("""
        SELECT COALESCE(category, 'Unknown') AS category, COUNT(*) AS count
        FROM products GROUP BY category ORDER BY count DESC
    """).fetchall()]


def get_insight_capability_coverage(conn):
    rows = conn.execute("""
        SELECT c.name AS capability, COUNT(DISTINCT pc.product_id) AS product_count
        FROM product_capabilities pc
        JOIN capabilities c ON pc.capability_id = c.id
        GROUP BY c.name ORDER BY product_count DESC
    """).fetchall()
    return [(r["capability"], r["product_count"]) for r in rows]


def get_insight_capability_by_category(conn):
    return [dict(r) for r in conn.execute("""
        SELECT p.category, c.name AS capability, COUNT(DISTINCT pc.product_id) AS product_count
        FROM product_capabilities pc
        JOIN capabilities c ON pc.capability_id = c.id
        JOIN products p ON pc.product_id = p.id
        WHERE p.category IS NOT NULL
        GROUP BY p.category, c.name
        ORDER BY p.category, product_count DESC
    """).fetchall()]


def get_insight_spec_averages_by_category(conn, spec_keys):
    if not spec_keys:
        return []
    placeholders = ",".join("?" * len(spec_keys))
    rows = conn.execute(f"""
        SELECT p.category, ps.spec_name AS spec_key,
               ROUND(AVG(CAST(ps.spec_value AS REAL)), 1) AS avg_val
        FROM product_specs ps
        JOIN products p ON ps.product_id = p.id
        WHERE p.category IS NOT NULL
          AND ps.spec_name IN ({placeholders})
          AND ps.spec_value GLOB '[0-9]*'
        GROUP BY p.category, ps.spec_name
        ORDER BY p.category, ps.spec_name
    """, spec_keys).fetchall()
    return [dict(r) for r in rows]


def get_insight_engineering_percent(conn):
    return [dict(r) for r in conn.execute("""
        SELECT name, slug,
               CAST(REPLACE(REPLACE(employees, ',', ''), '+', '') AS REAL) AS emp_numeric,
               CAST(REPLACE(REPLACE(engineering_employees, ',', ''), '+', '') AS REAL) AS eng_numeric,
               engineering_pct
        FROM companies
        WHERE employees != '' AND employees IS NOT NULL
          AND engineering_employees != '' AND engineering_employees IS NOT NULL
        ORDER BY engineering_pct DESC
    """).fetchall()]


def get_insight_engineering_by_category(conn):
    return [dict(r) for r in conn.execute("""
        SELECT p.category,
               ROUND(AVG(CAST(NULLIF(c.engineering_pct, '') AS REAL)), 1) AS avg_eng_pct,
               COUNT(DISTINCT c.id) AS company_count
        FROM companies c
        JOIN products p ON p.company_id = c.id
        WHERE c.engineering_pct != '' AND c.engineering_pct IS NOT NULL
        GROUP BY p.category
        ORDER BY avg_eng_pct DESC
    """).fetchall()]


def get_insight_case_studies_by_industry(conn):
    return [(r["industry"], r["count"]) for r in conn.execute("""
        SELECT COALESCE(NULLIF(industry, ''), 'Unknown') AS industry, COUNT(*) AS count
        FROM case_studies GROUP BY industry ORDER BY count DESC
    """).fetchall()]


def get_insight_top_customers(conn, limit=10):
    return [(r["customer"], r["count"]) for r in conn.execute("""
        SELECT customer, COUNT(*) AS count
        FROM case_studies WHERE customer IS NOT NULL AND customer != ''
        GROUP BY customer ORDER BY count DESC LIMIT ?
    """, (limit,)).fetchall()]


def get_insight_case_studies_by_company(conn):
    return [dict(r) for r in conn.execute("""
        SELECT c.name AS company, c.slug, COUNT(cs.id) AS cs_count
        FROM companies c
        JOIN case_studies cs ON cs.company_id = c.id
        GROUP BY c.id ORDER BY cs_count DESC
    """).fetchall()]


def get_insight_association_type_counts(conn):
    return [(r["association_type"], r["count"]) for r in conn.execute("""
        SELECT association_type, COUNT(*) AS count
        FROM company_associations GROUP BY association_type ORDER BY count DESC
    """).fetchall()]


def get_insight_most_connected(conn, limit=10):
    return [dict(r) for r in conn.execute("""
        SELECT c.name, c.slug, COUNT(ca.id) AS connection_count
        FROM companies c
        JOIN company_associations ca ON ca.company_id = c.id OR ca.associated_company_id = c.id
        GROUP BY c.id ORDER BY connection_count DESC LIMIT ?
    """, (limit,)).fetchall()]


def get_insight_people_by_company(conn):
    return [dict(r) for r in conn.execute("""
        SELECT c.name AS company, c.slug, COUNT(pr.id) AS people_count
        FROM companies c
        JOIN person_roles pr ON pr.entity_id = c.id AND pr.entity_type = 'company'
        GROUP BY c.id ORDER BY people_count DESC
    """).fetchall()]


def get_insight_role_distribution(conn):
    return [(r["role"], r["count"]) for r in conn.execute("""
        SELECT role, COUNT(*) AS count
        FROM person_roles GROUP BY role ORDER BY count DESC
    """).fetchall()]


def get_insight_bin_type_counts(conn):
    return [(r["bin_type"], r["count"]) for r in conn.execute("""
        SELECT bin_type, COUNT(*) AS count
        FROM product_bins GROUP BY bin_type ORDER BY count DESC
    """).fetchall()]


def get_insight_bins_detail(conn):
    return [dict(r) for r in conn.execute("""
        SELECT pb.*, p.name AS product_name, p.slug AS product_slug, p.category
        FROM product_bins pb
        JOIN products p ON pb.product_id = p.id
        ORDER BY p.category, p.name, pb.label
    """).fetchall()]


def get_insight_payload_histogram(conn):
    return [dict(r) for r in conn.execute("""
        SELECT p.name AS product_name, p.slug AS product_slug, pb.label, pb.max_payload_kg, pb.bin_type
        FROM product_bins pb
        JOIN products p ON pb.product_id = p.id
        WHERE pb.max_payload_kg IS NOT NULL
        ORDER BY pb.max_payload_kg
    """).fetchall()]


def get_insight_grid_heights(conn):
    return [dict(r) for r in conn.execute("""
        SELECT p.name AS product_name, p.slug AS product_slug, pb.label, pb.grid_height_m
        FROM product_bins pb
        JOIN products p ON pb.product_id = p.id
        WHERE pb.grid_height_m IS NOT NULL
        ORDER BY pb.grid_height_m
    """).fetchall()]


def get_insight_academic_origins(conn):
    return [dict(r) for r in conn.execute("""
        SELECT c.name AS company_name, c.slug, ac.name AS university, ca.notes
        FROM company_associations ca
        JOIN companies c ON ca.company_id = c.id
        JOIN companies ac ON ca.associated_company_id = ac.id
        WHERE ca.association_type = 'academic_origin'
        ORDER BY ac.name
    """).fetchall()]


# --- Case study metrics queries ---

def get_case_study_metrics(conn, metric_name=None, min_value=None):
    """Fetch structured case study metrics, optionally filtered by name and min numeric value."""
    query = """
        SELECT csm.*, cs.title AS case_title, cs.customer, cs.industry,
               cs.url AS case_url, co.name AS company_name, co.slug AS company_slug
        FROM case_study_metrics csm
        JOIN case_studies cs ON csm.case_study_id = cs.id
        JOIN companies co ON cs.company_id = co.id
        WHERE 1=1
    """
    params = []
    if metric_name:
        query += " AND csm.metric_name = ?"
        params.append(metric_name)
    if min_value is not None:
        query += " AND csm.metric_value_num >= ?"
        params.append(min_value)
    query += " ORDER BY csm.metric_value_num DESC"
    return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_case_study_metric_summary(conn, metric_name):
    """Get summary stats for a specific numeric metric."""
    rows = conn.execute("""
        SELECT COUNT(*) AS count,
               ROUND(AVG(metric_value_num), 1) AS avg_val,
               ROUND(MIN(metric_value_num), 1) AS min_val,
               ROUND(MAX(metric_value_num), 1) AS max_val,
               unit
        FROM case_study_metrics
        WHERE metric_name = ? AND metric_value_num IS NOT NULL
    """, (metric_name,)).fetchall()
    return [dict(r) for r in rows]


def get_case_study_metric_breakdown(conn, metric_name):
    """Get per-company average for a metric."""
    rows = conn.execute("""
        SELECT co.name AS company, co.slug,
               ROUND(AVG(csm.metric_value_num), 1) AS avg_val,
               COUNT(*) AS case_count,
               csm.unit
        FROM case_study_metrics csm
        JOIN case_studies cs ON csm.case_study_id = cs.id
        JOIN companies co ON cs.company_id = co.id
        WHERE csm.metric_name = ? AND csm.metric_value_num IS NOT NULL
        GROUP BY co.id
        ORDER BY avg_val DESC
    """, (metric_name,)).fetchall()
    return [dict(r) for r in rows]


def get_metric_coverage(conn):
    """Show which metrics are available for which companies (coverage matrix)."""
    rows = conn.execute("""
        SELECT co.name AS company, co.slug,
               csm.metric_name, csm.metric_value_num, csm.unit, csm.source
        FROM case_study_metrics csm
        JOIN case_studies cs ON csm.case_study_id = cs.id
        JOIN companies co ON cs.company_id = co.id
        ORDER BY co.name, csm.metric_name
    """).fetchall()
    return [dict(r) for r in rows]


def get_metric_names(conn):
    """Get all distinct metric names with counts."""
    rows = conn.execute("""
        SELECT metric_name, COUNT(*) AS count,
               COUNT(metric_value_num) AS numeric_count,
               MAX(metric_value_num) AS max_val, unit
        FROM case_study_metrics
        GROUP BY metric_name
        ORDER BY count DESC
    """).fetchall()
    return [dict(r) for r in rows]


# --- Image candidate queries ---

def get_product_image_candidates(conn, product_id):
    return [dict(r) for r in conn.execute("""
        SELECT * FROM product_image_candidates
        WHERE product_id = ? ORDER BY created_at DESC
    """, (product_id,)).fetchall()]

def get_company_image_candidates(conn, company_id):
    return [dict(r) for r in conn.execute("""
        SELECT * FROM company_image_candidates
        WHERE company_id = ? ORDER BY created_at DESC
    """, (company_id,)).fetchall()]

def set_product_image(conn, product_id, image_url):
    conn.execute("UPDATE products SET image_url = ?, image_source = 'manual' WHERE id = ?",
                 (image_url, product_id))
    conn.commit()

def set_company_image(conn, company_id, image_url):
    conn.execute("UPDATE companies SET logo_url = ?, image_source = 'manual' WHERE id = ?",
                 (image_url, company_id))
    conn.commit()

def reset_product_image(conn, product_id):
    conn.execute("UPDATE products SET image_source = 'auto' WHERE id = ?", (product_id,))
    conn.commit()

def reset_company_image(conn, company_id):
    conn.execute("UPDATE companies SET image_source = 'auto' WHERE id = ?", (company_id,))
    conn.commit()


# --- Image scraper ---

import urllib.request, urllib.parse, urllib.error
import re, ssl

def _fetch_url(url, timeout=8):
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None

def _extract_img_urls(html, base_url):
    urls = []
    parsed_base = urllib.parse.urlparse(base_url)
    has_base = bool(parsed_base.netloc)
    for m in re.finditer(r'<img[^>]+src=(["\'])(.*?)\1', html, re.I):
        src = m.group(2).strip()
        if src:
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                if not has_base:
                    continue
                src = f"{parsed_base.scheme}://{parsed_base.netloc}{src}"
            elif not src.startswith("http"):
                if not has_base:
                    continue
                src = urllib.parse.urljoin(base_url.rstrip("/") + "/", src)
            if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]):
                urls.append(src)
    return urls[:6]

def _favicon_url(domain):
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"

def _bing_image_search(query, max_results=4):
    q = urllib.parse.quote(query)
    url = f"https://www.bing.com/images/search?q={q}&form=HDRSC2"
    html = _fetch_url(url, timeout=10)
    if not html:
        return []
    urls = []
    seen = set()
    for m in re.finditer(r'<img[^>]+src=(["\'])(https?://.*?)\1', html, re.I):
        src = m.group(2)
        # Skip small / generic icons
        if any(seg in src.lower() for seg in ["flux-icon", "favicon", "th?id="]):
            continue
        if src not in seen:
            seen.add(src)
            urls.append(src)
        if len(urls) >= max_results:
            break
    return urls

def scrape_product_image_candidates(conn, product_id):
    p = get_product(conn, product_id)
    if not p:
        return [], "Product not found"
    if p.get("image_source") == "manual":
        return [], "Skipped (manual)"

    product_url = p.get("product_url")
    domain = urllib.parse.urlparse(product_url or "").netloc
    candidates = []

    # 1. Favicon
    fav = _favicon_url(domain)
    candidates.append(("favicon", fav))

    # 2. Img tags from product page
    html = ""
    if product_url:
        html = _fetch_url(product_url) or ""
    for src in _extract_img_urls(html, product_url or ""):
        candidates.append(("scrape", src))

    # 3. Bing image search
    search_terms = [f"{p['name']} robot", f"{p['name']} product"]
    for term in search_terms:
        for src in _bing_image_search(term):
            candidates.append(("search", src))

    # Dedup by URL
    seen = set()
    unique = []
    for source, src in candidates:
        if src not in seen:
            seen.add(src)
            unique.append((source, src))

    # Insert into DB
    inserted = 0
    for source, src in unique:
        existing = conn.execute("""
            SELECT id FROM product_image_candidates WHERE product_id = ? AND image_url = ?
        """, (product_id, src)).fetchone()
        if not existing:
            conn.execute("""INSERT INTO product_image_candidates
                            (product_id, image_url, source) VALUES (?, ?, ?)""",
                         (product_id, src, source))
            inserted += 1

    conn.commit()
    return unique, f"Found {len(unique)} candidates ({inserted} new)"

def scrape_company_image_candidates(conn, company_id):
    c = get_company(conn, company_id)
    if not c:
        return [], "Company not found"
    if c.get("image_source") == "manual":
        return [], "Skipped (manual)"

    domain = urllib.parse.urlparse(c.get("website") or "").netloc
    candidates = []

    # 1. Favicon
    fav = _favicon_url(domain)
    candidates.append(("favicon", fav))

    # 2. Img tags from website
    html = ""
    if c.get("website"):
        html = _fetch_url(c["website"]) or ""
    for src in _extract_img_urls(html, c["website"] or ""):
        candidates.append(("scrape", src))

    # 3. Bing image search
    for src in _bing_image_search(f"{c['name']} company logo"):
        candidates.append(("search", src))

    seen = set()
    unique = []
    for source, src in candidates:
        if src not in seen:
            seen.add(src)
            unique.append((source, src))

    inserted = 0
    for source, src in unique:
        existing = conn.execute("""
            SELECT id FROM company_image_candidates WHERE company_id = ? AND image_url = ?
        """, (company_id, src)).fetchone()
        if not existing:
            conn.execute("""INSERT INTO company_image_candidates
                            (company_id, image_url, source) VALUES (?, ?, ?)""",
                         (company_id, src, source))
            inserted += 1

    conn.commit()
    return unique, f"Found {len(unique)} candidates ({inserted} new)"

def scrape_all_product_image_candidates(conn):
    products = get_all_products(conn)
    results = []
    for p in products:
        if p.get("image_source") == "manual":
            results.append((p["name"], "skipped"))
            continue
        cand, msg = scrape_product_image_candidates(conn, p["id"])
        results.append((p["name"], msg))
    return results

def scrape_all_company_image_candidates(conn):
    companies = get_all_companies(conn)
    results = []
    for c in companies:
        if c.get("image_source") == "manual":
            results.append((c["name"], "skipped"))
            continue
        cand, msg = scrape_company_image_candidates(conn, c["id"])
        results.append((c["name"], msg))
    return results


# --- Case Study Scraper Utilities ---

def upsert_case_study(conn, data):
    """Insert a new case study or update by URL. Returns the row id."""
    existing = None
    if data.get("url"):
        existing = conn.execute(
            "SELECT id FROM case_studies WHERE url = ?", (data["url"],)
        ).fetchone()
    if existing:
        conn.execute("""UPDATE case_studies SET
            title=?, customer=?, industry=?, challenge=?, solution=?,
            results=?, metrics=?, featured_image=?, published_date=?,
            updated_at=CURRENT_TIMESTAMP
            WHERE id=?""",
            (data.get("title", ""), data.get("customer", ""),
             data.get("industry", ""), data.get("challenge", ""),
             data.get("solution", ""), data.get("results", ""),
             data.get("metrics", ""), data.get("featured_image", ""),
             data.get("published_date", ""), existing["id"]))
        conn.commit()
        return existing["id"]
    cur = conn.execute("""INSERT INTO case_studies
        (company_id, product_id, title, customer, industry,
         challenge, solution, results, metrics, url,
         featured_image, published_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (data.get("company_id"), data.get("product_id"),
         data.get("title", ""), data.get("customer", ""),
         data.get("industry", ""), data.get("challenge", ""),
         data.get("solution", ""), data.get("results", ""),
         data.get("metrics", ""), data.get("url", ""),
         data.get("featured_image", ""),
         data.get("published_date", "")))
    conn.commit()
    return cur.lastrowid


def get_case_study_by_url(conn, url):
    """Return a case study row dict by URL, or None."""
    row = conn.execute("SELECT * FROM case_studies WHERE url = ?", (url,)).fetchone()
    return dict(row) if row else None


def get_companies_for_scrape(conn):
    """Return companies suitable for case study scraping (has website, not educational/investor)."""
    rows = conn.execute("""
        SELECT * FROM companies
        WHERE website IS NOT NULL AND website != ''
          AND (company_type IS NULL OR company_type NOT IN ('educational', 'investor'))
        ORDER BY name
    """).fetchall()
    return [dict(r) for r in rows]


def get_existing_cs_urls(conn, company_id=None):
    """Return list of already-stored case study URLs, optionally filtered by company."""
    if company_id:
        rows = conn.execute(
            "SELECT url FROM case_studies WHERE company_id = ? AND url IS NOT NULL AND url != ''",
            (company_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT url FROM case_studies WHERE url IS NOT NULL AND url != ''"
        ).fetchall()
    return [r["url"] for r in rows]
