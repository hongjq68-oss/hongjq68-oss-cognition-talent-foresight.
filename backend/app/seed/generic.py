"""General-purpose knowledge used when the engine runs for a company other than Cognition.

Growth themes play the role of customer segments: each is a kind of business goal with the
business needs (problems) it creates and the skills those needs call for. Role types cover the
job families any growing tech company hires. All of it is analyst judgement (hypotheses)."""
from .capabilities import C

GENERIC = "*"

EXTRA_CAPABILITIES = [
    C("ml_research", "AI/ML research & model training", "technical",
      "Trains, evaluates and ships machine-learning models.", 5, 20, "hire",
      ["trained a model", "fine-tuned", "machine learning", "paper", "evaluation benchmark"]),
    C("data_science", "Data science & analytics", "technical",
      "Turns product and business data into decisions and experiments.", 3, 10, "hire",
      ["a/b test", "analytics", "data science", "forecasting model", "dashboard"]),
    C("product_management", "Product management", "delivery",
      "Decides what to build, for whom and why, and gets it shipped.", 3, 12, "hire",
      ["launched", "product roadmap", "product manager", "shipped feature", "user research"]),
    C("product_design", "Product & UX design", "technical",
      "Designs products people find easy and useful.", 3, 10, "hire",
      ["design system", "ux research", "prototype", "figma", "user experience"]),
    C("growth_marketing", "Marketing & growth", "commercial",
      "Builds demand: brand, content, product marketing and growth loops.", 3, 10, "hire",
      ["campaign", "go-to-market launch", "growth", "product marketing", "brand"]),
    C("customer_success", "Customer success & support", "delivery",
      "Keeps customers successful so they renew and expand.", 2, 8, "hire",
      ["customer success", "onboarding", "renewal", "support", "net retention"]),
    C("people_talent", "Recruiting & people", "transformation",
      "Hires and grows the team as the company scales.", 2, 8, "hire",
      ["hired", "recruiting", "talent acquisition", "people operations", "employer brand"]),
    C("business_ops", "Finance, legal & business operations", "transformation",
      "Runs finance, legal, compliance and operations for a scaling business.", 3, 12, "hire",
      ["finance", "legal", "compliance", "business operations", "entity setup"]),
]

# Growth themes. data mirrors the segment fields the UI shows.
def T(id, name, goals, challenges, needs, gtm):
    return dict(id=id, name=name, data=dict(goals=goals, challenges=challenges, cognition_needs=needs), gtm=gtm)

