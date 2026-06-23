# ==========================================
# 0. 기본 변수
# ==========================================

default actions_left = 2
# default db_save_id = 1
default player_name = "아진"

# sqlite DB 대신 Ren'Py 저장 변수로 데이터 관리
default db_player = {"name": "아진", "gold": 1000, "current_date": 1}
default db_status = {"hp": 100, "charm": 10, "intelligence": 10, "stress": 0}

default db_male = {
    1: "하원준",
    2: "류인환",
    3: "김용주",
    4: "김도경"
}

default db_male_title = {
    1: "냉철한 본부장",
    2: "다정한 선배",
    3: "완벽주의 동기",
    4: "대형견 인턴"
}

default db_affection = {
    1: 0,
    2: 0,
    3: 0,
    4: 0
}

default db_inventory = {
    1: 0,
    2: 0,
    3: 0,
    4: 0
}

default db_shop = {
    1: 100,
    2: 500,
    3: 300,
    4: 150
}

default db_item = {
    1: {"name": "비타민 음료", "effect": "스트레스 -20"},
    2: {"name": "고급 향수", "effect": "매력 +50"},
    3: {"name": "실무 엑셀 책", "effect": "지능 +30"},
    4: {"name": "야근 쿠키", "effect": "스트레스 -10, 매력 +5"}
}

default db_action_log = []
default db_ending_log = []


# ==========================================
# 1. 공통 함수
# ==========================================

init python:
    import random
    import uuid
    import json

    # default persistent.player_uuid = ""
    if not hasattr(persistent, "player_uuid") or not persistent.player_uuid:
        persistent.player_uuid = str(uuid.uuid4())[:8]

    api_url = "http://10.2.10.106:5000"
    API_BASE_URL = "http://10.2.10.106:5000"

    try:
        import requests
    except Exception:
        requests = None

    def api_post(path, payload):
        url = API_BASE_URL + path

        if requests is not None:
            response = requests.post(url, json=payload, timeout=3)
            return response.status_code, response.text

        # requests가 Ren'Py에서 안 잡힐 때를 대비한 표준 라이브러리 대체 코드
        import urllib.request
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        response = urllib.request.urlopen(req, timeout=3)
        return response.getcode(), response.read().decode("utf-8")

    def api_get(path):
        url = API_BASE_URL + path

        if requests is not None:
            response = requests.get(url, timeout=3)
            return response.status_code, response.text

        import urllib.request
        response = urllib.request.urlopen(url, timeout=3)
        return response.getcode(), response.read().decode("utf-8")

    def save_day_to_mariadb(show_message=True):
        payload = {
            "save_id": persistent.player_uuid,
            "player": db_player,
            "status": db_status,
            "affection": db_affection,
            "inventory": db_inventory,
            "action_log": db_action_log
        }

        try:
            status_code, text = api_post("/api/save_day", payload)

            if status_code == 200:
                if show_message:
                    renpy.notify("MariaDB 저장 완료")
                return True
            else:
                if show_message:
                    renpy.notify("MariaDB 저장 실패")
                return False

        except Exception as e:
            if show_message:
                renpy.notify("Flask 서버 연결 실패")
            return False

    def save_ending_to_mariadb(ending_id, best_male_id, highest_score, final_charm, final_intelligence, final_stress):
        payload = {
            "save_id": persistent.player_uuid,
            "ending_id": ending_id,
            "best_male_id": best_male_id,
            "highest_score": highest_score,
            "final_charm": final_charm,
            "final_intelligence": final_intelligence,
            "final_stress": final_stress
        }

        try:
            status_code, text = api_post("/api/save_ending", payload)

            if status_code == 200:
                renpy.notify("엔딩 DB 저장 완료")
                return True
            else:
                renpy.notify("엔딩 DB 저장 실패")
                return False

        except Exception as e:
            renpy.notify("Flask 서버 연결 실패")
            return False

    def load_from_mariadb(show_message=True):
        try:
            status_code, text = api_get("/api/load/{}".format(persistent.player_uuid))

            if status_code != 200:
                if show_message:
                    renpy.notify("DB 불러오기 실패")
                return False

            data = json.loads(text)

            if not data.get("success"):
                if show_message:
                    renpy.notify("저장 데이터 없음")
                return False

            save_data = data["data"]

            db_player.clear()
            db_player.update(save_data["player"])

            db_status.clear()
            db_status.update(save_data["status"])

            db_affection.clear()
            for k, v in save_data["affection"].items():
                db_affection[int(k)] = int(v)

            db_inventory.clear()
            for k, v in save_data["inventory"].items():
                db_inventory[int(k)] = int(v)

            db_action_log[:] = save_data["action_log"]

            if show_message:
                renpy.notify("DB 불러오기 완료")

            return True

        except Exception as e:
            if show_message:
                renpy.notify("Flask 서버 연결 실패")
            return False


    def choose_existing_image(file_list):
        candidates = list(file_list)
        random.shuffle(candidates)

        for filename in candidates:
            if renpy.loadable(filename):
                return filename

        return None

    def reset_game_data():
        db_player.clear()
        db_player.update({
            "name": "아진",
            "gold": 1000,
            "current_date": 1
        })

        db_status.clear()
        db_status.update({
            "hp": 100,
            "charm": 10,
            "intelligence": 10,
            "stress": 0
        })

        db_affection.clear()
        db_affection.update({
            1: 0,
            2: 0,
            3: 0,
            4: 0
        })

        db_inventory.clear()
        db_inventory.update({
            1: 0,
            2: 0,
            3: 0,
            4: 0
        })

        db_action_log[:] = []
        db_ending_log[:] = []

    def clamp_status():
        if db_status["stress"] < 0:
            db_status["stress"] = 0

        if db_status["stress"] > 100:
            db_status["stress"] = 100

        if db_status["charm"] < 0:
            db_status["charm"] = 0

        if db_status["intelligence"] < 0:
            db_status["intelligence"] = 0

        if db_player["gold"] < 0:
            db_player["gold"] = 0

    def add_action_log(action_name):
        db_action_log.append({
            "day": db_player["current_date"],
            "action_name": action_name
        })

    def get_affection(male_id):
        return db_affection.get(male_id, 0)

    def change_affection(male_id, amount):
        db_affection[male_id] = db_affection.get(male_id, 0) + amount

    def change_status(hp=0, charm=0, intelligence=0, stress=0):
        db_status["hp"] += hp
        db_status["charm"] += charm
        db_status["intelligence"] += intelligence
        db_status["stress"] += stress
        clamp_status()

    def add_gold(amount):
        db_player["gold"] += amount
        clamp_status()

    def buy_item(item_id, price):
        if db_player["gold"] < price:
            return False

        db_player["gold"] -= price
        db_inventory[item_id] = db_inventory.get(item_id, 0) + 1

        if item_id == 1:
            change_status(stress=-20)
        elif item_id == 2:
            change_status(charm=50)
        elif item_id == 3:
            change_status(intelligence=30)
        elif item_id == 4:
            change_status(stress=-10, charm=5)

        add_action_log("상점 구매")
        clamp_status()
        return True

    def get_best_male():
        best_male_id = max(db_affection, key=db_affection.get)
        highest_score = db_affection[best_male_id]
        return best_male_id, highest_score

    def resolve_ending_id():
        best_male_id, highest_score = get_best_male()

        final_intel = db_status["intelligence"]
        final_stress = db_status["stress"]

        if highest_score >= 100:
            if best_male_id == 1:
                return 1
            elif best_male_id == 2:
                return 2
            elif best_male_id == 3:
                return 3
            elif best_male_id == 4:
                return 4

        elif highest_score >= 60:
            if best_male_id == 1:
                return 5
            elif best_male_id == 2:
                return 6
            elif best_male_id == 3:
                return 7
            elif best_male_id == 4:
                return 8

        elif final_stress >= 90:
            return 10

        elif final_intel >= 120:
            return 9

        return 11


