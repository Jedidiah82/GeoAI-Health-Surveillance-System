import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    require_admin
)

from app.audit_logger import log_event


app = FastAPI(
    title="GeoAI Surveillance Secure API Gateway",
    description="Secure API mediation layer for privacy-preserving GeoAI surveillance intelligence.",
    version="1.0"
)


DATA_PATH = "data/geoai_surveillance_outputs.csv"


def load_data():
    return pd.read_csv(DATA_PATH)


@app.get("/")
def root():
    return {
        "message": "GeoAI Surveillance Secure API Gateway is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "GeoAI Surveillance API"
    }


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(
        form_data.username,
        form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        data={
            "sub": user["username"],
            "role": user["role"]
        }
    )

    log_event(
        user_role=user["role"],
        action="api_login",
        district=None
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"]
    }


@app.get("/districts")
def get_districts(current_user: dict = Depends(get_current_user)):
    df = load_data()

    districts = sorted(df["adm2_name"].dropna().unique().tolist())

    log_event(
        user_role=current_user["role"],
        action="api_view_districts",
        district=None
    )

    return {
        "districts": districts
    }


@app.get("/district/{district_name}")
def get_district_details(
    district_name: str,
    current_user: dict = Depends(get_current_user)
):
    df = load_data()

    district_df = df[df["adm2_name"] == district_name]

    if district_df.empty:
        raise HTTPException(
            status_code=404,
            detail="District not found"
        )

    latest_record = district_df.sort_values(
        ["Year", "Month"]
    ).iloc[-1]

    log_event(
        user_role=current_user["role"],
        action="api_view_district_details",
        district=district_name
    )

    return {
        "district": latest_record["adm2_name"],
        "county": latest_record["adm1_name"],
        "year": int(latest_record["Year"]),
        "month": int(latest_record["Month"]),
        "reported_cases": int(latest_record["COUNT_OBJECTID"]),
        "incidence_per_100k": float(latest_record["Incidence_100k"]),
        "rainfall_mm": float(latest_record["Rainfall_mm"]),
        "temperature_c": float(latest_record["Temperature_C"]),
        "outbreak_probability": float(latest_record["Outbreak_Probability"]),
        "risk_level": latest_record["Risk_Level"]
    }


@app.get("/risk/latest")
def get_latest_risk_summary(
    current_user: dict = Depends(get_current_user)
):
    df = load_data()

    latest_df = (
        df.sort_values(["Year", "Month"])
          .groupby("adm2_name")
          .tail(1)
    )

    summary = latest_df["Risk_Level"].value_counts().to_dict()

    log_event(
        user_role=current_user["role"],
        action="api_view_latest_risk_summary",
        district=None
    )

    return {
        "latest_risk_summary": summary
    }


@app.get("/risk/top")
def get_top_risk_districts(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    df = load_data()

    latest_df = (
        df.sort_values(["Year", "Month"])
          .groupby("adm2_name")
          .tail(1)
    )

    top_risk = latest_df.sort_values(
        "Outbreak_Probability",
        ascending=False
    ).head(limit)

    log_event(
        user_role=current_user["role"],
        action="api_view_top_risk_districts",
        district=None
    )

    return top_risk[
        [
            "adm2_name",
            "adm1_name",
            "Outbreak_Probability",
            "Risk_Level"
        ]
    ].rename(
        columns={
            "adm2_name": "district",
            "adm1_name": "county",
            "Outbreak_Probability": "outbreak_probability",
            "Risk_Level": "risk_level"
        }
    ).to_dict(orient="records")


@app.get("/admin/audit-log")
def view_audit_log(
    current_user: dict = Depends(require_admin)
):
    import os
    import csv

    audit_path = "logs/audit_log.csv"

    if not os.path.exists(audit_path):
        return {
            "message": "No audit log found yet"
        }

    records = []

    with open(audit_path, mode="r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            records.append(row)

    return records[-50:]