import os
import csv
import random
import uuid
import re
from datetime import datetime, timedelta

print("--- 일상 대화 중심 다양성 극대화 정상 데이터 생성 스크립트 시작 ---")

# --- 1. 설정 ---
# TODO: 생성된 CSV 파일들을 저장할 폴더 경로를 설정해주세요.
# 이 폴더는 나중에 preprocess_data.py의 raw_data_sources에 추가되어야 합니다.
output_directory = 'csv/normal'

# 생성할 파일 수
num_files = 9

# 파일당 메시지 수
messages_per_file = 100000

# 파일 이름 접두사
output_filename_prefix = 'normal_data_'

# CSV 파일 인코딩 (일반적으로 utf-8 사용)
output_encoding = 'utf-8'


# --- 2. 일상 대화 중심 다양성 극대화 정상 메시지 내용 템플릿 ---
# 이전 템플릿 + 더 많은 일상 대화, 알림, 정보 시나리오 추가
# <>로 묶인 부분은 임의 값으로 대체될 플레이스홀더입니다.
normal_message_templates = [
    # --- 친구/지인 대화 (캐주얼, 비격식, 약어, 이모티콘, 유행어 포함) ---
    "<GREETING_CASUAL>! <NAME>! <CHECK_IN_CASUAL> <EMOTICON>", 
    "주말에 뭐 할 거 <EXISTENCE_QUESTION_CASUAL>?", 
    "이번 주 <DAY>요일 <TIME>에 같이 <ACTIVITY> 할래?",
    "최근에 본 <MEDIA_TYPE> <MEDIA_TITLE> <ACTION_MEDIA> 좀 해줘!<EMOTICON_POSITIVE>", 
    "이거 완전 <REACTION_STRONG> ㅋㅋㅋ <VIDEO_URL>", 
    "이 기사 한번 봐봐. <ARTICLE_URL> <REACTION_MILD> 내용이야.",
    "어제 <SOCIAL_MEDIA_PLATFORM>에 올린 <SOCIAL_MEDIA_CONTENT_TYPE> 잘 봤어!<EMOTICON_HAPPY>",
    "<NAME>한테 <GREETING_SHORT> 좀 전해줘.",
    "생각나서 연락했어~ <EMOTICON_MILD>",
    "혹시 <NUMBER>시에 시간 <AVAILABILITY_QUESTION>? <REASON_CASUAL>", 
    "궁금한 게 있는데 잠시 <COMMUNICATION_TYPE_CASUAL> 가능?",
    "힘들면 언제든 <ACTION_CASUAL>!",
    "<ENCOURAGEMENT>! <SUPPORT_PHRASE>!<EMOTICON_CHEER>", 
    "우리 언제 한번 만나서 <PLAN_ACTIVITY_CASUAL> 하자!",
    "예전에 같이 갔던 <PLACE_CASUAL> 기억나?<EMOTICON_NOSTALGIA>",
    "<NUMBER>년 전에 <LOCATION_CASUAL>에서 찍은 <PHOTO_TYPE> 발견했어!<EMOTICON_HAPPY>", 
    "<ABBREVIATION_GREETING> <NAME>!<ABBREVIATION_QUESTION>", 
    "ㅋㅋㅋㅋ ㅠㅠ <EMOTICON_FUNNY>",
    "<RESPONSE_SHORT_POSITIVE>!", 
    "<RESPONSE_SHORT_NEGATIVE> ㅠㅠ", 
    "<EMOTION_TIRED>... 오늘 너무 <STATE_TIRED>.<EMOTICON_TIRED>", 
    "오늘 <WEATHER_CASUAL> <REACTION_WEATHER>", 
    "<NUMBER>분 뒤에 <LOCATION_CASUAL> 도착!<EMOTICON_TRAVEL>",
    "뭐해?", "어디야?", "집이야?", 
    "낼 시간 돼?", "이번 주말 콜?",
    "ㄱㄱ!", "ㅇㅇ 갈게!", 
    "<DAILY_ROUTINE_ACTION> <EMOTICON_DAILY>", 
    "심심하다...", "배고파...", "졸려...", 
    "이 짤 좀 봐봐 ㅋㅋㅋ <IMAGE_LINK>", 
    "<RESTAURANT_NAME> <FOOD_TYPE> <REVIEW_PHRASE> <PLACE_REVIEW_LINK>", 
    "오늘 저녁 <FOOD> 먹으러 가자!",
    "생각보다 <ADJECTIVE_CASUAL>!", 
    "혹시 <OBJECT> <EXISTENCE_QUESTION_CASUAL>?", 
    "<NUMBER>시에 <PLACE_MEETING>에서 볼 수 있어?", 
    "오늘 <EVENT_CASUAL> 어땠어?", 

    # --- 가족 대화 (편하게, 알림성, 돌봄) ---
    "<FAMILY_MEMBER_HONORIFIC>! <MEAL> 뭐 <COOKING_ACTION>?", 
    "<FAMILY_MEMBER_CASUAL>, 오늘 <SCHOOL_PLAN> 잘 <PROGRESS_VERB>?", 
    "집에 올 때 <ITEM> 좀 <REQUEST_ACTION_FAMILY> 줘.<EMOTICON_REQUEST>", 
    "오늘 날씨 <WEATHER_FAMILY>니까 <CLOTHING> 입고 나가!",
    "주말에 다 같이 <FAMILY_PLAN> 할까?",
    "<LOCATION_FAMILY>에 <FOOD> <EXISTENCE_PHRASE> <ACTION_FAMILY>~", 
    "필요한 거 <ITEM> <EXISTENCE_QUESTION_FAMILY>?", 
    "<ENCOURAGEMENT_FAMILY> <ACTION_FAMILY>.", 
    "내일 <TIME>에 <MEET_ACTION_FAMILY> 봐!", 
    "<RELATIVE_HONORIFIC>께 <GREETING_LONG> 전화 <ACTION_PHONE>니?",
    "집에 <OBJECT> 있는지 <ACTION_FAMILY> 줄 수 있어?",
    "오늘 <EVENT_FAMILY> 있었는데 <REACTION_FAMILY>!",
    "<FAMILY_MEMBER_CASUAL_DAD>, 엄마가 <ITEM> <LOCATION_FAMILY>에 뒀어. 잊지 말고 <ACTION_CHILD>!", 
    "<FAMILY_MEMBER_CASUAL_DAD>, 아빠 오늘 <TIME>에 퇴근해. <MEAL> 같이 먹자.",
    "<PARTNER_HONORIFIC>, 오늘 저녁은 <FOOD> 어때?<EMOTICON_LOVE>", 
    "<ITEM> 샀는데 맛있더라. <PHOTO_URL> 이거 봐봐!",
    "오늘 <CONDITION_CHILD>?", 
    "<RELATIVE_HONORIFIC> <CONDITION_RELATIVE_QUESTION>?", 
    "집 <STATUS_HOME> <CHECK_ACTION_FAMILY> 줄 수 있어?", 
    "오늘 <SHOP_FAMILY> 갔는데 <ITEM> 싸더라.", 
    "밥 <ACTION_EAT> <EMOTICON_OK>", 
    "<FAMILY_MEMBER_HONORIFIC>, <OBJECT> 어디에 뒀는지 <REMEMBER_QUESTION>?", 
    "<FAMILY_MEMBER_CASUAL>, <ITEM> 다 <ACTION_USE_COMPLETE>.", 
    "<NUMBER>시에 <PLACE_FAMILY>로 <MOVE_ACTION_FAMILY>.", 
    "오늘 <ACTION_HOUSEHOLD> <STATUS_HOUSEHOLD>.", 
    "<FAMILY_MEMBER_HONORIFIC>, <ITEM> <PREPARATION_QUESTION>?", 

    # --- 업무 관련 (정중체, 정보 전달, 요청, 확인) ---
    "<GREETING_WORK>, <NAME> <POSITION>님. <PROJECT> 관련 <DOCUMENT_TYPE> <FILE_LINK> 에 공유했습니다. <CLOSING_WORK>",
    "<GREETING_WORK>, <NAME> <POSITION>님. <MEETING_TIME> <MEETING_PURPOSE> 회의 참석 <AVAILABILITY_QUESTION_WORK>? <CLOSING_WORK>", 
    "금일 <TASK> 진행 상황 <REPORT_TYPE> 드립니다. <CLOSING_WORK>",
    "문의하신 내용은 <DATE>까지 <ACTION_WORK> 드리겠습니다.",
    "<SUBJECT_WORK> 관련 <COMMUNICATION_TYPE_WORK> 확인 부탁드립니다. <CLOSING_WORK>",
    "주간 업무 보고 제출 기한이 <DATE> <TIME>까지입니다.",
    "외근 중이라 문자 확인이 <STATE_WORK>. <TIME> 이후 <COMMUNICATION_TYPE_WORK> 가능합니다.",
    "<ACTION_WORK_AFTER_HOURS> 진행하겠습니다. <CLOSING_WORK>", 
    "첨부 파일 <ACTION_DOCUMENT>하시고 <OPINION_REQUEST> 부탁드립니다. <CLOSING_WORK>",
    "다음 주 <DAY_WORK>까지 <DELIVERY_ITEM> 준비 부탁드립니다. <CLOSING_WORK>",
    "<PROJECT> 예산 <AMOUNT>으로 확정되었습니다. <CLOSING_WORK>",
    "긴급) <ISSUE_WORK> 문제 발생. <ACTION_URGENT> 부탁드립니다.", 
    "[알림] 시스템 점검으로 인해 <SERVICE_WORK> 이용이 <DURATION> 중단됩니다. <CLOSING_WORK>",
    "<NUMBER>층 <LOCATION_WORK>에서 <MEETING_TIME> 회의 시작합니다.",
    "[공지] <EVENT_WORK> 안내. 자세한 내용은 <NOTICE_LINK> 참조. <CLOSING_WORK>",
    "[결제] <AMOUNT> 결제 완료 (<SERVICE_WORK>). <DATE> <TIME>", 
    "[승인] <REQUEST_ITEM> 승인 완료되었습니다. <CLOSING_WORK>",
    "[문의] <SUBJECT_WORK> 관련 문의드립니다. <CLOSING_WORK>",
    "금일 업무 <ACTION_FINISH_WORK>. 내일 <GREETING_WORK_SHORT>.", 
    "<NAME> <POSITION>님, <TASK> <ACTION_TASK_COMPLETE> 보고 드립니다.", 
    "주신 자료 잘 확인했습니다. <CLOSING_WORK_GRATITUDE>.", 
    "내일 오전 <TIME>까지 <TASK> <AVAILABILITY_PHRASE>.", 
    "회의록 <ACTION_DOCUMENT>했습니다. <FILE_LINK> 확인 부탁드립니다.", 
    "출장 보고서 <ACTION_DOCUMENT> 후 <DATE>까지 제출하겠습니다.", 
    "[요청] <TASK> 업무 협조 요청. 자세한 내용은 <COMMUNICATION_TYPE_WORK> 확인 부탁드립니다.", 
    "내일 <SCHEDULE_ITEM> 있습니다. <TIME> <LOCATION_WORK>입니다.", 
    "주간 회의 <DATE> <TIME>로 <ACTION_MEETING_CHANGE>되었습니다.", 
    "오늘 <TASK> <STATUS_TASK>.", 
    "파일 <ACTION_FILE>했습니다. <FILE_LINK> 확인해주세요.", 
    "<NUMBER>월 <NUMBER>일 <EVENT_WORK> 참여 신청했습니다.", 
    "오늘 <TIME>까지 <TASK> 완료 가능합니다.",

    # --- 일상 알림/정보 (시스템/기관 발신 느낌, 자동 알림) ---
    "[알림] 주문하신 <PRODUCT>이/가 <DATE> <TIME>에 <DELIVERY_STATUS> 예정입니다. <TRACKING_LINK>",
    "<BANK> <ACCOUNT_TYPE>에 <AMOUNT> 입금되었습니다. <DATE> <TIME> 잔액 <AMOUNT>", 
    "[카드 사용] <CARD_TYPE> <AMOUNT> 사용. <DATE> <TIME> (<SHOP>)", 
    "[예약] 예약하신 <SERVICE_NAME> 이용이 <DATE> <TIME> 확정되었습니다. <CONFIRM_LINK>", 
    "본인 확인 인증 번호: <NUMBER> 유효 시간 <NUMBER>분", 
    "[공지] 새로운 <INFORMATION_TYPE>이 등록되었습니다. 앱에서 <ACTION_APP>하세요. <APP_LINK>", 
    "[안내] 이번 달 청구 금액은 <AMOUNT>입니다. 납부 기한: <DATE> <PAYMENT_LINK>", 
    "[알림] <MEMBERSHIP_TYPE> 등급이 <GRADE>로 <ACTION_MEMBERSHIP>되었습니다. <BENEFIT_LINK>", 
    "[안내] 사용 기한 만료 예정 <ITEM_TYPE>이 <NUMBER>개 있습니다. 만료일: <EXPIRY_DATE>", 
    "[기상청] 미세먼지 농도 <LEVEL> (<LOCATION>). <SUGGESTION>", 
    "[안내] 오늘 <WEATHER_CONDITION>입니다. <WEATHER_DETAIL>", 
    "[알림] <EVENT_ALERT> 시작 예정입니다. 참여 방법: <PROMOTION_URL>", 
    "[정부24] <CIVIL_COMPLAINT_TYPE> 민원 처리 결과 안내. 확인: <OFFICIAL_LINK>", 
    "[교통위반] <VIOLATION_TYPE>으로 인한 과태료 <AMOUNT> 부과 예정. 문의: <PHONENUM>", 
    "[세금] <TAX_TYPE> 납부 기한 <DATE>까지 입니다. <PAYMENT_LINK>", 
    "[예비군] <EVENT_MILITARY> 훈련 일시 및 장소 안내. 확인: <OFFICIAL_LINK>", 
    "[선거] <ELECTION_TYPE> 투표 안내. 투표소 확인: <OFFICIAL_LINK>", 
    "[건강보험] <CHECKUP_TYPE> 검진 대상자 안내. 예약: <OFFICIAL_LINK>", 
    "[안전안내문자] <DISASTER_TYPE> 발생. <LOCATION> 주민은 <ACTION_DISASTER> 바랍니다.", 
    "[알림] <APP_NAME> <NOTIFICATION_TYPE_APP>이 도착했습니다. <NOTIFICATION_LINK>", 
    "[은행] OTP 인증 번호 <NUMBER>", 
    "[카드] <CARD_TYPE> 승인 <AMOUNT> (<SHOP>)", 
    "[택배] <COURIER_NAME> <DELIVERY_STATUS> 안내. 운송장 번호 <NUMBER> <TRACKING_LINK>", 
    "[쇼핑] <ORDER_NUMBER> 주문하신 상품 발송 완료. <TRACKING_LINK>", 
    "[고객센터] <SERVICE_NAME> 관련 문의 결과 안내. <DETAIL_LINK>", 
    "[이벤트] <EVENT_NAME> 당첨 안내. 경품 수령: <PRIZE_DELIVERY_INFO>", 
    "[멤버십] <MEMBERSHIP_TYPE> <POINT_GAIN> 포인트 적립되었습니다.", 
    "[앱 업데이트] <APP_NAME> 새로운 버전 출시! <UPDATE_LINK>", 
    "[안내] <SERVICE_NAME> 이용 약관 변경 안내",
    "[보안 알림] <ACCOUNT_TYPE> 로그인 알림. <DATE> <TIME> (<LOCATION>)",

    # --- 단순 알림/정보 (광고성 포함) ---
    "[광고] <SHOP> <ITEM_TYPE> <DISCOUNT_RATE>% 할인! <PROMOTION_URL> (<CLOSING_DATE>까지)", 
    "[이벤트] <EVENT_NAME> 참여하고 <PRIZE> 받으세요! <EVENT_URL> (<CLOSING_DATE>까지)", 
    "[정보] <TIP_CONTENT> 팁 확인하기! <ARTICLE_URL>", 
    "오늘의 운세: <FORTUNE_CONTENT>", 
    "주유 할인 안내: <DISCOUNT_RATE>% 할인! <LOCATION> 주유소 <PROMOTION_URL>", 
    "OO 멤버십 <POINT_GAIN> 포인트 적립! <POINT_CHECK_LINK>", 
    "[광고] <PRODUCT> 특가! <AMOUNT> <PROMOTION_URL>",
    "지금 가입하면 <ITEM_TYPE> <AMOUNT> 즉시 지급! <SIGNUP_LINK>", 

    # --- 플레이스홀더 자체를 활용한 템플릿 (오탐 감소 중요) ---
    "링크: <URL>", "번호: <PHONENUM>", "금액: <AMOUNT>", "인증번호: <NUMBER>", 
    "주소: <LOCATION>", "확인: <URL>", "문의: <PHONENUM>", "신청: <URL>", 
    "클릭: <URL>", "문의사항: <PHONENUM>", "결제: <AMOUNT>", "입금: <AMOUNT>",
    "배송조회: <TRACKING_LINK>", "납부: <PAYMENT_LINK>", "자세히 보기: <URL>",
    "다운로드: <FILE_LINK>", "설치: <APP_LINK>", "예약: <CONFIRM_LINK>",
    "바로가기: <URL>", "상세: <DETAIL_LINK>", "업데이트: <UPDATE_LINK>",
    "로그인: <URL>", "조회: <URL>", "본인확인: <URL>", "이동: <URL>",
]

