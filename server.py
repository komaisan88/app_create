from fastapi import (
    FastAPI,
    HTTPException,
)  # FastAPIフレームワークの基本機能とエラー処理用のクラス
from fastapi.middleware.cors import CORSMiddleware  # CORSを有効にするためのミドルウェア
from pydantic import BaseModel  # データのバリデーション（検証）を行うための基本クラス
from typing import Optional  # 省略可能な項目を定義するために使用
import sqlite3  # SQLiteデータベースを使用するためのライブラリ

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI()


# corsを無効化（開発時のみ）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# データベースの初期設定を行う関数
def init_db():
    # SQLiteデータベースに接続（ファイルが存在しない場合は新規作成）
    with sqlite3.connect("todos.db") as conn:
        # TODOを保存するテーブルを作成（すでに存在する場合は作成しない）
        # 自動増分する一意のID（INTEGER PRIMARY KEY AUTOINCREMENT）
        # TODOのタイトル（TEXT NOT NULL）
        # 完了状態（BOOLEAN DEFAULT FALSE）
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_title TEXT NOT NULL,
                artist TEXT NOT NULL,
                total_score INTEGER NOT NULL,
                pitch_score INTEGER NOT NULL,
                technique_score INTEGER NOT NULL,
                long_tone_score INTEGER NOT NULL,
                stability_score INTEGER NOT NULL,
                expression_score INTEGER NOT NULL,
                high_range_score INTEGER NOT NULL,
                comments TEXT,
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )


# アプリケーション起動時にデータベースを初期化
init_db()


# リクエストボディのデータ構造を定義するクラス
class Todo(BaseModel):
    song_title: str
    artist: str
    total_score: int
    pitch_score: int
    technique_score: int
    long_tone_score: int
    stability_score: int
    expression_score: int
    high_range_score: int
    comments: Optional[str] = None
    completed: Optional[bool] = False  # 完了状態（省略可能、デフォルトは未完了）


# レスポンスのデータ構造を定義するクラス（TodoクラスにIDを追加）
class KaraokeScoreResponse(Todo):
    id: int  # TODOのID
    performed_at: str


# 新規スコアを作成するエンドポイント
@app.post("/score", response_model=KaraokeScoreResponse)
def create_score(score: Todo):
    with sqlite3.connect("todos.db") as conn:
        cursor = conn.execute(
            """INSERT INTO todos (song_title, artist, total_score, pitch_score, technique_score, long_tone_score, stability_score, expression_score, high_range_score, comments) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (score.song_title, score.artist, score.total_score, score.pitch_score, score.technique_score, score.long_tone_score, score.stability_score, score.expression_score, score.high_range_score, score.comments)
        )
        score_id = cursor.lastrowid
        created_score = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (score_id,)
        ).fetchone()
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, created_score))


# 全てのスコアを取得するエンドポイント
@app.get("/scores")
def get_scores(search: Optional[str] = None, sort_by: Optional[str] = "performed_at", order: Optional[str] = "desc"):
    with sqlite3.connect("todos.db") as conn:
        query = "SELECT * FROM todos"
        params = []

        if search:
            query += """ WHERE song_title LIKE ? OR artist LIKE ? OR comments LIKE ?"""
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        valid_sort_columns = ["performed_at", "total_score", "song_title", "artist"]
        if sort_by in valid_sort_columns:
            query += f" ORDER BY {sort_by}"
            if order.lower() in ["asc", "desc"]:
                query += f" {order.upper()}"

        scores = conn.execute(query, params).fetchall()
        columns = [column[0] for column in conn.execute(query, params).description]
        return [dict(zip(columns, score)) for score in scores]


# 特定のスコアを取得するエンドポイント
@app.get("/scores/{score_id}")
def get_score(score_id: int):
    with sqlite3.connect("todos.db") as conn:
        score = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (score_id,)
        ).fetchone()
        if not score:
            raise HTTPException(status_code=404, detail="Score not found")
        columns = [column[0] for column in conn.execute(
            "SELECT * FROM todos LIMIT 1"
        ).description]
        return dict(zip(columns, score))


# 指定されたIDのスコアを削除するエンドポイント
@app.delete("/scores/{score_id}")
def delete_score(score_id: int):
    with sqlite3.connect("todos.db") as conn:
        cursor = conn.execute(
            "DELETE FROM todos WHERE id = ?", (score_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Score not found")
        return {"message": "Score deleted successfully"}