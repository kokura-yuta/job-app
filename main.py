from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import calendar
from datetime import datetime

app = FastAPI()

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
    memo TEXT,
    genre TEXT,
    priority TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    title TEXT,
    start_datetime TEXT,
    end_datetime TEXT,
    memo TEXT
)
""")
try:
    cursor.execute("ALTER TABLE companies ADD COLUMN genre TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE events ADD COLUMN location TEXT")
except sqlite3.OperationalError:
    pass

try: 
    cursor.execute("ALTER TABLE events ADD COLUMN event_type TEXT")
except sqlite3.OperationalError:
    pass


try:
    cursor.execute("ALTER TABLE companies ADD COLUMN priority TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE companies ADD COLUMN user_id INTEGER")
except sqlite3.OperationalError:
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
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()

    if keyword:
        cursor.execute(
            """
            SELECT * FROM companies 
            WHERE user_id = ?
            AND company_name LIKE ?
            ORDER BY deadline ASC
            """,
            (user_id, f"%{keyword}%",)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM companies 
            WHERE user_id = ?
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
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM companies
        WHERE id = ?
        AND user_id = ?
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
       WHERE company_id = ?
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
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM companies WHERE id = ? AND user_id = ?", (id, user_id))
    
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
        VALUES (?, ?, ?, ?, ?, ?, ?)
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
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM events WHERE id = ?", 
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
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
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
    start_datetime: str = Form(""),
    end_datetime: str = Form(""),
    location: str = Form(""),
    memo: str = Form("")
):
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE events
        SET title = ?,
            start_datetime = ?,
            end_datetime = ?,
            location = ?,
            memo = ?
        WHERE id = ?
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
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()

    cursor.execute(
        """ 
        SELECT * FROM companies WHERE id = ?
        AND user_id = ?
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
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT events.*, companies.company_name
        FROM events
        JOIN companies ON events.company_id = companies.id
        WHERE companies.user_id = ?
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
    user_id: int = Form("")
):
    local_conn = sqlite3.connect("job_app.db", timeout=30, check_same_thread=False)
    local_cursor = local_conn.cursor()
    local_cursor.execute("""
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
        memo = ?,
        genre = ?,
        priority = ?
    WHERE id = ? AND user_id = ?
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
    password: str = Form(...)
):
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
        """
        INSERT INTO users (username, password)
        VALUES (?,?)
        """,
        (username, password)
     )

        conn.commit()

    except sqlite3.IntegrityError:
      return HTMLResponse("このユーザー名はすでに使われています")

    return RedirectResponse(
        url="/login?error=ユーザー名とパスワードを入力してください",
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
    conn = sqlite3.connect("job_app.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
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