THEMES = [
    T("t_market", "Opening or growing a country",
      ["Win the first named customers in the country", "Build a local team that can sell and deliver"],
      ["No local brand or references yet", "Local language, laws and buying habits"],
      ["A country lead who has built a business from zero", "Local sellers with existing relationships"],
      {"market_creation": 1.0, "team_building": 0.8, "exec_stakeholder_mgmt": 0.6}),
    T("t_enterprise", "Winning large and regulated enterprise customers",
      ["Land multi-year enterprise contracts", "Pass security, risk and procurement review"],
      ["Long sales cycles", "Security and compliance review", "Many stakeholders per deal"],
      ["Enterprise sellers who have closed regulated customers", "Solution architects who can pass security review"],
      {"enterprise_sales_fsi": 1.0, "strategic_account_mgmt": 0.8, "solution_architecture": 0.8, "procurement_navigation": 0.6}),
    T("t_product", "Shipping product faster and scaling the platform",
      ["Ship features faster", "Keep the platform reliable as usage grows"],
      ["Hiring senior engineers is slow", "Platform reliability at scale"],
      ["Senior engineers who have scaled a product", "Product managers and designers close to customers"],
      {"software_engineering": 0.6}),
    T("t_ai", "Building AI into the product",
      ["Launch AI features customers pay for", "Run models safely and cheaply at scale"],
      ["Scarce ML talent", "Model quality, cost and safety"],
      ["Engineers who have shipped LLM or ML features", "Researchers who can train and evaluate models"],
      {"customer_discovery": 0.4}),
    T("t_partners", "Selling and delivering through partners",
      ["Partners bring and deliver a large share of deals", "Marketplace and reseller listings"],
      ["Partners need training and support", "Channel conflict"],
      ["Alliance leaders with SI or cloud-marketplace experience", "Partner engineers who can train partner teams"],
      {"partner_development": 1.0, "strategic_account_mgmt": 0.5}),
    T("t_growth", "Growing users and brand",
      ["Grow users and sign-ups in the region", "Become a known brand locally"],
      ["Low local awareness", "Localising product and marketing"],
      ["Marketers who have grown a product in the region", "Growth and data people who run experiments"],
      {"growth_marketing": 1.0, "customer_discovery": 0.5}),
    T("t_customers", "Keeping and expanding existing customers",
      ["Higher renewals and expansion", "Customers who succeed and refer others"],
      ["Onboarding at scale", "Proving value to justify expansion"],
      ["Customer success leads with expansion targets", "Technical support engineers"],
      {"customer_success": 1.0, "value_selling": 0.6, "strategic_account_mgmt": 0.6}),
    T("t_trust", "Security, privacy and compliance",
      ["Meet each country's data and security rules", "Make trust a selling point"],
      ["Data-residency and privacy laws", "Certifications and audits"],
      ["Security engineers and architects", "Compliance and legal people who know local rules"],
      {"procurement_navigation": 0.5}),
    T("t_scale", "Scaling the company",
      ["Hire quickly without lowering the bar", "Set up finance, legal and operations in each country"],
      ["Hiring speed", "Running entities and payroll in many countries"],
      ["Recruiters who have scaled teams in APAC", "Finance and operations leads for regional entities"],
      {"team_building": 0.6}),
]
THEME_GTM = {t["id"]: t["gtm"] for t in THEMES}

NOW, RAMP, LATER = [1.0, 1.0, 0.9, 0.8], [0.6, 0.9, 1.0, 1.0], [0.3, 0.6, 0.9, 1.0]


def N(id, theme, name, desc, severity, profile, caps):
    return dict(id=id, segment_id=theme, name=name, description=desc, severity=severity, complexity=3,
                pattern="industry_pattern", horizon_profile=profile, capabilities=caps, cognition_use_cases=[],
                adoption_barriers=[], signal_ids=[], evidence_class="hypothesis")

