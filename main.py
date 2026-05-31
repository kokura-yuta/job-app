from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

app = FastAPI()
companies = []

conn = sqlite3.connect("job_app.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    mypage_url TEXT,
    login_id TEXT,
    password TEXT,
    es_text TEXT,
    deadline TEXT,
    event_date TEXT,
    result TEXT,
    memo TEXT)
""")

conn.commit()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.post("/add")
def add_company(
    company_name: str = Form(""),
    mypage_url: str = Form(""),
    login_id: str = Form(""),
    password: str =Form(""),
    es_text: str = Form(""),
    deadline: str = Form(""),
    event_date: str = Form(""),
    result: str = Form("未定"),
    memo: str = Form("")

):
    cursor.execute("""
    INSERT INTO companies (
        company_name,
        mypage_url,
        login_id,
        password,
        es_text,
        deadline,
        event_date,
        result,
        memo
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    company_name,
        mypage_url,
        login_id,
        password,
        es_text,
        deadline,
        event_date,
        result,
        memo

))

    conn.commit()

    return RedirectResponse(
            url="/list",
            status_code=303
    )
@app.get("/list", response_class=HTMLResponse)
def show_list(request: Request, keyword: str = Query("")):
    if keyword:
        cursor.execute(
            "SELECT * FROM companies WHERE company_name LIKE? ORDER BY deadline ASC",
            (f"%{keyword}%",)
        )
    else:
        cursor.execute("SELECT * FROM companies ORDER BY deadline ASC")
    rows = cursor.fetchall()
    print(rows)

    companies = []
    for row in rows:
        company = {
            "id": row[0],
            "company_name":row[1],
            "mypage_url":row[2],
            "login_id":row[3],
            "password":row[4],
            "es_text":row[5],
            "deadline":row[6],
            "event_date":row[7],
            "result":row[8],
            "memo":row[9],
        }

        companies.append(company)
    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={"companies": companies}
)

@app.post("/delete/{id}")
def delete_company(id: int):
    cursor.execute("DELETE FROM companies WHERE id = ?", (id,))
    conn.commit()

    return RedirectResponse(
        url="/list",
        status_code=303
    )

@app.get("/edit/{id}")
def edit_company(id: int, request: Request):

    cursor.execute(
        "SELECT * FROM companies WHERE id = ?", 
        (id,)
    )
    row = cursor.fetchone()
    
    if row is None:
        return RedirectResponse(
            url="/list",
            status_code=303
        )

    company = {
        "id": row[0],
        "company_name":row[1],
        "mypage_url":row[2],
        "login_id":row[3],
        "password":row[4],
        "es_text":row[5],
        "deadline":row[6],
        "event_date":row[7],
        "result":row[8],
        "memo":row[9],

    }

    return templates.TemplateResponse(
        request=request,
        name="edit.html",
        context={"company": company}
    )




@app.post("/update/{id}")
def update_company(
    id: int,
    company_name: str = Form(""),
    mypage_url: str = Form(""),
    login_id: str = Form(""),
    password: str = Form(""),
    es_text: str = Form(""),
    deadline: str = Form(""),
    event_date: str = Form(""),
    result: str = Form(""),
    memo: str = Form("")
):
    cursor.execute("""
    UPDATE companies
    SET
        company_name = ?,
        mypage_url = ?,
        login_id = ?,
        password = ?,
        es_text = ?,
        deadline = ?,
        event_date = ?,
        result = ?,
        memo = ?
    WHERE id = ?
    """, (
        company_name,
        mypage_url,
        login_id,
        password,
        es_text,
        deadline,
        event_date,
        result,
        memo,
        id
    ))

    conn.commit()

    return RedirectResponse(
        url="/list",
        status_code=303
    )
