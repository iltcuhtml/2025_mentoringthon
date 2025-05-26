# 필요한 라이브러리 불러오기
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer 
# 모델 옵션 추가: Logistic Regression, Linear SVC, Multinomial Naive Bayes
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score
import joblib 
import os 
from scipy.sparse import hstack 
import numpy as np 
import re 

print("--- AI 모델 학습 시작 (processed_text에서 구조적 특징 추출, 튜닝/모델 옵션 포함) ---")

# --- 1. 설정 ---
# TODO: 이전 버전 preprocess_data.py에서 전처리된 데이터 .pkl 파일들이 저장된 폴더 경로를 설정해주세요.
# raw_text 컬럼이 포함되지 않은 .pkl 파일들이 있는 폴더 경로입니다.
processed_data_directory = 'data/processed_data' # 이전 preprocess_data.py의 output_processed_data_dir과 동일해야 함

# 최종 학습된 벡터라이저와 모델을 저장하고 불러올 파일 경로 설정
# 구조적 특징을 processed_text에서 추출했음을 반영하는 이름이 좋습니다.
final_vectorizer_save_path = 'data/tfidf_vectorizer/tfidf_vectorizer.pkl' # 파일 이름 변경
final_model_save_path = 'data/model/model.pkl'       # 파일 이름 변경

# TODO: 라벨 매핑 정보 (preprocess_data.py에서 라벨이 텍스트였고 변환했다면 사용한 것과 동일해야 함)
label_map = {'Normal': 0, 'Smishing': 1} 

# 2. 구조적 특징 추출 함수 (processed_text 기반)
# processed_text (토큰 대체된 텍스트)를 받아서 특징을 추출합니다.
def extract_structural_features_from_processed(processed_text):
    """
    전처리된 텍스트에서 구조적 특징들을 추출합니다. (raw_text 없을 경우 사용)
    정확도가 떨어질 수 있습니다.
    """
    if not isinstance(processed_text, str):
        # 학습 시 사용될 특징 개수에 맞게 0으로 채워진 Series 반환
        feature_names = ['message_length_proc', 'url_token_count', 'phone_token_count', 'amount_token_count', 
                         'number_token_count', 'special_chars_count_proc', 'all_caps_word_count_proc', 'has_url_token', 'has_phone_token', 'has_number_token'] 
        return pd.Series([0] * len(feature_names), index=feature_names)

    features = {}
    
    # 1. 전처리된 메시지 길이
    features['message_length_proc'] = len(processed_text)
    
    # 2. 플레이스홀더 토큰 개수 및 포함 여부
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
    features['has_amount_token'] = 1 if len(amount_tokens) > 0 else 0 # 이 특징은 TfidfVectorizer에도 포함되지만 중복 추가
    features['has_number_token'] = 1 if len(number_tokens) > 0 else 0 # 이 특징도 TfidfVectorizer에 포함되지만 중복 추가

    # 3. 특정 특수 문자 포함 여부 및 빈도 (전처리 후 텍스트 기준)
    # 전처리 함수에서 이미 대부분의 특수 문자를 제거했으므로, 의미 없을 수 있습니다.
    # 하지만 플레이스홀더 토큰 (<>)은 남아있으므로 이 패턴만 검사해 봅니다.
    special_chars_pattern_proc = r'[!@#$%^&*()_+=\[\]{};:\'",.<>/?\\|`~]' # 전처리 함수에서 제거한 패턴과 동일
    # 전처리 후에는 플레이스홀더 < > 만 남을 가능성이 높습니다.
    # <, > 자체의 개수를 세는 것은 의미 없을 수 있어 생략합니다.
    # 전처리 후 텍스트에 남아있을 수 있는 다른 특수 문자 패턴이 있다면 여기에 추가

    # 4. 모두 대문자인 단어 수 (전처리 후 텍스트 기준)
    # 전처리 후에는 토큰화되어 단어 구분이 명확할 수 있습니다.
    all_caps_words_proc = re.findall(r'\b[A-Z]+\b', processed_text) 
    features['all_caps_word_count_proc'] = len(all_caps_words_proc)
    
    # message_length_proc는 이미 위에서 계산함.

    # 특징 이름 순서 보장
    feature_names = ['message_length_proc', 'url_token_count', 'phone_token_count', 'amount_token_count', 
                         'number_token_count', 'has_url_token', 'has_phone_token', 'has_amount_token', 'has_number_token',
                         'all_caps_word_count_proc'] # 정의된 특징 이름 목록 나열

    # 실제로 추출된 특징만 반환 (keys() 순서는 보장되지 않을 수 있어 names로 순서 보장)
    return pd.Series(features)[feature_names]