def generate_placeholder(placeholder_type):
    """주어진 플레이스홀더 타입에 맞는 임의 문자열 생성"""
    # 일상 대화, 알림, 업무 등 다양한 시나리오 및 플레이스홀더 처리 로직 포함
    
    if placeholder_type == '<NUMBER>':
        # 숫자 형식 다양화: 정수, 콤마 포함 정수, 소수점, 전화번호 일부처럼 보이게
        formats = ["<NUM_INT>", "<NUM_COMMA>", "<NUM_FLOAT>", "<NUM_PHONE_PART>", "<NUM_CODE>"]
        choice = random.choice(formats)
        if choice == "<NUM_INT>": return str(random.randint(1, 999999999))
        elif choice == "<NUM_COMMA>": return format(random.randint(1000, 999999999), ',')
        elif choice == "<NUM_FLOAT>": return f"{random.randint(1, 100)}.{random.randint(0, 99)}"
        elif choice == "<NUM_PHONE_PART>": return str(random.randint(1000, 9999))
        elif choice == "<NUM_CODE>": return str(random.randint(100000, 999999)) # 인증번호 등
        
    elif placeholder_type == '<AMOUNT>':
         amount = random.randint(1000, 100000000000) 
         formats = ["<AMOUNT_KRW>", "<AMOUNT_UNIT>", "<AMOUNT_CURRENCY>", "<AMOUNT_DECIMAL>"]
         choice = random.choice(formats)
         if choice == "<AMOUNT_KRW>": return format(amount, ',') + random.choice(["원", "원정", "원입니다", ""])
         elif choice == "<AMOUNT_UNIT>": return str(random.randint(1, 1000)) + random.choice(["만원", "천원", "백원"])
         elif choice == "<AMOUNT_CURRENCY>": return format(random.randint(1, 10000), ',') + random.choice(["달러", " USD", "엔", " EUR"])
         elif choice == "<AMOUNT_DECIMAL>": return f"{random.randint(1, 100)}.{random.randint(0, 99)}만원"
         
    elif placeholder_type == '<NAME>':
         first_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "전", "홍", "고", "문", "양", "손", "배", "백", "허", "유", "남", "심", "노", "하", "곽", "성", "차", "구", "라", "나", "민", "진", "엄", "원", "주", "구", "지", "음", "빈", "현", "준", "봉", "천", "피", "탁", "추", "마", "좌", "맹"]
         last_names = ["민준", "서연", "지훈", "예은", "우진", "하윤", "지아", "현우", "은서", "도윤", "서준", "아린", "시우", "하준", "서아", "도은", "이안", "수아", "준서", "채원", "지후", "서현", "건우", "유진", "은찬", "서영", "주원", "하은", "지환", "수빈", "예준", "지유", "도현", "예원", "시윤", "다은", "건호", "아윤", "선우", "지원", "태준", "규리", "승우", "나은", "재준", "소율"]
         return random.choice(first_names) + random.choice(last_names)
    
    # 시간/날짜 관련 플레이스홀더
    elif placeholder_type == '<DAY>':
         days = ["월", "화", "수", "목", "금", "토", "일"]
         return random.choice(days) + random.choice(["요일", ""]) 
    elif placeholder_type == '<TIME>':
         hours_12 = [str(h) for h in range(1, 13)]
         hours_24 = [str(h) for h in range(0, 24)]
         minutes = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]
         am_pm = ["오전", "오후", ""]
         time_formats = [
             f"{random.choice(am_pm)} {random.choice(hours_12)}시 {random.choice(minutes)}분",
             f"{random.choice(hours_24)}:{random.choice(minutes)}",
             f"{random.choice(am_pm)} {random.choice(hours_12)}시",
             f"{random.choice(hours_24)}시",
             f"{random.choice(am_pm)} {random.choice(hours_12)}시 정각",
             "지금", "곧", "방금 전", "아까", "나중에",
             f"{random.choice(hours_12)}:{random.choice(minutes)}{random.choice(['AM', 'PM'])}" # 영어 시간 형식
         ]
         return random.choice(time_formats).strip()
    elif placeholder_type == '<DATE>':
         today = datetime.now()
         random_days_ago = random.randint(0, 1095) 
         target_date = today - timedelta(days=random_days_ago)
         date_formats = [
             "%Y년 %m월 %d일", 
             "%m월 %d일", 
             "%m/%d", 
             "%Y.%m.%d", 
             "%Y-%m-%d",
             "내일", "오늘", "어제", 
             "모레", "그저께",
             "이번 주 <DAY_SHORT>요일", 
             "다음 주 <DAY_SHORT>요일", 
             "%m월 %d일 (<DAY_SHORT>)",
             "%Y/%m/%d", "%Y-%m-%d", # 다른 날짜 형식
             "%m.%d (%a)" # 월.일 (요일 짧은 이름)
         ]
         chosen_format = random.choice(date_formats)
         if chosen_format in ["내일", "오늘", "어제", "모레", "그저께"]: 
              return chosen_format
         elif "주 <DAY_SHORT>요일" in chosen_format:
              days_kr = ["월", "화", "수", "목", "금", "토", "일"]
              return chosen_format.replace("<DAY_SHORT>", random.choice(days_kr))
         elif "(<DAY_SHORT>)" in chosen_format or "(%a)" in chosen_format: 
              days_kr = ["월", "화", "수", "목", "금", "토", "일"]
              # 요일 짧은 이름 (%a)을 한국어 요일로 대체 (예: Mon -> 월)
              day_abbr_eng = target_date.strftime("%a") # 영어 요일 짧은 이름
              day_mapping = {"Mon":"월", "Tue":"화", "Wed":"수", "Thu":"목", "Fri":"금", "Sat":"토", "Sun":"일"}
              korean_day = day_mapping.get(day_abbr_eng, "")
              return target_date.strftime("%m월 %d일") + f" ({korean_day})"

         return target_date.strftime(chosen_format)
    elif placeholder_type == '<DAY_SHORT>': 
         days_kr = ["월", "화", "수", "목", "금", "토", "일"]
         return random.choice(days_kr)
    elif placeholder_type == '<EXPIRY_DATE>': 
         today = datetime.now()
         random_days_later = random.randint(1, 365) 
         target_date = today + timedelta(days=random_days_later)
         date_formats = [
             "%Y년 %m월 %d일", 
             "%m월 %d일", 
             "%m/%d", 
             "%Y.%m.%d", 
             "내일", "다음 주 월요일", "이번 달 말일", "다음 달 초"
         ]
         chosen_format = random.choice(date_formats)
         if chosen_format in ["내일", "이번 달 말일", "다음 달 초"]: 
              return chosen_format
         return target_date.strftime(chosen_format)


    # URL 관련 플레이스홀더 (더 다양한 도메인, 경로, 형식, 파라미터)
    elif placeholder_type in ['<URL>', '<VIDEO_URL>', '<ARTICLE_URL>', '<FILE_LINK>', '<SOCIAL_MEDIA_PLATFORM_URL>', '<PHOTO_URL>', '<CORPORATE_URL>', '<EVENT_URL>', '<SURVEY_URL>', '<PROMOTION_URL>', '<NOTICE_LINK>', '<CONFIRM_LINK>', '<OFFICIAL_LINK>', '<TRACKING_LINK>', '<PAYMENT_LINK>', '<BENEFIT_LINK>', '<APP_LINK>', '<PLACE_REVIEW_LINK>', '<IMAGE_LINK>', '<SIGNUP_LINK>', '<POINT_CHECK_LINK>', '<UPDATE_LINK>', '<NOTIFICATION_LINK>', '<DETAIL_LINK>']:
         domains_legit = [
             "example.com", "myservice.co.kr", "company.org", "newsoutlet.co.kr", "shoppingmall.com", 
             "officialgov.kr", "bankname.co.kr", "cloudstorage.link", 
             "youtube.com", "instagram.com", "twitter.com", "facebook.com", "blog.naver.com", 
             "cafe.daum.net", "coupang.com", "gmarket.co.kr", "auction.co.kr", "tistory.com", 
             "brunch.co.kr", "reddit.com", "pinterest.com", "tiktok.com", "linkedin.com",
             "namu.wiki", "ko.wikipedia.org", "dict.naver.com", "map.naver.com", "map.kakao.com", 
             "travel.example.com", "food.example.com", "sports.example.com", 
             "drive.google.com", "dropbox.com", "onedrive.live.com", 
             "plus.kakao.com", 
             "section.blog.naver.com", "post.naver.com", 
             "pann.nate.com", "instiz.net", "theqoo.net", 
             "www.naver.com", "www.google.com", "www.daum.net" 
         ]
         paths_common = [
             "/view/", "/article/", "/files/", "/watch?v=", "/post/", "/survey?id=", "/event/", 
             "/notice/", "/confirm/", "/promotion/", "/product/", "/board/", "/qna/", 
             "/download/", "/mypage/", "/item/", "/review/", "/location/", "/search/", "/entry/",
             "/channel/", "/clip/", "/photo/", "/status/", "/order/", "/tracking/", "/pay/",
             "/benefit/", "/app/", "/place/", "/image/", "/signup/", "/point/", "/update/", "/notification/", "/detail/",
             "/read/", "/bbs/", "/data/", "/public/", "/service/", "/info/" 
         ]
         extensions_common = [".html", ".pdf", ".jpg", ".png", ".gif", ".mp4", ".zip", ".exe", ".apk", "", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv"] 
         params_common = ["?ref=msg", "?utm_source=kakao", "?v=", "?id=", "?seq=", "?key=", "?code=", "?type=", "?source=", "?ver=", "?lang=ko", "?ref=", "?from=", "?_=1", ""]
         
         domain = random.choice(domains_legit)
         path = "".join(random.choices(paths_common, k=random.randint(1, 5))) 
         unique_id = uuid.uuid4().hex[:random.randint(6, 25)] 
         extension = random.choice(extensions_common) if random.random() > 0.1 else "" 
         params = "".join(random.choices(params_common, k=random.randint(0, 4))) 

         base_url = f"http://{domain}{path}{unique_id}{extension}{params}"

         # 특정 플레이스홀더에 맞는 URL 형식 모방
         if placeholder_type == '<VIDEO_URL>':
             video_ids = [uuid.uuid4().hex[:11], f"v={uuid.uuid4().hex[:10]}"]
             base_url = f"https://youtu.be/{random.choice(video_ids)}" if random.random() < 0.7 else f"https://www.youtube.com/watch?v={random.choice(video_ids)}" 
         elif placeholder_type == '<ARTICLE_URL>':
             news_domains = ['news.naver.com', 'v.daum.net', 'somearticle.co.kr', 'media.example.com', 'hani.co.kr', 'joins.com', 'chosun.com', 'khan.co.kr', 'ohmynews.com', 'ytn.co.kr', 'sbs.co.kr']
             base_url = f"https://{random.choice(news_domains)}/link/{uuid.uuid4().hex[:random.randint(10,15)]}"
         elif placeholder_type == '<SOCIAL_MEDIA_PLATFORM_URL>':
              platform_domains = ["instagram.com", "twitter.com", "facebook.com", "tiktok.com", "band.us", "cafe.naver.com", "section.blog.naver.com"]
              paths_sm = ["/user/", "/public/", "/p/", "/story/", "/reel/", "/videos/", "/posts/", "/channel/", "/members/"]
              base_url = f"https://{random.choice(platform_domains)}{random.choice(paths_sm)}{uuid.uuid4().hex[:random.randint(6,15)]}"
         elif placeholder_type == '<OFFICIAL_LINK>': 
             gov_domains = ["gov.kr", "go.kr", "or.kr", "police.go.kr", "minwon.go.kr", "kisa.or.kr", "nts.go.kr", "nhis.or.kr", "koreanair.com", "asiana.com", "korail.com", "molit.go.kr", "mofa.go.kr", "customs.go.kr", "keco.or.kr", "kwater.or.kr"] 
             paths_gov = ["/verify/", "/info/", "/check/", "/service/", "/guide/", "/notice/", "/data/", "/confirm/", "/view/", "/status/"]
             base_url = f"https://{random.choice(gov_domains)}{random.choice(paths_gov)}{uuid.uuid4().hex[:random.randint(10,20)]}"
         elif placeholder_type == '<TRACKING_LINK>': 
             courier_domains = ["cjlogistics.com", "hanjin.co.kr", "epost.go.kr", "lotteglogis.com", "kdexp.com", "postserv.com"]
             base_url = f"https://{random.choice(courier_domains)}/track/{random.randint(1000000000, 999999999999)}" 
         elif placeholder_type == '<PAYMENT_LINK>': 
             pay_domains = ["pay.example.com", "billing.myservice.co.kr", "tax.gov.kr", "pay.kakao.com", "toss.im/pay", "securepay.com"]
             base_url = f"https://{random.choice(pay_domains)}/pay?id={uuid.uuid4().hex[:random.randint(10, 15)]}"
         elif placeholder_type == '<BENEFIT_LINK>': 
             benefit_domains = ["benefit.example.com", "coupon.shoppingmall.com", "event.myservice.co.kr", "promotion.company.com"]
             base_url = f"https://{random.choice(benefit_domains)}/coupon/{uuid.uuid4().hex[:random.randint(8, 15)]}"
         elif placeholder_type == '<APP_LINK>': 
             app_domains = ["app.example.com", "play.google.com", "apps.apple.com", "apk.example.com"]
             base_url = f"https://{random.choice(app_domains)}/{random.choice(['details?id=', 'app/'])}/{uuid.uuid4().hex[:random.randint(10, 20)]}"
         elif placeholder_type == '<PLACE_REVIEW_LINK>': 
             map_domains = ["map.naver.com", "place.map.kakao.com", "diningcode.com", "yogiyo.co.kr/review", "store.naver.com/restaurants/review"]
             base_url = f"https://{random.choice(map_domains)}/place/{random.randint(100000, 9999999)}/review/{uuid.uuid4().hex[:random.randint(5,10)]}"
         elif placeholder_type == '<IMAGE_LINK>': 
             image_domains = ["imgur.com", "prnt.sc", "drive.google.com", "dropbox.com", "onedrive.live.com", "postimg.cc", "tistory.com/attach", "blog.naver.com/attach"]
             base_url = f"https://{random.choice(image_domains)}/photo/{uuid.uuid4().hex[:random.randint(8, 15)]}"
         elif placeholder_type == '<SIGNUP_LINK>':
             signup_domains = ["signup.example.com", "join.myservice.co.kr", "member.company.org", "register.service.com"]
             base_url = f"https://{random.choice(signup_domains)}/register?code={uuid.uuid4().hex[:random.randint(8, 12)]}"
         elif placeholder_type == '<POINT_CHECK_LINK>':
             point_domains = ["point.example.com", "member.shoppingmall.com/point", "mypage.service.com/point"]
             base_url = f"https://{random.choice(point_domains)}/check/{uuid.uuid4().hex[:random.randint(8, 12)]}"
         elif placeholder_type == '<UPDATE_LINK>':
             update_domains = ["update.example.com", "version.myservice.co.kr", "appupdate.service.com"]
             base_url = f"https://{random.choice(update_domains)}/latest?v={random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0,9)}"
         elif placeholder_type == '<NOTIFICATION_LINK>':
             noti_domains = ["notice.example.com", "alert.myservice.co.kr", "myinfo.service.com/notification"]
             base_url = f"https://{random.choice(noti_domains)}/view/{uuid.uuid4().hex[:random.randint(10, 15)]}"
         elif placeholder_type == '<DETAIL_LINK>':
             detail_domains = ["detail.example.com", "info.myservice.co.kr", "service.com/detail"]
             base_url = f"https://{random.choice(detail_domains)}/item/{uuid.uuid4().hex[:random.randint(10, 15)]}"


         # 40% 확률로 단축 URL처럼 보이게 함 
         if random.random() < 0.4:
             short_domains = ["bit.ly", "goo.gl", "t.co", "me2.do", "c11.kr", "url.kr", "shorturl.at", "tinyurl.com", "zrr.kr", "asq.kr"] 
             return f"http://{random.choice(short_domains)}/{uuid.uuid4().hex[:random.randint(4, 10)]}"
             
         return base_url.replace("http://", random.choice(["http://", "https://"])) 

    # 다양한 상황/행동 관련 플레이스홀더
    elif placeholder_type == '<GREETING_CASUAL>':
        greetings = ["안녕하세요", "안녕하신가", "야!", "어이", "반가워", "수고!", "안녕", "왔어?", "ㅎㅇ", "ㅂㄱ", "ㅇㄴ", "안뇽", "방가방가"]
        return random.choice(greetings)
    elif placeholder_type == '<CHECK_IN_CASUAL>':
         checks = ["잘 지내?", "뭐해?", "요즘 어떻게 지내?", "잘 지내지?", "바빠?", "괜찮아?", "별일 없어?", "어때?", "몸은 괜찮고?", "잘 지내지 궁금했어"]
         return random.choice(checks)
    elif placeholder_type == '<ACTIVITY>': 
         activities = ["밥 먹기", "술 마시기", "카페 가기", "영화 보기", "운동하기", "쇼핑하기", "산책하기", "게임하기", "수다 떨기", "놀러 가기", "드라이브 가기", "공부하기", "일하기", "게임하기", "여행 가기", "등산하기"]
         return random.choice(activities)
    elif placeholder_type == '<MEDIA_TYPE>':
         media_types = ["영화", "드라마", "책", "웹툰", "음악", "애니", "팟캐스트", "유튜브 채널", "웹소설", "만화"]
         return random.choice(media_types)
    elif placeholder_type == '<MEDIA_TITLE>': 
         titles = [
             "극한직업", "기생충", "오징어 게임", "더 글로리", "파친코", "나는 솔로", "무한도전", "런닝맨", 
             "하얼빈", "베테랑2", "범죄도시4", "서울의 봄", "밀수", "콘크리트 유토피아", 
             "세이노의 가르침", "불편한 편의점", "아몬드", "달러구트 꿈 백화점", "나미야 잡화점의 기적", 
             "외모지상주의", "나혼자만 레벨업", "신의 탑", "재벌집 막내아들", 
             "뉴진스", "아이브", "BTS", "블랙핑크", "방탄소년단", "트와이스", "세븐틴" 
         ] + [f"oo {random.choice(['영화', '드라마', '책', '웹툰', '웹소설'])}"] 
         return random.choice(titles)
    elif placeholder_type == '<ACTION_MEDIA>':
         actions = ["추천", "얘기", "봤어", "읽었어", "들어봤어", "어때", "봤냐", "읽었냐", "어땠어"]
         return random.choice(actions)
    elif placeholder_type == '<REACTION_STRONG>':
         reactions = ["완전 웃김", "대박", "소름 돋음", "미쳤다", "헐", "핵잼", "꿀잼", "개웃김", "레전드", "역대급"]
         return random.choice(reactions)
    elif placeholder_type == '<REACTION_MILD>':
         reactions = ["흥미로운", "재밌는", "신기한", "유용한", "새로운", "괜찮은", "좋은", "쏠쏠한"]
         return random.choice(reactions)
    elif placeholder_type == '<SOCIAL_MEDIA_PLATFORM>':
         platforms = ["인스타", "페북", "트위터", "유튜브", "카톡 프로필", "밴드", "틱톡", "네이버 블로그", "티스토리"]
         return random.choice(platforms)
    elif placeholder_type == '<SOCIAL_MEDIA_CONTENT_TYPE>':
         contents = ["사진", "글", "영상", "스토리", "게시물", "라방", "릴스", "쇼츠", "포스팅"]
         return random.choice(contents)
    elif placeholder_type == '<GREETING_SHORT>':
         greetings = ["안부", "소식", "안부 좀", "안부 대신 좀", "안부 전해줘"]
         return random.choice(greetings)
    elif placeholder_type == '<AVAILABILITY_QUESTION>':
         questions = ["괜찮아?", "시간 돼?", "가능해?", "시간 비어?", "언제 시간 나?", "언제쯤 괜찮아?"]
         return random.choice(questions)
    elif placeholder_type == '<REASON_CASUAL>':
         reasons = ["잠깐 물어볼 게 있어서", "같이 가려고", "드릴 말씀이 있어서", "자료 전달해주려고", "얼굴 좀 보려고", "도움이 필요해서", "심심해서", "같이 하고 싶어서", "궁금한 거 있어서"]
         return random.choice(reasons)
    elif placeholder_type == '<COMMUNICATION_TYPE_CASUAL>':
         types = ["통화", "톡", "문자", "잠깐 볼 수 있어", "잠깐 얘기할 수 있어", "전화"]
         return random.choice(types)
    elif placeholder_type == '<ACTION_CASUAL>':
         actions = ["연락해", "말해줘", "얘기해줘", "풀어놔", "전화해", "톡해줘", "문자 줘"]
         return random.choice(actions)
    elif placeholder_type == '<ENCOURAGEMENT>':
         encouragements = ["잘하고 있어", "고생했어", "힘내", "파이팅", "걱정마", "잘 될 거야", "힘내라", "토닥토닥"]
         return random.choice(encouragements)
    elif placeholder_type == '<SUPPORT_PHRASE>':
         phrases = ["응원할게!", "내가 있잖아!", "도와줄게!", "같이 하자!", "힘내자!", "네 편이야!"]
         return random.choice(phrases)
    elif placeholder_type == '<PLAN_ACTIVITY_CASUAL>':
         activities = ["밥 먹기", "술 한잔", "수다 떨기", "영화 보기", "카페 가기", "운동하기", "쇼핑", "피시방 가기", "놀러 가기", "드라이브 가기", "공부하기", "일하기", "게임하기", "여행 가기", "등산하기", "전시회 가기"]
         return random.choice(activities)
    elif placeholder_type == '<PLACE_CASUAL>':
         places = ["강남", "홍대", "을지로", "집 앞", "회사 근처", "학교 앞", "cgv", "스타벅스", "우리 동네", "거기", "여기", "영화관", "카페", "공원", "서점", "백화점", "쇼핑몰", "미술관", "박물관"]
         return random.choice(places)
    elif placeholder_type == '<LOCATION_CASUAL>':
         locations = ["서울", "부산", "제주도", "해외", "여기", "거기", "집", "학교", "회사", "동네", "XX시", "XX구", "XX동"]
         return random.choice(locations)
    elif placeholder_type == '<ABBREVIATION_GREETING>':
         greetings = ["ㅎㅇ", "ㅂㄱ", "ㅇㄴ"]
         return random.choice(greetings)
    elif placeholder_type == '<ABBREVIATION_QUESTION>':
         questions = ["ㄱㅊ?", "ㅇㄸ?", "ㅁㅎ?", "ㅇㄷㅇ?", "ㅃㅃ?", "ㅎㄱ?", "ㅇㄷ?", "ㅇㅌ?"] 
         return random.choice(questions)
    elif placeholder_type == '<ABBREVIATION_OK>':
         oks = ["ㅇㅋ", "ㅇㅇ", "ㄱㄱ", "콜", "ㅇㅈ", "ㅇㅇㅇ"] 
         return random.choice(oks)
    elif placeholder_type == '<WEATHER_CASUAL>':
         weathers = ["추워", "더워", "비 와", "눈 와", "습해", "건조해", "미세먼지 심해", "날씨 좋아", "쌀쌀해", "따뜻해"]
         return random.choice(weathers)
    elif placeholder_type == '<REACTION_WEATHER>':
         reactions = ["ㅠㅠ", "좋다", "싫다", "조심해", "힘들다", "나가기 싫다", "나가고 싶다"]
         return random.choice(reactions)
    elif placeholder_type == '<DAILY_ROUTINE_ACTION>':
         actions = ["밥 먹는 중", "출근 중", "퇴근 중", "자러 가는 중", "쉬는 중", "운동하는 중", "공부하는 중", "일하는 중", "씻는 중", "준비 중", "이동 중", "밥 먹었어", "자고 있어", "깨어 있어"]
         return random.choice(actions)
    elif placeholder_type == '<EMOTION_TIRED>': # 누락 플레이스홀더 처리
         emotions = ["피곤해", "졸려", "힘들어", "지쳤어", "녹초야", "힘들다", "피곤하다"] 
         return random.choice(emotions)
    elif placeholder_type == '<STATE_TIRED>':
         states = ["피곤하다", "힘들다", "졸리다", "지친다", "빡세다", "피곤하다"] 
         return random.choice(states)
    elif placeholder_type == '<EVENT_CASUAL>':
         events = ["데이트", "약속", "모임", "친구 만나는 거", "소개팅", "번개"]
         return random.choice(events)
    elif placeholder_type == '<PLACE_MEETING>':
         places = ["카페", "식당", "역 앞", "집 근처", "회사 로비", "OO 건물 앞", "OO 출구"]
         return random.choice(places)
    elif placeholder_type == '<ADJECTIVE_CASUAL>': # 누락 플레이스홀더 처리
        adjectives = ["어렵네", "쉽네", "재밌네", "별로네", "좋네", "힘드네", "괜찮네"]
        return random.choice(adjectives)
    elif placeholder_type == '<PHOTO_TYPE>': # 누락 플레이스홀더 처리
        types = ["사진", "셀카", "풍경 사진", "음식 사진", "같이 찍은 사진"]
        return random.choice(types)
    elif placeholder_type == '<RESTAURANT_NAME>': # 누락 플레이스홀더 처리
        names = ["OO 식당", "XX 카페", "OO 맛집", "XX 빵집", "OO 레스토랑", "XX 술집"]
        return random.choice(names)
    elif placeholder_type == '<FOOD_TYPE>': # 누락 플레이스홀더 처리
        types = ["파스타", "스테이크", "커피", "빵", "케이크", "떡볶이", "피자", "치킨", "햄버거", "초밥", "삼겹살"]
        return random.choice(types)
    elif placeholder_type == '<REVIEW_PHRASE>': # 누락 플레이스홀더 처리
        phrases = ["진짜 맛있어", "분위기 좋아", "최고야", "추천해", "별로였어", "괜찮더라", "줄 서서 먹더라"]
        return random.choice(phrases)

    # 가족 관련 플레이스홀더
    elif placeholder_type == '<FAMILY_MEMBER_HONORIFIC>':
         members = ["엄마", "아빠", "어머니", "아버지"]
         return random.choice(members)
    elif placeholder_type == '<MEAL>':
         meals = ["아침", "점심", "저녁", "야식", "아점", "브런치", "밥", "식사", "간단히"]
         return random.choice(meals)
    elif placeholder_type == '<COOKING_ACTION>':
         actions = ["해?", "먹어?", "차려?", "준비됐어?"]
         return random.choice(actions)
    elif placeholder_type == '<FAMILY_MEMBER_CASUAL>':
         members = ["오빠", "언니", "동생", "아들", "딸", "자기야"]
         return random.choice(members)
    elif placeholder_type == '<FAMILY_MEMBER_CASUAL_DAD>': # 누락 플레이스홀더 처리
         return "아빠"
    elif placeholder_type == '<SCHOOL_PLAN>': # 누락 플레이스홀더 처리
         plans = ["학교", "학원", "오늘 뭐 할 거야", "오늘 계획이 뭐야", "오늘 수업은?"]
         return random.choice(plans)
    elif placeholder_type == '<PROGRESS_VERB>': # 누락 플레이스홀더 처리
        verbs = ["갔어?", "했어?", "마쳤어?"]
        return random.choice(verbs)
    elif placeholder_type == '<ITEM>': # 누락 플레이스홀더 처리
         items = ["우유", "빵", "휴지", "과일", "물", "두부", "라면", "김치", "계란", "생수", "간식", "반찬", "약", "음료수", "과자", "커피", "먹을 거"]
         return random.choice(items)
    elif placeholder_type == '<REQUEST_ACTION_FAMILY>': # 누락 플레이스홀더 처리
         actions = ["사다", "가져다", "사와", "가져와"]
         return random.choice(actions)
    elif placeholder_type == '<RELATIVE_HONORIFIC>': # 누락 플레이스홀더 처리
         relatives = ["할머니", "할아버지", "외할머니", "외할아버지", "친할머니", "친할아버지", "이모", "삼촌", "고모", "고모부", "이모부"]
         return random.choice(relatives)
    elif placeholder_type == '<GREETING_LONG>': # 누락 플레이스홀더 처리
        greetings = ["안부"]
        return random.choice(greetings)
    elif placeholder_type == '<ACTION_PHONE>': # 누락 플레이스홀더 처리
         actions = ["드렸", "했", "걸었"]
         return random.choice(actions)
    elif placeholder_type == '<MEET_ACTION_FAMILY>': # 누락 플레이스홀더 처리
         actions = ["집에서", "학교에서", "여기서"]
         return random.choice(actions)
    elif placeholder_type == '<PARTNER_HONORIFIC>': # 누락 플레이스홀더 처리
         hon = ["자기", "여보"]
         return random.choice(hon)
    elif placeholder_type == '<CONDITION_CHILD>': # 누락 플레이스홀더 처리
         conditions = ["학교 어땠어?", "오늘 뭐 배웠어?", "몸은 괜찮아?", "숙제 다 했어?", "오늘 하루 어땠어?"]
         return random.choice(conditions)
    elif placeholder_type == '<CONDITION_RELATIVE_QUESTION>': # 누락 플레이스홀더 처리
         conditions = ["건강 어떠셔?", "별일 없으셔?", "잘 지내셔?", "아프신 데는 없으셔?"]
         return random.choice(conditions)
    elif placeholder_type == '<STATUS_HOME>': # 누락 플레이스홀더 처리
         status = ["문 잘 잠겼는지", "가스 불 껐는지", "창문 닫았는지", "보일러 껐는지"]
         return random.choice(status)
    elif placeholder_type == '<CHECK_ACTION_FAMILY>': # 누락 플레이스홀더 처리
         actions = ["확인해", "봐줘", "점검해줘"]
         return random.choice(actions)
    elif placeholder_type == '<SHOP_FAMILY>': # 누락 플레이스홀더 처리
         shops = ["마트", "시장", "슈퍼"]
         return random.choice(shops)
    elif placeholder_type == '<ACTION_EAT>': # 누락 플레이스홀더 처리
         actions = ["먹었어?", "먹었니?", "먹었냐?", "드셨어요?"]
         return random.choice(actions)
    elif placeholder_type == '<OBJECT>': # 누락 플레이스홀더 처리
         objects = ["우산", "충전기", "책", "리모컨", "가방", "지갑", "열쇠", "안경", "모자", "이어폰"]
         return random.choice(objects)
    elif placeholder_type == '<REMEMBER_QUESTION>': # 누락 플레이스홀더 처리
        questions = ["기억나?", "어디에 뒀는지 알아?", "본 적 있어?"]
        return random.choice(questions)
    elif placeholder_type == '<ACTION_USE_COMPLETE>': # 누락 플레이스홀더 처리
        actions = ["다 먹었어", "다 썼어", "다 마셨어"]
        return random.choice(actions)
    elif placeholder_type == '<PLACE_FAMILY>': # 누락 플레이스홀더 처리
        places = ["병원", "마트", "학원", "집", "친척 집"]
        return random.choice(places)
    elif placeholder_type == '<MOVE_ACTION_FAMILY>': # 누락 플레이스홀더 처리
        actions = ["갈게", "데려다줄게", "모시러 갈게", "바래다줄게"]
        return random.choice(actions)
    elif placeholder_type == '<ACTION_HOUSEHOLD>': # 누락 플레이스홀더 처리
        actions = ["청소", "빨래", "설거지", "분리수거"]
        return random.choice(actions)
    elif placeholder_type == '<STATUS_HOUSEHOLD>': # 누락 플레이스홀더 처리
        status = ["다 했어", "끝냈어", "처리했어"]
        return random.choice(status)
    elif placeholder_type == '<PREPARATION_QUESTION>': # 누락 플레이스홀더 처리
        questions = ["준비됐어?", "다 됐어?", "다 차렸어?"]
        return random.choice(questions)
    elif placeholder_type == '<LOCATION_FAMILY>': # 누락 플레이스홀더 처리
         locations = ["집", "냉장고", "부엌", "거실", "내 방"]
         return random.choice(locations)
    elif placeholder_type == '<FOOD>': # 누락 플레이스홀더 처리
         foods = ["김치찌개", "된장찌개", "카레", "냉면", "치킨", "피자", "족발", "보쌈", "파스타", "삼겹살", "샐러드", "볶음밥", "김밥", "떡볶이", "국", "반찬", "과일"]
         return random.choice(foods)
    elif placeholder_type == '<EXISTENCE_PHRASE>': # 누락 플레이스홀더 처리
        phrases = ["있으니", "준비돼 있으니"]
        return random.choice(phrases)
    elif placeholder_type == '<ENCOURAGEMENT_FAMILY>': # 누락 플레이스홀더 처리
         encouragements = ["걱정 말고", "신경 쓰지 말고", "맘 편히"]
         return random.choice(encouragements)
    elif placeholder_type == '<WEATHER_FAMILY>': # 누락 플레이스홀더 처리
         weather_conditions = ["추우니까", "더우니까", "비 오니까", "눈 오니까", "날씨 안 좋으니까"]
         return random.choice(weather_conditions)
    elif placeholder_type == '<CLOTHING>': # 누락 플레이스홀더 처리
         clothing_suggestions = ["옷 따뜻하게", "옷 시원하게", "우산 챙겨서", "얇게 여러 겹"]
         return random.choice(clothing_suggestions)
    elif placeholder_type == '<FAMILY_PLAN>': # 누락 플레이스홀더 처리
         plans = ["여행", "대청소", "가족 외식", "영화 보기", "캠핑", "나들이", "집에서 쉬기"]
         return random.choice(plans)
    elif placeholder_type == '<REACTION_FAMILY>': # 누락 플레이스홀더 처리
         reactions = ["재밌었어", "힘들었어", "괜찮았어", "별로였어", "좋았어", "나빴어"]
         return random.choice(reactions)
    elif placeholder_type == '<EVENT_FAMILY>': # 누락 플레이스홀더 처리
         events = ["학교에서 발표", "회사에서 회식", "친구랑 약속", "병원 진료", "수업", "오늘 있었던 일"]
         return random.choice(events)
    elif placeholder_type == '<ACTION_CHILD>': # 누락 플레이스홀더 처리
        actions = ["챙겨", "가져가"]
        return random.choice(actions)
    elif placeholder_type == '<EXISTENCE_QUESTION_FAMILY>': # 누락 플레이스홀더 처리
        questions = ["없어?", "있니?"]
        return random.choice(questions)


    # 업무 관련 플레이스홀더
    elif placeholder_type == '<GREETING_WORK>':
         greetings = ["안녕하세요", "안녕하십니까", "수고하십니다"]
         return random.choice(greetings)
    elif placeholder_type == '<POSITION>':
         positions = ["팀장", "부장", "과장", "대리", "주임", "선임", "책임", "수석", "프로님", "매니저님", "님"]
         return random.choice(positions)
    elif placeholder_type == '<MEETING_TIME>': 
         hours = [str(h) for h in range(9, 20)] 
         minutes = ["00", "15", "30", "45"]
         return f"{random.choice(hours)}시 {random.choice(minutes)}분"
    elif placeholder_type == '<MEETING_PURPOSE>':
         purposes = ["금일", "주간", "월간", "긴급", "프로젝트", "서비스", "운영", "업무 보고", "진행 상황 공유", "이슈 논의"]
         return random.choice(purposes)
    elif placeholder_type == '<PROJECT>':
         projects = ["신규 서비스 개발", "마케팅 전략 수립", "영업 실적 분석", "IT 시스템 구축", "HR 관리 개선", "UI/UX 개선", "고객 만족도 조사", "OO 프로젝트"]
         return random.choice(projects)
    elif placeholder_type == '<DOCUMENT_TYPE>':
         docs = ["보고서", "회의록", "발표 자료", "기획안", "견적서", "계약서 초안", "제안서", "설명서", "요약본", "참고 자료", "결과 보고서", "계획서"]
         return random.choice(docs)
    elif placeholder_type == '<CLOSING_WORK>':
         closings = ["감사합니다", "확인 부탁드립니다", "수고하십시오", "네, 알겠습니다", "문의사항 있으면 언제든 연락 주세요", "좋은 하루 되십시오", "검토 부탁드립니다", "빠른 확인 부탁드립니다", "잘 부탁드립니다"]
         return random.choice(closings)
    elif placeholder_type == '<REPORT_TYPE>':
         reports = ["진행 상황", "중간 보고", "결과 보고", "일일 보고", "주간 보고", "월간 보고", "최종 보고", "요약 보고"]
         return random.choice(reports)
    elif placeholder_type == '<ACTION_WORK>':
         actions = ["회신", "전달", "확인", "처리", "반영", "검토", "업데이트", "공유", "작성", "수정", "마무리", "점검"]
         return random.choice(actions)
    elif placeholder_type == '<COMMUNICATION_TYPE_WORK>':
         types = ["이메일", "메시지", "전화", "문자", "메신저"]
         return random.choice(types)
    elif placeholder_type == '<STATE_WORK>':
         states = ["늦었습니다", "어렵습니다", "가능합니다", "어려울 것 같습니다", "가능할 것 같습니다"]
         return random.choice(states)
    elif placeholder_type == '<ACTION_WORK_AFTER_HOURS>': # 누락 플레이스홀더 처리
         actions = ["퇴근 후 확인", "업무 시간 외 처리", "귀가 후 검토", "퇴근 후 진행"]
         return random.choice(actions)
    elif placeholder_type == '<ACTION_DOCUMENT>': # 누락 플레이스홀더 처리
         actions = ["확인", "검토", "작성", "수정", "제출"]
         return random.choice(actions)
    elif placeholder_type == '<OPINION_REQUEST>': # 누락 플레이스홀더 처리
         requests = ["의견", "피드백", "검토 결과", "확인 결과", "코멘트"]
         return random.choice(requests)
    elif placeholder_type == '<DAY_WORK>': # 누락 플레이스홀더 처리
         days = ["월요일", "화요일", "수요일", "목요일", "금요일"]
         return random.choice(days)
    elif placeholder_type == '<DELIVERY_ITEM>': # 누락 플레이스홀더 처리
         items = ["샘플", "계약서", "제품 카탈로그", "견적서", "발주서", "자료", "시제품", "서류", "기자재"]
         return random.choice(items)
    elif placeholder_type == '<ACTION_URGENT>': # 누락 플레이스홀더 처리
         actions = ["즉시 확인", "빠른 처리", "긴급 조치", "우선 검토", "바로 확인"]
         return random.choice(actions)
    elif placeholder_type == '<DURATION>': # 누락 플레이스홀더 처리
         durations = ["일시적으로", "잠시", "오전 중", "오후 중", "예정입니다", "동안", "당분간"]
         return random.choice(durations)
    elif placeholder_type == '<LOCATION_WORK>': # 누락 플레이스홀더 처리
         locations = ["회의실", "사무실", "탕비실", "로비", "접견실", "제1 회의실", "본사", "지사", "회의실"] # 반복
         return random.choice(locations)
    elif placeholder_type == '<EVENT_WORK>': # 누락 플레이스홀더 처리
         events = ["사내 행사", "정기 교육", "팀 워크샵", "신년회", "종무식", "세미나", "발표회", "워크숍", "강의", "세미나"] # 반복
         return random.choice(events)
    elif placeholder_type == '<REQUEST_ITEM>': # 누락 플레이스홀더 처리
         items = ["휴가 신청", "보고서", "지출 결의", "출장 신청", "업무 요청", "승인 요청", "결재 서류"]
         return random.choice(items)
    elif placeholder_type == '<SUBJECT_WORK>': # 누락 플레이스홀더 처리
         subjects = ["자료 요청", "문의 사항", "긴급 이슈", "일정 조율", "협업 제안", "업무 협조 요청", "미팅 요청", "보고", "승인 요청"]
         return random.choice(subjects)
    elif placeholder_type == '<ACTION_FINISH_WORK>': # 누락 플레이스홀더 처리
        actions = ["마감했습니다", "종료했습니다", "끝났습니다"]
        return random.choice(actions)
    elif placeholder_type == '<GREETING_WORK_SHORT>': # 누락 플레이스홀더 처리
        greetings = ["뵙겠습니다", "뵙죠", "뵐게요"]
        return random.choice(greetings)
    elif placeholder_type == '<ACTION_TASK_COMPLETE>': # 누락 플레이스홀더 처리
        actions = ["완료", "완료했음", "마무리했음"]
        return random.choice(actions)
    elif placeholder_type == '<CLOSING_WORK_GRATITUDE>': # 누락 플레이스홀더 처리
        closings = ["감사합니다", "고맙습니다", "잘 받았습니다", "확인했습니다. 감사합니다."]
        return random.choice(closings)
    elif placeholder_type == '<AVAILABILITY_PHRASE>': # 누락 플레이스홀더 처리
        phrases = ["완료 가능합니다", "가능할 것 같습니다", "마무리될 예정입니다", "될 것 같습니다"]
        return random.choice(phrases)
    elif placeholder_type == '<SCHEDULE_ITEM>': # 누락 플레이스홀더 처리
        items = ["미팅", "회의", "발표", "교육", "출장"]
        return random.choice(items)
    elif placeholder_type == '<ACTION_MEETING_CHANGE>': # 누락 플레이سholder 추가
        actions = ["변경", "취소", "연기"]
        return random.choice(actions)
    elif placeholder_type == '<STATUS_TASK>': # 누락 플레이스홀더 추가
        status = ["완료했음", "진행 중", "마무리 단계", "시작 전"]
        return random.choice(status)
    elif placeholder_type == '<ACTION_FILE>': # 누락 플레이스홀더 추가
        actions = ["업로드", "다운로드", "공유", "첨부"]
        return random.choice(actions)
    elif placeholder_type == '<ISSUE_WORK>': # 누락 플레이스홀더 처리
         issues = ["서버 장애", "네트워크 문제", "시스템 오류", "결제 오류", "로그인 문제", "개인 정보 변경", "계정 보안 문제", "이용 제한"]
         return random.choice(issues)
    elif placeholder_type == '<SERVICE_WORK>': # 누락 플레이스홀더 처리
         services = ["로그인", "결제", "게시판", "검색", "푸시 알림", "본인 인증", "계좌 이체", "비밀번호 변경"]
         return random.choice(services)


    # 알림/정보 관련 플레이스홀더
    elif placeholder_type == '<PRODUCT>': # 누락 플레이스홀더 처리
        products = ["상품", "주문품", "물품", "제품", "서비스", "아이템"]
        return random.choice(products)
    elif placeholder_type == '<DELIVERY_STATUS>': # 누락 플레이스홀더 처리
        statuses = ["배송 중", "배송 완료", "배송 지연", "방문 예정", "출고 완료", "도착", "수거 완료", "집화 완료"]
        return random.choice(statuses)
    elif placeholder_type == '<BANK>': # 누락 플레이스홀더 처리
         banks = ["우리", "국민", "신한", "하나", "카카오", "농협", "기업", "새마을금고", "우체국", "SC제일", "씨티", "산업은행", "대구은행", "부산은행", "광주은행", "제주은행", "전북은행", "경남은행"] + ["우리은행", "국민은행", "신한은행", "하나은행", "NH농협은행", "카카오뱅크", "IBK기업은행"] 
         return random.choice(banks)
    elif placeholder_type == '<ACCOUNT_TYPE>': # 누락 플레이스홀더 처리
         types = ["계좌", "카드", "통장", "체크카드", "신용카드", "입출금 계좌", "적금 계좌", "대출 계좌"]
         return random.choice(types)
    elif placeholder_type == '<CARD_TYPE>': # 누락 플레이스홀더 처리
         types = ["신용", "체크", "법인", "개인"] + ["oo 카드"] 
         return random.choice(types)
    elif placeholder_type == '<SHOP>': # 누락 플레이스홀더 처리
         shops = ["스타벅스", "다이소", "쿠팡", "배달의민족", "지마켓", "옥션", "네이버쇼핑", "동네마트", "온라인 스토어", "백화점", "대형마트", "편의점", "올리브영", "다이소", "PC방", "극장", "병원", "약국", "미용실", "식당"] 
         return random.choice(shops)
    elif placeholder_type == '<SERVICE_NAME>': # 누락 플레이스홀더 처리
         services = ["미용실", "병원", "식당", "피트니스 센터", "클리닉", "수리점", "세탁소", "영화관", "렌터카", "정비소", "학원", "도서관", "문화센터", "주민센터", "온라인 서비스", "모바일 뱅킹"]
         return random.choice(services)
    elif placeholder_type == '<INFORMATION_TYPE>': # 누락 플레이스홀더 처리
         types = ["공지사항", "새로운 게시물", "업데이트", "알림", "이벤트 소식", "긴급 안내", "필독 정보", "중요 안내", "점검 안내", "보안 안내"]
         return random.choice(types)
    elif placeholder_type == '<ACTION_APP>': # 누락 플레이스홀더 처리
         actions = ["확인", "보기", "설치", "업데이트", "실행", "접속", "이동", "바로가기"]
         return random.choice(actions)
    elif placeholder_type == '<MEMBERSHIP_TYPE>': # 누락 플레이스홀더 처리
         types = ["회원", "고객", "멤버십", "등급", "회원님", "고객님"]
         return random.choice(types)
    elif placeholder_type == '<GRADE>': # 누락 플레이스홀더 처리
         grades = ["VIP", "골드", "실버", "프리미엄", "VVIP", "우수 회원", "일반 회원", "패밀리 등급", "프렌즈 등급", "플래티넘"]
         return random.choice(grades)
    elif placeholder_type == '<ACTION_MEMBERSHIP>': # 누락 플레이스홀더 처리
         actions = ["상향", "변경", "조정", "업데이트", "달성", "되었습니다"]
         return random.choice(actions)
    elif placeholder_type == '<ITEM_TYPE>': # 누락 플레이스홀더 처리
         types = ["쿠폰", "포인트", "적립금", "할인권", "캐시", "마일리지", "상품권", "기프트콘"]
         return random.choice(types)
    elif placeholder_type == '<LEVEL>': # 누락 플레이스홀더 처리
         levels = ["좋음", "보통", "나쁨", "매우 나쁨", "안전", "주의", "경고", "심각", "매우 좋음", "약간 나쁨"]
         return random.choice(levels)
    elif placeholder_type == '<LOCATION>': # 누락 플레이스홀더 처리
         locations = ["강남구", "종로구", "부산 해운대", "우리 지역", "서울", "경기도", "전국", "XX시", "XX군", "XX구", "XX동", "XX로", "XX길", "XX아파트", "XX빌딩"] # 주소 구성 요소
         return random.choice(locations)
    elif placeholder_type == '<SUGGESTION>': # 누락 플레이스홀더 처리
         suggestions = ["마스크 착용 권장", "외출 자제 권고", "안전 운전하세요", "조심하세요", "우산 챙기세요", "더위 조심하세요", "추위 조심하세요", "건강 유의하세요"]
         return random.choice(suggestions)
    elif placeholder_type == '<WEATHER_CONDITION>': # 누락 플레이스홀더 처리
         conditions = ["맑음", "흐림", "비", "눈", "구름 많음", "안개", "소나기", "태풍", "황사", "강풍", "폭염", "한파"]
         return random.choice(conditions)
    elif placeholder_type == '<WEATHER_DETAIL>': # 누락 플레이스홀더 처리
         details = ["기온 XX도", "체감 온도 XX도", "강수량 XXmm", "바람 XXm/s"] 
         return details[0].replace("XX", str(random.randint(-10, 30))) 
    elif placeholder_type == '<EVENT_ALERT>': # 누락 플레이스홀더 처리
         events = ["이벤트", "세일", "교육", "웨비나", "점검", "업데이트", "긴급 알림", "정기 알림", "이용 안내"]
         return random.choice(events)
    elif placeholder_type == '<CIVIL_COMPLAINT_TYPE>': # 누락 플레이스홀더 처리
         types = ["전입 신고", "주차 위반", "민원 신청", "사실 증명 발급", "세금 신고", "출생 신고", "사망 신고", "혼인 신고"]
         return random.choice(types)
    elif placeholder_type == '<VIOLATION_TYPE>': # 누락 플레이스홀더 처리
         types = ["주정차 위반", "과속 위반", "신호 위반", "교통 법규 위반", "속도 위반", "음주 운전"]
         return random.choice(types)
    elif placeholder_type == '<TAX_TYPE>': # 누락 플레이스홀더 처리
         types = ["재산세", "종합소득세", "부가가치세", "주민세", "양도소득세", "상속세", "법인세", "소득세"]
         return random.choice(types)
    elif placeholder_type == '<EVENT_MILITARY>': # 누락 플레이스홀더 처리
         types = ["예비군", "민방위", "병무청"]
         return random.choice(types) + " 훈련" + random.choice([" 안내", " 소집"])
    elif placeholder_type == '<ELECTION_TYPE>': # 누락 플레이스홀더 처리
         types = ["대통령", "국회의원", "지방선거", "보궐선거"] + ["OO 선거"]
         return random.choice(types)
    elif placeholder_type == '<CHECKUP_TYPE>': # 누락 플레이스홀더 처리
         types = ["건강검진", "암 검진", "구강 검진", "영유아 검진", "국가 건강검진"]
         return random.choice(types)
    elif placeholder_type == '<DISASTER_TYPE>': # 누락 플레이스홀더 처리
         types = ["호우 경보", "폭염 주의보", "태풍 특보", "지진 발생", "산불 발생", "황사 경보", "대설 주의보", "강풍 경보"]
         return random.choice(types)
    elif placeholder_type == '<ACTION_DISASTER>': # 누락 플레이스홀더 처리
         actions = ["대피", "안전한 곳으로 이동", "주의", "대비", "행동 요령 확인"]
         return random.choice(actions)
    elif placeholder_type == '<APP_NAME>': # 누락 플레이스홀더 처리
         apps = ["카카오톡", "인스타그램", "유튜브", "쿠팡", "배달의민족", "토스", "카카오페이", "네이버", "구글"] + ["XX 앱", "OO 서비스 앱"] 
         return random.choice(apps)
    elif placeholder_type == '<NOTIFICATION_TYPE_APP>': # 누락 플레이스홀더 처리
         types = ["알림", "메시지", "새로운 게시물", "업데이트 알림", "이벤트 알림"]
         return random.choice(types)
    elif placeholder_type == '<COURIER_NAME>': # 누락 플레이스홀더 처리
        couriers = ["CJ대한통운", "한진택배", "우체국택배", "롯데택배", "로젠택배", "CU택배", "GS포스트"] + ["OO 택배"]
        return random.choice(couriers)
    elif placeholder_type == '<ORDER_NUMBER>': # 누락 플레이스홀더 처리
        return f"{random.randint(100000000, 999999999)}" + random.choice(["", "-A", "-B", "-01"]) 
    elif placeholder_type == '<POINT_GAIN>': # 누락 플레이스홀더 처리
        return str(random.randint(10, 50000)) + random.choice(["포인트", "점", "p"]) 
    elif placeholder_type == '<CLOSING_DATE>': # 누락 플레이스홀더 처리
         today = datetime.now()
         random_days_later = random.randint(1, 180) 
         target_date = today + timedelta(days=random_days_later)
         date_formats = [
             "%Y년 %m월 %d일", 
             "%m월 %d일", 
             "%m/%d", 
             "내일", "이번 주 <DAY_SHORT>요일", "다음 주 <DAY_SHORT>요일", "오늘" 
         ]
         chosen_format = random.choice(date_formats)
         if chosen_format in ["내일", "오늘"]: 
              return chosen_format
         elif "주 <DAY_SHORT>요일" in chosen_format:
              days_kr = ["월", "화", "수", "목", "금", "토", "일"]
              return chosen_format.replace("<DAY_SHORT>", random.choice(days_kr))
         return target_date.strftime(chosen_format)
    elif placeholder_type == '<PRIZE>': # 누락 플레이스홀더 처리
        prizes = ["포인트", "쿠폰", "할인", "상품권", "커피 쿠폰", "선물", "기프티콘", "치킨 쿠폰", "피자 쿠폰", "영화 티켓", "현금", "캐시"]
        return random.choice(prizes)
    elif placeholder_type == '<EVENT_NAME>': # 누락 플레이스홀더 처리
        names = ["럭키 추첨", "오늘의 특가", "선착순 할인", "봄 맞이 세일", "회원 전용 이벤트", "신규 가입 이벤트", "친구 초대 이벤트", "OO 기념 이벤트", "OO 페스티벌", "OO 대잔치"] + ["OO 이벤트"]
        return random.choice(names)
    elif placeholder_type == '<TIP_CONTENT>': # 누락 플레이스홀더 처리
         contents = ["건강 관리", "재테크", "업무 효율", "요리", "육아", "여행", "청소", "정리 수납", "사진 촬영", "영상 편집", "꿀팁"]
         return random.choice(contents)
    elif placeholder_type == '<FORTUNE_CONTENT>': # 누락 플레이스홀더 처리
         fortunes = [
             "오늘은 재물운이 따르는 하루입니다.", "애정운이 상승하니 좋은 만남이 있을 수 있습니다.", 
             "학업/업무에서 노력한 만큼 좋은 결과가 따릅니다.", "건강에 유의하고 휴식을 취하세요.",
             "작은 행운이 찾아올 것입니다. 기대해도 좋습니다.", "스트레스 관리가 중요한 하루입니다.",
             "계획대로 술술 풀리는 하루가 될 것입니다.", "뜻밖의 좋은 소식을 들을 수 있습니다."
         ]
         return random.choice(fortunes)
    elif placeholder_type == '<DISCOUNT_RATE>': # 누락 플레이스홀더 처리
         rates = [str(random.randint(5, 50)), str(random.randint(5, 9)) + "0", "최대 " + str(random.randint(50, 99)), "XX%", "XX%"] 
         chosen_rate = random.choice(rates)
         if chosen_rate == "XX%": return f"{random.randint(5, 99)}%"
         return chosen_rate
    elif placeholder_type == '<POINT_CHECK_LINK>': # 누락 플레이스홀더 처리
         point_domains = ["point.example.com", "member.shoppingmall.com/point", "mypage.service.com/point"]
         base_url = f"https://{random.choice(point_domains)}/check/{uuid.uuid4().hex[:random.randint(8, 12)]}"
         if random.random() < 0.4:
             short_domains = ["bit.ly", "goo.gl", "t.co", "me2.do", "c11.kr"] 
             return f"http://{random.choice(short_domains)}/{uuid.uuid4().hex[:random.randint(4, 10)]}"
         return base_url.replace("http://", random.choice(["http://", "https://"]))

    elif placeholder_type == '<SIGNUP_LINK>': # 누락 플레이스홀더 처리
         signup_domains = ["signup.example.com", "join.myservice.co.kr", "member.company.org", "register.service.com"]
         base_url = f"https://{random.choice(signup_domains)}/register?code={uuid.uuid4().hex[:random.randint(8, 12)]}"
         if random.random() < 0.4:
             short_domains = ["bit.ly", "goo.gl", "t.co", "me2.do", "c11.kr"] 
             return f"http://{random.choice(short_domains)}/{uuid.uuid4().hex[:random.randint(4, 10)]}"
         return base_url.replace("http://", random.choice(["http://", "https://"]))
    
    elif placeholder_type == '<PRIZE_DELIVERY_INFO>': # 누락 플레이스홀더 처리
        infos = ["개별 안내 예정", "당첨자 발표 후 지급", "배송지 정보 확인 요청", "OO일까지 정보 입력 필요", "고객센터 문의"]
        return random.choice(infos)
    
    # 오류 수정
    elif placeholder_type == '<ACTION_FAMILY>':
         actions = ["먹어", "마셔", "확인해", "챙겨", "쉬어", "힘내", "봐줘", "점검해줘", "사다"]
         return random.choice(actions)

    elif placeholder_type == '<AVAILABILITY_QUESTION_WORK>':
         questions = ["가능하신가요?", "시간 되시나요?", "참석 가능하신가요?"]
         return random.choice(questions)

    elif placeholder_type == '<EXISTENCE_QUESTION_CASUAL>':
         questions = ["있어?", "없어?", "있니?", "없니?"]
         return random.choice(questions)
    elif placeholder_type == '<EMOTICON_TIRED>': 
         emotions = ["피곤해", "졸려", "힘들어", "지쳤어", "녹초야", "힘들다", "피곤하다"] 
         return random.choice(emotions)

    elif placeholder_type == '<TASK>':
         tasks = ["보고서 작성", "데이터 분석", "고객 미팅", "발표 자료 준비", "회의록 정리", "자료 조사", "업무 처리"]
         return random.choice(tasks)

    # 이모티콘/구두점/감탄사 등
    elif placeholder_type == '<EMOTICON>':
        emoticons = ["😊", "👍", "😂", "🙏", "❤️", "🔥", "✨", "🎉", "🤔", "^^", "ㅎㅎ", "ㅋㅋ", "ㅠㅠ", "😭😭", "👍👍", "❤️❤️", "✨✨", "🎉🎉", ":)", ":(", ":D", ";)", ";p", "😊😊", "ㅋㅋㅋ", "😂😂", ""] 
        return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_POSITIVE>':
         emoticons = ["😊", "👍", "❤️", "✨", "🎉", ":)", ":D", "굿", "최고", "😍", "🤩"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_HAPPY>':
         emoticons = ["😂", "ㅋㅋㅋ", "ㅎㅎ", "😊", ":D", "👍", "🤣", "배꼽 빠짐", "넘 웃겨"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_OK>':
         emoticons = ["ㅇㅇ", "👍", "👌", ":)", "^^", "ㅇㅋ", "넵"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_REQUEST>':
         emoticons = ["🙏", "🥺", "😭", "ㅠㅠ", "플리즈", "부탁", "제발"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_LOVE>':
         emoticons = ["❤️", "😍", "😘", "💕", "💖", "🥰"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_MILD>':
         emoticons = ["😊", "^^", ":)", ";)", "🤔", "😮", "😐"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_CHEER>':
         emoticons = ["파이팅", "힘내", "👍", "✨", "🔥", "아자아자"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_NOSTALGIA>':
         emoticons = ["😊", "ㅠㅠ", "😭", "🥺", "👍", "그립다", "옛날 생각"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_FUNNY>':
         emoticons = ["😂", "🤣", "ㅋㅋㅋ", "ㅎㅎ", "ㅠㅠ", "개웃겨", "짤", "밈"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_TRAVEL>':
         emoticons = ["✈️", "🚗", "🚌", "🚄", "🚂", "🚢", "🗺️"]
         return random.choice(emoticons)
    elif placeholder_type == '<EMOTICON_DAILY>':
         emoticons = ["😊", "👍", "✨", "💻", "📚", "🏋️‍♀️", "🍽️", "☕", "🏠", "🏢"]
         return random.choice(emoticons)

    elif placeholder_type == '<PUNCTUATION>':
        punctuations = ["!", "?", ".", "~", "!!!", "???", "~~~", "!?", "!!", "...", "..", "??!!", ".!", "??", "ㅎ", "ㅋ", "ㅠ"] 
        return random.choice(punctuations)
    elif placeholder_type == '<GREETING_CASUAL>':
        greetings = ["안녕하세요", "안녕하신가", "야!", "어이", "반가워", "수고!", "안녕", "왔어?", "ㅎㅇ", "ㅂㄱ", "ㅇㄴ", "안뇽", "방가방가"]
        return random.choice(greetings)
    elif placeholder_type == '<CLOSING_CASUAL>':
        closings = ["감사합니다", "그럼 이만", "안녕", "잘 가", "또 봐", "수고해", "좋은 하루 보내", "낼 봐", "담에 봐", "ㅂㅂ"]
        return random.choice(closings)
    elif placeholder_type == '<MEAL>':
         meals = ["아침", "점심", "저녁", "야식", "아점", "브런치", "밥", "식사", "간단히"]
         return random.choice(meals)
    elif placeholder_type == '<RESPONSE_SHORT_POSITIVE>': # 누락 플레이스홀더 처리
        responses = ["ㅇㅇ", "넵", "ㅇㅋ", "웅", "그래", "맞아", "응", "네네", "오키", "좋아", "콜"]
        return random.choice(responses)
    elif placeholder_type == '<RESPONSE_SHORT_NEGATIVE>': # 누락 플레이스홀더 처리
        responses = ["ㄱㅊ", "안돼", "어려워", "힘들어", "무리", "안될 것 같아", "괜찮아", "별로야"]
        return random.choice(responses)

    # 누락되었던 기타 플레이스홀더들
    elif placeholder_type == '<PHONENUM>': # 누락 플레이스홀더 처리
        # 다양한 형태의 전화번호
        formats = ["010-<NUMBER_MID>-<NUMBER_END>", "02-<NUMBER_SHORT>-<NUMBER_END>", "031-<NUMBER_SHORT>-<NUMBER_END>", "070-<NUMBER_MID>-<NUMBER_END>", "15<NUMBER_SHORT>", "16<NUMBER_SHORT>", "18<NUMBER_SHORT>", "051-<NUMBER_SHORT>-<NUMBER_END>", "053-<NUMBER_SHORT>-<NUMBER_END>"] # 지역번호 추가
        mid = str(random.randint(1000, 9999))
        end = str(random.randint(1000, 9999))
        short = str(random.randint(100, 999))
        
        chosen_format = random.choice(formats)
        if chosen_format == "010-<NUMBER_MID>-<NUMBER_END>":
            return f"010-{mid}-{end}"
        elif chosen_format.startswith("02-") or chosen_format.startswith("031-") or chosen_format.startswith("051-") or chosen_format.startswith("053-"):
             return f"{chosen_format[:3]}{short}-{end}"
        elif chosen_format == "070-<NUMBER_MID>-<NUMBER_END>":
            return f"070-{mid}-{end}"
        elif chosen_format.startswith("15") or chosen_format.startswith("16") or chosen_format.startswith("18"):
            return chosen_format[:2] + short # 1588, 1661 등 모방

    elif placeholder_type == '<ISSUE_WORK>': # 누락 플레이스홀더 처리
         issues = ["서버 장애", "네트워크 문제", "시스템 오류", "결제 오류", "로그인 문제", "개인 정보 변경", "계정 보안 문제", "이용 제한"]
         return random.choice(issues)
    elif placeholder_type == '<SERVICE_WORK>': # 누락 플레이스홀더 처리
         services = ["로그인", "결제", "게시판", "검색", "푸시 알림", "본인 인증", "계좌 이체", "비밀번호 변경"]
         return random.choice(services)
    elif placeholder_type == '<PRIZE_DELIVERY_INFO>': # 누락 플레이스홀더 처리
        infos = ["개별 안내 예정", "당첨자 발표 후 지급", "배송지 정보 확인 요청", "OO일까지 정보 입력 필요", "고객센터 문의"]
        return random.choice(infos)


    else:
        print(f"경고: 알 수 없는 플레이스홀더 타입: <{placeholder_type}>")
        return f"<{placeholder_type}>" # 알 수 없는 타입은 그대로 반환

def generate_normal_message():
    """랜덤한 정상 메시지를 생성하고 플레이스홀더를 대체합니다."""
    template = random.choice(normal_message_templates)
    
    # 정규식을 사용하여 모든 플레이스홀더 (<...>) 찾기
    placeholders_found = re.findall(r'<([^<>]+)>', template) 
    
    message = template
    # 플레이스홀더를 순회하며 대체. 동일한 플레이스홀더가 템플릿에 여러 번 있을 수 있으므로 모두 대체
    for placeholder_content in set(placeholders_found): 
        full_placeholder = f'<{placeholder_content}>' 
        
        # 동일한 플레이스홀더라도 호출될 때마다 다른 값을 생성하도록 generate_placeholder를 여기서 호출
        try:
            replacement_value = generate_placeholder(full_placeholder) 
        except KeyError as e:
             # generate_placeholder 내부에서 발생한 KeyError 처리
             print(f"경고: generate_placeholder 내부에서 오류 발생 - 알 수 없는 타입 {e}")
             replacement_value = full_placeholder # 대체 실패 시 원본 플레이스홀더 유지
        except Exception as e:
             print(f"경고: generate_placeholder 처리 중 예상치 못한 오류 발생 - {e} (타입: {full_placeholder})")
             replacement_value = full_placeholder # 대체 실패 시 원본 플레이스홀더 유지


        message = message.replace(full_placeholder, replacement_value) 

    # 생성된 메시지의 앞뒤 공백 제거 및 여러 공백 하나로 줄이기
    message = re.sub(r'\s+', ' ', message).strip()
    
    # 첫 글자를 대문자로 시작하거나, 소문자로 시작하는 등 문체 다양성 추가 고려 (필요시)
    # 예: message = message.capitalize() if random.random() > 0.3 else message

    return message 


# --- 3. 데이터 생성 및 파일 저장 ---

# 출력 폴더 생성 (없으면)
if not os.path.exists(output_directory):
    os.makedirs(output_directory)
    print(f"출력 폴더 '{output_directory}' 생성 완료.")


print(f"\n--- 정상 데이터 생성 시작 (총 {num_files}개 파일, 파일당 {messages_per_file}건) ---")

total_generated_messages = 0

for i in range(num_files):
    output_filename = os.path.join(output_directory, f"{output_filename_prefix}{i+1:02d}.csv") # 파일명에 0 채우기 (01~09)
    
    try:
        # CSV 파일 열기 (write mode, 인코딩 지정, 개행 문자는 OS 기본값 사용)
        # quoting=csv.QUOTE_ALL 옵션을 사용하여 모든 필드를 큰따옴표로 묶습니다.
        with open(output_filename, 'w', encoding=output_encoding, newline='') as csvfile:
            csv_writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL) 

            # 첫 줄 (헤더) 쓰기 - 요청 형식에 맞게 큰따옴표 없이
            csvfile.write("SEQ,CN\n") 

            print(f">>> 파일 '{output_filename}' 생성 중... ({i+1}/{num_files})")

            # 메시지 생성 및 쓰기
            for j in range(messages_per_file):
                seq_number = total_generated_messages + j + 1 
                
                message_content = generate_normal_message()
                
                csv_writer.writerow([str(seq_number), message_content])

                # 진행 상황 출력 (선택 사항)
                if (j + 1) % 10000 == 0:
                    print(f"    - {j + 1}/{messages_per_file} 건 작성 완료") 

            print(f">>> 파일 '{output_filename}' 작성 완료. 총 {messages_per_file} 건 생성.")
            total_generated_messages += messages_per_file

    except Exception as e:
        print(f"오류: 파일 '{output_filename}' 생성 중 오류 발생: {e}")
        if os.path.exists(output_filename):
             os.remove(output_filename)
             print(f"오류 발생 파일 '{output_filename}' 삭제 완료.")
        break 

print(f"\n--- 정상 데이터 생성 완료. 총 {total_generated_messages} 건 생성 ---")
print(f"파일 저장 경로: '{output_directory}'")
print("--- 스크립트 종료 ---")