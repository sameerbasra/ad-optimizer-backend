from fastapi import APIRouter, HTTPException
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

router = APIRouter()

def get_google_ads_client():
    try:
        client = GoogleAdsClient.load_from_dict({
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
            "use_proto_plus": True
        })
        return client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Google Ads client: {str(e)}")

@router.get("/customers")
def get_accessible_customers():
    try:
        client = get_google_ads_client()
        customer_service = client.get_service("CustomerService")
        accessible_customers = customer_service.list_accessible_customers()
        customer_ids = [
            resource_name.split("/")[-1]
            for resource_name in accessible_customers.resource_names
        ]
        return {"customer_ids": customer_ids}
    except GoogleAdsException as ex:
        raise HTTPException(status_code=400, detail=f"Google Ads API error: {ex.error.code().name}")

@router.get("/campaigns")
def get_campaigns(customer_id: str):
    try:
        client = get_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.all_conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
            AND campaign.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
        """
        response = ga_service.search(customer_id=customer_id, query=query)
        campaigns = []
        for row in response:
            spend = row.metrics.cost_micros / 1_000_000
            revenue = row.metrics.all_conversions_value
            roas = round(revenue / spend, 2) if spend > 0 else 0
            cpc = round(row.metrics.average_cpc / 1_000_000, 2)
            campaigns.append({
                "id": str(row.campaign.id),
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "spend": round(spend, 2),
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": round(row.metrics.conversions, 1),
                "ctr": round(row.metrics.ctr * 100, 2),
                "cpc": cpc,
                "roas": roas,
            })
        return {"campaigns": campaigns, "total": len(campaigns)}
    except GoogleAdsException as ex:
        raise HTTPException(status_code=400, detail=f"Google Ads API error: {ex.error.code().name}")

@router.get("/metrics")
def get_account_metrics(customer_id: str):
    try:
        client = get_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")
        query = """
            SELECT
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.all_conversions_value
            FROM customer
            WHERE segments.date DURING LAST_30_DAYS
        """
        response = ga_service.search(customer_id=customer_id, query=query)
        total_spend = 0
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        total_revenue = 0
        for row in response:
            total_spend += row.metrics.cost_micros / 1_000_000
            total_impressions += row.metrics.impressions
            total_clicks += row.metrics.clicks
            total_conversions += row.metrics.conversions
            total_revenue += row.metrics.all_conversions_value
        roas = round(total_revenue / total_spend, 2) if total_spend > 0 else 0
        ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0
        cpc = round(total_spend / total_clicks, 2) if total_clicks > 0 else 0
        return {
            "spend": round(total_spend, 2),
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": round(total_conversions, 1),
            "roas": roas,
            "ctr": ctr,
            "cpc": cpc,
        }
    except GoogleAdsException as ex:
        raise HTTPException(status_code=400, detail=f"Google Ads API error: {ex.error.code().name}")

@router.get("/demo")
def get_demo_data():
    return {
        "metrics": {
            "roas": 4.2,
            "cpc": 0.84,
            "ctr": 3.6,
            "spend": 4280,
            "impressions": 118888,
            "clicks": 4280,
            "conversions": 231
        },
        "campaigns": [
            {"id": "1", "name": "Brand Search", "status": "ENABLED", "spend": 1240, "impressions": 76190, "clicks": 3200, "conversions": 87, "ctr": 4.2, "cpc": 0.39, "roas": 6.1},
            {"id": "2", "name": "Competitor Keywords", "status": "ENABLED", "spend": 880, "impressions": 85714, "clicks": 1800, "conversions": 28, "ctr": 2.1, "cpc": 0.49, "roas": 2.8},
            {"id": "3", "name": "Remarketing All", "status": "ENABLED", "spend": 760, "impressions": 55263, "clicks": 2100, "conversions": 54, "ctr": 3.8, "cpc": 0.36, "roas": 5.4},
            {"id": "4", "name": "Broad Discovery", "status": "PAUSED", "spend": 0, "impressions": 0, "clicks": 0, "conversions": 0, "ctr": 0, "cpc": 0, "roas": 0},
            {"id": "5", "name": "Shopping Electronics", "status": "ENABLED", "spend": 1400, "impressions": 81666, "clicks": 980, "conversions": 42, "ctr": 1.2, "cpc": 1.43, "roas": 3.9}
        ],
        "trend": [
            {"date": "Apr 1", "roas": 3.2, "spend": 580},
            {"date": "Apr 5", "roas": 3.6, "spend": 620},
            {"date": "Apr 9", "roas": 3.1, "spend": 590},
            {"date": "Apr 13", "roas": 3.9, "spend": 710},
            {"date": "Apr 17", "roas": 4.1, "spend": 680},
            {"date": "Apr 21", "roas": 3.8, "spend": 640},
            {"date": "Apr 25", "roas": 4.2, "spend": 460}
        ]
    }