# ==========================================
# 2. 캐릭터 정의
# ==========================================

define p = Character("아진", color="#ffb3b3")
define m1 = Character("하원준(본부장)", color="#b3b3ff")
define m2 = Character("류인환(선배)", color="#80ff80")
define m3 = Character("김용주(동기)", color="#ffff80")
define m4 = Character("김도경(인턴)", color="#ffb366")

# 남주별 대화용 이미지 파일명
# 01번은 기본 사진으로 고정.
# 말 걸고 선택지 이후 남주가 반응할 때는 02~03번 중 하나를 랜덤으로 사용.
default wonjun_base_image = "images/wonjun_01_cold.png"
default wonjun_reaction_images = [
    "images/wonjun_02_soft.png",
    "images/wonjun_03_close.png"
]

default inhwan_base_image = "images/inhwan_01_smile.png"
default inhwan_reaction_images = [
    "images/inhwan_02_coffee.png",
    "images/inhwan_03_worried.png"
]

default yongju_base_image = "images/yongju_01_cool.png"
default yongju_reaction_images = [
    "images/yongju_02_teasing.png",
    "images/yongju_03_serious.png"
]

default dokyung_base_image = "images/dokyung_01_bright.png"
default dokyung_reaction_images = [
    "images/dokyung_02_puppy.png",
    "images/dokyung_03_flustered.png"
]

# 엔딩용 전체화면 CG 파일명
# 해피엔딩은 남주별 1장씩 사용.
# 배드엔딩은 공통 배드엔딩용 이미지를 사용.
# 파일이 없으면 검은 배경으로 진행되게 처리함.
default wonjun_ending_happy_image = "images/wonjun_ending_happy.png"
default inhwan_ending_happy_image = "images/inhwan_ending_happy.png"
default yongju_ending_happy_image = "images/yongju_ending_happy.png"
default dokyung_ending_happy_image = "images/dokyung_ending_happy.png"

default ending_workaholic_image = "images/ending_workaholic.png"
default ending_bad_burnout_image = "images/ending_bad_burnout.png"
default ending_bad_plain_image = "images/ending_bad_plain.png"

