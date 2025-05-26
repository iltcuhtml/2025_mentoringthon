# 필요한 라이브러리 불러오기
import re
from konlpy.tag import Okt
import joblib
from scipy.sparse import hstack
import pandas as pd
import numpy as np

print("--- AI 모델 로드 및 예측 준비 (processed_text에서 구조적 특징 추출) ---")

# --- 1. 설정 ---
# TODO: train_model.py에서 최종 저장한 모델과 벡터라이저 파일 경로를 실제 경로로 변경해주세요.
vectorizer_load_path = 'data/tfidf_vectorizer/tfidf_vectorizer.pkl' # train_model.py에서 저장한 최종 벡터라이저
model_load_path = 'data/model/model.pkl' # train_model.py에서 저장한 최종 모델

# TODO: 라벨 매핑 정보 (학습 단계에서 사용한 것과 동일해야 함)
label_map = {'Normal': 0, 'Smishing': 1} 

# 라벨 매핑 정보가 있다면 사용, 없다면 기본값 설정
try:
    _ = label_map 
    reverse_label_map = {v: k for k, v in label_map.items()}
except NameError:
    reverse_label_map = {0: '0', 1: '1'} 

# --- 2. 저장된 최종 벡터라이저와 모델 불러오기 ---
try:
    vectorizer = joblib.load(vectorizer_load_path)
    model = joblib.load(model_load_path)
    print(f"최종 TF-IDF 벡터라이저 '{vectorizer_load_path}' 불러오기 완료. 특징 수: {len(vectorizer.vocabulary_)}")
    if hasattr(model, 'feature_names_in_'):
        print(f"최종 모델 학습 특징 개수: {len(model.feature_names_in_)}")
    print(f"최종 학습된 모델 '{model_load_path}' 불러오기 완료.")
    print("AI 모델 예측 준비 완료.")
except FileNotFoundError as e:
    print(f"오류: 필요한 최종 파일이 없습니다. '{e.filename}'")
    print("train_model.py를 먼저 성공적으로 실행하여 최종 파일을 생성해주세요.") # 메시지 수정
    exit() # sys.exit()
except Exception as e:
    print(f"최종 모델/벡터라이저 불러오기 중 오류 발생: {e}")
    exit() # sys.exit()

# --- 3. 데이터 전처리 함수 (processed_text 생성용 - preprocess_data.py와 동일) ---
okt = Okt() 

def preprocess_text(text):
    """
    텍스트 데이터 전처리 함수: 노이즈 제거 및 형태소 토큰화 후 문자열 반환.
    (preprocess_data.py의 텍스트 전처리 부분과 완전히 동일해야 합니다.)
    """
    korean_stopwords = ['의', '가', '이', '은', '는', '와', '과', '에게', '에게서', '에서', '로', '으로', '와', '으로', '하다', '이다', '되다', '있다', '에게', '입니다', '습니다'] 

    if not isinstance(text, str): 
        return ""

    text = re.sub(r'https?://\S+|www\.\S+', '<URL>', text)
    text = re.sub(r'(\d{2,4}[-\.\s]?\d{3,4}[-\.\s]?\d{4})|(tel:\d+)', '<PHONENUM>', text) 
    text = re.sub(r'\d{1,3}(,\d{3})*\s*원|\d+만원', '<AMOUNT>', text)
    text = re.sub(r'\d+', '<NUMBER>', text)

    text = re.sub(r'[^가-힣a-zA-Z<>\s]', ' ', text)

    text = re.sub(r'\s+', ' ', text).strip()

    if not text:
        return ""
    tokens = okt.morphs(text, stem=True) 
    tokens = [word for word in tokens if word not in korean_stopwords and (len(word) > 1 or word in ['<URL>', '<PHONENUM>', '<AMOUNT>', '<NUMBER>'])] 

    return ' '.join(tokens)

# 4. 구조적 특징 추출 함수 (processed_text 기반 - train_model.py와 동일)
def extract_structural_features_from_processed(processed_text):
    """
    전처리된 텍스트에서 구조적 특징들을 추출합니다. (raw_text 없을 경우 사용)
    정확도가 떨어질 수 있습니다.
    (train_model.py에 사용된 함수와 완전히 동일해야 합니다.)
    """
    if not isinstance(processed_text, str):
        feature_names = ['message_length_proc', 'url_token_count', 'phone_token_count', 'amount_token_count', 
                         'number_token_count', 'has_url_token', 'has_phone_token', 'has_amount_token', 'has_number_token',
                         'all_caps_word_count_proc'] 
        return pd.Series([0] * len(feature_names), index=feature_names)


    features = {}
    features['message_length_proc'] = len(processed_text)
    
    url_tokens = re.findall(r'<URL>', processed_text)
    phone_tokens = re.findall(r'<PHONENUM>', processed_text)
    amount_tokens = re.findall(r'<AMOUNT>', processed_text)
    number_tokens = re.findall(r'<NUMBER>', processed_text)

    features['url_token_count'] = len(url_tokens)
    features['phone_token_count'] = len(phone_tokens)
    features['amount_token_count'] = len(amount_tokens)
    features['number_token_count'] = len(number_tokens)

    features['has_url_token'] = 1 if len(url_tokens) > 0 else 0
    features['has_phone_token'] = 1 if len(phone_tokens) > 0 else 0
    features['has_amount_token'] = 1 if len(amount_tokens) > 0 else 0 
    features['has_number_token'] = 1 if len(number_tokens) > 0 else 0 

    all_caps_words_proc = re.findall(r'\b[A-Z]+\b', processed_text) 
    features['all_caps_word_count_proc'] = len(all_caps_words_proc)
    
    feature_names = ['message_length_proc', 'url_token_count', 'phone_token_count', 'amount_token_count', 
                         'number_token_count', 'has_url_token', 'has_phone_token', 'has_amount_token', 'has_number_token',
                         'all_caps_word_count_proc'] 
                         
    return pd.Series(features)[feature_names]