# --- 3. 전처리 데이터 로드 및 합치기 ---

# 최종 벡터라이저와 모델 파일이 이미 존재하는지 확인 (학습 단계 전체 건너뛰기)
if os.path.exists(final_vectorizer_save_path) and os.path.exists(final_model_save_path):
    print(f"\n--- 기존 최종 벡터라이저 ('{final_vectorizer_save_path}') 및 모델 ('{final_model_save_path}')이 존재합니다. 학습 단계를 건너킵니다. ---")
    print("predict_with_model.py를 실행하여 예측을 수행할 수 있습니다.")
    exit() # sys.exit()
    
# 기존 최종 파일이 없으면 데이터를 불러와 합치고 벡터라이저를 학습
print("\n--- 기존 최종 모델 및 벡터라이저 파일이 없습니다. 데이터 로드, 합치기 및 벡터라이저 학습을 진행합니다. ---")

combined_df = pd.DataFrame() 
pkl_extension = '.pkl' 

if not os.path.isdir(processed_data_directory):
    print(f"오류: 전처리된 데이터 폴더 '{processed_data_directory}'가 존재하지 않습니다. preprocess_data.py를 먼저 실행해주세요.") # 오타 수정
    exit() # sys.exit()

pkl_files = [os.path.join(processed_data_directory, f) for f in os.listdir(processed_data_directory) if f.endswith(pkl_extension)]

if not pkl_files:
    print(f"오류: 폴더 '{processed_data_directory}'에 {pkl_extension} 파일이 없습니다. preprocess_data.py를 먼저 실행하여 파일을 생성해주세요.")
    exit() # sys.exit()

print(f"폴더 '{processed_data_directory}'에서 {len(pkl_files)}개의 {pkl_extension} 파일을 찾았습니다. 합치기 시작...")

# 데이터 합치기 과정 (시간이 소요될 수 있습니다)
# processed_text, label 컬럼만 불러옵니다 (raw_text는 없다고 가정)
columns_to_load = ['processed_text', 'label'] 

for pkl_file in pkl_files:
    try:
        df_part = pd.read_pickle(pkl_file)
        
        # 필요한 모든 컬럼이 있는지 확인
        if all(col in df_part.columns for col in columns_to_load):
             # 필요한 컬럼만 선택하여 합치기
             combined_df = pd.concat([combined_df, df_part[columns_to_load]], ignore_index=True)
        else:
             print(f"경고: '{pkl_file}' 파일에 필요한 모든 컬럼이 없습니다. 이 파일은 합치지 않습니다.")
             missing_cols = [col for col in columns_to_load if col not in df_part.columns]
             print(f"  누락된 컬럼: {missing_cols}")


    except Exception as e:
        print(f"오류: '{pkl_file}' 파일 불러오기/합치기 중 오류 발생: {e}")

if combined_df.empty:
    print("오류: 불러온 전처리된 데이터가 비어 있습니다. 모든 .pkl 파일 로드에 실패했거나 파일에 데이터가 없습니다. 프로그램을 종료합니다.")
    exit() # sys.exit()

print(f"\n--- 총 {len(combined_df)} 건의 전처리된 데이터 합치기 완료 ---")
print("합쳐진 데이터 확인 (처음 5개 행):")
print(combined_df.head())

# --- 합쳐진 전체 데이터의 라벨 분포 확인 (중요) ---
print(f"\n합쳐진 전체 데이터 라벨별 수:\n{combined_df['label'].value_counts()}")
print("--------------------------------------------")
# --- 합쳐진 전체 데이터의 라벨 분포 확인 끝 ---

# --- 4. 피처 추출 (텍스트 + processed_text에서 추출한 구조적 특징) ---
# 합쳐진 전체 데이터셋을 사용하여 하나의 TF-IDF 벡터라이저를 학습시킵니다.

# 벡터화에 사용할 텍스트 데이터와 라벨 분리
X_data_processed_text = combined_df['processed_text']
y_data = combined_df['label']

# TODO: LogisticRegression에서 요구하는 최소 클래스 수 (2)를 만족하는지 확인
if len(y_data.unique()) < 2:
    print("\n오류: 합쳐진 전체 데이터에 2개 미만의 클래스가 포함되어 있습니다.")
    print(f"확인된 클래스: {y_data.unique()}")
    print("preprocess_data.py 스크립트 설정(raw_data_sources)과 원본 데이터 파일을 다시 확인하여 정상 및 스미싱 데이터가 모두 로드/파싱되었는지 점검해주세요.")
    exit() # sys.exit()

