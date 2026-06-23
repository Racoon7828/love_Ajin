from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)

# =========================================================
# MariaDB 접속 정보
# password만 본인 MariaDB 비밀번호로 수정
# 비밀번호가 없으면 password="" 로 둔다.
# =========================================================
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "database": "love_ajin",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def ok(data=None, message="success"):
    return jsonify({
        "success": True,
        "message": message,
        "data": data
    })


def fail(error, status_code=500):
    return jsonify({
        "success": False,
        "error": str(error)
    }), status_code


@app.route("/api/test", methods=["GET"])
def test_server():
    return ok({"server": "running", "db": DB_CONFIG["database"]}, "Flask server is running")


@app.route("/api/characters", methods=["GET"])
def get_characters():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM male_character ORDER BY male_id")
            rows = cur.fetchall()
        return ok(rows, "characters loaded")
    except Exception as e:
        return fail(e)
    finally:
        conn.close()


@app.route("/api/save_day", methods=["POST"])
def save_day():
    data = request.get_json(force=True)

    save_id = str(data.get("save_id", "unknown"))
    player = data["player"]
    status = data["status"]
    affection = data.get("affection", {})
    inventory = data.get("inventory", {})
    action_log = data.get("action_log", [])

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # 1. 플레이어 현재 상태 저장 또는 갱신
            cur.execute(
                """
                INSERT INTO player_save
                (save_id, player_name, current_day, gold, hp, charm, intelligence, stress)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    player_name = VALUES(player_name),
                    current_day = VALUES(current_day),
                    gold = VALUES(gold),
                    hp = VALUES(hp),
                    charm = VALUES(charm),
                    intelligence = VALUES(intelligence),
                    stress = VALUES(stress)
                """,
                (
                    save_id,
                    player.get("name", "아진"),
                    int(player.get("current_date", 1)),
                    int(player.get("gold", 0)),
                    int(status.get("hp", 0)),
                    int(status.get("charm", 0)),
                    int(status.get("intelligence", 0)),
                    int(status.get("stress", 0)),
                )
            )

            # 2. 남주별 호감도 저장 또는 갱신
            for male_id, score in affection.items():
                cur.execute(
                    """
                    INSERT INTO affection_save
                    (save_id, male_id, affection)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        affection = VALUES(affection)
                    """,
                    (save_id, int(male_id), int(score))
                )

            # 3. 인벤토리 저장 또는 갱신
            for item_id, item_count in inventory.items():
                cur.execute(
                    """
                    INSERT INTO inventory_save
                    (save_id, item_id, item_count)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        item_count = VALUES(item_count)
                    """,
                    (save_id, int(item_id), int(item_count))
                )

            # 4. 행동 로그는 현재 게임 로그 기준으로 다시 저장
            #    하루마다 저장해도 중복이 안 생기도록 기존 로그 삭제 후 재삽입
            cur.execute("DELETE FROM action_log WHERE save_id = %s", (save_id,))

            for log in action_log:
                cur.execute(
                    """
                    INSERT INTO action_log
                    (save_id, day, action_name)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        save_id,
                        int(log.get("day", 0)),
                        str(log.get("action_name", ""))
                    )
                )

        conn.commit()
        return ok({"save_id": save_id}, "day saved")

    except Exception as e:
        conn.rollback()
        return fail(e)

    finally:
        conn.close()


@app.route("/api/save_ending", methods=["POST"])
def save_ending():
    data = request.get_json(force=True)

    save_id = str(data.get("save_id", "unknown"))

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ending_log
                (save_id, ending_id, best_male_id, highest_score,
                 final_charm, final_intelligence, final_stress)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    save_id,
                    int(data["ending_id"]),
                    int(data["best_male_id"]),
                    int(data["highest_score"]),
                    int(data["final_charm"]),
                    int(data["final_intelligence"]),
                    int(data["final_stress"]),
                )
            )

        conn.commit()
        return ok({"save_id": save_id}, "ending saved")

    except Exception as e:
        conn.rollback()
        return fail(e)

    finally:
        conn.close()


@app.route("/api/load/<string:save_id>", methods=["GET"])
def load_game(save_id):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM player_save WHERE save_id = %s", (save_id,))
            player_row = cur.fetchone()

            if not player_row:
                return ok(None, "no save data")

            cur.execute("SELECT male_id, affection FROM affection_save WHERE save_id = %s", (save_id,))
            affection_rows = cur.fetchall()

            cur.execute("SELECT item_id, item_count FROM inventory_save WHERE save_id = %s", (save_id,))
            inventory_rows = cur.fetchall()

            cur.execute("SELECT day, action_name FROM action_log WHERE save_id = %s ORDER BY log_id", (save_id,))
            action_rows = cur.fetchall()

        result = {
            "player": {
                "name": player_row["player_name"],
                "gold": player_row["gold"],
                "current_date": player_row["current_day"],
            },
            "status": {
                "hp": player_row["hp"],
                "charm": player_row["charm"],
                "intelligence": player_row["intelligence"],
                "stress": player_row["stress"],
            },
            "affection": {str(row["male_id"]): row["affection"] for row in affection_rows},
            "inventory": {str(row["item_id"]): row["item_count"] for row in inventory_rows},
            "action_log": action_rows,
        }

        return ok(result, "save loaded")

    except Exception as e:
        return fail(e)

    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
