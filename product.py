import re
import time
import joblib
import pandas as pd
import numpy as np
from selenium import webdriver
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from scipy.sparse import hstack

# --- 경로 설정 ---
vectorizer_load_path = 'data/tfidf_vectorizer/tfidf_vectorizer.pkl'
model_load_path = 'data/model/model.pkl'

label_map = {'Normal': 0, 'Smishing': 1}
reverse_label_map = {v: k for k, v in label_map.items()}

# --- 모델 로드 ---
try:
    vectorizer = joblib.load(vectorizer_load_path)
    model = joblib.load(model_load_path)
except FileNotFoundError as e:
    print(f"오류: 필요한 파일이 없습니다. '{e.filename}'")
    exit()
except Exception as e:
    print(f"오류 발생: {e}")
    exit()

# --- 전처리 함수 ---
okt = Okt()
def preprocess_text(text):
    korean_stopwords = ['의', '가', '이', '은', '는', '와', '과', '에게', '에서', '로', '으로', '하다', '이다', '되다', '있다']
    if not isinstance(text, str):
        return ""
    text = re.sub(r'https?://\S+|www\.\S+', '<URL>', text)
    text = re.sub(r'(\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{4})|(tel:\d+)', '<PHONENUM>', text)
    text = re.sub(r'\d{1,3}(,\d{3})*\s*원|\d+만원', '<AMOUNT>', text)
    text = re.sub(r'\d+', '<NUMBER>', text)
    text = re.sub(r'[^가-힣a-zA-Z<>\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return ""
    tokens = okt.morphs(text, stem=True)
    tokens = [word for word in tokens if word not in korean_stopwords and (len(word) > 1 or word in ['<URL>', '<PHONENUM>', '<AMOUNT>', '<NUMBER>'])]
    return ' '.join(tokens)

# --- 구조적 특징 추출 ---
def extract_structural_features_from_processed(processed_text):
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

    features['has_url_token'] = int(bool(url_tokens))
    features['has_phone_token'] = int(bool(phone_tokens))
    features['has_amount_token'] = int(bool(amount_tokens))
    features['has_number_token'] = int(bool(number_tokens))

    all_caps_words_proc = re.findall(r'\b[A-Z]+\b', processed_text)
    features['all_caps_word_count_proc'] = len(all_caps_words_proc)

    return pd.Series(features)


# 일반 URL + 단축 URL 패턴 포함
def extract_urls(message):
    url_pattern = r'(https?://[^\s,]+|www\.[^\s,]+)'
    urls = re.findall(url_pattern, message)
    return urls

# --- 스미싱 예측 함수 ---
def predict_smishing(raw_message):
    if not isinstance(raw_message, str):
        print(f"경고: 입력이 문자열이 아닙니다.")
        return "판별 불가", 0.0

    processed_message = preprocess_text(raw_message)
    structural_features = extract_structural_features_from_processed(processed_message).values.reshape(1, -1)
    text_features = vectorizer.transform([processed_message])
    X_combined = hstack([text_features, structural_features])
    label_id = model.predict(X_combined)[0]
    prob = model.predict_proba(X_combined)[0][model.classes_.tolist().index(1)]
    return reverse_label_map.get(label_id, '알 수 없음'), prob

# --- URL 실제 접속 검사 ---
def check_url_safety(urls):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    results = []

    for url in urls:
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(10)
            driver.get(url)
            time.sleep(3)
            source = driver.page_source.lower()

            # 간단한 악성 키워드 검색
            keywords = ['malware', 'phishing', 'warning', 'attack', 'blocked', 'hacked', 'suspicious']
            if any(keyword in source for keyword in keywords):
                results.append((url, '위험'))
            else:
                results.append((url, '안전'))
        except Exception as e:
            results.append((url, f'위험: 오류 발생 ({str(e)[:30]}...)'))
        finally:
            try:
                driver.quit()
            except:
                pass

    # 전체 판단: 하나라도 위험이면 '위험'
    overall = '위험' if any('위험' in r[1] for r in results) else '안전'
    return overall, results

# --- 사용자 인터페이스 ---
def main():
    print("스미싱 문자 및 링크 검사기")
    while True:
        msg = input("\n검사할 문자를 입력하세요 (종료: exit): ")

        if msg.lower() == 'exit':
            print("프로그램을 종료합니다.")
            break

        label, prob = predict_smishing(msg)  # '정상' 또는 '스미싱 의심'
        urls = extract_urls(msg)

        if urls:
            result, detail = check_url_safety(urls)
        else:
            result = 'URL 없음'
            detail = []

        # 결과 출력
        print("\n[메시지 분석 결과]")
        print(f"- 메시지 판단: {label}")
        print(f"- URL 추출: {urls if urls else '없음'}")
        print(f"- 링크 상태: {result}")
        for url, status in detail:
            print(f"  > {url} : {status}")

        # 종합 판단
        print("\n[최종 판단]")
        if label == '스미싱 의심' and result == '위험':
            print("매우 위험한 메시지입니다. 절대 클릭하지 마세요.")
        elif label == '스미싱 의심':
            print("스미싱 의심 메시지입니다. 주의하세요.")
        elif result == '위험':
            print("링크에 위험 요소가 있습니다. 클릭하지 마세요.")
        else:
            print("정상 메시지입니다.")

if __name__ == '__main__':
    main()