# TfidfVectorizer 초기화 및 학습 (전체 데이터로 fit_transform)
print("\n--- 합쳐진 데이터로 TF-IDF 벡터라이저 학습 시작 ---")
# --- 최적화 포인트: max_features, min_df, ngram_range 값을 조절합니다. ---
vectorizer = TfidfVectorizer(
    min_df=1,         
    max_df=0.95,      
    ngram_range=(1, 2), 
    max_features=100000 
) 

# 전체 전처리된 텍스트 데이터에 맞춰 vectorizer 학습 및 변환
X_text_features = vectorizer.fit_transform(X_data_processed_text)

print(f"--- TF-IDF 피처 학습 및 변환 완료. 형태: {X_text_features.shape} ---")

# --- processed_text에서 구조적 특징 추출 ---
print("--- processed_text에서 구조적 특징 추출 시작 ---")
X_structural_features_df = X_data_processed_text.apply(extract_structural_features_from_processed)
X_structural_features = X_structural_features_df.values # DataFrame을 numpy 배열로 변환
print(f"--- 구조적 특징 추출 완료. 형태: {X_structural_features.shape} ---")

# TF-IDF 피처와 구조적 특징 합치기 (가로 방향으로)
X = hstack([X_text_features, X_structural_features]) 

print(f"--- 최종 피처 행렬 형태 (TF-IDF + 구조적 특징): {X.shape} ---")

# 최종 학습된 벡터라이저 저장 (텍스트 특징 변환에 사용)
# 구조적 특징 추출 로직 자체는 저장할 필요 없음.
try:
    joblib.dump(vectorizer, final_vectorizer_save_path)
    print(f"최종 TF-IDF 벡터라이저가 '{final_vectorizer_save_path}'에 성공적으로 저장되었습니다.")
except Exception as e:
     print(f"경고: 벡터라이저 저장 중 오류 발생: {e}")
     print("다음 실행 시 벡터라이저를 다시 학습하게 됩니다.")

# --- 5. 데이터 분割 (학습 세트와 테스트 세트) ---
# 최종 피처 행렬 X와 라벨 y_data 사용
X_train, X_test, y_train, y_test = train_test_split(X, y_data, test_size=0.2, random_state=42, stratify=y_data)

print(f"\n--- 데이터 분할 완료 ---")
print(f"학습 데이터 수: {X_train.shape[0]}, 특징 수: {X_train.shape[1]}")
print(f"테스트 데이터 수: {X_test.shape[0]}, 특징 수: {X_test.shape[1]}")

# --- 학습 데이터 라벨 분포 확인 (중요) ---
print(f"\n학습 데이터 라벨별 수:\n{pd.Series(y_train).value_counts()}")
print("--------------------------------------------")
# --- 학습 데이터 라벨 분포 확인 끝 ---

# 데이터 불균형 처리 고려 (필요 시) - 주석 처리된 상태 유지
# from imblearn.over_sampling import SMOTE 

# --- 6. AI 모델 선택, 하이퍼파라미터 튜닝 및 학습 ---
# 여러 모델과 하이퍼파라미터 조합을 시도합니다.

# TODO: 시도할 모델 선택 ('LogisticRegression', 'LinearSVC', 'MultinomialNB')
model_name_to_train = 'LogisticRegression' 

print(f"\n--- 모델 선택: {model_name_to_train} ---")

# 구조적 특징이 포함된 피처 행렬 (Dense 부분)은 음수 값을 가질 수 있습니다 (예: 메시지 길이 등은 음수 아님, 하지만 다른 특징 추가시).
# MultinomialNB는 음수 값을 처리하지 못하므로, NB 사용 시 Min-Max 스케일링 등으로 0 이상의 값으로 변환 필요.
# 현재 구조적 특징은 모두 0 이상의 값이므로 MultinomialNB 사용 가능하지만, 일반적으로 다른 모델이 더 적합.
if model_name_to_train == 'LogisticRegression':
    param_distributions = {
        'C': [0.001, 0.01, 0.1, 1, 10, 100], 
        'solver': ['liblinear'], 
        'class_weight': [None, 'balanced'] 
    }
    model_base = LogisticRegression(random_state=42, max_iter=2000, verbose=0) 
    n_iter_search = 20 

elif model_name_to_train == 'LinearSVC':
    param_distributions = {
        'C': [0.001, 0.01, 0.1, 1, 10, 100], 
        'class_weight': [None, 'balanced']
    }
    model_base = LinearSVC(random_state=42, max_iter=2000, dual=True, verbose=0) 
    n_iter_search = 20