# 투명 PNG 캐릭터를 화면 크기에 맞춰 자동 배치
# fit "contain"은 이미지 비율을 유지한 채 지정 박스 안에 전부 들어가게 함
# 하단 대사창에 가려지는 것을 줄이기 위해 화면 높이의 76% 안에서만 표시
transform male_full_center:
    xalign 0.5
    yalign 0.02
    xysize (config.screen_width, int(config.screen_height * 0.76))
    fit "contain"

# 엔딩 CG 자동 배치
# 전체 화면에 맞추되 잘리지 않게 contain 사용
transform ending_full_fit:
    xalign 0.5
    yalign 0.5
    xysize (config.screen_width, config.screen_height)
    fit "contain"


# ==========================================
# 3. 화면 UI
# ==========================================

screen status_panel(day, gold, charm, intelligence, stress, actions_left):
    frame:
        xalign 0.02
        yalign 0.03
        background "#00000099"
        padding (18, 12)

        vbox:
            spacing 6
            text "DAY [day] / 10" size 24 color "#ffffff"
            text "남은 행동: [actions_left]회" size 22 color "#ffff99"
            text "돈: [gold]G" size 20 color "#ffe6a7"
            text "매력: [charm]" size 20 color "#ffb3d9"
            text "지능: [intelligence]" size 20 color "#b3e0ff"
            text "스트레스: [stress]" size 20 color "#ff9999"


# ==========================================
# 4. 게임 시작
# ==========================================

label start:

    $ actions_left = 2
    $ player_name = "아진"

    python:
        reset_game_data()

    scene black

    "드디어 '아진산업' 첫 출근이다."
    "정규직 전환을 위해 나에게 주어진 시간은 단 10일."
    "일도 사랑도 모두 쟁취해 보이겠어."

    jump daily_loop


# ==========================================
# 5. 하루 일과 루프
# ==========================================

label daily_loop:

    python:
        clamp_status()

        current_day = db_player["current_date"]
        current_gold = db_player["gold"]

        cur_charm = db_status["charm"]
        cur_intel = db_status["intelligence"]
        cur_stress = db_status["stress"]

    if current_day > 10:
        hide screen status_panel
        jump ending_branch

    scene black
    show screen status_panel(current_day, current_gold, cur_charm, cur_intel, cur_stress, actions_left)

    "아진산업의 아침이 밝았다."
    "오늘도 살아남아야 한다. 정규직도, 사랑도, 내 손으로 쟁취해야 한다."
    "오늘은 총 [actions_left]번 행동할 수 있다."

    menu:
        "오늘은 무엇을 할까?"

        "폭풍 업무를 한다":
            jump action_work

        "외모를 정비한다":
            jump action_beauty

        "사내 매점에 간다":
            jump action_shop

        "남직원들에게 말을 건다":
            jump action_talk

        "잠깐 쉰다":
            jump action_rest


# ==========================================
# 6. 기본 행동
# ==========================================

label action_work:

    "타닥타닥."
    "엑셀과 파이썬을 넘나들며 미친 듯이 일했다."
    "머리는 똑똑해졌지만, 스트레스가 쌓인다."

    python:
        change_status(intelligence=15, stress=20)
        add_gold(150)
        add_action_log("폭풍 업무")

    "업무 메일 37개, 엑셀 파일 12개, 그리고 내 영혼 하나를 처리했다."

    jump after_action


label action_beauty:

    "화장실 거울 앞에 섰다."
    "립을 다시 바르고, 머리를 정리하고, 출근길에 구겨진 자존심도 살짝 펴봤다."

    python:
        change_status(charm=20, stress=-5)
        add_action_log("외모관리")

    "오늘의 나는 조금 더 반짝이는 것 같다."

    jump after_action


label action_rest:

    "옥상으로 올라가 잠깐 바람을 쐬었다."
    "아진산업 건물 사이로 부는 바람이 이상하게 위로가 된다."

    python:
        change_status(stress=-25)
        add_action_log("휴식")

    "스트레스가 조금 내려갔다."

    jump after_action


# ==========================================
# 7. 상점
# ==========================================

label action_shop:

    $ current_gold = db_player["gold"]

    "사내 매점 아주머니가 반갑게 맞이해 주신다."
    "현재 지갑에는 [current_gold]G가 있다."

    menu:
        "무엇을 살까?"

        "비타민 음료 100G - 스트레스 감소":
            $ buy_id = 1
            $ buy_price = 100
            jump process_buy

        "고급 향수 500G - 매력 대폭 상승":
            $ buy_id = 2
            $ buy_price = 500
            jump process_buy

        "실무 엑셀 책 300G - 지능 상승":
            $ buy_id = 3
            $ buy_price = 300
            jump process_buy

        "야근 쿠키 150G - 스트레스 감소, 매력 소폭 상승":
            $ buy_id = 4
            $ buy_price = 150
            jump process_buy

        "구경만 하고 나온다":
            jump daily_loop


label process_buy:

    python:
        success = buy_item(buy_id, buy_price)

    if success:
        "결제 완료."
        "아이템 효과가 즉시 적용되었다."
        jump after_action
    else:
        "잔액이 부족하다."
        "월급을 더 모아오자."
        jump daily_loop


# ==========================================
# 8. 남주 공략 - 선택지형 대화
#    실루엣 카드 제거
#    남주 선택 시 전체 화면 사진 바로 표시
# ==========================================