# 5. 스미싱 판별 함수 정의
def predict_smishing(raw_message): # 원본 raw 메시지를 입력으로 받습니다.
    """
    입력 문자 메시지가 스미싱인지 정상인지 판별하는 함수입니다.
    """
    if not isinstance(raw_message, str):
         print(f"경고: 입력이 문자열이 아닙니다.")
         return "판별 불가", 0.0

    # 1. 입력 메시지 전처리 (텍스트 특징 추출용)
    processed_message = preprocess_text(raw_message)
    
    # 2. 전처리된 메시지에서 구조적 특징 추출
    structural_features_series = extract_structural_features_from_processed(processed_message) # <-- processed_message 사용
    X_structural_features = structural_features_series.values.reshape(1, -1) 

    # 전처리 후 텍스트가 비어있다면 TF-IDF 벡터는 0 벡터가 됩니다.
    # 구조적 특징은 추출되었을 것입니다.
    X_text_features = vectorizer.transform([processed_message]) 

    # 3. 텍스트 피처와 구조적 특징 합치기
    X_combined = hstack([X_text_features, X_structural_features]) 

    # 4. 학습된 모델로 예측
    prediction_label_id = model.predict(X_combined)[0]
    
    predicted_label = reverse_label_map.get(prediction_label_id, '알 수 없음')

    # 스미싱일 확률도 함께 확인
    probabilities = model.predict_proba(X_combined)
    smishing_probability = probabilities[0][model.classes_.tolist().index(1)]

    return predicted_label, smishing_probability

# # --- 6. 예측 함수 실행 예시 ---
# # ... (예시 메시지 목록은 train_model.py와 동일하게 유지하거나 추가) ...

# print("\n--- 새로운 메시지 판별 예시 (raw_text 입력, processed_text에서 구조적 특징 추출) ---")

# test_messages = [
#     "안녕하세요. 오늘 하루도 힘내세요!", 
#     "[국외발신] 귀하의 계정이 도용되었습니다. 본인 확인 위해 https://suspicious.link/verify 즉시 접속바랍니다.", 
#     "축하합니다! 100만원 상금 당첨! 지금 바로 010-1234-5678 으로 연락하세요.", 
#     "다음주 모임 일정 다시 확인 부탁드려요.", 
#     "[Web발신] 최신 스마트폰 무료 지급 이벤트! 참여하려면 http://lucky-event.win/prize 클릭!", 
#     "택배 도착 예정입니다. 문 앞에 두고 가겠습니다.", 
#     "인증번호는 123456 입니다.", 
#     "안녕하세요 김철수님, 내일 3시에 회의 있습니다.", 
#     "[알림] 고객님 카드 5000원 사용 (스타벅스)", 
#     "이 사진 좀 봐봐 ㅋㅋ https://drive.google.com/file/d/abcdef12345/view", 
#     "택배 운송장번호 1234567890 조회: http://logistics.co.kr/track", 
#     "!!! 긴급 !!! 지금 바로 확인하세요 -> https://very-suspicious.co.kr", 
#     "OOO님께, 결제 오류 발생. 고객센터 070-5678-1234 연락 바랍니다.", 
#     "OOO에서 50000원 사용 승인되었습니다. 본인이 아닐 경우 즉시 신고하세요.", 
#     "안녕하세요? 잘 지내시죠? ^^", 
#     "점심 뭐 먹을지 정했어? ㅋㅋㅋ", 
#     "내일 오전 10시까지 보고서 제출 부탁드립니다.", 
#     "[알림] 새로운 메시지가 도착했습니다. 앱에서 확인하세요.", 
#     "무료쿠폰 지급! https://free-coupon.xyz 놓치지 마세요!", 
#     "00님, 안녕하세요. 주문번호 123456789 확인되었습니다.", 
# ]

# for msg in test_messages:
#     result, prob = predict_smishing(msg) 
#     print(f"'{msg}'")
#     if result == "판별 불가":
#          print(f" -> 판별 결과: {result}")
#     else:
#          print(f" -> 판별 결과: {result} (스미싱 확률: {prob:.2f})")
#     print("-" * 30)

# --- 새로운 메시지를 직접 입력받아 판별하는 루프 (선택 사항) ---
print("\n--- 직접 메시지 입력하여 판별하기 (종료: 'quit' 또는 'exit') ---")
while True:
    user_input = input("판별할 문자 메시지를 입력하세요 (종료: 'quit' 또는 'exit'): ")
    if user_input.lower() in ['quit', 'exit']:
        break
    result, prob = predict_smishing(user_input)
    if result == "판별 불가":
        print(f" -> 판별 결과: {result}")
    else:
        print(f" -> 판별 결과: {result} (스미싱 확률: {prob:.2f})")
    print("-" * 30)