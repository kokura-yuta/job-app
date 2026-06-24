from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import psycopg2
import calendar
from datetime import datetime
app = FastAPI()
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

@app.get("/")
def home():
    return RedirectResponse(
        url="/login",
        status_code=303
    )

@app.get("/add_page", response_class=HTMLResponse)
def add_page(request: Request, user_id: int):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request":request,
            "user_id": user_id
        }
    )
companies = []

conn = get_conn()
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_name TEXT,
    mypage_url TEXT,
    login_id TEXT,
    password TEXT,
    es_text TEXT,
    deadline TEXT,
    event_date TEXT,
    result TEXT,
    memo TEXT,
    genre TEXT,
    priority TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT,
    password TEXT
)
""")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT")
except Exception:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token TEXT")
except Exception:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expire TEXT")
except Exception:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY ,
    company_id INTEGER,
    title TEXT,
    start_datetime TEXT,
    end_datetime TEXT,
    memo TEXT
)
""")
try:
    cursor.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS genre TEXT")
except Exception:
    conn.rollback()
    pass

try:
    cursor.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS location TEXT")
except Exception:
    conn.rollback()
    pass

try: 
    cursor.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS event_type TEXT")
except Exception:
    conn.rollback()
    pass


try:
    cursor.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS priority TEXT")
except Exception:
    conn.rollback()
    pass

try:
    cursor.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS user_id INTEGER")
except Exception:
    conn.rollback()
    pass


conn.commit()
templates = Jinja2Templates(directory="templates")



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
    memo: str = Form(""),
    genre: str = Form(""),
    priority: str = Form(""),
    user_id: int = Form(...)

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
        memo,
        genre,
        priority,
        user_id
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        genre,
        priority,
        user_id

))

    conn.commit()
    

    return RedirectResponse(
            url=f"/list?user_id={user_id}",
            status_code=303
    )
@app.get("/list", response_class=HTMLResponse)
def show_list(request: Request, user_id: int, keyword: str = Query("")):
    conn = get_conn()
    cursor = conn.cursor()

    if keyword:
        cursor.execute(
            """
            SELECT * FROM companies 
            WHERE user_id = %s
            AND company_name LIKE %s
            ORDER BY deadline ASC
            """,
            (user_id, f"%{keyword}%",)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM companies 
            WHERE user_id = %s
            ORDER BY deadline ASC
            """,
            (user_id,)
        )
    rows = cursor.fetchall()
    conn.close()

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
            "genre":row[10],
            "priority":row[11],
            "user_id":row[12]

        }

        companies.append(company)
    
    grouped_companies = {}

    for company in companies:
        genre = company.get("genre") or "未設定"
        if genre not in grouped_companies:
            grouped_companies[genre] = []
        grouped_companies[genre].append(company)

    return templates.TemplateResponse(
         request=request,
         name="list.html",
         context={
            "request":request,
            "companies": companies,
            "grouped_companies": grouped_companies,
            "user_id": user_id,
        }
)

@app.get("/company/{company_id}", response_class=HTMLResponse)
def company_detail(
    request: Request, 
    company_id: int, 
    user_id: int
):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM companies
        WHERE id = %s
        AND user_id = %s
        """,
        (company_id, user_id)
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return HTMLResponse("企業が見つかりません, status_code=404")

    cursor.execute(
       """
       SELECT * FROM events
       WHERE company_id = %s
       ORDER BY start_datetime ASC
       """,
       (company_id,)
)

    event_rows = cursor.fetchall()
    conn.close()


    company = {
       "id": row[0],
       "company_name": row[1],
       "mypage_url": row[2],
       "login_id": row[3],
       "password": row[4],
       "es_text": row[5],
       "deadline": row[6],
       "event_date": row[7],
       "result": row[8],
       "memo": row[9],
       "genre": row[10],
       "priority": row[11],
       "user_id": row[12]
   }
    return templates.TemplateResponse(
        request=request,
        name="company_detail.html",
        context={
           "request":request,
           "company": company,
           "user_id": user_id,
           "events": event_rows
           }
   )

@app.post("/delete/{id}")
def delete_company(id: int, user_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM companies WHERE id = %s AND user_id = %s", (id, user_id))
    
    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/list?user_id={user_id}",
        status_code=303
    )


@app.post("/add_event/{company_id}")
def add_event(
    company_id: int, 
    user_id: int, 
    title: str = Form(""),
    start_date: str = Form(""),
    start_time: str = Form(""),
    end_date: str = Form(""),
    end_time: str = Form(""),
    location: str = Form(""),
    memo: str = Form(""),
    event_type: str = Form("その他")
):
    start_datetime = f"{start_date} {start_time}"
    end_datetime = f"{end_date} {end_time}"
    cursor.execute(
        """
        INSERT INTO events (
            company_id,
            title,
            start_datetime,
            end_datetime,
            location,
            memo,
            event_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            company_id,
            title,
            start_datetime,
            end_datetime,
            location,
            memo,
            event_type
        )
    )

    conn.commit()

    return RedirectResponse(
        url=f"/company/{company_id}?user_id={user_id}",
        status_code=303
    )

@app.post("/delete_event/{event_id}")
def delete_company(event_id: int, user_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM events WHERE id = %s", 
        (event_id,)
        )
    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/calendar?user_id={user_id}",
        status_code=303
    )

@app.get("/edit_event/{event_id}", response_class=HTMLResponse)
def edit_event_page(request: Request, event_id: int, user_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    conn.close()
    if not event:
        return RedirectResponse(
            url=f"/calendar?user_id={user_id}",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="edit_event.html",
        context={
            "request":request,
            "event": event,
            "user_id": user_id
        }
    )

@app.post("/edit_event/{event_id}")
def edit_event(
    event_id: int,
    user_id: int,
    title: str = Form(""),
    start_date: str = Form(""),
    start_time: str = Form(""),
    end_date: str = Form(""),
    end_time: str = Form(""),
    location: str = Form(""),
    memo: str = Form("")
):  
    start_datetime = f"{start_date} {start_time}"
    end_datetime = f"{end_date} {end_time}"

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE events
        SET title = %s,
            start_datetime = %s,
            end_datetime = %s,
            location = %s,
            memo = %s
        WHERE id = %s
    """, (
        title,
        start_datetime,
        end_datetime,
        location,
        memo,
        event_id
    ))

    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/calendar?user_id={user_id}",
        status_code=303
    )