label show_affection_change_text(male_id, gain):

    $ cur_aff = get_affection(male_id)
    $ gain_text = "호감도 +{}".format(gain) if gain >= 0 else "호감도 {}".format(gain)

    "[db_male[male_id]]"
    "[gain_text]"
    "현재 호감도: [cur_aff]"

    return


label show_male_image(image_list):

    $ male_img = choose_existing_image(image_list)

    hide male_sprite

    if male_img:
        show expression Image(male_img) as male_sprite at male_full_center

    with dissolve

    return


label show_ending_cg(image_name):

    scene expression Solid("#1b1b24")

    if image_name and renpy.loadable(image_name):
        show expression Image(image_name) as ending_cg at ending_full_fit

    with dissolve

    return


label action_talk:

    python:
        aff1 = get_affection(1)
        aff2 = get_affection(2)
        aff3 = get_affection(3)
        aff4 = get_affection(4)

    scene black

    "휴게실 문을 열자, 형광등 아래 공기마저 괜히 설레는 것 같았다."
    "오늘은 누구에게 말을 걸까?"

    menu:
        "누구에게 다가갈까?"

        "하원준 본부장  |  호감도 [aff1]":
            jump talk_wonjun

        "류인환 선배  |  호감도 [aff2]":
            jump talk_inhwan

        "김용주 동기  |  호감도 [aff3]":
            jump talk_yongju

        "김도경 인턴  |  호감도 [aff4]":
            jump talk_dokyung

        "부끄러워서 그냥 자리로 돌아간다":
            "아직은 심장이 업무 결재를 못 받았다."
            jump daily_loop


# ==========================================
# 8-1. 하원준 본부장
# ==========================================

label talk_wonjun:

    scene expression Solid("#1b1b24")
    $ male_img = choose_existing_image([wonjun_base_image])
    hide male_sprite
    if male_img:
        show expression Image(male_img) as male_sprite at male_full_center
    with dissolve

    python:
        line = random.choice([
            "아진씨, 보고서보다 당신 표정이 더 신경 쓰입니다.",
            "업무 시간에 이렇게 사람 마음 흔들어도 됩니까.",
            "내가 원래 사적인 감정은 업무에 안 섞는데, 당신은 예외로 하죠.",
            "오늘 일정표에 없는 일이 생겼습니다. 당신과 커피 마시는 일.",
            "결재는 제가 빠른 편인데, 당신 생각은 계속 보류 중입니다.",
            "아진씨가 웃으면 회의실 공기가 달라집니다. 꽤 위험하게.",
            "나한테 이렇게 신경 쓰이는 사람, 처음입니다.",
            "내가 차가운 사람이라 생각했다면 틀렸습니다. 당신 앞에서는 자꾸 녹거든요."
        ])

    m1 "[line]"
    "본부장님의 시선이 묘하게 오래 머문다."

    menu:
        "뭐라고 대답할까?"

        "“그럼 제 일정에도 본부장님 넣어둘게요.”":
            $ gain = 28
            python:
                change_affection(1, gain)
                change_status(charm=6, stress=-5)
                add_action_log("하원준 대화 - 일정 플러팅")
            call show_male_image(wonjun_reaction_images) from _call_show_male_image
            m1 "좋습니다. 그 일정은 제가 직접 관리하겠습니다."
            "순간 회의실보다 내 심장이 더 조용해졌다."
            call show_affection_change_text(1, gain) from _call_show_affection_change_text
            jump after_action

        "“본부장님, 지금 저 꼬시는 거예요?”":
            $ gain = 20
            python:
                change_affection(1, gain)
                change_status(charm=4)
                add_action_log("하원준 대화 - 직진 확인")
            call show_male_image(wonjun_reaction_images) from _call_show_male_image_1
            m1 "아직 시작도 안 했습니다."
            "무심한 얼굴로 저런 말을 하는 건 명백한 반칙이다."
            call show_affection_change_text(1, gain) from _call_show_affection_change_text_1
            jump after_action

        "“보고서 말고 제 마음도 검토해 주세요.”":
            $ gain = 24
            python:
                change_affection(1, gain)
                change_status(charm=5, stress=-3)
                add_action_log("하원준 대화 - 보고서 플러팅")
            call show_male_image(wonjun_reaction_images) from _call_show_male_image_2
            m1 "검토 결과, 반려할 수 없겠군요."
            "본부장님의 낮은 목소리에 정신이 잠깐 로그아웃됐다."
            call show_affection_change_text(1, gain) from _call_show_affection_change_text_2
            jump after_action

        "“본부장님이 보면 자꾸 긴장돼서 실수할 것 같아요.”":
            $ gain = 13
            python:
                change_affection(1, gain)
                change_status(stress=3, charm=2)
                add_action_log("하원준 대화 - 솔직 답변")
            call show_male_image(wonjun_reaction_images) from _call_show_male_image_3
            m1 "그럼 내가 옆에서 잡아주겠습니다. 실수하지 않게."
            "차가운 말투인데 묘하게 다정했다."
            call show_affection_change_text(1, gain) from _call_show_affection_change_text_3
            jump after_action

        "“그럼 커피는 제가 사겠습니다. 대신 퇴근 후에요.”":
            $ gain = 18
            python:
                change_affection(1, gain)
                change_status(charm=3, stress=-2)
                add_action_log("하원준 대화 - 퇴근 후 약속")
            call show_male_image(wonjun_reaction_images) from _call_show_male_image_4
            m1 "퇴근 후라. 그 말은 사적인 시간이라는 뜻입니까?"
            "질문은 차분했지만, 분위기는 전혀 차분하지 않았다."
            call show_affection_change_text(1, gain) from _call_show_affection_change_text_4
            jump after_action

        "“죄송합니다. 업무에 집중하겠습니다.”":
            $ gain = -6
            python:
                change_affection(1, gain)
                change_status(stress=6)
                add_action_log("하원준 대화 - 거리두기")
            call show_male_image(wonjun_reaction_images) from _call_show_male_image_5
            m1 "그렇게 선을 긋는군요."
            "괜히 분위기가 차가워졌다."
            call show_affection_change_text(1, gain) from _call_show_affection_change_text_5
            jump after_action