elif model_name_to_train == 'MultinomialNB':
     model_base = MultinomialNB()
     # RandomizedSearchCV를 사용하지 않고 직접 모델 학습
     print("\n--- 모델 학습 시작 (Multinomial Naive Bayes) ---")
     if len(pd.Series(y_train).unique()) < 2:
         print("\n오류: 학습 데이터 세트(y_train)에 2개 미만의 클래스가 포함되어 있습니다.")
         exit() # sys.exit()
     
     # NB는 음수 특징값을 처리 못하므로, 구조적 특징 중 음수 값이 있다면 문제 발생 가능.
     # 현재 추출하는 구조적 특징은 모두 0 이상이므로 직접 사용 가능.
     model = model_base.fit(X_train, y_train)
     print("--- 모델 학습 완료 ---")
     # 하이퍼파라미터 튜닝 과정 건너뛰고 바로 평가/저장으로 이동
     best_model = model
     best_params = {}
     best_score = None 

else:
    print(f"오류: 알 수 없는 모델 이름 '{model_name_to_train}'")
    exit() # sys.exit()

# Randomized Search를 이용한 하이퍼파라미터 튜닝 (NB 제외)
if model_name_to_train != 'MultinomialNB':
    print(f"\n--- 하이퍼파라미터 튜닝 시작 ({n_iter_search}개 조합 탐색) ---")
    
    scorer = 'accuracy' 

    random_search = RandomizedSearchCV(
        estimator=model_base,
        param_distributions=param_distributions,
        n_iter=n_iter_search,
        scoring=scorer, 
        cv=3, 
        verbose=2, 
        random_state=42,
        n_jobs=-1 
    )

    try:
        random_search.fit(X_train, y_train)
        
        best_model = random_search.best_estimator_
        best_params = random_search.best_params_
        best_score = random_search.best_score_

        print("\n--- 하이퍼파라미터 튜닝 완료 ---")
        print(f"최적 파라미터: {best_params}")
        print(f"최적 교차 검증 스코어 ({scorer}): {best_score:.4f}")

        model = best_model 

    except Exception as e:
        print(f"\n오류: 하이퍼파라미터 튜닝 중 오류 발생: {e}")
        print("튜닝 없이 기본 모델로 다시 시도합니다.")
        
        if len(pd.Series(y_train).unique()) < 2:
             print("\n오류: 학습 데이터 세트(y_train)에 2개 미만의 클래스가 포함되어 있습니다.")
             exit() # sys.exit()
        
        if model_name_to_train == 'LogisticRegression':
             model_fallback = LogisticRegression(C=1.0, solver='liblinear', max_iter=2000, random_state=42, verbose=1, class_weight='balanced')
        elif model_name_to_train == 'LinearSVC':
             model_fallback = LinearSVC(C=1.0, random_state=42, max_iter=2000, dual=True, verbose=1, class_weight='balanced')
        
        model = model_fallback.fit(X_train, y_train)
        best_model = model 
        best_params = {} 
        best_score = None 

# --- 최종 모델 저장 ---
if 'model' in locals() and model is not None:
    try:
        joblib.dump(model, final_model_save_path) 
        print(f"최종 학습된 모델이 '{final_model_save_path}'에 성공적으로 저장되었습니다.")
    except Exception as e:
         print(f"경고: 최종 모델 저장 중 오류 발생: {e}")
         print("모델이 저장되지 않았습니다.")
else:
     print("\n오류: 최종 모델 객체가 생성되지 않아 저장할 수 없습니다.")

# --- 7. 모델 성능 평가 ---
if 'model' in locals() and model is not None: 
    print("\n--- 모델 예측 및 평가 ---")
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    try:
        _ = label_map 
        reverse_label_map = {v: k for k, v in label_map.items()}
    except NameError:
        reverse_label_map = {0: '0', 1: '1'} 

    if hasattr(model, 'classes_'):
        target_names = [reverse_label_map.get(cls, str(cls)) for cls in model.classes_]
    else:
         target_names = [reverse_label_map.get(0, '0'), reverse_label_map.get(1, '1')]

    report = classification_report(y_test, predictions, target_names=target_names)

    print(f"\n모델 정확도 (Accuracy): {accuracy:.4f}") 
    print("\n모델 분류 리포트:")
    print(report)
else:
    print("\n모델 학습에 실패하여 예측 및 평가를 건너뜁니다.")

print("\n--- AI 모델 학습 스크립트 종료 ---")