@app.get("/edit/{id}")
def edit_company(id: int, request: Request, user_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """ 
        SELECT * FROM companies WHERE id = %s
        AND user_id = %s
        """, 
        (id, user_id)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return RedirectResponse(
            url=f"/list?user_id={user_id}",
            status_code=303
        )

    company = {
        "id": row[0],
        "company_name":row[1],
        "mypage_url":row[2],
        "login_id":row[3],
        "password":row[4],
        "es_text":row[5],
        "result":row[6],
        "memo":row[7],
        "genre":row[8],
        "priority":row[9],
        "user_id":row[10]

    }
    
    return templates.TemplateResponse(
        request=request,
        name="edit.html",
        context={
            "request":request,
            "company": company,
            "user_id": user_id}
    )

@app.get("/calendar", response_class=HTMLResponse)
def calendar_page(
    request: Request,
    user_id: int,
    year: int = None,
    month: int = None
):
    now = datetime.now()

    if year is None:
       year = now.year
    if month is None:
       month = now.month

    prev_month = month - 1
    prev_year = year

    if prev_month == 0:
       prev_month = 12
       prev_year = year - 1

    next_month = month + 1
    next_year = year

    if next_month == 13:
        next_month = 1
        next_year = year + 1
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT events.*, companies.company_name
        FROM events
        JOIN companies ON events.company_id = companies.id
        WHERE companies.user_id = %s
        ORDER BY events.start_datetime ASC
   """, (user_id,))

    events = cursor.fetchall()
    conn.close()
    cal = calendar.monthcalendar(year, month)

    return templates.TemplateResponse(
         request=request,
        name="calendar.html",
        context={
            "request":request,
            "calendar_days": cal,
            "events": events,
            "year": year,
            "month": month,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "user_id": user_id
            }
    )




@app.post("/update/{id}")
def update_company(
    id: int,
    user_id: int,
    company_name: str = Form(""),
    mypage_url: str = Form(""),
    login_id: str = Form(""),
    password: str = Form(""),
    es_text: str = Form(""),
    deadline: str = Form(""),
    event_date: str = Form(""),
    result: str = Form(""),
    memo: str = Form(""),
    genre: str = Form(""),
    priority: str = Form(""),
   
):
    local_conn = get_conn()
    local_cursor = local_conn.cursor()
    local_cursor.execute("""
    UPDATE companies
    SET
        company_name = %s,
        mypage_url = %s,
        login_id = %s,
        password = %s,
        es_text = %s,
        deadline = %s,
        event_date = %s,
        result = %s,
        memo = %s,
        genre = %s,
        priority = %s
    WHERE id = %s AND user_id = %s
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
        genre,
        priority,
        id,
        user_id
    ))

    local_conn.commit()
    local_conn.close()

    return RedirectResponse(
        url=f"/list?user_id={user_id}",
        status_code=303
    )
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request":request}
    )

@app.post("/register")
def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
        """
        INSERT INTO users (username, email, password)
        VALUES (%s,%s,%s)
        """,
        (username, email, password)
     )

        conn.commit()

    except Exception:
      conn.rollback()
      return HTMLResponse("このユーザー名はすでに使われています")

    return RedirectResponse(
        url="/login?error=ユーザー名とパスワードを入力してください",
        status_code=303
)

@app.get("/forgot-password")
def forget_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="forget_password.html",
        context={"request": request}
    )

@app.post("/forget-password")
def forget_password(request: Request, email: str = Form(...)):
    if email == "":
        return templates.TemplateResponse(
            request=request,
            name="forget_password.html",
            context={
                "request": request,
                "error": "メールアドレスを入力してください"
            }
        )

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "request": request,
                "email": email
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="forget_password.html",
        context={
            "request": request,
            "error": "このメールアドレスは登録されていません"
        }
    )
@app.post("/reset-password")
def reset_password(
    email: str = Form(...),
    new_password: str = Form(...)
):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (new_password, email)
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url="/login",
        status_code=303
    )



@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
         request=request,
        name="login.html",
        context={"request":request}
    ) 
    

@app.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if username == "" or password == "":
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request":request,
            "error": "ユーザー名とパスワードを入力してください",
            }
        )
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username = %s AND password = %s",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        return RedirectResponse(
            url=f"/list?user_id={user[0]}",
            status_code=303
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"request":request, "error": "ユーザー名またはパスワードが違います"}
        )
@app.get("/logout")
def logout():
    return RedirectResponse(
        url="/login",
        status_code=303
    )
@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request}
    )

@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="terms.html",
        context={"request": request}
    )