# ==========================================
# 8-2. 류인환 선배
# ==========================================

label talk_inhwan:

    scene expression Solid("#1b1b24")
    $ male_img = choose_existing_image([inhwan_base_image])
    hide male_sprite
    if male_img:
        show expression Image(male_img) as male_sprite at male_full_center
    with dissolve

    python:
        line = random.choice([
            "아진씨, 오늘 힘들었죠? 표정에 다 쓰여 있어요.",
            "점심 같이 먹을래요? 혼자 먹기엔 오늘 하늘이 너무 예쁘잖아요.",
            "일은 내가 도와줄게요. 대신 아진씨는 웃어주기만 해요.",
            "오늘도 잘 버텼어요. 그거면 충분히 멋져요.",
            "아진씨가 괜찮다고 해도, 나는 그냥 지나칠 자신이 없어요.",
            "커피는 달게 샀어요. 오늘 하루가 충분히 썼을 것 같아서요.",
            "내가 옆에 있으면 조금 덜 힘들었으면 좋겠어요.",
            "좋아하는 사람한테는 괜히 더 다정해지나 봐요."
        ])

    m2 "[line]"
    "선배의 목소리는 이상하게 퇴근 알림보다 더 위로가 된다."

    menu:
        "뭐라고 대답할까?"

        "“선배랑 있으면 야근도 괜찮을 것 같아요.”":
            $ gain = 28
            python:
                change_affection(2, gain)
                change_status(stress=-10, charm=3)
                add_action_log("류인환 대화 - 야근 플러팅")
            call show_male_image(inhwan_reaction_images) from _call_show_male_image_6
            m2 "그럼 오늘은 내가 끝까지 옆에 있어줄게요."
            "다정함이 과하면 심장에 해롭다."
            call show_affection_change_text(2, gain) from _call_show_affection_change_text_6
            jump after_action

        "“저 힘든 거 어떻게 알았어요?”":
            $ gain = 18
            python:
                change_affection(2, gain)
                change_status(stress=-6)
                add_action_log("류인환 대화 - 솔직 답변")
            call show_male_image(inhwan_reaction_images) from _call_show_male_image_7
            m2 "좋아하는 사람 표정은 모를 수가 없거든요."
            "그 말에 잠깐 숨을 고르는 법을 잊었다."
            call show_affection_change_text(2, gain) from _call_show_affection_change_text_7
            jump after_action

        "“선배는 사람을 너무 설레게 해요.”":
            $ gain = 24
            python:
                change_affection(2, gain)
                change_status(charm=5, stress=-5)
                add_action_log("류인환 대화 - 설렘 고백")
            call show_male_image(inhwan_reaction_images) from _call_show_male_image_8
            m2 "아진씨한테만 그러는 거면, 괜찮죠?"
            "웃는 얼굴이 너무 반칙이라 눈을 피했다."
            call show_affection_change_text(2, gain) from _call_show_affection_change_text_8
            jump after_action

        "“그럼 오늘 점심은 선배 옆자리로 예약할게요.”":
            $ gain = 20
            python:
                change_affection(2, gain)
                change_status(stress=-7)
                add_action_log("류인환 대화 - 점심 약속")
            call show_male_image(inhwan_reaction_images) from _call_show_male_image_9
            m2 "예약 확인했습니다. 취소는 안 돼요."
            "선배가 웃자 점심시간이 갑자기 멀게 느껴졌다."
            call show_affection_change_text(2, gain) from _call_show_affection_change_text_9
            jump after_action

        "“저도 선배한테 기대도 돼요?”":
            $ gain = 26
            python:
                change_affection(2, gain)
                change_status(stress=-12)
                add_action_log("류인환 대화 - 기대기")
            call show_male_image(inhwan_reaction_images) from _call_show_male_image_10
            m2 "언제든요. 넘어지기 전에 내가 먼저 잡을게요."
            "따뜻한 말 한마디가 오늘 하루를 버티게 했다."
            call show_affection_change_text(2, gain) from _call_show_affection_change_text_10
            jump after_action

        "“괜찮아요. 혼자 할 수 있어요.”":
            $ gain = -4
            python:
                change_affection(2, gain)
                change_status(stress=4)
                add_action_log("류인환 대화 - 독립 답변")
            call show_male_image(inhwan_reaction_images) from _call_show_male_image_11
            m2 "그럼 정말 힘들 때는 꼭 불러줘요."
            "선배의 표정에 살짝 서운함이 스쳤다."
            call show_affection_change_text(2, gain) from _call_show_affection_change_text_11
            jump after_action


