from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient  
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

# Create FastAPI application
app = FastAPI()

# MongoDB connection setup
client = AsyncIOMotorClient("mongodb://192.168.134.129:27017")
db = client["correspondence_db"]
correspondence_collection = db["correspondences"]
organizations_collection = db["organizations"]

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")


# --- Data models ---
class Correspondence(BaseModel):
    type: str = Field(..., example="Letter")
    date: str = Field(..., example="2024-12-15")
    organization_name: str = Field(..., example="OOO Navigator")


class Organization(BaseModel):
    name: str = Field(..., example="OOO Navigator")
    address: str = Field(..., example="Moscow, Bolshaya Akademicheskaya, 13")
    director: str = Field(..., example="Markin Anatolii")


# --- API methods ---
# Add correspondence
@app.post("/add-correspondence/", response_class=RedirectResponse)
async def add_correspondence(
    type: str = Form(...),
    date: str = Form(...),
    organization_name: str = Form(...),
):
    correspondence = Correspondence(type=type, date=date, organization_name=organization_name)
    await correspondence_collection.insert_one(correspondence.dict())
    return RedirectResponse("/", status_code=303)


# Add organization
@app.post("/add-organization/", response_class=RedirectResponse)
async def add_organization(
    name: str = Form(...),
    address: str = Form(...),
    director: str = Form(...),
):
    organization = Organization(name=name, address=address, director=director)
    await organizations_collection.insert_one(organization.dict())
    return RedirectResponse("/", status_code=303)

# Search combined information by organization name
@app.get("/search/", response_class=HTMLResponse)
async def search_combined(request: Request, organization_name: str = Query(...)):
    organization = await organizations_collection.find_one({"name": organization_name})
    correspondences = await correspondence_collection.find({"organization_name": organization_name}).to_list(100)

    if not organization and not correspondences:
        raise HTTPException(status_code=404, detail="No data found for the specified organization")

    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "organization": organization,
            "correspondences": correspondences,
        },
    )

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    organizations = await organizations_collection.find().to_list(100)
    correspondences = await correspondence_collection.find().to_list(100)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "organizations": organizations,
            "correspondences": correspondences,
        },
    )

# Delete all data by organization name
@app.post("/delete/", response_class=RedirectResponse)
async def delete_by_organization_name(organization_name: str=Form(...)):
    org_result = await organizations_collection.delete_one({"name": organization_name})
    corr_result = await correspondence_collection.delete_many({"organization_name": organization_name})

    if org_result.deleted_count == 0 and corr_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No data found for the specified organization")

    return RedirectResponse("/", status_code=303)


# --- HTML Rendering ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})