NEEDS = [
    N("g-market-launch", "t_market", "Build a business in a new country",
      "Someone has to own the country: first customers, first hires and local partners.", 1.0, NOW,
      {"market_creation": (1.0, "Builds the market from zero"), "team_building": (0.8, "Hires the first local team"),
       "exec_stakeholder_mgmt": (0.6, "Opens doors with local leaders"), "ambiguity": (0.5, "")}),
    N("g-market-local-sales", "t_market", "Sell in the local language and culture",
      "Local buyers expect local sellers and local references.", 0.8, RAMP,
      {"solution_selling": (0.8, ""), "customer_discovery": (0.6, ""), "japanese_enterprise": (0.3, "If Japan is in scope")}),
    N("g-ent-deals", "t_enterprise", "Close large enterprise deals",
      "Big customers buy through committees, security review and procurement.", 1.0, NOW,
      {"enterprise_sales_fsi": (1.0, ""), "procurement_navigation": (0.8, ""), "solution_architecture": (0.8, ""),
       "exec_stakeholder_mgmt": (0.7, ""), "security_architecture": (0.5, "")}),
    N("g-ent-deploy", "t_enterprise", "Get enterprise customers live",
      "Deals only turn into revenue when the product is running inside the customer.", 0.8, RAMP,
      {"technical_implementation": (1.0, ""), "systems_integration": (0.7, ""), "change_management": (0.5, "")}),
    N("g-prod-speed", "t_product", "Ship product faster",
      "More product and engineering capacity close to customers.", 0.9, NOW,
      {"software_engineering": (1.0, ""), "product_management": (0.8, ""), "product_design": (0.6, ""), "qa_test_automation": (0.3, "")}),
    N("g-prod-scale", "t_product", "Keep the platform fast and reliable",
      "More users and data put pressure on infrastructure.", 0.7, RAMP,
      {"cloud_infra": (1.0, ""), "dev_productivity": (0.6, ""), "data_engineering": (0.5, "")}),
    N("g-ai-features", "t_ai", "Launch AI features",
      "Customers expect AI built into the product.", 0.9, NOW,
      {"agentic_systems": (1.0, ""), "ml_research": (0.7, ""), "data_engineering": (0.6, ""), "product_management": (0.4, "")}),
    N("g-ai-research", "t_ai", "Train and evaluate models",
      "Model quality and cost decide the product.", 0.7, RAMP,
      {"ml_research": (1.0, ""), "data_science": (0.6, ""), "cloud_infra": (0.4, "")}),
    N("g-partner-channel", "t_partners", "Build a partner channel",
      "Consultancies, resellers and cloud marketplaces bring deals.", 0.9, RAMP,
      {"partner_development": (1.0, ""), "change_management": (0.6, "Train partner teams"), "technical_implementation": (0.5, "")}),
    N("g-growth-demand", "t_growth", "Create demand in the region",
      "Awareness, sign-ups and pipeline from marketing.", 0.9, NOW,
      {"growth_marketing": (1.0, ""), "data_science": (0.5, ""), "customer_discovery": (0.4, "")}),
    N("g-cust-retain", "t_customers", "Renew and expand customers",
      "Retention and expansion drive most long-term revenue.", 0.8, RAMP,
      {"customer_success": (1.0, ""), "strategic_account_mgmt": (0.7, ""), "value_selling": (0.6, ""), "technical_troubleshooting": (0.5, "")}),
    N("g-trust", "t_trust", "Meet security and data rules",
      "Each country has its own privacy, residency and certification rules.", 0.8, RAMP,
      {"security_architecture": (1.0, ""), "appsec_remediation": (0.6, ""), "business_ops": (0.5, "Legal and compliance")}),
    N("g-scale-org", "t_scale", "Hire and run the company at speed",
      "Recruiting, finance, legal and operations keep up with growth.", 0.7, NOW,
      {"people_talent": (1.0, ""), "business_ops": (0.8, ""), "operating_model": (0.4, "")}),
]


def R(id, name, summary, weights, keywords, backgrounds=(), assessment=()):
    return dict(id=id, name=name, summary=summary, capability_weights=weights, posting_keywords=list(keywords),
                unconventional_backgrounds=list(backgrounds), assessment=list(assessment))