# ==========================================
# 8-3. 김용주 동기
# ==========================================

label talk_yongju:

    scene expression Solid("#1b1b24")
    $ male_img = choose_existing_image([yongju_base_image])
    hide male_sprite
    if male_img:
        show expression Image(male_img) as male_sprite at male_full_center
    with dissolve

    python:
        line = random.choice([
            "너 오늘 좀 괜찮다. 아니, 꽤.",
            "넥타이 삐뚤어졌어. 가만히 있어. 내가 해줄게.",
            "나 원래 남 일에 관심 없는데, 너는 자꾸 눈에 밟혀.",
            "내가 완벽주의자인데, 요즘 제일 신경 쓰이는 오차가 너야.",
            "너랑 있으면 계획이 자꾸 틀어져. 근데 이상하게 싫지가 않아.",
            "네가 웃으면 집중이 깨져. 업무 방해로 신고해야 하나.",
            "나는 확실한 게 좋은데, 너 앞에서는 자꾸 헷갈려.",
            "완벽한 하루의 조건이 바뀌었어. 네가 있어야 하더라."
        ])

    m3 "[line]"
    "무심한 말투인데, 이상하게 귀 끝이 뜨거워진다."

    menu:
        "뭐라고 대답할까?"

        "“그 오차, 계속 신경 써도 돼.”":
            $ gain = 27
            python:
                change_affection(3, gain)
                change_status(charm=6)
                add_action_log("김용주 대화 - 오차 플러팅")
            call show_male_image(yongju_reaction_images) from _call_show_male_image_12
            m3 "큰일났네. 나 꽤 집요한데."
            "그의 미소가 너무 완벽해서 억울했다."
            call show_affection_change_text(3, gain) from _call_show_affection_change_text_12
            jump after_action

        "“너도 오늘 좀 괜찮네. 아니, 많이.”":
            $ gain = 18
            python:
                change_affection(3, gain)
                change_status(charm=4)
                add_action_log("김용주 대화 - 맞받아치기")
            call show_male_image(yongju_reaction_images) from _call_show_male_image_13
            m3 "드디어 안목이 생겼네."
            "얄미운데, 또 설렜다."
            call show_affection_change_text(3, gain) from _call_show_affection_change_text_13
            jump after_action

        "“그럼 내 표정만 보지 말고 내 마음도 봐.”":
            $ gain = 25
            python:
                change_affection(3, gain)
                change_status(charm=5, stress=-2)
                add_action_log("김용주 대화 - 마음 도발")
            call show_male_image(yongju_reaction_images) from _call_show_male_image_14
            m3 "이미 보고 있었어. 네가 모른 척했을 뿐이지."
            "말끝이 가벼운데 눈빛은 전혀 가볍지 않았다."
            call show_affection_change_text(3, gain) from _call_show_affection_change_text_14
            jump after_action

        "“너 때문에 나도 자꾸 계획이 틀어져.”":
            $ gain = 21
            python:
                change_affection(3, gain)
                change_status(charm=3)
                add_action_log("김용주 대화 - 계획 고백")
            call show_male_image(yongju_reaction_images) from _call_show_male_image_15
            m3 "그럼 우리 둘 다 실패네. 근데 나쁘지 않다."
            "완벽주의자가 실패를 웃으며 말하는 건 처음 봤다."
            call show_affection_change_text(3, gain) from _call_show_affection_change_text_15
            jump after_action

        "“업무 방해면 책임져. 오늘 커피 사.”":
            $ gain = 16
            python:
                change_affection(3, gain)
                change_status(stress=-3)
                add_action_log("김용주 대화 - 커피 요구")
            call show_male_image(yongju_reaction_images) from _call_show_male_image_16
            m3 "커피로 끝낼 생각은 아니었는데."
            "장난처럼 들렸지만 심장은 진지하게 반응했다."
            call show_affection_change_text(3, gain) from _call_show_affection_change_text_16
            jump after_action

        "“그런 말 하지 마. 헷갈려.”":
            $ gain = 5
            python:
                change_affection(3, gain)
                change_status(stress=4)
                add_action_log("김용주 대화 - 회피 답변")
            call show_male_image(yongju_reaction_images) from _call_show_male_image_17
            m3 "헷갈리는 게 꼭 나쁜 건 아니잖아."
            "대화가 더 위험해졌다."
            call show_affection_change_text(3, gain) from _call_show_affection_change_text_17
            jump after_action


# ==========================================
# 8-4. 김도경 인턴
# ==========================================

label talk_dokyung:

    scene expression Solid("#1b1b24")
    $ male_img = choose_existing_image([dokyung_base_image])
    hide male_sprite
    if male_img:
        show expression Image(male_img) as male_sprite at male_full_center
    with dissolve

    python:
        line = random.choice([
            "선배님, 저 오늘 복사 안 씹히게 했어요. 칭찬해 주세요.",
            "저는 선배님 편이에요. 회식 때도, 야근 때도, 세상이 무너져도요.",
            "선배님이 웃으면 저 오늘 퇴근 안 해도 괜찮을 것 같아요.",
            "저, 선배님한테 잘 보이고 싶어서 넥타이 세 번 다시 맸어요.",
            "선배님 부르면 저 어디든 달려갈 수 있어요. 사무실 끝에서 끝까지도요.",
            "오늘 제 목표는 선배님한테 칭찬 한 번 받는 거예요.",
            "선배님, 저 방금 프린터보다 더 뜨거워진 것 같아요.",
            "저는 아직 부족하지만, 선배님 옆자리는 누구보다 열심히 지킬 수 있어요."
        ])

    m4 "[line]"
    "김도경 인턴의 눈빛은 거의 퇴근길 강아지 같았다."

    menu:
        "뭐라고 대답할까?"

        "“잘했어. 오늘도 귀엽네.”":
            $ gain = 28
            python:
                change_affection(4, gain)
                change_status(stress=-7)
                add_action_log("김도경 대화 - 칭찬 답변")
            call show_male_image(dokyung_reaction_images) from _call_show_male_image_18
            m4 "선배님이 귀엽다고 했어. 저 오늘 잠 못 자요."
            "이 정도면 복지가 아니라 치유다."
            call show_affection_change_text(4, gain) from _call_show_affection_change_text_18
            jump after_action

        "“그럼 내일도 내 옆자리 예약이야.”":
            $ gain = 22
            python:
                change_affection(4, gain)
                change_status(charm=3)
                add_action_log("김도경 대화 - 옆자리 예약")
            call show_male_image(dokyung_reaction_images) from _call_show_male_image_19
            m4 "정말요? 저 자리 지키려고 오늘부터 야근할래요."
            "그의 눈이 반짝였다."
            call show_affection_change_text(4, gain) from _call_show_affection_change_text_19
            jump after_action

        "“나 부르면 진짜 바로 올 거야?”":
            $ gain = 18
            python:
                change_affection(4, gain)
                change_status(stress=-4)
                add_action_log("김도경 대화 - 호출 확인")
            call show_male_image(dokyung_reaction_images) from _call_show_male_image_20
            m4 "네. 선배님 목소리면 알람보다 빨라요."
            "너무 해맑아서 오히려 내가 졌다."
            call show_affection_change_text(4, gain) from _call_show_affection_change_text_20
            jump after_action

        "“그럼 오늘 칭찬 쿠폰 하나 줄게.”":
            $ gain = 24
            python:
                change_affection(4, gain)
                change_status(stress=-5, charm=2)
                add_action_log("김도경 대화 - 칭찬 쿠폰")
            call show_male_image(dokyung_reaction_images) from _call_show_male_image_21
            m4 "저 그거 평생 보관해도 돼요?"
            "종이 한 장도 아닌 말 한마디에 저렇게 행복해하다니."
            call show_affection_change_text(4, gain) from _call_show_affection_change_text_21
            jump after_action

        "“내 편이면 오늘 커피도 내 편으로 사와.”":
            $ gain = 14
            python:
                change_affection(4, gain)
                change_status(stress=-2)
                add_action_log("김도경 대화 - 장난 답변")
            call show_male_image(dokyung_reaction_images) from _call_show_male_image_22
            m4 "네. 선배님 취향까지 외워서 오겠습니다."
            "대형견 같은 충성심이 조금 부담스럽고 꽤 귀여웠다."
            call show_affection_change_text(4, gain) from _call_show_affection_change_text_22
            jump after_action

        "“일단 일부터 제대로 하자.”":
            $ gain = -5
            python:
                change_affection(4, gain)
                change_status(intelligence=3)
                add_action_log("김도경 대화 - 선긋기")
            call show_male_image(dokyung_reaction_images) from _call_show_male_image_23
            m4 "네. 그래도 저 열심히 할게요."
            "축 처진 어깨가 조금 신경 쓰였다."
            call show_affection_change_text(4, gain) from _call_show_affection_change_text_23
            jump after_action


# ==========================================
# 9. 행동 1회 종료 처리
# ==========================================

label after_action:

    $ actions_left -= 1

    if actions_left > 0:
        "아직 오늘 할 수 있는 행동이 [actions_left]번 남았다."
        jump daily_loop
    else:
        "오늘은 더 이상 행동할 힘이 없다."
        jump end_of_day


# ==========================================
# 10. 하루 마무리
# ==========================================

label end_of_day:

    "오늘의 일과를 모두 마쳤다."
    "집에 돌아와 침대에 누웠다."
    "눈을 감자 오늘 마주친 얼굴들이 하나씩 떠올랐다."

    $ save_day_to_mariadb()

    $ db_player["current_date"] += 1
    $ actions_left = 2

    jump daily_loop


# ==========================================
# 11. 엔딩 분기
# ==========================================