ROLE_TYPES = [
    R("g_country_lead", "Country lead / general manager", "Owns a country: revenue, first hires and local partners.",
      {"market_creation": 1.0, "team_building": 0.9, "exec_stakeholder_mgmt": 0.8, "solution_selling": 0.5},
      ["General Manager", "Country Manager", "Country Lead", "Head of APAC", "Head of Japan", "Head of Korea", "Head of India", "Managing Director"],
      ["Founders who built and sold a local business", "Regional leads at cloud companies"], ["Plan the first 12 months in-country"]),
    R("g_enterprise_ae", "Enterprise account executive", "Wins and grows large enterprise customers.",
      {"enterprise_sales_fsi": 1.0, "solution_selling": 0.8, "strategic_account_mgmt": 0.7, "procurement_navigation": 0.6},
      ["Account Executive", "Account Director", "Sales Director", "Enterprise Sales", "Head of Sales", "Sales Manager", "Business Development"],
      ["Consultancy partners who sold large programmes", "Cloud company sellers"], ["Walk through a deal you won from first call"]),
    R("g_solutions", "Solutions engineer / architect", "Technical pre-sales: designs the solution and wins the technical decision.",
      {"solution_architecture": 1.0, "technical_implementation": 0.7, "customer_discovery": 0.6, "security_architecture": 0.4},
      ["Solutions Engineer", "Solutions Architect", "Sales Engineer", "Solution Architect", "Pre-Sales", "Presales", "Technical Account"],
      ["Bank platform engineers", "Consultancy architects"], ["Design a solution live for a sample customer"]),
    R("g_fde", "Forward-deployed / implementation engineer", "Gets the product live inside customers.",
      {"technical_implementation": 1.0, "software_engineering": 0.8, "independent_problem_solving": 0.7, "systems_integration": 0.6},
      ["Forward Deployed", "Deployment", "Implementation", "Integration Engineer", "Professional Services", "Customer Engineer", "Applied AI"],
      ["Consultants with real code history", "Startup engineers who did their own deployments"], ["Debug an unfamiliar codebase"]),
    R("g_software_eng", "Software engineer", "Builds and ships the product.",
      {"software_engineering": 1.0, "cloud_infra": 0.4, "qa_test_automation": 0.3},
      ["Software Engineer", "Engineer, ", "Backend", "Frontend", "Full Stack", "Fullstack", "Mobile", "iOS", "Android", "Developer", "Engineering Manager", "Member of Technical Staff"],
      ["Open-source maintainers", "Bank and telco product engineers"], ["Hands-on coding exercise"]),
    R("g_ml", "AI / ML engineer or researcher", "Builds, trains and evaluates the models behind AI features.",
      {"ml_research": 1.0, "agentic_systems": 0.8, "data_engineering": 0.5, "software_engineering": 0.5},
      ["Machine Learning", "ML Engineer", "Research Engineer", "Research Scientist", "AI Engineer", "Applied Scientist", "Researcher"],
      ["PhD graduates who published", "Engineers who shipped LLM features at startups"], ["Explain an evaluation they designed"]),
    R("g_data", "Data engineer / data scientist", "Builds data pipelines and turns data into decisions.",
      {"data_engineering": 1.0, "data_science": 0.9, "cloud_infra": 0.3},
      ["Data Engineer", "Data Scientist", "Analytics", "Data Analyst", "Analyst"],
      ["Bank and telco analytics teams"], ["Case study on a decision they changed with data"]),
    R("g_infra", "Infrastructure / reliability engineer", "Keeps the platform fast, reliable and cheap to run.",
      {"cloud_infra": 1.0, "dev_productivity": 0.7, "software_engineering": 0.6},
      ["Infrastructure", "SRE", "Site Reliability", "DevOps", "Platform Engineer", "Cloud Engineer", "Network"],
      ["Cloud company support engineers"], ["Incident walk-through"]),
    R("g_security", "Security engineer / architect", "Keeps the product and customers' data safe and passes security reviews.",
      {"security_architecture": 1.0, "appsec_remediation": 0.8, "cloud_infra": 0.4},
      ["Security", "Trust", "Privacy Engineer"], ["Bank security teams", "Security consultancies"], ["Threat-model a sample system"]),
    R("g_product", "Product manager", "Decides what to build next and gets it shipped.",
      {"product_management": 1.0, "customer_discovery": 0.7, "data_science": 0.3},
      ["Product Manager", "Product Lead", "Head of Product", "Product Owner", "Technical Program Manager", "Program Manager"],
      ["Founders", "Consultants who ran digital products"], ["Prioritise a sample roadmap"]),
    R("g_design", "Product designer", "Designs products people find easy and useful.",
      {"product_design": 1.0, "customer_discovery": 0.5, "product_management": 0.3},
      ["Designer", "Design Lead", "UX", "Researcher, User"], ["Agency designers who shipped products"], ["Portfolio review"]),
    R("g_marketing", "Marketing & growth", "Builds awareness and pipeline in the region.",
      {"growth_marketing": 1.0, "customer_discovery": 0.5, "data_science": 0.3},
      ["Marketing", "Growth", "Brand", "Communications", "Content", "Community", "Events", "PR "],
      ["Journalists and community builders"], ["Plan a launch in a new country"]),
    R("g_partner", "Partnerships / alliances", "Builds the partner channel: consultancies, resellers and marketplaces.",
      {"partner_development": 1.0, "strategic_account_mgmt": 0.6, "exec_stakeholder_mgmt": 0.5},
      ["Partner", "Alliance", "Channel", "Ecosystem"], ["Consultancy alliance managers", "Cloud marketplace leads"], ["Design a partner programme"]),
    R("g_customer_success", "Customer success & support", "Keeps customers successful so they renew and expand.",
      {"customer_success": 1.0, "technical_troubleshooting": 0.6, "value_selling": 0.5, "strategic_account_mgmt": 0.5},
      ["Customer Success", "Account Manager", "Support", "Customer Experience", "Onboarding", "Technical Support"],
      ["Hospitality and service leaders who moved into tech"], ["Rescue an at-risk account"]),
    R("g_recruiting", "Recruiting & people", "Hires and grows the team as the company scales.",
      {"people_talent": 1.0, "team_building": 0.5}, ["Recruit", "Talent", "People", "HR ", "Human Resources"],
      ["Agency recruiters who moved in-house"], ["Plan hiring for a new office"]),
    R("g_ops", "Finance, legal & operations", "Runs finance, legal, compliance and operations for each country.",
      {"business_ops": 1.0, "operating_model": 0.5, "procurement_navigation": 0.3},
      ["Finance", "Legal", "Counsel", "Compliance", "Operations", "Accounting", "Tax", "Strategy", "Policy", "Workplace"],
      ["Big-four accountants and lawyers"], ["Set up a new country entity"]),
]