label ending_branch:

    scene black
    hide screen status_panel

    "어느덧 아진산업에 입사한 지 10일이 지났다."
    "오늘 드디어 정규직 전환 및 부서 배치가 발표되는 날이다."

    python:
        best_male_id, highest_score = get_best_male()

        final_intel = db_status["intelligence"]
        final_stress = db_status["stress"]
        final_charm = db_status["charm"]
        final_day = db_player["current_date"]

        final_ending_id = resolve_ending_id()

        db_ending_log.append({
            "ending_id": final_ending_id,
            "achieved_date": final_day,
            "best_male_id": best_male_id,
            "highest_score": highest_score,
            "final_intelligence": final_intel,
            "final_stress": final_stress,
            "final_charm": final_charm
        })

    $ save_day_to_mariadb(show_message=False)
    $ save_ending_to_mariadb(final_ending_id, best_male_id, highest_score, final_charm, final_intel, final_stress)

    if final_ending_id == 1:
        call show_ending_cg(wonjun_ending_happy_image) from _call_show_ending_cg
        m1 "아진씨, 10일 동안 지켜봤습니다."
        m1 "이제 인턴이 아니라... 제 사람으로 남아주십시오."
        "까칠한 줄만 알았던 하원준 본부장님과 사내 연애를 시작했다."
        "하원준 해피엔딩."

    elif final_ending_id == 2:
        call show_ending_cg(inhwan_ending_happy_image) from _call_show_ending_cg_1
        m2 "아진아, 나 사실 처음 봤을 때부터 너 좋아했어."
        m2 "일도 도와주고 싶었지만, 사실은 네 하루에 내가 있고 싶었어."
        "다정다감한 류인환 선배와 연인이 되었다."
        "류인환 해피엔딩."

    elif final_ending_id == 3:
        call show_ending_cg(yongju_ending_happy_image) from _call_show_ending_cg_2
        m3 "너랑 같은 팀이라는 게, 이제 좀 위험해졌어."
        m3 "일보다 네가 더 신경 쓰이거든."
        "김용주 동기와 완벽하지만 위험한 사내연애를 시작했다."
        "김용주 해피엔딩."

    elif final_ending_id == 4:
        call show_ending_cg(dokyung_ending_happy_image) from _call_show_ending_cg_3
        m4 "선배님, 저 이제 인턴 말고..."
        m4 "선배님 남자친구로 채용해 주세요."
        "김도경 인턴의 대형견 같은 고백을 받아주었다."
        "김도경 해피엔딩."

    elif final_ending_id == 5:
        scene expression Solid("#1b1b24")
        call show_male_image([wonjun_base_image]) from _call_show_male_image_24
        m1 "아진씨, 좋은 사람입니다."
        m1 "지금은 여기까지지만... 언젠가 다시 제대로 말하겠습니다."
        "하원준 본부장과 묘한 여운을 남긴 채 10일이 끝났다."
        "하원준 노멀엔딩."

    elif final_ending_id == 6:
        scene expression Solid("#1b1b24")
        call show_male_image([inhwan_base_image]) from _call_show_male_image_25
        m2 "아진씨랑 함께한 시간, 저는 꽤 소중했어요."
        m2 "다음에는 조금 더 용기 내볼게요."
        "류인환 선배와 따뜻한 관계를 유지하게 되었다."
        "류인환 노멀엔딩."

    elif final_ending_id == 7:
        scene expression Solid("#1b1b24")
        call show_male_image([yongju_base_image]) from _call_show_male_image_26
        m3 "너, 꽤 신경 쓰이는 사람이야."
        m3 "아직 고백은 아니고. 그냥 사실 확인."
        "김용주 동기와 애매하지만 설레는 관계가 되었다."
        "김용주 노멀엔딩."

    elif final_ending_id == 8:
        scene expression Solid("#1b1b24")
        call show_male_image([dokyung_base_image]) from _call_show_male_image_27
        m4 "선배님, 저 아직 부족하지만 계속 옆에 있어도 돼요?"
        "김도경 인턴과 귀여운 가능성을 남겼다."
        "김도경 노멀엔딩."

    elif final_ending_id == 9:
        call show_ending_cg(ending_workaholic_image) from _call_show_ending_cg_4
        "회장님: 아진 사원의 뛰어난 업무 능력. 오늘부터 팀장으로 특별 승진시킵니다."
        "연애는 무슨. 일에 미쳐 살았더니 10일 만에 초고속 승진했다."
        "워커홀릭 엔딩."

    elif final_ending_id == 10:
        call show_ending_cg(ending_bad_burnout_image) from _call_show_ending_cg_5
        "10일 동안 너무 무리했다."
        "연애도, 일도, 나 자신도 챙기지 못한 채 번아웃이 와버렸다."
        "번아웃 배드엔딩."

    else:
        call show_ending_cg(ending_bad_plain_image) from _call_show_ending_cg_6
        "10일이 지났지만, 나는 아무런 존재감 없는 평범한 사원이 되었다."
        "일도 사랑도 어중간했다."
        "평범한 직장인 배드엔딩."

    "--- 게임 오버 ---"
    "수고하셨습니다."

    return