# Skills for the new capabilities, added to the tracked companies whose people typically have them.
_BIG_TECH = ["aws", "microsoft", "gcp", "atlassian", "datadog", "gitlab", "snowflake", "oracle", "ibm", "redhat"]
EXTRA_ORG_CAPS = {
    **{o: ["product_management", "product_design", "growth_marketing", "customer_success", "data_science", "people_talent"] for o in _BIG_TECH},
    **{o: ["ml_research", "data_science"] for o in ("gcp", "microsoft", "aws", "snowflake", "ibm")},
    **{o: ["data_science", "product_management", "customer_success", "business_ops"] for o in ("dbs", "ocbc", "uob", "scb", "hsbc", "jpm", "citi", "cba", "digibanks", "insurers", "telcos", "mizuho")},
    **{o: ["business_ops", "people_talent", "data_science"] for o in ("accenture", "deloitte", "pwc_ey")},
    **{o: ["product_management", "customer_success"] for o in ("infosys", "tcs_wipro", "cognizant", "thoughtworks")},
}

# APAC consumer-tech and SaaS companies: large pools of product, design, data and growth talent.
_APAC_TECH = [
    ("grab", "Grab", ["SG"], "South-east Asia's super-app."), ("sea", "Sea (Shopee / Garena)", ["SG"], "E-commerce, gaming and payments."),
    ("rakuten", "Rakuten", ["JP"], "E-commerce and fintech."), ("lineyahoo", "LY Corp (LINE Yahoo)", ["JP"], "Messaging and internet services."),
    ("mercari", "Mercari", ["JP"], "Marketplace with an English-speaking engineering org."),
    ("naver", "Naver", ["KR"], "Search, cloud and AI."), ("kakao", "Kakao", ["KR"], "Messaging, payments and mobility."),
    ("flipkart", "Flipkart", ["IN"], "E-commerce at India scale."), ("freshworks", "Freshworks / Zoho", ["IN"], "Global SaaS built from India."),
    ("canva", "Canva", ["AU"], "Design platform; large product and design org."), ("airwallex", "Airwallex", ["AU", "SG"], "Global payments."),
]
APAC_TECH_ORGS = [dict(
    id=i, name=n, pool_type="adjacent", markets=m, segment_ids=["tech_digital"],
    capability_ids=["software_engineering", "cloud_infra", "data_engineering", "data_science", "product_management", "product_design",
                    "growth_marketing", "customer_success", "ml_research", "people_talent", "security_architecture", "team_building"],
    why_relevant=w, teams=["Product & engineering", "Data & AI", "Growth"], starting_titles=["Senior Engineer", "Product Manager", "Designer"],
    value_to_cognition="Large local pools of product, data and growth talent.", sensitivity="none", sensitivity_note=None, signal_ids=[])
    for i, n, m, w in _APAC_TECH]
